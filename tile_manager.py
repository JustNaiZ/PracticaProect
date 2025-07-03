# Разбиение изображения на тайлы (части)

from OpenGL.GL import *
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


    def get_visible_tiles(self, viewport_width, viewport_height, pan, zoom):
        visible_tiles = []
        for tile in self.tiles:
            # Проверяем, попадает ли тайл в область видимости
            tile_screen_x = tile.x * zoom + pan.x()
            tile_screen_y = tile.y * zoom + pan.y()
            tile_screen_width = tile.width * zoom
            tile_screen_height = tile.height * zoom

            if (tile_screen_x + tile_screen_width > 0 and
                    tile_screen_y + tile_screen_height > 0 and
                    tile_screen_x < viewport_width and
                    tile_screen_y < viewport_height):
                visible_tiles.append(tile)
        return visible_tiles

    def is_empty(self):
        return len(self.tiles) == 0
