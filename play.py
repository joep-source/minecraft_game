import logging
import random
import sys
from copy import deepcopy
from enum import Enum
from functools import lru_cache
from os import path
from time import time
from typing import List, Set, Tuple, Union

import numpy as np
from matplotlib import pyplot as plt
from ursina.camera import instance as camera
from ursina.color import color, gray, light_gray, red, yellow
from ursina.curve import out_expo
from ursina.entity import Entity
from ursina.hit_info import HitInfo
from ursina.input_handler import held_keys
from ursina.main import time as utime
from ursina.models.procedural.grid import Grid
from ursina.mouse import instance as mouse
from ursina.prefabs.button import Button
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.health_bar import HealthBar
from ursina.prefabs.sky import Sky
from ursina.raycaster import raycast
from ursina.scene import instance as scene
from ursina.texture_importer import load_texture
from ursina.ursinamath import distance_xz
from ursina.ursinastuff import destroy, invoke
from ursina.vec3 import Vec3
from ursina.window import instance as window

import conf
from block import Biomes
from generate_world import (
    NOISE_HEAT,
    NOISE_HEIGHT_ISLAND,
    Map2D,
    combine_maps,
    convert_to_blocks_map,
    create_circular_map_mask,
    generate_noise_map,
    random_seed,
    world_map_colors,
)
from main_menu import MainMenuUrsina
from utils import Z_2D, X, Y, Z, points_in_2dcircle, pos_to_xyz, setup_logger, timeit

# from ursina import *

WATER_BLOCKS = [Biomes.LAKE, Biomes.SEA]

logger = logging.getLogger(conf.LOGGER_NAME)


class GameState(Enum):
    MAIN_MENU = 0
    STARTING = 1
    PLAYING = 2


class Player(FirstPersonController):
    position: List
    position_previous: List
    health_bar: HealthBar
    hp: int
    max_hp: int = 100
    health_bar_len = 0.6
    health_bar_width = 0.02

    def __init__(self, position_start, speed, allow_fly=False):
        super().__init__()
        self.allow_fly = allow_fly
        self.speed = speed
        position_start[Y] += 3  # Let player fall on the map from sky
        self.position = self.position_previous = position_start
        self.hp = self.max_hp
        position = deepcopy(window.bottom)
        position[X] -= self.health_bar_len / 2
        position[Z_2D] += self.health_bar_width * 2
        self.health_bar = HealthBar(
            max_value=self.max_hp,
            value=self.hp,
            scale=(self.health_bar_len, self.health_bar_width),
            position=position,
            roundness=0.5,
            bar_color=red,
        )
        self.health_bar.text_entity.text = ""
        logger.info(f"Player position start {self.position}")

    def delete(self):
        logger.info("Delete Player")
        self.enabled = False
        destroy(self.health_bar)
        destroy(self)

    def input(self, key):
        if key == "space":
            self.jump()
            self.gravity = 1
        if key == "i":
            logger.info(f"Player position is {self.position}, {self.speed=}")
        if key == "e" and self.allow_fly:
            self.gravity = 0

    def update(self):
        if self.allow_fly:
            self.direction = Vec3(self.up * (held_keys["e"] - held_keys["q"])).normalized()
            self.position += self.direction * self.speed * utime.dt
        super().update()

    def has_new_position(self) -> bool:
        pos_cur = pos_to_xyz(self.position)
        pos_old = pos_to_xyz(self.position_previous)
        if (pos_cur[X], pos_cur[Z]) != (pos_old[X], pos_old[Z]):
            logger.info(f"Player position new {pos_to_xyz(self.position)}")
            return True
        return False

    def hit(self, damage=10):
        self.hp -= damage
        self.health_bar.value = self.hp
        self.health_bar.text_entity.text = ""
        self.health_bar.bar.blink(yellow, duration=0.3)


