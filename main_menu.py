import string
import sys

from ursina import color
from ursina.camera import instance as camera
from ursina.entity import Entity
from ursina.main import Ursina
from ursina.prefabs.animator import Animator
from ursina.prefabs.button import Button
from ursina.prefabs.slider import Slider
from ursina.sequence import Func, Sequence, Wait

import conf


class MenuButton(Button):
    def __init__(self, text="", **kwargs):
        super().__init__(text, scale=(0.25, 0.075), highlight_color=color.azure, **kwargs)

        for key, value in kwargs.items():
            setattr(self, key, value)


class MainMenuUrsina(Ursina):
    button_spacing = 0.1
    menu_parent = None
    state_handler = None
    main_menu = None
    custom_menu = None

    def __init__(self) -> None:
        super().__init__()
        self.menu_parent = Entity(parent=camera.ui)
        self.set_background()
        self.main_menu = Entity(parent=self.menu_parent)
        self.custom_menu = Entity(parent=self.menu_parent)
        self.state_handler = Animator(
            {"main_menu": self.main_menu, "custom_menu": self.custom_menu}
        )
        self.setup_main_menu_buttons()
        self.setup_custom_menu_buttons()

    def setup_main_menu_buttons(self):
        self.main_menu.buttons = [
            MenuButton(
                "Classic", on_click=Func(self.pre_start_game, seed=conf.ISLAND_SEED_CLASSIC)
            ),
            MenuButton("Random island", on_click=self.pre_start_game),
            MenuButton(
                "Custom game", on_click=Func(setattr, self.state_handler, "state", "custom_menu")
            ),
            MenuButton("Quit", on_click=Sequence(Wait(0.01), Func(sys.exit))),
        ]
        for i, button in enumerate(self.main_menu.buttons):
            button.parent = self.main_menu
            button.color = color.black66
            button.y = -i * self.button_spacing

    def setup_custom_menu_buttons(self):
        speed_slider = Slider(text="Player speed", min=1, max=20, step=1, default=conf.PLAYER_SPEED)
        render_slider = Slider(
            text="Player blocks view:", min=4, max=30, step=1, default=conf.BLOCKS_RENDER_DISTANCE
        )
        size_slider = Slider(text="World size:", min=50, max=2000, step=5, default=conf.WORLD_SIZE)
        enemies_total_slider = Slider(
            text="Number of enemies", min=0, max=500, step=10, default=conf.ENEMIES_TOTAL
        )

        self.custom_settings = {
            "player_speed": speed_slider,
            "render_size": render_slider,
            "world_size": size_slider,
            "enemies_total": enemies_total_slider,
        }

        self.custom_menu.buttons = [
            MenuButton(text="Start", on_click=Func(self.pre_start_game, custom=True)),
            MenuButton(
                text="Back", on_click=Func(setattr, self.state_handler, "state", "main_menu")
            ),
        ]

        for i, entity in enumerate(list(self.custom_settings.values()) + self.custom_menu.buttons):
            entity.parent = self.custom_menu
            entity.y = -i * self.button_spacing + 0.2

    def pre_start_game(self, **kwargs):
        settings = kwargs
        if kwargs.get("custom"):
            settings = self.custom_settings.copy()
            for key, entity in settings.items():
                settings[key] = entity.value
        self.menu_parent.enabled = False
        self.start_game(**settings)

    def start_game(self, **kwargs):
        self.background.enabled = False

    def quit_game(self):
        self.menu_parent.enabled = True
        self.background.enabled = True

    def input(self, key):
        if __name__ == "__main__" and key in ["escape", "space"] + list(string.ascii_lowercase):
            self.quit_game()
        super().input(key)

    def set_background(self):
        self.background = Entity(
            model="quad",
            texture="shore",
            parent=self.menu_parent.parent,
            scale=(camera.aspect_ratio, 1),
            color=color.white,
            z=1,
        )


if __name__ == "__main__":
    app = MainMenuUrsina()
    app.run()
