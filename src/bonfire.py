#
# bonfire.py - Создаёт класс костра.
#


# Импортируем:
from gdf.graphics import *
from gdf.math import *


# Класс костра:
class BonfireBlock:
    def __init__(self, position: vec2, sprites: dict, sounds: dict, tilesize: float, light: Light2D.LightLayer) -> None:
        self.position = position.xy
        self.size     = vec2(tilesize)
        self.anim     = sprites["bonfire-anim"]
        self.new      = sprites["bonfire-new"]
        self.burnt    = sprites["bonfire-burnt"]
        self.lit_fire = sounds["lit-fire"]

        self.timer    = 60.0   # Время жизни костра (это константа).
        self.fire     = 1.0    # Насколько разжён костёр от 0.0 до 1.0.
        self.is_burnt = False  # Сгорел ли костёр или нет.

        self.animator = Animator2D(len(self.anim), 0.1)

        # Освещение от костра:
        self.light = Light2D.SpriteLight(
            light, sprites["light"]["point"],
            self.position.xy, 0.0,
            vec2(2048), [1.0, 0.8, 0.6]
        )

        # Искры:
        self.sparks = ParticleEffect2D(
            texture       = [sprites["effect-spark"]],
            position      = vec2(0, 0),
            direction     = vec2(0, +10),
            start_size    = vec2(6, 6),
            end_size      = vec2(0, 0),
            speed         = vec2(64, 92),
            damping       = 0.001,
            duration      = vec2(1, 2),
            count         = 6,
            gravity       = vec2(+32.0, +0.0),
            start_angle   = 0.0,
            end_angle     = 0.0,
            size_exp      = 1.0,
            angle_exp     = 1.0,
            is_infinite   = True,
            is_local_pos  = False,
            is_dir_angle  = False,
            spawn_in      = ParticleEffect2D.SpawnInCircle(24)
        ).create()

        # Дым:
        self.smoke = ParticleEffect2D(
            texture       = [sprites["effect-smoke"]],
            position      = vec2(0, 0),
            direction     = vec2(0, +20),
            start_size    = vec2(0, 0),
            end_size      = vec2(48, 48),
            speed         = vec2(256, 256),
            damping       = 0.0025,
            duration      = vec2(5, 5),
            count         = 8,
            gravity       = vec2(+32.0, +0.0),
            start_angle   = 0.0,
            end_angle     = 0.0,
            size_exp      = 0.375,
            angle_exp     = 1.0,
            is_infinite   = True,
            is_local_pos  = False,
            is_dir_angle  = False,
            spawn_in      = ParticleEffect2D.SpawnInPoint()
        ).create()

        self.lit_fire.set_position(vec3(self.position.xy, 0.0))
        self.light.position.xy  = self.position.xy
        self.sparks.position.xy = self.position.xy
        self.smoke.position.xy  = self.position.xy

        self.animator.start()
        self.lit_fire.play(True)

    # Обновление костра:
    def update(self, delta_time: float) -> None:
        # Уменьшаем разгар костра:
        self.fire -= delta_time / self.timer
        if self.fire <= 0.0: self.is_burnt = True  # Если уровень огня меньше нуля, значит костёр сгорел.
        self.fire = clamp(self.fire, 0.0, 1.0)

        # Обновление анимации:
        self.animator.update(delta_time)

        # Если костёр сгорел:
        if self.is_burnt:
            self.lit_fire.stop()
            self.sparks.is_infinite = False
            self.smoke.is_infinite = False
            self.light.color = [0, 0, 0, 0]

        # Обновление позиций:
        self.lit_fire.set_position(vec3(self.position.xy, 0.0))
        self.light.position.xy  = self.position.xy
        self.sparks.position.xy = self.position.xy
        self.smoke.position.xy  = self.position.xy

        # Обновление систем частиц:
        self.sparks.update(delta_time)
        self.smoke.update(delta_time)

    # Рисуем костёр:
    def render(self, batch: SpriteBatch2D) -> None:
        sprite = self.anim[self.animator.get_frame()] if not self.is_burnt else self.burnt
        batch.draw(sprite, *self.position.xy-self.size.xy/2, *self.size.xy)

        self.sparks.render(batch=batch)

    # Рисуем эффекты:
    def render_effects(self, batch: SpriteBatch2D) -> None:
        self.smoke.render(batch=batch)
