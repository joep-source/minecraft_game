import logging
import random
import sys
from enum import Enum
from functools import lru_cache
from os import path
from typing import List

import numpy as np
from matplotlib import pyplot as plt
from ursina.camera import instance as camera
from ursina.color import color, gray, light_gray
from ursina.entity import Entity
from ursina.mouse import instance as mouse
from ursina.prefabs.button import Button
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.health_bar import HealthBar
from ursina.prefabs.sky import Sky
from ursina.scene import instance as scene
from ursina.texture_importer import load_texture
from ursina.ursinastuff import destroy
from ursina.window import instance as window

import conf
from block import Biomes
from generate_world import (
    NOISE_HEAT,
    NOISE_HEIGHT_ISLAND,
    Map2D,
    combine_maps,
    convert_to_blocks_map,
    create_circulair_map_mask,
    generate_noise_map,
    random_seed,
    world_map_colors,
)
from main_menu import MainMenuUrsina
from utils import X, Y, Z, pos_to_xyz, setup_logger, timeit

# from ursina import *


logger = logging.getLogger(conf.LOGGER_NAME)


class GameState(Enum):
    MAIN_MENU = 0
    STARTING = 1
    PLAYING = 2
    # PAUSED = 3


class Player(FirstPersonController):
    position: List
    position_previous: List

    def __init__(self, position_start, speed, enable_fly=False):
        super().__init__()
        self.enable_fly = enable_fly
        self.set_fly(on=False)
        self.speed = speed
        position_start[Y] += 3  # Let player fall on the map from sky
        self.position = self.position_previous = position_start
        logger.info(f"Player position start {self.position}")

    def delete(self):
        logger.info("Delete Player")
        self.enabled = False
        self.destroy = True

    def input(self, key):
        if key == "space":
            self.jump()
            self.set_fly(on=False)
        if key == "i":
            logger.debug(f"Player position is {self.position}, {self.speed=}")
        if self.enable_fly:
            if key == "e":
                self.set_fly(on=True)
                self.y += 1
            if key == "q" and self.fly:
                self.y -= 1

    def check_new_position(self) -> bool:
        pos_cur = pos_to_xyz(self.position)
        pos_old = pos_to_xyz(self.position_previous)
        if (pos_cur[X], pos_cur[Z]) != (pos_old[X], pos_old[Z]):
            logger.info(f"Player position new {pos_to_xyz(self.position)}")
            self.position_previous = self.position
            return True
        return False

    def set_fly(self, on: bool):
        self.fly = on
        if self.fly:
            self.gravity = 0
        else:
            self.gravity = 1


@lru_cache(maxsize=None)
def get_texture(biome: str):
    get_file = lambda name: path.join("textures", name)
    if biome == Biomes.SEA:
        return load_texture(get_file("sea.png"))
    elif biome == Biomes.LAKE:
        return load_texture(get_file("water.png"))
    elif biome == Biomes.DESERT:
        return load_texture(get_file("sand.png"))
    elif biome == Biomes.SAVANNA:
        return load_texture(get_file("savanna.png"))
    elif biome == Biomes.PLANE:
        return load_texture(get_file("grass.png"))
    elif biome == Biomes.HILL:
        return load_texture(get_file("grass_stone.png"))
    elif biome == Biomes.MOUNTAIN:
        return load_texture(get_file("stone.png"))
    elif biome == Biomes.MOUNTAIN_SNOW:
        return load_texture(get_file("snow.png"))


class Block(Button):
    destroy = False
    create_position = None
    is_lowest = False

    # By setting the parent to scene and the model to 'cube' it becomes a 3d button.
    def __init__(
        self,
        position=(0, 0, 0),
        biome: str = Biomes.HILL,
        is_lowest=True,
        fix_pos=0.5,
    ):
        position = list(position)
        position[X] = position[X] + fix_pos
        position[Z] = position[Z] + fix_pos
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            texture=get_texture(biome),
            scale=1,
            color=color(0, 0, random.uniform(0.95, 1)),
            highlight_color=light_gray,
        )
        self.is_lowest = is_lowest

    def delete(self):
        self.destroy = True

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                self.create_position = self.position + mouse.normal
            if key == "right mouse down":
                self.delete()


