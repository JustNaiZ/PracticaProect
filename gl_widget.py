# Виджет OpenGL (масштабирование, перемещение)

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint
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
            glTranslatef(self.pan.x(), self.pan.y(), 0)
            glScalef(self.zoom, self.zoom, 1.0)

            for tile in self.tile_manager.get_visible_tiles(self.width(), self.height(), self.pan, self.zoom):
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
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.zoom *= zoom_factor
        else:
            self.zoom /= zoom_factor
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
