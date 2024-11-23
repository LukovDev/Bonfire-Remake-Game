#
# player.py - Создаёт класс игрока.
#


# Импортируем:
from gdf.graphics import *
from gdf.input import *
from gdf.math import *
from gdf.utils import *


# Класс игрока:
class Player:
    def __init__(self, position: vec2, sprites: dict, light: Light2D.LightLayer) -> None:
        self.position = position.xy

        self.size        = vec2(92, 92)
        self.stick_speed = 3.0
        self.speed       = 5.0
        self.shift_speed = 10.0
        self.throw_force = 10.0

        self.run_anim  = sprites["player-run"]
        self.stick_anim = sprites["player-stick"]
        self.animator  = Animator2D(len(self.run_anim), 0.1)

        # Освещение от игрока:
        self.light = Light2D.SpriteLight(
            light, sprites["light"]["point"],
            self.position.xy, 0.0,
            vec2(256), [1, 1, 1]
        )

        self.pickup_stick = False
        self.run_animator = self.animator.get_active()
        self.flip_x = False

        self.collected       = 0     # Количество сожжённых ресурсов.
        self.stamina         = 1.0   # Выносливость от 0.0 до 1.0.
        self.stamina_heal    = 0.25  # Восстановление выносливости в секунду.
        self.stamina_loss    = 0.25  # Потеря выносливости в секунду.
        self.stamina_per_sec = 0.01  # Сколько раз восстанавливать выносливость в секунду (100 раз).
        self.stamina_timer   = 0.0   # Таймер для восстановления выносливости.

    # Обновление игрока:
    def update(self, delta_time: float, camera: Camera2D, input: InputHandler, spawn_stick, throw_stick) -> None:
        key_pressed = input.get_key_pressed()  # Нажатые клавиши.

        # Обработка управления персонажем:
        velocity = vec2(0.0)  # Вектор направления движения.

        # Перемещение по вертикали:
        if key_pressed[Key.K_w]:  # Вверх:
            velocity.y += 1.0
        if key_pressed[Key.K_s]:  # Вниз:
            velocity.y -= 1.0

        # Перемещение по горизонтали:
        if key_pressed[Key.K_a]:  # Влево:
            velocity.x -= 1.0
            if not self.flip_x: self.flip_x = True
        if key_pressed[Key.K_d]:  # Вправо:
            velocity.x += 1.0
            if self.flip_x: self.flip_x = False

        # Выбрасываем палку:
        if input.get_key_down()[Key.K_SPACE] and self.pickup_stick:
            self.pickup_stick = False
            direction = Utils2D.get_direction_in_angle(
                Utils2D.get_angle_points(self.position, Utils2D.local_to_global(camera, input.get_mouse_pos()))
            )
            self.flip_x = True if direction.x < 0.0 else False
            spawn_stick(self.position.xy, self.throw_force*100, direction)
            throw_stick()

        # Можем ли бегать. Если да, тратим выносливость:
        shift_active = key_pressed[Key.K_LSHIFT] and self.stamina > 0 and length(velocity) > 0 and not self.pickup_stick
        if shift_active: self.stamina -= self.stamina_loss * delta_time

        # Восстанавливаем выносливость игрока:
        if self.stamina_timer <= 0.0:
            # Восстанавливаем выносливость только если мы не двигаемся и не несём ресурс:
            if not (length(velocity) > 0.0 and key_pressed[Key.K_LSHIFT]) and not self.pickup_stick:
                self.stamina += self.stamina_heal * delta_time
            self.stamina_timer = self.stamina_per_sec
        self.stamina_timer -= delta_time
        self.stamina = clamp(self.stamina, 0.0, 1.0)

        # Перемещаем игрока:
        if length(velocity) > 0.0: velocity = normalize(velocity)
        speed = self.stick_speed if self.pickup_stick else self.shift_speed if shift_active else self.speed
        self.position.xy += velocity * speed * 100 * delta_time

        # Перемещаем источник света:
        self.light.position.xy = self.position.xy

        # Обработка анимации:
        self.animator.update(delta_time*(speed/self.speed))
        if length(velocity) > 0.0:
            if not self.run_animator: self.animator.start() ; self.run_animator = True
        elif self.run_animator: self.animator.stop() ; self.run_animator = False

    # Рисуем игрока:
    def render(self, batch: SpriteBatch2D) -> None:
        anim_set = self.run_anim if not self.pickup_stick else self.stick_anim
        batch.draw(
            anim_set[self.animator.get_frame()],
            self.position.x-self.size.x/2 + (self.size.x if self.flip_x else 0),
            self.position.y-self.size.y/2,
            self.size.x if not self.flip_x else -self.size.x,
            self.size.y
        )
