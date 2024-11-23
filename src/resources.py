#
# resources.py - Создаёт классы ресурсов.
#


# Импортируем:
from gdf.graphics import *
from gdf.math import *


# Класс палки:
class StickResource:
    heal = 0.20  # Восстановить 20% жара костра.

    def __init__(self, position: vec2, sprites: dict, tilesize: float, force: float, direction: vec2) -> None:
        self.position  = position.xy
        self.size      = vec2(tilesize) * 0.75  # Размер объекта на 25% меньше чем размер плитки пола.
        self.sprite    = sprites["resources"]["stick"]
        self.force     = force if force is not None else 0.0
        self.origforce = self.force
        self.direction = direction if direction is not None else vec2(0.0)
        self.pick_up_per_sec = 1.0  # Сколько секунд надо для поднятия ресурса после броска.
        self.pick_up_timer   = 0.0

        self.set_pick_up_timer()

    # Установить таймер на поднятие ресурса:
    def set_pick_up_timer(self) -> None:
        self.pick_up_timer = self.pick_up_per_sec

    # Обновление палки:
    def update(self, delta_time: float) -> None:
        self.force -= self.origforce * delta_time
        self.force = max(self.force, 0.0)
        direction = vec2(0.0) if length(self.direction) <= 0.0 else normalize(self.direction)
        self.position.xy += self.direction * self.force * delta_time

        # Уменьшаем таймер на поднятие:
        self.pick_up_timer = clamp(self.pick_up_timer-delta_time, 0.0, self.pick_up_per_sec)

    # Рисуем палку:
    def render(self, batch: SpriteBatch2D) -> None:
        batch.draw(self.sprite, *self.position.xy-self.size.xy/2, *self.size.xy)
