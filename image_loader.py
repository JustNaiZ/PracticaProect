# Загрузка изображений

from PIL import Image
import numpy as np

class ImageLoader:
    def __init__(self):
        self.image_data = None
        self.width = 0
        self.height = 0
        Image.MAX_IMAGE_PIXELS = None  # Отключаем лимит (или задаем свой)

    def load(self, file_path):
        try:
            image = Image.open(file_path)
            image = image.convert("RGBA")
            self.width, self.height = image.size
            self.image_data = np.array(image, dtype=np.uint8)
        except Exception as e:
            raise ValueError(f"Ошибка загрузки изображения: {str(e)}")
