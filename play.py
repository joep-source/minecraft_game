from functools import lru_cache
import random
import sys
from typing import List
from os import path
from matplotlib import pyplot as plt

# from ursina import *
from ursina.camera import instance as camera
from ursina.color import light_gray, color
from ursina.entity import Entity
from ursina.mouse import instance as mouse
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.first_person_controller import Button
from ursina.prefabs.sky import Sky
from ursina.scene import instance as scene
from ursina.texture_importer import load_texture
from ursina.ursinastuff import destroy

from block import Bioms
from generate_world import random_seed, generate_world_map, world_map_colors
from main_menu import MainMenuUrsina
from utils import *


class Player(FirstPersonController):
    position_previous = None

    def __init__(self, position_start, **kwargs):
        super().__init__()
        self.position = self.position_previous = position_start
        self.gravity = 0
        self.speed = 15
        self.update()
        print(f"Position start {self.position}")

    def delete(self):
        print("Delete Player")
        self.destroy = True

    def input(self, key):
        if key == "space":
            self.gravity = 1
            self.jump()
        if key == "q":
            self.y += 3
            self.gravity = 0
        if key == "e":
            self.y -= 1

    def new_position(self) -> bool:
        pos_cur = pos_to_xyz(self.position)
        pos_old = pos_to_xyz(self.position_previous)
        if (pos_cur[X], pos_cur[Z]) != (pos_old[X], pos_old[Z]):
            # print(f"Position new {pos_to_xyz(self.position)}")
            self.position_previous = self.position
            return True
        return False


@lru_cache(maxsize=None)
def get_texture(biome: str):
    get_file = lambda name: path.join("textures", name)
    if biome == Bioms.SEA:
        return load_texture(get_file("sea.png"))
    elif biome == Bioms.LAKE:
        return load_texture(get_file("water.png"))
    elif biome == Bioms.DESERT:
        return load_texture(get_file("sand.png"))
    elif biome == Bioms.SAVANNA:
        return load_texture(get_file("savanna.png"))
    elif biome == Bioms.PLANE:
        return load_texture(get_file("grass.png"))
    elif biome == Bioms.HILL:
        return load_texture(get_file("grass_stone.png"))
    elif biome == Bioms.MOUNTAIN:
        return load_texture(get_file("stone.png"))
    elif biome == Bioms.MOUNTAIN_SNOW:
        return load_texture(get_file("snow.png"))


class Block(Button):
    destroy = False
    create_position = None
    is_lowest = False

    # By setting the parent to scene and the model to 'cube' it becomes a 3d button.
    def __init__(
        self,
        position=(0, 0, 0),
        biome: str = Bioms.HILL,
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
        # print("Delete Block")
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
        print("Delete MiniMap")
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
        img = world_map_colors(self.world_map2d, self.world_size)
        plt.imsave(path, img)

    def get_minimap_path(self):
        return path.join("maps", f"seed_{self.seed}.png")


class World:
    blocks: List[Block] = list()
    render_size: int = 10

    def __init__(self, world_map2d, world_size, position_start):
        print("Initialize World")
        self.world_map2d = world_map2d
        self.world_size = world_size
        self.blocks_init(position_start)

    def delete(self):
        print("Delete World")
        for block in self.blocks:
            block.delete()
        self.blocks = list()

    def update(self, player_position):
        print(f"Total blocks {len(self.blocks)}")
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
        # __blocks_len = len(self.blocks)
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
        # print(f"add {len(self.blocks) - __blocks_len} blocks")

    def move_destroy(self, player_position):
        # __blocks_len = len(self.blocks)
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
        # print(f"del {__blocks_len - len(self.blocks)} blocks")

    def fill_vertical(self):
        # __blocks_len = len(self.blocks)
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
                self.blocks.append(
                    Block(position=(x, y - 1, z), biome=block_around.biome)
                )
                block.is_lowest = False
                break
        # print(f"low {len(self.blocks) - __blocks_len} blocks")

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

    def start_game(self, world_size=512):
        super().start_game()
        seed = 34315  # random_seed()
        position_start = [250.5, 40, 250.5]
        self.world_map2d = generate_world_map(size=world_size, seed=seed)
        self.world = World(self.world_map2d, world_size, position_start)
        self.player = Player(position_start=position_start)
        self.minimap = MiniMap(self.world_map2d, seed, world_size)
        self.game_background = Sky()
        self.game_active = True

    def quit_game(self):
        if not self.game_active:
            sys.exit()
        print("Quiting game")
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

    def input(self, key):
        if key == "escape":
            self.quit_game()
        super().input(key)

    def _update(self, task):
        if self.game_active:
            if self.player.new_position():
                self.world.update(self.player.position)
            self.world.click_handler()
        return super()._update(task)


if __name__ == "__main__":
    app = UrsinaMC()
    app.run()
