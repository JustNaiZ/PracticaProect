from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt
from OpenGL.GL import *
from tile_manager import TileManager, TILE_SIZE


class TiledRasterWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tile_manager = TileManager()

        self.scale = 1.0
        self.translation = [0.0, 0.0]
        self.last_mouse_pos = None

    def load_image(self, path):
        self.makeCurrent()  # важно для OpenGL
        print("[INFO] Загружаю изображение...")
        try:
            self.tile_manager.load_image(path)
            print("[INFO] Изображение загружено и разбито на тайлы")
            print("[INFO] Начинаю создавать текстуры")
            self.tile_manager.generate_textures()
            print("[INFO] Текстуры созданы")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке изображения: {e}")
            return

        self.update()

    def initializeGL(self):
        print("[INIT] OpenGL инициализация")
        glClearColor(0, 0, 0, 1)
        glEnable(GL_TEXTURE_2D)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Применяем трансформации
        glTranslatef(self.translation[0], self.translation[1], 0)
        glScalef(self.scale, self.scale, 1)

        w = self.width()
        h = self.height()

        for tile in self.tile_manager.tiles:
            # Координаты тайла в мировом пространстве
            world_x = tile.x * self.scale + self.translation[0]
            world_y = tile.y * self.scale + self.translation[1]

            # Проверяем, виден ли тайл в окне (в координатах экрана)
            if world_x + TILE_SIZE * self.scale < 0 or world_x > w:
                continue
            if world_y + TILE_SIZE * self.scale < 0 or world_y > h:
                continue

            if tile.texture_id is None:
                continue

            glBindTexture(GL_TEXTURE_2D, tile.texture_id)

            # Рисуем в локальных координатах (трансформации уже применены)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0);
            glVertex2f(tile.x, tile.y)
            glTexCoord2f(1, 0);
            glVertex2f(tile.x + TILE_SIZE, tile.y)
            glTexCoord2f(1, 1);
            glVertex2f(tile.x + TILE_SIZE, tile.y + TILE_SIZE)
            glTexCoord2f(0, 1);
            glVertex2f(tile.x, tile.y + TILE_SIZE)
            glEnd()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        factor = 1.1 if delta > 0 else 0.9
        self.scale *= factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.translation[0] += dx
            self.translation[1] -= dy
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = None
