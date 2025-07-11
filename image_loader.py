from PIL import Image
import numpy as np

class ImageLoader:
    def __init__(self):
        self.image_data = None
        self.width = 0
        self.height = 0
        self.dpi = (600, 600)  # Значение по умолчанию
        Image.MAX_IMAGE_PIXELS = None

    def load(self, file_path, target_dpi=600):
        try:
            image = Image.open(file_path)
            original_dpi = image.info.get('dpi', (72, 72))

            # Масштабирование до target_dpi
            if original_dpi[0] != target_dpi:
                scale_factor = target_dpi / original_dpi[0]
                new_size = (
                    int(image.width * scale_factor),
                    int(image.height * scale_factor)
                )
                image = image.resize(new_size, Image.LANCZOS)

            self.dpi = (target_dpi, target_dpi)
            image = image.convert("RGBA")
            self.width, self.height = image.size
            self.image_data = np.array(image, dtype=np.uint8)

        except Exception as e:
            raise ValueError(f"Ошибка загрузки изображения: {str(e)}")