class MiniMap:
    map: Entity

    def __init__(self, world_map2d, seed, world_size):
        self.world_map2d = world_map2d
        self.seed = seed
        self.world_size = world_size
        self.save_minimap()
        self.map = self.create_minimap()

    def delete(self):
        logger.info("Delete MiniMap")
        destroy(self.map)

    def create_minimap(self):
        return Entity(
            parent=camera.ui,
            model="quad",
            scale=(0.25, 0.25),
            x=0.75,
            y=0.35,
            texture=self.get_minimap_path(),
        )

    @timeit
    def save_minimap(self):
        """Save minimap as PNG image"""
        path = self.get_minimap_path()
        img = np.array(world_map_colors(self.world_map2d))
        plt.imsave(path, img)

    def get_minimap_path(self):
        return path.join("maps", f"seed_{self.seed}.png")


class World:
    render_size: int
    blocks: List[Block] = list()

    def __init__(self, world_map2d: Map2D, world_size: int, position_start, render_size: int):
        logger.info("Initialize World")
        self.world_map2d = world_map2d
        self.world_size = world_size
        self.render_size = render_size
        self.blocks_init(position_start)

    def delete(self):
        logger.info("Delete World")
        for block in self.blocks:
            block.delete()
        self.blocks = list()

    def update(self, player_position):
        logger.debug(f"Total blocks {len(self.blocks)}")
        self.move_destroy(player_position)
        self.move_create(player_position)
        self.fill_vertical()

    def render_block(self, position):
        x, y, z = pos_to_xyz(position)
        if all([0 <= pos < self.world_size for pos in (x, z)]):
            biome = self.world_map2d[x][z].biome
            y = self.world_map2d[x][z].world_height
            if biome in [Biomes.LAKE, Biomes.SEA]:
                y -= 0.3
            self.blocks.append(Block(position=(x, y, z), biome=biome))

    def blocks_init(self, position_start=[0, 0, 0]):
        for z in range(-self.render_size, self.render_size + 1):
            z += position_start[Z]
            for x in range(-self.render_size, self.render_size + 1):
                x += position_start[X]
                self.render_block([x, 0, z])
        self.fill_vertical()

    def move_create(self, player_position):
        _start_blocks_count = len(self.blocks)
        blocks_x = set([int(b.position.x) for b in self.blocks])
        blocks_z = set([int(b.position.z) for b in self.blocks])

        player_x, _, player_z = pos_to_xyz(player_position)
        size = self.render_size
        new_x = [n for n in [player_x - size, player_x + size] if n not in blocks_x]
        new_z = [n for n in [player_z - size, player_z + size] if n not in blocks_z]

        for x in new_x:
            for z in blocks_z:
                self.render_block([x, 0, z])
            blocks_x.add(x)
        for z in new_z:
            for x in blocks_x:
                self.render_block([x, 0, z])
        logger.debug(f"Add {len(self.blocks) - _start_blocks_count} blocks")

    def move_destroy(self, player_position):
        _start_blocks_count = len(self.blocks)
        player_x, _, player_z = pos_to_xyz(player_position)
        for block in reversed(self.blocks):
            if (
                block.position.x < player_x - self.render_size + 0.5
                or block.position.x > player_x + self.render_size + 0.5
                or block.position.z < player_z - self.render_size + 0.5
                or block.position.z > player_z + self.render_size + 0.5
            ):
                self.blocks.remove(block)
                destroy(block)
        logger.debug(f"Del {_start_blocks_count - len(self.blocks)} blocks")

    def fill_vertical(self):
        _start_blocks_count = len(self.blocks)
        self.blocks.sort(key=lambda b: b.position.y, reverse=True)
        for block in self.blocks:
            x = int(block.position.x)
            y = int(block.position.y)
            z = int(block.position.z)
            if not block.is_lowest:
                continue
            for x_diff, z_diff in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
                try:
                    block_around = self.world_map2d[x + x_diff][z + z_diff]
                except IndexError:
                    continue
                if y - block_around.world_height < 2:  # Skip high difference < 2
                    continue
                self.blocks.append(Block(position=(x, y - 1, z), biome=block_around.biome))
                block.is_lowest = False
                break
        logger.debug(f"Fill {len(self.blocks) - _start_blocks_count} blocks")

    def click_handler(self):
        for block in reversed(self.blocks):
            if block.destroy:
                self.blocks.remove(block)
                destroy(block)
            elif block.create_position:
                new_block = Block(
                    position=block.create_position,
                    biome=None,
                    is_lowest=False,
                    fix_pos=False,
                )
                self.blocks.append(new_block)
                block.create_position = None


