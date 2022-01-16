from typing import List
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from generate_world import world_init
from utils import pos_to_xyz


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
            self.y += 1
            self.gravity = 0
        if key == "e":
            self.y -= 1
        if key == "escape":
            quit()

    def new_position(self) -> bool:
        pos_cur = pos_to_xyz(self.position)
        pos_old = pos_to_xyz(self.position_previous)
        if (pos_cur[0], pos_cur[2]) != (pos_old[0], pos_old[2]):
            print(f"Position new {pos_to_xyz(self.position)}")
            self.position_previous = self.position
            return True
        return False


class Block(Button):
    destroy = False
    create_position = None

    # By setting the parent to scene and the model to 'cube' it becomes a 3d button.
    def __init__(self, position=(0, 0, 0), colour=None):
        if not colour:
            colour = color.color(0, 0, random.uniform(0.9, 1.0))
        else:
            colour = rgb(*colour)

        super().__init__(
            parent=scene,
            position=[pos + 0.5 for pos in position],
            model="cube",
            texture="white_cube",
            color=colour,
            highlight_color=color.lime,
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                self.create_position = self.position + mouse.normal
            if key == "right mouse down":
                self.destroy = True


class UrsinaMC(Ursina):
    blocks: List[Block] = []
    render_size = 16
    world_size = 100

    def __init__(self, **kwargs):
        self.world_map = world_init(self.world_size)
        position_start = [15.5, 1, 15.5]
        self.world_create(position_start=position_start)
        super().__init__(**kwargs)
        self.player = CustomFirstPersonController(position_start=position_start)

    def _update(self, task):
        if self.player.new_position():
            # print(f"Total blocks {len(self.blocks)}")
            self.world_move_destroy()
            self.world_move_create()
        self.world_click_handler()
        return super()._update(task)

    # ========================================================================

    def world_render_block(self, position):
        x, y, z = pos_to_xyz(position)
        if all([0 <= pos < self.world_size for pos in (x, z)]):
            colour = self.world_map[x][z].color(multiply=255)
            self.blocks.append(Block(position=(x, y, z), colour=colour))

    def world_create(self, position_start=[0, 0, 0]):
        for z in range(-self.render_size, self.render_size + 1):
            z += position_start[2]
            for x in range(-self.render_size, self.render_size + 1):
                x += position_start[0]
                self.world_render_block([x, 0, z])

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
                self.blocks.append(Block(position=block.create_position))


app = UrsinaMC()
app.run()