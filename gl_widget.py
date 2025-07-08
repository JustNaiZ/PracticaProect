# Виджет OpenGL (масштабирование, перемещение)

import os
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint, QPointF, QSizeF, pyqtSignal, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
from image_loader import ImageLoader
from tile_manager import TileManager
import numpy as np

class RasterObject:
    def __init__(self, tile_manager, position=QPointF(0, 0), size=QSizeF(100, 100), file_path=""):
        self.tile_manager = tile_manager
        self.position = position
        self.size = size
        self.selected = False
        self.hovered = False
        self.is_active = False
        self.rotation_angle = 0
        self.rotation_center = QPointF(size.width() / 2, size.height() / 2)
        self.dpi = (600, 600)
        self.file_path = file_path  # Сохраняем путь к файлу

    def get_physical_size_mm(self): # Просто для вывода размеров изображения
        return QSizeF(
            self.size.width() * 25.4 / self.dpi[0],
            self.size.height() * 25.4 / self.dpi[1]
        )

    def contains_point(self, point):
        # Проверка попадания точки с учетом поворота
        local_x = point.x() - self.position.x()
        local_y = point.y() - self.position.y()

        dx = local_x - self.rotation_center.x()
        dy = local_y - self.rotation_center.y()

        angle_rad = -np.radians(self.rotation_angle)
        cos_val = np.cos(angle_rad)
        sin_val = np.sin(angle_rad)

        rotated_x = dx * cos_val - dy * sin_val + self.rotation_center.x()
        rotated_y = dx * sin_val + dy * cos_val + self.rotation_center.y()

        return (0 <= rotated_x <= self.size.width() and 0 <= rotated_y <= self.size.height())