class UrsinaMC(MainMenuUrsina):
    world_map2d: Map2D = None
    world = None
    player = None
    minimap = None
    game_background = None
    loading_step: int = 0

    def __init__(self):
        super().__init__()
        self.game_state = GameState.MAIN_MENU

    def start_game(self, **kwargs):
        self.game_state = GameState.STARTING
        logger.info("Game starting")
        self.seed = kwargs.get("seed", random_seed())
        self.world_size = kwargs.get("world_size", conf.WORLD_SIZE)
        self.world_shape = (self.world_size, self.world_size)
        self.speed = kwargs.get("player_speed", conf.PLAYER_SPEED)
        self.render_size = kwargs.get("render_size", conf.BLOCKS_RENDER_DISTANCE)
        print(f"Settings: {self.seed=}, {self.world_size=}, {self.speed=}, {self.render_size=}")

    def load_game_sequentially(self):
        if self.loading_step == 0:
            self.game_background = Sky()
            self.loading_bar = HealthBar(
                max_value=100,
                value=1,
                position=(-0.5, -0.35, -2),
                scale_x=1,
                animation_duration=0,
                bar_color=gray,
            )
        elif self.loading_step == 10:
            # Generate map 1/3
            heigth_map = generate_noise_map(self.world_shape, self.seed, **NOISE_HEIGHT_ISLAND)
            circulair_map = create_circulair_map_mask(self.world_size)
            self._heigth_map_island = combine_maps(heigth_map, circulair_map)
        elif self.loading_step == 20:
            # Generate map 2/3
            self._heat_map = generate_noise_map(self.world_shape, self.seed, **NOISE_HEAT)
        elif self.loading_step == 30:
            # Generate map 3/3
            self.world_map2d = convert_to_blocks_map(self._heigth_map_island, self._heat_map)
        elif self.loading_step == 40:
            self.start_position = self.random_start_position(world_size=self.world_size)
            self.world = World(
                self.world_map2d, self.world_size, self.start_position, self.render_size
            )
        elif self.loading_step == 50:
            self.minimap = MiniMap(self.world_map2d, self.seed, self.world_size)
            self.minimap.map.visible = False
        elif self.loading_step == 90:
            destroy(self.loading_bar)
            self.loading_bar = None
            self.minimap.map.visible = True
            self.player = Player(
                position_start=self.start_position, speed=self.speed, enable_fly=True
            )
            super().start_game()
            self.game_state = GameState.PLAYING
            logger.info("Game playing")
            return
        self.loading_bar.value = self.loading_step
        self.loading_step += 2

    def quit_game(self):
        if self.game_state == GameState.MAIN_MENU:
            logger.info("Exit game")
            sys.exit()
        logger.info("Quiting game")
        self.reset_game()
        self.game_state = GameState.MAIN_MENU
        super().quit_game()

    def reset_game(self):
        self.world_map2d = None
        self.world.delete()
        self.world = None
        self.player.delete()
        self.player = None
        self.minimap.delete()
        self.minimap = None
        destroy(self.game_background)
        self.game_background = None
        self.loading_step = 0

    @timeit
    def random_start_position(self, world_size: int):
        while True:
            x = random.randint(1, world_size - 1)
            z = random.randint(1, world_size - 1)
            biome_block = self.world_map2d[x][z]
            position = [x + 0.5, biome_block.world_height, z + 0.5]
            logger.debug(f"Random position {position=}")
            if biome_block.biome not in [Biomes.SEA, Biomes.LAKE]:
                return position

    def input(self, key):
        if key == "escape":
            self.quit_game()
        super().input(key)

    def _update(self, task):
        if self.game_state == GameState.STARTING:
            self.load_game_sequentially()
        elif self.game_state == GameState.PLAYING:
            if self.player.check_new_position():
                self.world.update(self.player.position)
            self.world.click_handler()
        return super()._update(task)


if __name__ == "__main__":
    setup_logger(logger=logger)
    app = UrsinaMC()

    window.title = "Mincraft Ursina"
    window.borderless = True
    window.fullscreen = False
    window.exit_button.visible = False
    window.fps_counter.enabled = True

    app.run()
