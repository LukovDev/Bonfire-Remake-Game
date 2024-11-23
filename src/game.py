#
# game.py - Создаёт основную игровую сцену.
#


# Импортируем:
import os
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

# Прочий импорт:
from arrow import Arrow
from bonfire import BonfireBlock
from datapack import DataPackage
from loader import GameLoader
from player import Player
from resources import StickResource


# Игровая сцена:
class GameScene(Scene):
    def __init__(self, datapack: DataPackage) -> None:
        self.datapack  = datapack                               # Класс пакета данных игры.
        self.load_file = lambda path: self.datapack.open(path)  # Загрузить файл из пакета данных.

        self.input      = None   # Обработчик ввода.
        self.camera     = None   # Игровая камера.
        self.trgt_pos   = None   # Позиция цели слежения камеры.
        self.trgt_zoom  = None   # Целевой масштаб камеры.
        self.controller = None   # Контроллер камеры для свободного передвижения. ДЛЯ ОТЛАДКИ.
        self.debug_mode = False  # Режим отладки.

        self.layers        = [[] for _ in range(256)]  # Массив массивов функций для отрисовки по слоям (256 слоёв).
        self.batch         = None      # Пакетная отрисовка.
        self.floor         = None      # Пакетная отрисовка пола.
        self.floorsize     = 128       # Размер пола.
        self.tile_size     = 92        # Размер тайла.
        self.day_per_sec   = 1/(60*3)  # 1 день в 3 минуты.
        self.record        = 0         # Максимальный рекорд по сожённым ресурсам.
        self.game_run      = True      # Запущена ли основная игра.
        self.game_tutorial = True      # Игровой туториал + настройки.
        self.game_menu     = False     # Игровое меню.
        self.game_over     = False     # Конец игры.
        self.game_time     = 0.0       # Игровое время (отдельное от времени окна).

        self.light_layer   = None  # Слой освещения.
        self.player_light  = None  # Освещение игрока.
        self.bonfire_light = None  # Освещение костра.

        self.sprites   = None  # Спрайты.
        self.sounds    = None  # Звуки.
        self.listener  = None  # Слушатель.
        self.sound_env = None  # Звуковое окружение.
        self.font      = None  # Шрифт.
        self.fonts     = None  # Шрифты.

        self.bonfire       = None  # Костёр.
        self.player        = None  # Игрок.
        self.bonfire_arrow = None  # Стрелка для костра.
        self.resources     = []    # Список ресурсов.

    # Обновить окно:
    def init(self) -> None:
        self.window.set_config(
            title      = "Bonfire [ReMaked on PyGDF-v1.2]",
            icon       = files.load_image("./data/icons/runapp-icon.png"),
            size       = None,
            vsync      = True,
            fps        = 60,
            visible    = True,
            titlebar   = True,
            resizable  = True,
            fullscreen = False,
            min_size   = vec2(960, 540) * 0.75,
            max_size   = vec2(float("inf"), float("inf")),
            samples    = 16
        )

    # Функция случайной позиции в тайлах:
    def random_tile_pos(self) -> vec2:
        return vec2(
            random.randint(0, self.floorsize-1),
            random.randint(0, self.floorsize-1)
        ) * self.tile_size+self.tile_size/2

    # Создать костёр:
    def create_bonfire(self) -> None:
        # Позиция костра на карте со смещением от краёв в 16 тайлов:
        pos = vec2(
            random.randint(16, self.floorsize-16),
            random.randint(16, self.floorsize-16)
        )*self.tile_size+self.tile_size/2

        self.bonfire = BonfireBlock(pos, self.sprites, self.sounds, self.tile_size, self.light_layer)
        self.layers[0].append(self.bonfire.render)          # Добавляем костёр на нулевой слой отрисовки.
        self.layers[2].append(self.bonfire.render_effects)  # Добавляем эффекты на слой выше, чем слой игрока.

    # Создать игрока:
    def create_player(self) -> None:
        # Позиция игрока в пределах 4 тайлов от костра:
        player_bonfire_offset = vec2(0, 0)
        gen_pos = lambda x, y: random.randint(x, y)*self.tile_size
        # Генерируем координату до тех пор, пока она НЕ будет равна нулю:
        while player_bonfire_offset.x == 0.0: player_bonfire_offset.x = gen_pos(-4, 4)
        while player_bonfire_offset.y == 0.0: player_bonfire_offset.y = gen_pos(-4, 4)

        # Создаём игрока:
        self.player = Player(self.bonfire.position.xy+player_bonfire_offset, self.sprites, self.light_layer)
        if not self.debug_mode: self.camera.position.xy = self.player.position.xy
        self.layers[1].append(self.player.render)

    # Создать палку:
    def spawn_stick(self, position: vec2 = None, force: float = None, direction: vec2 = None) -> None:
        stick = StickResource(
            self.random_tile_pos() if position is None else position,
            self.sprites, self.tile_size, force, direction)
        self.resources.append(stick)
        self.layers[0].append(stick.render)

    # Удалить ресурс:
    def kill_resource(self, resource) -> None:
        self.resources.remove(resource)
        self.layers[0].remove(resource.render)

    # Поднять палку:
    def pickup_stick(self, stick: StickResource) -> None:
        # Удаляем палку:
        self.kill_resource(stick)

        # Наделяем игрока эффектом поднятой палки:
        self.player.pickup_stick = True

        # Воспроизводим звук поднятия палки:
        self.sounds["pick-up"].set_position(vec3(self.player.position.xy, 0.0))
        self.sounds["pick-up"].play()

    # Бросить палку:
    def throw_stick(self) -> None:
        # Уменьшаем 10% стамины у игрока:
        self.player.stamina -= 0.1
        # Воспроизводим звук бросания палки:
        self.sounds["throw-stick"].set_position(vec3(self.player.position.xy, 0.0))
        self.sounds["throw-stick"].play()

    # Сжечь палку:
    def burn_stick(self) -> None:
        # Воспроизводим звук сжигания палки:
        self.sounds["splash-fire"].set_position(vec3(self.player.position.xy, 0.0))
        self.sounds["splash-fire"].play()

        # Добавляем здоровье костру:
        self.bonfire.fire += StickResource.heal

        # Создаём новую палку:
        self.spawn_stick()

    # Загрузить игровые данные:
    def load_game_data(self) -> None:
        if os.path.isfile("data/game.data"):
            data = files.load_json("data/game.data")
            self.record = data["collected"]
            self.sound_env.volume = data["sound-volume"]

    # Сохранить игровые данные:
    def save_game_data(self) -> None:
        files.save_json("data/game.data", {
            "collected": self.record,
            "sound-volume": self.sound_env.volume,
        })

    # Перезапуск игры:
    def restart(self) -> None:
        if self.bonfire is not None:
            self.bonfire.light.destroy()
            self.bonfire = None
        if self.player is not None:
            self.player.light.destroy()
            self.player = None

        self.resources.clear()
        [layer.clear() for layer in self.layers]

        # Создаём костёр:
        self.create_bonfire()

        # Создаём игрока:
        self.create_player()

        # Создаём стрелку для костра:
        self.bonfire_arrow = Arrow(self.player.position, self.bonfire.position, self.sprites, self.tile_size)

        # Создаём 48 палок на карте:
        for i in range(48): self.spawn_stick()

        self.game_menu = False
        self.game_over = False
        self.game_run = True
        self.game_time = 0.0

    # Вызывается при переключении на эту сцену:
    def start(self) -> None:
        # Обновляем окно:
        self.init()

        # Наш обработчик ввода данных:
        self.input = InputHandler(self.window)

        # 2D камера:
        self.camera = Camera2D(
            width    = self.window.get_width(),
            height   = self.window.get_height(),
            position = vec2(0, 0),
            angle    = 0.0,
            zoom     = 0.75
        )

        # Цели камеры:
        self.trgt_pos  = self.camera.position.xy
        self.trgt_zoom = self.camera.zoom

        # Контроллер камеры:
        self.controller = CameraController2D(self.input, self.camera)

        # Пакетная отрисовка:
        self.batch = SpriteBatch2D()

        # Пакетная отрисовка пола:
        self.floor = SpriteBatch2D()

        # Загрузка игровых данных:

        # Спрайты:
        self.sprites = GameLoader.load_sprites(self.load_file)

        # Звуки:
        self.sounds = GameLoader.load_sounds(self.load_file)

        # Слушатель:
        self.listener = Listener()

        # Звуковое окружение:
        self.sound_env = SoundEnvironment(self.listener, 0.5)
        for sound in self.sounds.values(): self.sound_env.add(sound, 2*self.tile_size, 24*self.tile_size, 4.0)

        # Шрифты:
        self.font = FontFile(self.load_file("fonts/pixel-font.ttf")).load()
        self.fonts = {
            "fire":      FontGenerator(self.font),
            "stamina":   FontGenerator(self.font),
            "record":    FontGenerator(self.font),
            "collected": FontGenerator(self.font),
            "game-over": FontGenerator(self.font),
            "restart":   FontGenerator(self.font),
        }

        # Предварительно рисуем пол:
        self.floor.begin()
        fs, ts, land = self.floorsize, self.tile_size, self.sprites["lands"]["snow"]
        [self.floor.draw(land, x*ts, y*ts, ts, ts) for y in range(fs) for x in range(fs)]
        self.floor.end()

        # Настраиваем освещение:
        self.light_layer = Light2D.LightLayer(self.camera, [0.0, 0.0, 0.0, 0.0], 1.0, 0.0)

        # Игровые данные:
        self.load_game_data()

        # Настройка игры:

        self.restart()  # Перезапуском всё настроим.

    # Вызывается каждый кадр (игровой цикл):
    def update(self, delta_time: float, event_list: list) -> None:
        # Если нажимают F4 + F5, включаем режим отладки:
        k_down = self.input.get_key_down()
        if k_down[Key.K_F4] and k_down[Key.K_F5]: self.debug_mode = not self.debug_mode

        # Обновляем контроллер камеры для отладки:
        if self.debug_mode:
            if k_down[Key.K_r]: self.restart()  # Если в режиме отладки нажать R, то уровень перезагрузится.
            if k_down[Key.K_g]: self.game_run = not self.game_run  # Если нажать G, то можно останавливать игру.
            self.controller.update(delta_time)
            self.camera.zoom = clamp(self.camera.zoom, 0.01, 1000)
        else: self.controller.target_pos.xy = self.trgt_pos.xy

        # Показать или скрыть игровое меню:
        if k_down[Key.K_ESCAPE]:
            self.game_menu = not self.game_menu
            self.game_run = not self.game_menu

        # Если надо показать туториал:
        if self.game_tutorial:
            if k_down.keycodes:
                self.sounds["lit-fire"].play(True)
                self.game_tutorial = False
                self.game_menu = False
                self.game_run = True
                self.camera.zoom = 0.0
            else:
                self.game_run = False
                self.game_menu = False
                self.sounds["lit-fire"].stop()

        # Если конец игры:
        if self.game_over:
            self.game_menu = False
            self.game_run = False
            self.sounds["lit-fire"].stop()

        # Игровое меню:
        if self.game_menu:
            print(1)

        # Если игра работает:
        if self.game_run:
            self.game_time += delta_time  # Увеличиваем игровое время.

            # Обновляем рекорд:
            if self.player.collected > self.record: self.record = self.player.collected

            # Обновляем сутки:
            self.light_layer.ambient[3] = float(((sin(radians(self.game_time*self.day_per_sec*360))+1)/2)*0.933)

            # Обновляем игрока:
            if self.player:
                self.player.update(delta_time, self.camera, self.input, self.spawn_stick, self.throw_stick)
                # Ограничиваем игрока в рамках пола:
                self.player.position.xy = clamp(self.player.position.xy, vec2(0.0), vec2(self.floorsize*self.tile_size))
                self.trgt_pos = self.player.position.xy  # Обновляем цель слежения камеры.

            # Позиция и радиус игрока:
            pp, pr = self.player.position.xy, max(abs(self.player.size))/3

            # Проверяем пересечение игрока с ресурсом:
            for r in self.resources:
                # Обновляем и ограничиваем координаты ресурса на карте:
                r.update(delta_time)
                r.position.xy = clamp(r.position.xy, vec2(0.0), vec2(self.floorsize*self.tile_size))

                rp, rr = r.position.xy, max(abs(r.size))/3
                if Intersects.circle_circle(pp, pr, rp, rr) and not self.player.pickup_stick and r.pick_up_timer <= 0:
                    if isinstance(r, StickResource): self.pickup_stick(r)

                # Проверяем пересечение игрока с костром:
                bp, br = self.bonfire.position.xy, max(abs(self.bonfire.size))/3
                if Intersects.circle_circle(rp, rr, bp, br) and not self.bonfire.is_burnt:
                    self.kill_resource(r)       # Удаляем ресурс.
                    self.player.collected += 1  # Увеличиваем кол-во сожжённых ресурсов на 1.
                    self.burn_stick()           # Сжигаем палку.

            # Проверяем пересечение игрока с костром:
            # bp, br = self.bonfire.position.xy, max(abs(self.bonfire.size))/3
            # if Intersects.circle_circle(pp, pr, bp, br) and self.player.pickup_stick and not self.bonfire.is_burnt:
            #     self.player.pickup_stick = False  # Убираем у игрока эффект поднятой палки.
            #     self.player.collected    += 1     # Увеличиваем кол-во сожжённых ресурсов на 1.
            #     self.burn_stick()                 # Сжигаем палку.

            # Обновляем костёр:
            self.bonfire.update(delta_time)

            # Если костёр сгорел, игра окончена:
            if self.bonfire.is_burnt: self.game_over = True

            # Обновляем параметры камеры:
            if not self.debug_mode:
                self.camera.position.xy += (self.trgt_pos.xy-self.camera.position.xy)*0.1*self.camera.meter*delta_time
                self.trgt_zoom = clamp(self.trgt_zoom-(self.input.get_mouse_scroll().y*0.1), 0.75, 1.5)
                self.camera.zoom += (self.trgt_zoom-self.camera.zoom) * 10.0 * delta_time

        # Обновляем звук:
        self.listener.set_position(vec3(*self.camera.position.xy, 0.0))
        self.sound_env.update()

        # Обновляем камеру:
        self.camera.update()

    # Вызывается каждый кадр (игровая отрисовка):
    def render(self, delta_time: float) -> None:
        # Очищаем окно (значения цвета от 0 до 1):
        self.window.clear(0.95, 0.96, 0.98)

        if not self.game_tutorial:
            # Рисуем пол:
            self.floor.render(clear_batch=False)

            # Рисуем существ:
            self.batch.begin()
            for layer in self.layers:
                for func in layer: func(self.batch)
            self.batch.end()
            self.batch.render()

            # Рисуем свет:
            self.light_layer.render()

            # Рисуем стрелку:
            self.bonfire_arrow.render([1.0, 0.5, 0.0])

        # Рисуем интерфейс:
        self.camera.ui_begin()
        width = 256
        height = 16
        lines = 2
        self.sprites["ui"]["pixel"].render(
            self.window.get_width()/2-width/2, self.window.get_height()-height*lines,
            width, height*lines, color=[0.25, 0.25, 0.25]
        )
        self.sprites["ui"]["pixel"].render(
            self.window.get_width()/2-width/2, self.window.get_height()-height*1,
            (self.bonfire.fire)*width, height, color=[1.0, 0.5, 0.0]
        )
        self.sprites["ui"]["pixel"].render(
            self.window.get_width()/2-width/2, self.window.get_height()-height*2,
            (self.player.stamina)*width, height, color=[0.15, 0.85, 0.15]
        )

        # Запекаем тексты:
        self.fonts["fire"].bake_texture(f"{round(self.bonfire.fire*100)}%", 14, [1, 1, 1], smooth=False)
        self.fonts["stamina"].bake_texture(f"{round(self.player.stamina*100)}%", 14, [1, 1, 1], smooth=False)
        self.fonts["collected"].bake_texture(f"Collected: {self.player.collected}", 24, [1, 1, 1], smooth=False)
        self.fonts["record"].bake_texture(f"Record: {self.record}", 18, [1, 1, 1], smooth=False)
        self.fonts["game-over"].bake_texture("Game Over", 32, smooth=False)
        self.fonts["restart"].bake_texture("Restart", 24, smooth=False)

        fire_texture = self.fonts["fire"].get_texture()
        Sprite2D(fire_texture).render(
            self.window.get_width()/2-fire_texture.width/2,
            self.window.get_height()-(height*1)/2-fire_texture.height/2
        )

        stamina_texture = self.fonts["stamina"].get_texture()
        Sprite2D(stamina_texture).render(
            self.window.get_width()/2-stamina_texture.width/2,
            self.window.get_height()-(height*3)/2-stamina_texture.height/2
        )

        Sprite2D(self.fonts["record"].get_texture()).render(32, 64)
        Sprite2D(self.fonts["collected"].get_texture()).render(32, 32)

        # Если игра окончена:
        if self.game_over:
            size = self.window.get_size()

            # Затемняем экран:
            Sprite2D().render(0, 0, size.x, size.y, color=(0.0, 0.0, 0.0, 0.4))

            # Рисуем текст конца игры:
            gameover_texture = self.fonts["game-over"].get_texture()
            gameover_size = vec2(gameover_texture.width, gameover_texture.height)
            Sprite2D(gameover_texture).render(size.x/2-gameover_size.x/2, size.y/2-gameover_size.y/2+48)

            # Кнопка перезапуска игры:
            butt_size  = vec2(256, 80)
            butt_color = [0.15, 0.15, 0.15]
            butt_rect  = [size.x/2-butt_size.x/2, size.y/2-butt_size.y/2-48, butt_size.x, butt_size.y]

            # Проверка пересечения мыши с кнопкой перезапуска:
            mouse_pos = vec2(self.input.get_mouse_pos().x, size.y-self.input.get_mouse_pos().y)
            if Intersects.point_rectangle(mouse_pos, butt_rect):
                if self.input.get_mouse_down()[0]: self.restart()  # При нажатии, перезапускаем игру.
                butt_color = [0.25, 0.25, 0.25]  # Меняем цвет кнопки при наведении на неё.

            # Рисуем подложку кнопки и саму кнопку:
            Sprite2D().render(butt_rect[0]-4, butt_rect[1]-4, butt_rect[2]+8, butt_rect[3]+8, color=[0.25, 0.25, 0.25])
            Sprite2D().render(*butt_rect, color=butt_color)

            # Рисуем текст кнопки:
            restart_texture = self.fonts["restart"].get_texture()
            restart_size = vec2(restart_texture.width, restart_texture.height)
            Sprite2D(restart_texture).render(size.x/2-restart_size.x/2, size.y/2-restart_size.y/2-48)
        self.camera.ui_end()

        # Если надо показать туториал:
        if self.game_tutorial:
            self.window.clear(0.0, 0.0, 0.0)
            self.camera.ui_begin()
            tut_size = vec2(self.sprites["ui"]["tutorial"].width, self.sprites["ui"]["tutorial"].height)*4
            self.sprites["ui"]["tutorial"].render(
                self.window.get_width()/2-tut_size.x/2, self.window.get_height()/2-tut_size.y/2, *tut_size.xy)
            self.camera.ui_end()

        # Отрисовываем всё в окно:
        self.window.display()

    # Вызывается при изменении размера окна:
    def resize(self, width: int, height: int) -> None:
        self.camera.resize(width, height)  # Обновляем размер камеры.

    # Вызывается при разворачивании окна:
    def show(self) -> None:
        pass

    # Вызывается при сворачивании окна:
    def hide(self) -> None:
        pass

    # Вызывается при закрытии сцены:
    def destroy(self) -> None:
        self.datapack.destroy()
        self.save_game_data()
