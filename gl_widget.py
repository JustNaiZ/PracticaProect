# Виджет OpenGL (масштабирование, перемещение)

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint, QPointF
from OpenGL.GL import *
from OpenGL.GLU import *
from image_loader import ImageLoader
from tile_manager import TileManager

class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_loader = ImageLoader()
        self.tile_manager = TileManager()

        self.zoom = 1.0
        self.pan = QPoint(0, 0)
        self.last_pos = QPoint(0, 0)
        self.dragging = False

        # Добавляем переменные для поворота
        self.rotation_angle = 0  # Угол поворота в градусах
        self.rotation_center = QPointF(0, 0)  # Центр вращения

    def set_rotation(self, angle):
        """Установка угла поворота"""
        self.rotation_angle = angle % 360
        self.update()

    def rotate(self, delta_angle):
        """Относительный поворот"""
        self.set_rotation(self.rotation_angle + delta_angle)

    def load_image(self, file_path, progress_callback=None):
        self.image_loader.load(file_path)
        self.tile_manager.split_into_tiles(
            self.image_loader.image_data,
            self.image_loader.width,
            self.image_loader.height,
            progress_callback
        )
        self.update()


    def initializeGL(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, w, h, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        if not self.tile_manager.is_empty():
            glPushMatrix()

            # Перенос в центр вращения
            glTranslatef(self.pan.x() + self.rotation_center.x(),
                         self.pan.y() + self.rotation_center.y(), 0)

            # Поворот
            glRotatef(self.rotation_angle, 0, 0, 1)

            # Масштабирование
            glScalef(self.zoom, self.zoom, 1.0)

            # Возврат к исходной позиции
            glTranslatef(-self.rotation_center.x(), -self.rotation_center.y(), 0)

            for tile in self.tile_manager.get_visible_tiles(self.width(), self.height(), self.pan,
                    self.zoom, self.rotation_angle, self.rotation_center):
                glBindTexture(GL_TEXTURE_2D, tile.texture_id)
                glBegin(GL_QUADS)
                glTexCoord2f(0, 0);
                glVertex2f(tile.x, tile.y)
                glTexCoord2f(1, 0);
                glVertex2f(tile.x + tile.width, tile.y)
                glTexCoord2f(1, 1);
                glVertex2f(tile.x + tile.width, tile.y + tile.height)
                glTexCoord2f(0, 1);
                glVertex2f(tile.x, tile.y + tile.height)
                glEnd()

            glPopMatrix()

    def wheelEvent(self, event):
        # Получаем позицию курсора относительно виджета
        mouse_pos = event.pos()

        # Преобразуем координаты курсора в координаты сцены (до масштабирования)
        scene_pos_before = QPointF(
            (mouse_pos.x() - self.pan.x()) / self.zoom,
            (mouse_pos.y() - self.pan.y()) / self.zoom
        )

        # Применяем масштабирование
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.zoom *= zoom_factor
        else:
            self.zoom /= zoom_factor

        # Преобразуем координаты курсора в координаты сцены после масштабирования
        scene_pos_after = QPointF(
            (mouse_pos.x() - self.pan.x()) / self.zoom,
            (mouse_pos.y() - self.pan.y()) / self.zoom
        )

        # Корректируем pan для сохранения позиции курсора
        delta = scene_pos_after - scene_pos_before
        self.pan += QPoint(int(delta.x() * self.zoom), int(delta.y() * self.zoom))

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.pos() - self.last_pos
            self.pan += delta
            self.last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

