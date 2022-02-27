from functools import lru_cache
import random
from typing import List
from os import path
from matplotlib import pyplot as plt

# from ursina import *
from ursina.camera import instance as camera
from ursina.color import rgb, magenta, light_gray, color
from ursina.entity import Entity
from ursina.main import Ursina
from ursina.mouse import instance as mouse
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.first_person_controller import Button
from ursina.prefabs.sky import Sky
from ursina.scene import instance as scene
from ursina.texture_importer import load_texture
from ursina.ursinastuff import destroy
from block import Bioms

from generate_world import random_seed, generate_world_map, world_map_colors
from utils import *

sand_block_texture = None


class CustomFirstPersonController(FirstPersonController):
    position_previous = None

    def __init__(self, position_start, **kwargs):
        super().__init__()
        self.position = self.position_previous = position_start
        self.update()
        print(f"Position start {self.position}")

    def input(self, key):
        if key == "space":
            self.gravity = 1
            self.jump()
        if key == "q":
            self.y += 3
            self.gravity = 0
        if key == "e":
            self.y -= 1
        if key == "escape":
            quit()

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
    if biome == Bioms.SEA:
        return load_texture("textures/sea.png")
    elif biome == Bioms.LAKE:
        return load_texture("textures/water.png")
    elif biome == Bioms.DESERT:
        return load_texture("textures/sand.png")
    elif biome == Bioms.SAVANNA:
        return load_texture("textures/savanna.png")
    elif biome == Bioms.PLANE:
        return load_texture("textures/grass.png")
    elif biome == Bioms.HILL:
        return load_texture("textures/grass_stone.png")
    elif biome == Bioms.MOUNTAIN:
        return load_texture("textures/stone.png")
    elif biome == Bioms.MOUNTAIN_SNOW:
        return load_texture("textures/snow.png")


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

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                self.create_position = self.position + mouse.normal
            if key == "right mouse down":
                self.destroy = True


class MiniMap:
    def __init__(self, world_map2d, seed, world_size):
        self.world_map2d = world_map2d
        self.seed = seed
        self.world_size = world_size
        self.save_minimap()
        self.create_minimap()

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
        path = self.get_minimap_path()
        img = world_map_colors(self.world_map2d, self.world_size)
        plt.imsave(path, img)

    def get_minimap_path(self):
        return path.join("maps", f"seed_{self.seed}.png")


class UrsinaMC(Ursina):
    blocks: List[Block] = []
    render_size = 10
    world_size = 512
    seed = 34315  # random_seed()  # 34315

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        position_start = [250.5, 40, 250.5]
        self.world_map2d = generate_world_map(size=self.world_size, seed=self.seed)
        self.world_create(position_start=position_start)
        self.player = CustomFirstPersonController(position_start=position_start)
        self.player.gravity = 0j
        self.player.speed = 15
        self.minimap = MiniMap(self.world_map2d, self.seed, self.world_size)
        Sky()

    def _update(self, task):
        if self.player.new_position():
            print(f"Total blocks {len(self.blocks)}")
            self.world_move_destroy()
            self.world_move_create()
            self.world_fill_vertical()
        self.world_click_handler()
        return super()._update(task)

    # ========================================================================

    def world_render_block(self, position):
        x, y, z = pos_to_xyz(position)
        if all([0 <= pos < self.world_size for pos in (x, z)]):
            y = self.world_map2d[x][z].world_height
            biome = self.world_map2d[x][z].biome
            self.blocks.append(Block(position=(x, y, z), biome=biome))

    def world_create(self, position_start=[0, 0, 0]):
        for z in range(-self.render_size, self.render_size + 1):
            z += position_start[Z]
            for x in range(-self.render_size, self.render_size + 1):
                x += position_start[X]
                self.world_render_block([x, 0, z])
        self.world_fill_vertical()

    def world_move_destroy(self):
        # __blocks_len = len(self.blocks)
        player_x, _, player_z = pos_to_xyz(self.player.position)
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

    def world_fill_vertical(self):
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

    def world_move_create(self):
        # __blocks_len = len(self.blocks)
        blocks_x = set([int(b.position.x) for b in self.blocks])
        blocks_z = set([int(b.position.z) for b in self.blocks])

        player_x, _, player_z = pos_to_xyz(self.player.position)
        size = self.render_size
        new_x = [n for n in [player_x - size, player_x + size] if n not in blocks_x]
        new_z = [n for n in [player_z - size, player_z + size] if n not in blocks_z]

        for x in new_x:
            for z in blocks_z:
                self.world_render_block([x, 0, z])
            blocks_x.add(x)
        for z in new_z:
            for x in blocks_x:
                self.world_render_block([x, 0, z])
        # print(f"add {len(self.blocks) - __blocks_len} blocks")

    def world_click_handler(self):
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


if __name__ == "__main__":
    app = UrsinaMC()
    app.run()
