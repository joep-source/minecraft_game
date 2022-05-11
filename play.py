import logging
import random
import sys
from functools import lru_cache
from os import path
from typing import List

import numpy as np
from matplotlib import pyplot as plt
from ursina.camera import instance as camera
from ursina.color import color, light_gray
from ursina.entity import Entity
from ursina.mouse import instance as mouse
from ursina.prefabs.first_person_controller import Button, FirstPersonController
from ursina.prefabs.sky import Sky
from ursina.scene import instance as scene
from ursina.texture_importer import load_texture
from ursina.ursinastuff import destroy, invoke

import conf
from block import Biomes
from generate_world import generate_world_map, random_seed, world_map_colors
from main_menu import MainMenuUrsina
from utils import X, Y, Z, pos_to_xyz, setup_logger, timeit

# from ursina import *


logger = logging.getLogger(conf.LOGGER_NAME)


class Player(FirstPersonController):
    position: List
    position_previous: List

    def __init__(self, position_start, speed, enable_fly=False):
        super().__init__()
        self.enable_fly = enable_fly
        self.speed = speed
        position_start[Y] += 2
        self.position_start = position_start.copy()
        position_start[Y] = -10
        self.position = self.position_previous = position_start
        invoke(setattr, self, "position", self.position_start, delay=5)
        logger.info(f"Player position start {self.position_start}")

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

    def save_minimap(self):
        """Save minimap as PNG image"""
        path = self.get_minimap_path()
        img = np.array(world_map_colors(self.world_map2d))
        plt.imsave(path, img)

    def get_minimap_path(self):
        return path.join("maps", f"seed_{self.seed}.png")


class World:
    blocks: List[Block] = list()
    render_size: int = conf.BLOCKS_RENDER_DISTANCE

    def __init__(self, world_map2d, world_size, position_start):
        logger.info("Initialize World")
        self.world_map2d = world_map2d
        self.world_size = world_size
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
            y = self.world_map2d[x][z].world_height
            biome = self.world_map2d[x][z].biome
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
    def __init__(self):
        super().__init__()
        self.game_active = False

    def start_game(self, **kwargs):
        seed = kwargs.get("seed", random_seed())
        world_size = kwargs.get("world_size", conf.WORLD_SIZE)
        speed = kwargs.get("player_speed", conf.PLAYER_SPEED)
        logger.info(f"Settings: {seed=}, {world_size=}, {speed=}")

        self.world_map2d = generate_world_map(size=world_size, seed=seed)
        start_position = self.random_start_position(world_size=world_size)
        self.world = World(self.world_map2d, world_size, start_position)
        self.minimap = MiniMap(self.world_map2d, seed, world_size)
        self.game_background = Sky()
        self.player = Player(position_start=start_position, speed=speed, enable_fly=True)

        self.game_active = True
        logger.info("Game active")
        super().start_game()

    def quit_game(self):
        if not self.game_active:
            sys.exit()
        logger.info("Quiting game")
        self.game_active = False
        self.world_map2d = None
        self.world.delete()
        self.world = None
        self.player.delete()
        self.player = None
        self.minimap.delete()
        self.minimap = None
        destroy(self.game_background)
        self.game_background = None
        super().quit_game()

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
        if self.game_active:
            if self.player.check_new_position():
                self.world.update(self.player.position)
            self.world.click_handler()
        return super()._update(task)


if __name__ == "__main__":
    setup_logger(logger=logger)
    app = UrsinaMC()
    app.run()
