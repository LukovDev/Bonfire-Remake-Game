#
# arrow.py - Создаёт класс стрелки, указывающий на костёр.
#


# Импортируем:
from gdf.graphics import *
from gdf.math import *
from gdf.utils import *


# Класс стрелки:
class Arrow:
    def __init__(self, player_pos: vec2, bonfire_pos: vec2, sprites: dict, tile_size: float) -> None:
        self.player_pos  = player_pos
        self.bonfire_pos = bonfire_pos
        self.sprite      = sprites["ui"]["arrow"]
        self.size        = vec2(28, 28)
        self.length      = 64
        self.near_dist   = 8.0 * tile_size + self.length

    # Рисуем стрелку:
    def render(self, color: list) -> None:
        if length(self.bonfire_pos.xy-self.player_pos.xy) < self.near_dist: return
        angle = Utils2D.get_angle_points(self.player_pos.xy, self.bonfire_pos.xy)
        offset = vec2(sin(radians(angle))*self.length, cos(radians(angle))*self.length)
        self.sprite.render(*self.player_pos.xy-self.size.xy/2+offset.xy, *self.size.xy, angle, color)
