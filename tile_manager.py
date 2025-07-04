# Разбиение изобрaжения на тайлы (части)

from OpenGL.GL import *
from PyQt5.QtCore import QPointF

class Tile:
    def __init__(self, x, y, width, height, texture_id):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.texture_id = texture_id

class TileManager:
    def __init__(self):
        self.tiles = []
        self.tile_size = 1024

    def split_into_tiles(self, image_data, img_width, img_height, progress_callback=None):
        self.tiles.clear()
        total_tiles = ((img_height + self.tile_size - 1) // self.tile_size) * \
                      ((img_width + self.tile_size - 1) // self.tile_size)
        current_tile = 0

        for y in range(0, img_height, self.tile_size):
            for x in range(0, img_width, self.tile_size):
                tile_width = min(self.tile_size, img_width - x)
                tile_height = min(self.tile_size, img_height - y)

                tile_data = image_data[y:y + tile_height, x:x + tile_width]

                texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tile_width, tile_height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, tile_data)

                self.tiles.append(Tile(x, y, tile_width, tile_height, texture_id))

                current_tile += 1
                if progress_callback:
                    percent = int((current_tile / total_tiles) * 100)
                    progress_callback(percent)

    def get_visible_tiles(self, viewport_width, viewport_height, pan, zoom, rotation_angle=0,
                          rotation_center=QPointF(0, 0)):
        visible_tiles = []

        # Рассчитываем расширенную область видимости с учетом поворота
        expanded_viewport = max(viewport_width, viewport_height) * 1.5

        for tile in self.tiles:
            # Центр тайла в мировых координатах
            tile_center_x = tile.x + tile.width / 2
            tile_center_y = tile.y + tile.height / 2

            # Преобразуем координаты с учетом поворота
            if rotation_angle != 0:
                # Смещаем в систему координат с центром в rotation_center
                dx = tile_center_x - rotation_center.x()
                dy = tile_center_y - rotation_center.y()

                # Поворачиваем
                import math
                angle_rad = math.radians(rotation_angle)
                cos_val = math.cos(angle_rad)
                sin_val = math.sin(angle_rad)
                rotated_dx = dx * cos_val - dy * sin_val
                rotated_dy = dx * sin_val + dy * cos_val

                # Возвращаем в мировые координаты
                tile_center_x = rotated_dx + rotation_center.x()
                tile_center_y = rotated_dy + rotation_center.y()

            # Проверяем, попадает ли тайл в расширенную область видимости
            tile_screen_x = tile_center_x * zoom + pan.x() - (tile.width * zoom) / 2
            tile_screen_y = tile_center_y * zoom + pan.y() - (tile.height * zoom) / 2
            tile_screen_width = tile.width * zoom
            tile_screen_height = tile.height * zoom

            if (tile_screen_x + tile_screen_width > -expanded_viewport and
                    tile_screen_y + tile_screen_height > -expanded_viewport and
                    tile_screen_x < viewport_width + expanded_viewport and
                    tile_screen_y < viewport_height + expanded_viewport):
                visible_tiles.append(tile)

        return visible_tiles

    def is_empty(self):
        return len(self.tiles) == 0