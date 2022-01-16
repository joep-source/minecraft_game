from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from generate_world import world_init


class CustomFirstPersonController(FirstPersonController):
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

    def pos(self, axis):
        return floor(getattr(self.position, axis))


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
            position=position,
            model="cube",
            origin_y=0.5,
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
    blocks = []
    render_size = 16
    world_size = 100

    def __init__(self, **kwargs):
        self.world_map = world_init(self.world_size)
        self.player_position_start = [50, 3, 50]
        self.world_create()
        super().__init__(**kwargs)
        self.gravity = 0
        self.player = CustomFirstPersonController()
        self.player_old_pos = self.player.position

    def _update(self, task):
        if self.new_pos():
            print(f"blocks {len(self.blocks)}")
            self.world_move_destroy()
            self.world_move_create()
        self.world_click_handler()
        return super()._update(task)

    def new_pos(self):
        for i in range(3):
            if floor(self.player.position[i]) != floor(self.player_old_pos[i]):
                self.player_old_pos = self.player.position
                return True
        return False

    # ========================================================================

    def pos_player_to_world(self, x, z):
        new_x = int(x) + self.player_position_start[0]
        new_z = int(z) + self.player_position_start[2]
        return [new_x, new_z]

    def world_render_block(self, x, z):
        world_pos = self.pos_player_to_world(x=x, z=z)
        if all([0 <= pos < self.world_size for pos in world_pos]):
            colour = self.world_map[world_pos[0]][world_pos[1]].color(multiply=255)
            self.blocks.append(Block(position=(x, 0, z), colour=colour))

    def world_create(self):
        for z in range(-self.render_size, self.render_size):
            for x in range(-self.render_size, self.render_size):
                self.world_render_block(x=x, z=z)

    def world_move_destroy(self):
        __blocks_len = len(self.blocks)
        player_x, player_z = self.player.pos("x"), self.player.pos("z")
        block: Block
        for block in reversed(self.blocks):
            if self.render_size < max(
                abs(block.position.x - player_x), abs(block.position.z - player_z)
            ):
                self.blocks.remove(block)
                destroy(block)
        print(f"del {__blocks_len - len(self.blocks)} blocks")

    def world_move_create(self):
        __blocks_len = len(self.blocks)
        blocks_x = set([b.position.x for b in self.blocks])
        blocks_z = set([b.position.z for b in self.blocks])

        pos_x = self.player.pos("x")
        pos_z = self.player.pos("z")
        size = self.render_size

        new_x = [n for n in [pos_x - size, pos_x + size] if n not in blocks_x]
        new_z = [n for n in [pos_z - size, pos_z + size] if n not in blocks_z]

        for x in new_x:
            for z in blocks_z:
                self.world_render_block(x=x, z=z)
            blocks_x.add(x)
        for z in new_z:
            for x in blocks_x:
                self.world_render_block(x=x, z=z)
        print(f"add {len(self.blocks) - __blocks_len} blocks")

    def world_click_handler(self):
        for block in reversed(self.blocks):
            if block.destroy:
                self.blocks.remove(block)
                destroy(block)
            elif block.create_position:
                self.blocks.append(Block(position=block.create_position))


app = UrsinaMC()
app.run()
