import string
import sys

from ursina.audio import Audio
from ursina.camera import instance as camera

from ursina import color
from ursina.entity import Entity
from ursina.main import Ursina
from ursina.prefabs.animator import Animator
from ursina.prefabs.first_person_controller import Button
from ursina.prefabs.slider import Slider
from ursina.sequence import Wait, Func, Sequence

# from ursina import *


class MenuButton(Button):
    def __init__(self, text="", **kwargs):
        super().__init__(
            text, scale=(0.25, 0.075), highlight_color=color.azure, **kwargs
        )

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
            MenuButton("Start game", on_click=self.start_game),
            MenuButton(
                "Custom game",
                on_click=Func(setattr, self.state_handler, "state", "custom_menu"),
            ),
            MenuButton("Quit", on_click=Sequence(Wait(0.01), Func(sys.exit))),
        ]
        for i, button in enumerate(self.main_menu.buttons):
            button.parent = self.main_menu
            button.y = -i * self.button_spacing

    def setup_custom_menu_buttons(self):
        def set_volume_multiplier():
            Audio.volume_multiplier = volume_slider.value

        volume_slider = Slider(
            0,
            1,
            default=Audio.volume_multiplier,
            step=0.1,
            text="Master Volume:",
            parent=self.custom_menu,
            x=-0.25,
        )
        volume_slider.on_value_changed = set_volume_multiplier

        items = [volume_slider]

        self.custom_menu.back_button = MenuButton(
            parent=self.custom_menu,
            text="Back",
            y=((-len(items) - 2) * self.button_spacing),
            x=-0.25,
            origin_x=-0.5,
            on_click=Func(setattr, self.state_handler, "state", "main_menu"),
        )

    def set_background(self):
        self.background = Entity(
            model="quad",
            texture="shore",
            parent=self.menu_parent.parent,
            scale=(camera.aspect_ratio, 1),
            color=color.white,
            z=1,
        )

    def start_game(self):
        self.menu_parent.enabled = False
        self.background.enabled = False

    def quit_game(self):
        self.menu_parent.enabled = True
        self.background.enabled = True

    def input(self, key):
        if __name__ == "__main__" and key in ["escape", "space"] + list(
            string.ascii_lowercase
        ):
            self.quit_game()
        super().input(key)


if __name__ == "__main__":
    app = MainMenuUrsina()
    app.run()
