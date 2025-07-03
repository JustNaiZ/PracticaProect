from PIL import Image
from OpenGL.GL import *
Image.MAX_IMAGE_PIXELS = None

TILE_SIZE = 1024

class Tile:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image  # PIL.Image
        self.texture_id = None

class TileManager:
    def __init__(self):
        self.tiles = []
        self.image_width = 0
        self.image_height = 0

    def load_image(self, path):
        img = Image.open(path).convert("RGB")
        self.image_width, self.image_height = img.size

        print(f"[INFO] Загружаю и режу на тайлы: {self.image_width}x{self.image_height}")

        self.tiles.clear()
        for y in range(0, self.image_height, TILE_SIZE):
            for x in range(0, self.image_width, TILE_SIZE):
                box = (x, y, min(x + TILE_SIZE, self.image_width), min(y + TILE_SIZE, self.image_height))
                tile_img = img.crop(box)
                self.tiles.append(Tile(x, y, tile_img))

        print(f"[INFO] Всего тайлов: {len(self.tiles)}")

    def generate_textures(self):
        # Создаём текстуры для первых N тайлов, можно ограничить
        max_tiles = 100  # лимит, чтобы не грузить все сразу
        count = 0
        for tile in self.tiles:
            if count >= max_tiles:
                break
            if tile.texture_id is None:
                tile.texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tile.texture_id)
                img = tile.image.transpose(Image.FLIP_TOP_BOTTOM)
                img_bytes = img.tobytes()
                width, height = tile.image.size
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                             GL_RGB, GL_UNSIGNED_BYTE, img_bytes)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                count += 1
