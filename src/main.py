#
# main.py - Основной запускаемый файл программы.
#


# Импортируем:
import gdf
from gdf.audio import *
from gdf.graphics import *
from gdf.graphics.gl import *
from gdf.net import *
from gdf.physics import *
from gdf.controllers import *
from gdf import files
from gdf.input import *
from gdf.math import *
from gdf.utils import *

from datapack import DataPackage
from game import GameScene
from logoscreen import LogoScreenScene


# Основной класс:
class MainClass(Window):
    def __init__(self) -> None:
        # Создаём окно и переходим в игровой цикл:
        self.init()

    # Создать окно:
    def init(self) -> None:
        super().__init__(
            title      = "Bonfire [ReMake]",
            icon       = files.load_image("./data/icons/runapp-icon.png"),
            size       = vec2(960, 540),
            vsync      = False,
            fps        = 60,
            visible    = True,
            titlebar   = True,
            resizable  = True,
            fullscreen = False,
            min_size   = vec2(960, 540) * 0.75,
            max_size   = vec2(float("inf"), float("inf")),
            samples    = 16
        )

    # Вызывается при создании окна:
    def start(self) -> None:
        # Класс пакета данных игры:
        datapack = DataPackage()

        # Загружаем пакет данных игры:
        datapack.load("./data/content.pkg")

        # Игровая сцена:
        game_scene = GameScene(datapack)

        # Сцена с логотипами:
        logoscreen = LogoScreenScene(game_scene, 1.0, 1.0, [
            (datapack.open("logoscreen/lakuworx/logo.png"), 0.5),
            (datapack.open("logoscreen/pygdf/logo.png"), 0.5),
        ])

        show_logoscreen = True

        # Показываем сцену с логотипами:
        if show_logoscreen: self.window.set_scene(logoscreen)
        else: self.window.set_scene(game_scene)

    # Вызывается каждый кадр (игровой цикл):
    def update(self, delta_time: float, event_list: list) -> None:
        pass

    # Вызывается каждый кадр (игровая отрисовка):
    def render(self, delta_time: float) -> None:
        pass

    # Вызывается при изменении размера окна:
    def resize(self, width: int, height: int) -> None:
        pass

    # Вызывается при разворачивании окна:
    def show(self) -> None:
        pass

    # Вызывается при сворачивании окна:
    def hide(self) -> None:
        pass

    # Вызывается при закрытии окна:
    def destroy(self) -> None:
        pass


# Если этот скрипт запускают:
if __name__ == "__main__":
    MainClass()
