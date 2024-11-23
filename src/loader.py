#
# loader.py - Создаёт функции для загрузки игровых данных.
#


# Импортируем:
from gdf.audio import *
from gdf.graphics import *
from gdf import files


# Класс загрузчика игровых данных:
class GameLoader:
    # Загрузить спрайты:
    @staticmethod
    def load_sprites(load_file) -> dict:
        load_sprite = lambda path, pixelized: files.load_sprite(load_file(path), pixelized=pixelized)
        return {
            # Костёр:
            "bonfire-anim": [load_sprite(f"sprites/bonfire/anim-{c+1}.png", True) for c in range(8)],
            "bonfire-new":   load_sprite("sprites/bonfire/new.png", pixelized=True),
            "bonfire-burnt": load_sprite("sprites/bonfire/burnt.png", pixelized=True),

            # Эффекты:
            "effect-smoke": load_sprite("sprites/effects/smoke.png", pixelized=True),
            "effect-spark": load_sprite("sprites/effects/spark.png", pixelized=True),

            # Поверхности:
            "lands": {
                "snow": load_sprite("sprites/lands/snow.png", pixelized=True),
            },

            # Игрок:
            "player-run":  [load_sprite(f"sprites/player/run/anim-{c+1}.png", pixelized=True) for c in range(4)],
            "player-stick": [load_sprite(f"sprites/player/stick/anim-{c+1}.png", pixelized=True) for c in range(4)],

            # Ресурсы:
            "resources": {
                "stick": load_sprite(f"sprites/resources/stick.png", pixelized=True),
            },

            # Интерфейс:
            "ui": {
                "arrow":    load_sprite(f"sprites/ui/arrow.png", pixelized=True),
                "pixel":    load_sprite(f"sprites/ui/pixel.png", pixelized=True),
                "tutorial": load_sprite(f"sprites/ui/tutorial.png", pixelized=True),
            },

            # Освещение:
            "light": {
                "point": load_sprite(f"sprites/light/point.png", pixelized=False),
            },
        }


    # Загрузить звуки:
    @staticmethod
    def load_sounds(load_file) -> dict:
        return {
            "lit-fire":    Sound().load(load_file("sounds/lit-fire.ogg")),
            "pick-up":     Sound().load(load_file("sounds/pick-up.ogg")),
            "splash-fire": Sound().load(load_file("sounds/splash-fire.ogg")),
            "throw-stick": Sound().load(load_file("sounds/throw-stick.ogg")),
        }