class GLWidget(QOpenGLWidget):
    objectActivated = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_loader = ImageLoader()
        self.tile_manager = TileManager()
        self.raster_objects = []
        self.active_object = None
        self.hovered_object = None

        # Режим: True — движение сцены, False — работа с растром (перемещение/вращение)
        self.mode_move = True

        self.zoom = 1.0
        self.pan = QPoint(0, 0)
        self.last_pos = QPoint(0, 0)
        self.dragging = False
        self.selection_mode = False

        self.setMouseTracking(True)

    def set_mode_move(self, enabled: bool):
        self.mode_move = enabled
        if enabled:
            if self.active_object:
                self.active_object.is_active = False
                self.active_object = None
                self.objectActivated.emit(False)
            self.selection_mode = False
            self.hovered_object = None
        else:
            self.selection_mode = True
            # self.center_camera_on_raster() - оставляем там, где пользователь изволит
        self.update()

    def set_selection_enabled(self, enabled: bool):
        self.selection_mode = enabled
        if not enabled:
            self.hovered_object = None
            if self.active_object:
                self.active_object.is_active = False
                self.active_object = None
                self.objectActivated.emit(False)
        self.update()

    def add_image(self, file_path, progress_callback=None):
        try:
            # Проверка существования файла
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            # Загрузка с автоматическим приведением к 600 DPI
            new_loader = ImageLoader()
            new_loader.load(file_path, target_dpi=600)

            # Создание тайлов с обработкой прогресса
            new_tile_manager = TileManager()
            new_tile_manager.split_into_tiles(
                new_loader.image_data,
                new_loader.width,
                new_loader.height,
                progress_callback
            )

            # Позиционирование нового изображения со смещением
            new_pos = QPointF(0, 0)
            if self.raster_objects:
                last_obj = self.raster_objects[-1]
                new_pos = QPointF(
                    last_obj.position.x() + 20 / self.zoom,
                    last_obj.position.y() + 20 / self.zoom
                )

            # Создание объекта растра с сохранением пути к файлу
            obj = RasterObject(
                new_tile_manager,
                new_pos,
                QSizeF(new_loader.width, new_loader.height),
                file_path  # Добавляем путь к файлу
            )
            obj.rotation_center = QPointF(new_loader.width / 2, new_loader.height / 2)
            obj.dpi = (600, 600)

            self.raster_objects.append(obj)

            # Центрирование камеры для первого изображения
            if len(self.raster_objects) == 1:
                self.center_camera_on_raster()

            self.update()
            return True

        except Exception as e:
            print(f"Ошибка при добавлении изображения: {str(e)}")
            return False

    def load_image(self, file_path, progress_callback=None):
        try:
            # Проверка существования файла
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            self.clear_rasters()

            # Загрузка изображения
            self.image_loader = ImageLoader()
            self.image_loader.load(file_path, target_dpi=600)

            # Создание тайлов
            self.tile_manager = TileManager()
            self.tile_manager.split_into_tiles(
                self.image_loader.image_data,
                self.image_loader.width,
                self.image_loader.height,
                progress_callback
            )

            # Создание основного объекта растра
            obj = RasterObject(
                self.tile_manager,
                QPointF(0, 0),
                QSizeF(self.image_loader.width, self.image_loader.height),
                file_path  # Добавляем путь к файлу
            )
            obj.rotation_center = QPointF(self.image_loader.width / 2, self.image_loader.height / 2)
            obj.dpi = (600, 600)

            self.raster_objects.append(obj)
            self.center_camera_on_raster()
            self.update()

            return True  # Указываем на успешную загрузку

        except Exception as e:
            print(f"Ошибка при загрузке изображения: {str(e)}")
            raise  # Пробрасываем исключение для обработки в MainWindow

    def clear_rasters(self):
        self.raster_objects = []
        self.active_object = None
        self.hovered_object = None
        self.update()

    def rotate(self, angle):
        if self.active_object and not self.mode_move:
            self.active_object.rotation_angle = (self.active_object.rotation_angle + angle) % 360
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
        if not self.raster_objects:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width(), self.height(), 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(self.pan.x(), self.pan.y(), 0)
        glScalef(self.zoom, self.zoom, 1.0)

        for obj in self.raster_objects:
            glPushMatrix()

            glTranslatef(obj.position.x(), obj.position.y(), 0)
            glTranslatef(obj.rotation_center.x(), obj.rotation_center.y(), 0)
            glRotatef(obj.rotation_angle, 0, 0, 1)
            glTranslatef(-obj.rotation_center.x(), -obj.rotation_center.y(), 0)

            if obj.tile_manager and not obj.tile_manager.is_empty():
                for tile in obj.tile_manager.tiles:
                    # Светлее, если наведён и в режиме работы с растром
                    if not self.mode_move:
                        if obj == self.active_object:
                            glColor4f(0.65, 0.65, 0.65, 1.0)  # Тёмнее — активный растр
                        elif obj == self.hovered_object:
                            glColor4f(1.0, 1.0, 1.0, 0.7)  # Полупрозрачный при наведении
                        else:
                            glColor4f(1.0, 1.0, 1.0, 1.0)
                    else:
                        glColor4f(1.0, 1.0, 1.0, 1.0)

                    if not tile.texture_id:
                        continue
                    glBindTexture(GL_TEXTURE_2D, tile.texture_id)
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 0)
                    glVertex2f(tile.x, tile.y)
                    glTexCoord2f(1, 0)
                    glVertex2f(tile.x + tile.width, tile.y)
                    glTexCoord2f(1, 1)
                    glVertex2f(tile.x + tile.width, tile.y + tile.height)
                    glTexCoord2f(0, 1)
                    glVertex2f(tile.x, tile.y + tile.height)
                    glEnd()

            glPopMatrix()

    def mouseDoubleClickEvent(self, event):
        if not self.mode_move and self.selection_mode and event.button() == Qt.LeftButton:
            scene_pos = self.map_to_scene(event.pos())
            for obj in reversed(self.raster_objects):
                if obj.contains_point(scene_pos):
                    if self.active_object:
                        self.active_object.is_active = False
                    self.active_object = obj
                    obj.is_active = True
                    self.objectActivated.emit(True)
                    self.update()
                    break

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()
            scene_pos = self.map_to_scene(event.pos())

            if self.mode_move:
                self.dragging = True
            else:
                # Режим работы с растром: можно двигать активный объект
                if self.active_object and self.active_object.contains_point(scene_pos):
                    self.dragging = True
                else:
                    self.dragging = False

    def mouseMoveEvent(self, event):
        scene_pos = self.map_to_scene(event.pos())

        if not self.mode_move and self.selection_mode:
            # Обновляем hovered объект только в режиме работы с растром и при включенном выделении
            new_hovered = None
            for obj in reversed(self.raster_objects):
                if obj.contains_point(scene_pos):
                    new_hovered = obj
                    break

            if new_hovered != self.hovered_object:
                self.hovered_object = new_hovered
                self.update()

        if self.dragging:
            delta = event.pos() - self.last_pos
            if self.mode_move:
                self.pan += delta
            else:
                if self.active_object and self.selection_mode:  # Добавили проверку selection_mode
                    self.active_object.position += QPointF(delta.x() / self.zoom, delta.y() / self.zoom)
            self.last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def wheelEvent(self, event):
        mouse_pos = event.pos()
        scene_pos_before = QPointF(
            (mouse_pos.x() - self.pan.x()) / self.zoom,
            (mouse_pos.y() - self.pan.y()) / self.zoom
        )

        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.zoom *= zoom_factor
        else:
            self.zoom /= zoom_factor

        scene_pos_after = QPointF(
            (mouse_pos.x() - self.pan.x()) / self.zoom,
            (mouse_pos.y() - self.pan.y()) / self.zoom
        )

        delta = scene_pos_after - scene_pos_before
        self.pan += QPoint(int(delta.x() * self.zoom), int(delta.y() * self.zoom))
        self.update()

    def map_to_scene(self, widget_point):
        return QPointF(
            (widget_point.x() - self.pan.x()) / self.zoom,
            (widget_point.y() - self.pan.y()) / self.zoom
        )

    def center_camera_on_raster(self):
        if not self.raster_objects:
            return

        obj = self.raster_objects[-1]
        img_w = obj.size.width()
        img_h = obj.size.height()

        zoom_x = self.width() / img_w
        zoom_y = self.height() / img_h
        self.zoom = min(zoom_x, zoom_y) * 0.95

        # Центр изображения в координатах сцены
        img_center = QPointF(img_w / 2, img_h / 2)

        # Центр окна в экранных координатах
        widget_center = QPoint(self.width() // 2, self.height() // 2)

        # Переводим сцену так, чтобы центр изображения оказался в центре окна
        self.pan = widget_center - QPoint(
            int(img_center.x() * self.zoom),
            int(img_center.y() * self.zoom)
        )

        # print(f"[DEBUG] zoom={self.zoom:.4f}, pan={self.pan}")
        self.update()