class Enemy(Entity):
    # Based on FirstPersonController but without camera
    player_ref: Player
    health_bar: Entity
    hp: int
    max_hp: int = 100
    speed: int = 4
    minimum_attack_distance: int = 2
    height: int = 2
    jump_height: float = 1.5
    attack_cooldown_time: float = 1.5
    turn_cooldown_time: float = 0.4
    attack_cooldown: float = 0
    turn_cooldown: float = 0
    grounded: bool = False
    jump_up_duration: float = 0.5
    fall_after: float = 0.35
    air_time: float = 0
    hp_scale: float = 1.5
    to_be_deleted: bool = False

    def __init__(self, player, position):
        self.hp = self.max_hp
        self.attack_cooldown = self.attack_cooldown_time
        self.turn_cooldown = time()
        self.player_ref = player
        position[Y] += 1
        super().__init__(
            model="enemy",
            texture="enemy",
            scale=0.95,
            collider="mesh",
            position=position,
        )
        self.health_bar = Entity(
            parent=self, y=2.8, model="cube", color=red, world_scale=(self.hp_scale, 0.1, 0.1)
        )
        self.disable()

    def delete(self):
        logger.info("Delete Enemy")
        destroy(self.health_bar)
        self.rotation_z = 70
        _destroy = lambda: destroy(self)
        invoke(_destroy, delay=0.5)
        self.to_be_deleted = True

    def input(self, key):
        if self.hovered and key == "left mouse down":
            mouse.hovered_entity.hit()

    def update(self):
        def _raycast(origin):
            return raycast(origin=origin, direction=self.forward, distance=0.5, ignore=(self,))

        if not self.player_ref.enabled:
            return  # Bugfix while destroying game
        if time() - self.turn_cooldown > self.turn_cooldown_time:
            self.turn_cooldown = time()
            self.look_at_2d(self.player_ref.position, "y")
            self.rotation_y -= 180
        hit_feet: HitInfo = _raycast(origin=self.position + Vec3(0, 0.1, 0))
        hit_head: HitInfo = _raycast(origin=self.position + Vec3(0, self.height - 0.1, 0))
        distance_to_player: int = distance_xz(self.player_ref.position, self.position)

        if hit_head.hit and isinstance(hit_head.entity, Block):
            pass
        elif distance_to_player < self.minimum_attack_distance:
            if self.attack_cooldown <= 0:
                logger.info("Enemy attack")
                self.blink(yellow, duration=0.3)
                self.shake()
                self.player_ref.hit()
                self.attack_cooldown = self.attack_cooldown_time
        elif hit_feet.hit and isinstance(hit_feet.entity, Block):
            self.jump()
        else:
            # Move backward to correct model facing direction
            self.position += self.back * self.speed * utime.dt

        self.update_gravity()
        self.health_bar.alpha = max(0, self.health_bar.alpha - utime.dt)
        self.attack_cooldown = max(0, self.attack_cooldown - utime.dt)

    def update_gravity(self):
        hit_down: HitInfo = raycast(
            origin=self.world_position + (0, self.height, 0),
            direction=self.down,
            ignore=tuple(e for e in scene.entities if isinstance(e, Enemy)),
        )
        if hit_down.distance <= self.height + 0.1:
            self.grounded = True
            self.air_time = 0
        else:
            self.grounded = False
            self.y -= min(self.air_time, hit_down.distance - 0.05) * utime.dt * 100
            self.air_time += utime.dt * 0.25

    def jump(self):
        if not self.grounded:
            return
        if self.to_be_deleted:
            return  # Prevent invoke function when going to be deleted
        self.grounded = False
        self.animate_y(
            self.y + self.jump_height,
            self.jump_up_duration,
            resolution=int(1 // utime.dt),
            curve=out_expo,
        )
        invoke(self.y_animator.pause, delay=self.fall_after)

    def hit(self, damage=20):
        self.blink(red, duration=0.3)
        self.hp -= damage
        self.health_bar.world_scale_x = self.hp / self.max_hp * self.hp_scale
        self.health_bar.alpha = 1


@lru_cache(maxsize=None)
def get_texture(biome: Union[str, None]):
    get_file = lambda name: path.join("assets", name)
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
    elif biome == None:
        return load_texture(get_file("plank.png"))


class Block(Button):
    destroyable: bool = False
    destroy: bool = False
    create_position = None
    fix_pos: int

    def __init__(
        self,
        position: List[int],
        biome: str,
        fix_pos=0.5,
        destroyable=False,
    ):
        self.fix_pos = fix_pos
        self.biome = biome
        self.destroyable = destroyable
        position = list(position)
        position[X] += self.fix_pos
        position[Z] += self.fix_pos
        texture = get_texture(self.biome if not self.create_position else None)
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            texture=texture,
            scale=1,
            color=color(0, 0, random.uniform(0.95, 1)),
            highlight_color=light_gray,
        )
        if self.biome in WATER_BLOCKS:
            self.collider = None

    def delete(self):
        self.destroy = True

    def get_map_position(self) -> Tuple[int, int, int]:
        return (
            int(self.position.x - self.fix_pos),
            int(self.position.y),
            int(self.position.z - self.fix_pos),
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down" and self.destroyable:
                self.delete()
            if key == "right mouse down" and self.biome not in WATER_BLOCKS:
                self.create_position = self.position + mouse.normal


class MiniMap:
    map: Entity
    player_icon: Entity
    world_size: int

    def __init__(self, world_map2d, seed, world_size):
        self.world_size = world_size
        self.save_minimap(world_map2d, seed)
        self.map = Entity(
            parent=camera.ui,
            model="quad",
            scale=(0.3, 0.3),
            origin=(-0.5, 0.5),
            position=window.top_left,
            texture=self.get_minimap_path(seed),
        )
        self.player_icon_max = 0.95
        self.player_icon = Entity(
            parent=self.map,
            model="sphere",
            scale=0.025,
            origin=(-1, 1),
            z=-999,
            texture="white_cube",
            color=red,
        )

    def delete(self):
        logger.info("Delete MiniMap")
        destroy(self.map)
        destroy(self.player_icon)

    def update_positions(self, position):
        x, _, z = pos_to_xyz(position=position)
        self.player_icon.x = x / self.world_size * self.player_icon_max
        self.player_icon.y = z / self.world_size * self.player_icon_max - self.player_icon_max

    @timeit
    def save_minimap(self, world_map2d, seed):
        """Save minimap as PNG image"""
        path = self.get_minimap_path(seed)
        img = np.rot90(np.array(world_map_colors(world_map2d)))
        plt.imsave(path, img)

    def get_minimap_path(self, seed):
        return path.join("maps", f"seed_{seed}.png")


class World:
    render_size: int
    player: Player
    world_map2d: Map2D
    world_size: int
    position_start: List[int]
    enemies: List[Enemy] = list()
    blocks: List[Block] = list()

    def __init__(self, world_map2d: Map2D, world_size: int, render_size: int):
        logger.info("Initialize World")
        self.world_map2d = world_map2d
        self.world_size = world_size
        self.render_size = render_size
        self.hidden_floor = Entity(
            model=Grid(1, 1),
            rotation_x=90,
            collider="box",
            scale=self.world_size * 2,
            position=(0, -1.9, 0),
            visible=False,
        )
        self.position_start = self.random_island_position(self.world_map2d, self.world_size)
        self.update_positions(self.position_start, None)

    def init_player(self, speed, allow_fly=False):
        self.player = Player(position_start=self.position_start, speed=speed, allow_fly=True)

    def init_enemies(self, total_enemies=1):
        positions_taken = points_in_2dcircle(
            radius=self.render_size,
            x_offset=int(self.player.position[X]),
            y_offset=int(self.player.position[Z]),
        )
        for _ in range(total_enemies):
            try_count = 0
            while try_count < 10:
                position = self.random_island_position(self.world_map2d, self.world_size)
                position_2d = (position[X] + 0.5, position[Z] + 0.5)
                if position_2d not in positions_taken:
                    self.enemies.append(Enemy(player=self.player, position=position))
                    positions_taken.add(position_2d)
                    break
            try_count += 1
        print(positions_taken)

    def delete(self):
        logger.info("Delete World")
        self.player.delete()
        self.player = None
        for enemy in self.enemies:
            enemy.delete()
        self.enemies = list()
        for block in self.blocks:
            block.delete()
        self.blocks = list()

    def update_enemies(self):
        for enemy in reversed(self.enemies):
            if enemy.hp <= 0 and enemy.to_be_deleted == False:
                self.enemies.remove(enemy)
                enemy.delete()

    def update_positions(self, player_position_new, player_position_old):
        points_wanted_2d = points_in_2dcircle(
            radius=self.render_size,
            x_offset=int(player_position_new[X]),
            y_offset=int(player_position_new[Z]),
        )
        points_current_2d = set()
        if player_position_old:
            points_current_2d = points_in_2dcircle(
                radius=self.render_size,
                x_offset=int(player_position_old[X]),
                y_offset=int(player_position_old[Z]),
            )
        self.update_blocks(points_wanted_2d, points_current_2d)
        self.update_enemies_enabled(points_wanted_2d)

    def update_blocks(
        self, points_wanted_2d: Set[Tuple[int, int]], points_current_2d: Set[Tuple[int, int]]
    ):
        points_del_2d = points_current_2d.difference(points_wanted_2d)
        for block in reversed(self.blocks):
            x, _, z = block.get_map_position()
            if any(x == point[X] and z == point[Z_2D] for point in points_del_2d):
                self.blocks.remove(block)
                destroy(block)

        points_add_2d = points_wanted_2d.difference(points_current_2d)
        for point in points_add_2d:
            self.render_block(position=[point[X], -1, point[Z_2D]])
        logger.debug(f"Total blocks {len(self.blocks)}")

    def update_enemies_enabled(self, points_current_2d: Set[Tuple[int, int]]):
        for enemy in self.enemies:
            x, _, z = pos_to_xyz(enemy.position)
            if any(x == point[X] and z == point[Z_2D] for point in points_current_2d):
                enemy.enable()
            else:
                enemy.disable()

    def render_block(self, position):
        x, y, z = pos_to_xyz(position)
        if not all([0 <= pos < self.world_size for pos in (x, z)]):
            return  # Skip if outside of world
        biome = self.world_map2d[x][z].biome
        if y == -1:
            y = self.world_map2d[x][z].world_height
        if biome in WATER_BLOCKS:
            y -= 0.3
        self.blocks.append(Block(position=(x, y, z), biome=biome))
        if biome not in WATER_BLOCKS:
            self.fill_block_below((x, y, z))

    def fill_block_below(self, position):
        x, y, z = pos_to_xyz(position)
        blocks_around = []
        for x_diff, z_diff in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
            try:
                blocks_around.append(self.world_map2d[x + x_diff][z + z_diff])
            except IndexError:
                continue  # Skip if outside of world
        if any(y - block.world_height > 1 for block in blocks_around):
            self.render_block(position=(x, y - 1, z))

    def block_click_handler(self):
        for block in reversed(self.blocks):
            if block.destroy:
                self.blocks.remove(block)
                destroy(block)
            elif block.create_position:
                new_block = Block(
                    position=block.create_position, biome=None, fix_pos=0, destroyable=True
                )
                self.blocks.append(new_block)
                block.create_position = None

    @staticmethod
    def random_island_position(world_map2d: Map2D, world_size: int) -> List[int]:
        while True:
            x = random.randint(1, world_size - 1)
            z = random.randint(1, world_size - 1)
            biome_block = world_map2d[x][z]
            position = [x + 0.5, biome_block.world_height, z + 0.5]
            if biome_block.biome not in [Biomes.SEA, Biomes.LAKE]:
                logger.debug(f"Random position {position=}")
                return position


class UrsinaMC(MainMenuUrsina):
    world_map2d: Map2D = None
    world = None
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
        self.enemies_total = kwargs.get("enemies_total", conf.ENEMIES_TOTAL)
        logger.info(
            f"Settings: {self.seed=}, {self.world_size=}, {self.speed=}, {self.render_size=}, {self.enemies_total=}"
        )

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
            height_map = generate_noise_map(self.world_shape, self.seed, **NOISE_HEIGHT_ISLAND)
            circular_map = create_circular_map_mask(self.world_size)
            self._height_map_island = combine_maps(height_map, circular_map)
        elif self.loading_step == 20:
            # Generate map 2/3
            self._heat_map = generate_noise_map(self.world_shape, self.seed, **NOISE_HEAT)
        elif self.loading_step == 30:
            # Generate map 3/3
            self.world_map2d = convert_to_blocks_map(self._height_map_island, self._heat_map)
        elif self.loading_step == 40:
            self.world = World(self.world_map2d, self.world_size, self.render_size)
        elif self.loading_step == 50:
            self.minimap = MiniMap(self.world_map2d, self.seed, self.world_size)
            self.minimap.update_positions(self.world.position_start)
            self.minimap.map.visible = False
            self.minimap.player_icon.visible = False
        elif self.loading_step == 80:
            self.world.init_player(speed=self.speed, allow_fly=True)
            self.world.init_enemies(total_enemies=self.enemies_total)
        elif self.loading_step == 90:
            destroy(self.loading_bar)
            self.loading_bar = None
            self.minimap.map.visible = True
            self.minimap.player_icon.visible = True
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
        self.minimap.delete()
        self.minimap = None
        destroy(self.game_background)
        self.game_background = None
        self.loading_step = 0

    def input(self, key):
        if key == "escape":
            self.quit_game()
        super().input(key)

    def _update(self, task):
        if self.game_state == GameState.STARTING:
            self.load_game_sequentially()
        elif self.game_state == GameState.PLAYING:
            self.world.update_enemies()
            player = self.world.player
            if player.has_new_position():
                self.world.update_positions(player.position, player.position_previous)
                player.position_previous = player.position
                self.minimap.update_positions(player.position)
            self.world.block_click_handler()
        return super()._update(task)


if __name__ == "__main__":
    setup_logger(logger=logger)
    app = UrsinaMC()

    window.title = "Minecraft Ursina"
    window.borderless = True
    window.fullscreen = True
    window.exit_button.enabled = False
    window.fps_counter.enabled = True

    app.run()
