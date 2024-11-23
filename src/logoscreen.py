#
# logoscreen.py - Сцена (экран) с логотипами.
#


# Импортируем:
from gdf.graphics import *
from gdf.input import *
from gdf.math import *
from gdf import files


# Класс сцены:
class LogoScreenScene(Scene):
    def __init__(self, next_scene: Scene, logo_time: float, logo_delay: float, files: list, bg: list = None) -> None:
        # Цвет заливки фона:
        self.bg_color = [0.0, 0.0, 0.0] if bg is None else bg

        self.next_scene       = next_scene  # Следующая сцена.
        self.logo_time        = logo_time   # Скорость показа одного логотипа.
        self.logo_delay       = logo_delay  # Задержка на логотипе.
        self.logo_files       = files       # Список картинок-логотипов.
        self.logo_delay_timer = 0.0         # Таймер задержки логотипа.
        self.logos            = []          # Список загруженных спрайтов (логотипов).
        self.switch_alpha     = False       # Переключатель показа-скрытия логотипа.
        self.current_logo     = 0           # Текущий логотип.
        self.camera           = None        # 2D камера.

    # Вызывается при переключении на эту сцену:
    def start(self) -> None:
        # 2D камера:
        self.camera = Camera2D(
            width    = self.window.get_width(),
            height   = self.window.get_height(),
            position = vec2(0, 0),
            angle    = 0.0,
            zoom     = 1.0,
            meter    = 100
        )

        # Обработчик ввода:
        self.input = InputHandler(self.window)

        # Загружаем логотипы:
        for logo in self.logo_files:
            self.logos.append([Sprite2D(files.load_texture(logo[0])), logo[1], 0.0])

    # Вызывается каждый кадр (игровой цикл):
    def update(self, delta_time: float, event_list: list) -> None:
        # Обновляем альфа канал логотипа:
        if self.switch_alpha:
            # Скрываем логотип:
            if self.logo_delay_timer > 0.0: self.logo_delay_timer -= delta_time
            else: self.logos[self.current_logo][2] -= delta_time * 1/self.logo_time
        else:
            # Показываем логотип:
            self.logos[self.current_logo][2] += delta_time * 1/self.logo_time
            if self.logos[self.current_logo][2] >= 1.0:
                self.logo_delay_timer = self.logo_delay
                self.switch_alpha = True

        # Если отпустили любую кнопку на клавиатуре, пропускаем показ логотипа:
        key_up = self.input.get_key_up()
        if any(key_up.keycodes if key_up.keycodes else [False]):
            # self.logos[self.current_logo][2] = 0.0
            self.logo_delay_timer = 0.0
            self.switch_alpha = True

        # Если альфа канал логотипа меньше или равен нулю после второй стадии, переключаем логотип:
        if self.logos[self.current_logo][2] <= 0.0 and self.switch_alpha:
            self.current_logo += 1
            self.switch_alpha = False

        # Если мы отрисовали все возможные логотипы, переключаем сцену:
        if self.current_logo >= len(self.logos):
            self.current_logo = len(self.logos)-1
            self.window.set_scene(self.next_scene)

        self.camera.update()

    # Вызывается каждый кадр (игровая отрисовка):
    def render(self, delta_time: float) -> None:
        self.window.clear(*self.bg_color)

        # Рисуем логотип:
        logo = self.logos[self.current_logo]
        sprite, scale, alpha = logo[0], logo[1], logo[2]
        sprite_size = vec2(sprite.texture.width * scale, sprite.texture.height * scale)
        sprite.render(
            -sprite_size.x/2, -sprite_size.y/2,
            sprite_size.x, sprite_size.y, 0.0,
            [1.0, 1.0, 1.0, clamp(alpha, 0.0, 1.0)]
        )

        self.window.display()

    # Вызывается при изменении размера окна:
    def resize(self, width: int, height: int) -> None:
        self.camera.resize(width, height)

    # Вызывается при разворачивании окна:
    def show(self) -> None:
        pass

    # Вызывается при сворачивании окна:
    def hide(self) -> None:
        pass

    # Вызывается при закрытии сцены:
    def destroy(self) -> None:
        # Удаляем текстуры логотипов:
        for logo in self.logos:
            logo[0].destroy()
