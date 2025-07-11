# Виджет OpenGL (масштабирование, перемещение)

import os

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint, QPointF, QSizeF, pyqtSignal
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
        self.scale_settings = ScaleSettings()  # Добавляем настройки шкалы

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

class ScaleSettings:
    def __init__(self):
        self.time_visible = False
        self.amplitude_visible = False
        self.time_min = 0.0
        self.time_max = 60.0
        self.time_step = 10.0
        self.amplitude_min = 0.0
        self.amplitude_max = 5.0
        self.amplitude_step = 0.5
        self.color = (1.0, 0.0, 0.0, 1.0)
        self.line_width = 1.0

class VectorCurve:
    def __init__(self, raster_object, color=(0.0, 1.0, 0.0, 1.0), line_width=2.0):
        self.points = []  # Точки кривой в локальных координатах растра
        self.raster_object = raster_object  # Ссылка на растровый объект
        self.color = color
        self.line_width = line_width
        self.completed = False  # Завершена ли кривая

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

        self.vectorization_mode = False
        self.current_curve = None
        self.curves = []  # Все кривые
        self.current_color_index = 0
        self.current_color = (1.0, 0.0, 0.0, 1.0)  # Красный по умолчанию

    def start_vectorization(self):
        try:
            if not self.active_object:
                return False

            self.vectorization_mode = True
            self.current_curve = VectorCurve(self.active_object, self.current_color)
            self.setCursor(Qt.CrossCursor)
            self.update()
            return True
        except Exception as e:
            print(f"Ошибка! Не удалось начать векторизацию: {str(e)}")
            return False

    def finish_vectorization(self):
        """Завершает режим векторизации"""
        try:
            self.vectorization_mode = False

            # Безопасное завершение текущей кривой
            if hasattr(self, 'current_curve') and self.current_curve:
                if len(self.current_curve.points) > 1:
                    self.finish_current_curve()
                else:
                    # Если точек недостаточно, просто отбрасываем кривую
                    self.current_curve = None

            # Восстанавливаем курсор
            try:
                self.setCursor(Qt.ArrowCursor)
            except:
                self.unsetCursor()

            self.update()
        except Exception as e:
            print(f"Ошибка при завершении векторизации: {str(e)}")
            # Принудительное восстановление состояния
            self.vectorization_mode = False
            self.current_curve = None
            self.unsetCursor()
    def finish_current_curve(self):
        if self.current_curve and len(self.current_curve.points) > 1:
            self.current_curve.completed = True
            self.curves.append(self.current_curve)
            self.current_curve = None
            self.update()

    def clear_all_curves(self):
        if not self.active_object:
            return

        # Удаляем только кривые, привязанные к активному растру
        self.curves = [curve for curve in self.curves if curve.raster_object != self.active_object]

        if self.current_curve and self.current_curve.raster_object == self.active_object:
            self.current_curve = None

        self.update()

    def _scene_to_raster_local(self, scene_point, raster_object):
        """Преобразует глобальные координаты сцены в локальные координаты растра с учетом поворота"""
        # Сначала вычитаем позицию растра
        local_x = scene_point.x() - raster_object.position.x()
        local_y = scene_point.y() - raster_object.position.y()

        # Затем учитываем поворот
        dx = local_x - raster_object.rotation_center.x()
        dy = local_y - raster_object.rotation_center.y()

        angle_rad = -np.radians(raster_object.rotation_angle)
        cos_val = np.cos(angle_rad)
        sin_val = np.sin(angle_rad)

        rotated_x = dx * cos_val - dy * sin_val + raster_object.rotation_center.x()
        rotated_y = dx * sin_val + dy * cos_val + raster_object.rotation_center.y()

        return QPointF(rotated_x, rotated_y)

    def set_mode_move(self, enabled: bool):
        self.mode_move = enabled
        self.vectorization_mode = False  # Выходим из режима векторизации
        self.setCursor(Qt.ArrowCursor)
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
            # Отрисовка шкал поверх изображения
            self.draw_scales(obj)

        # Отрисовка кривых векторизации
        glDisable(GL_TEXTURE_2D)
        for curve in self.curves:
            self._draw_curve(curve)

        if self.current_curve and len(self.current_curve.points) > 0:
            self._draw_curve(self.current_curve)
        glEnable(GL_TEXTURE_2D)

    def _draw_curve(self, curve):
        if not curve or not curve.raster_object:
            return

        try:
            # Проверяем корректность цвета
            if not hasattr(curve, 'color') or len(curve.color) != 4:
                curve.color = (1.0, 0.0, 0.0, 1.0)  # Красный по умолчанию при ошибке

            glColor4f(*curve.color)
            glLineWidth(curve.line_width if hasattr(curve, 'line_width') else 2.0)

            glPushMatrix()
            # Применяем преобразования растра
            glTranslatef(curve.raster_object.position.x(), curve.raster_object.position.y(), 0)
            glTranslatef(curve.raster_object.rotation_center.x(), curve.raster_object.rotation_center.y(), 0)
            glRotatef(curve.raster_object.rotation_angle, 0, 0, 1)
            glTranslatef(-curve.raster_object.rotation_center.x(), -curve.raster_object.rotation_center.y(), 0)

            if hasattr(curve, 'points') and curve.points:
                glBegin(GL_LINE_STRIP if len(curve.points) > 1 else GL_POINTS)
                for point in curve.points:
                    if isinstance(point, QPointF):
                        glVertex2f(point.x(), point.y())
                glEnd()

                # Рисуем точки
                glPointSize(5.0)
                glBegin(GL_POINTS)
                for point in curve.points:
                    if isinstance(point, QPointF):
                        glVertex2f(point.x(), point.y())
                glEnd()

            glPopMatrix()
        except Exception as e:
            print(f"Ошибка отрисовки кривой: {str(e)}")

    def draw_scales(self, obj):
        if not obj.scale_settings.time_visible and not obj.scale_settings.amplitude_visible:
            return

        glPushMatrix()
        glTranslatef(obj.position.x(), obj.position.y(), 0)
        glTranslatef(obj.rotation_center.x(), obj.rotation_center.y(), 0)
        glRotatef(obj.rotation_angle, 0, 0, 1)
        glTranslatef(-obj.rotation_center.x(), -obj.rotation_center.y(), 0)

        # Устанавливаем параметры линий
        glColor4f(*obj.scale_settings.color)
        glLineWidth(obj.scale_settings.line_width)

        # ВРЕМЕННАЯ ШКАЛА (горизонтальные линии)
        if obj.scale_settings.time_visible and obj.scale_settings.time_max > obj.scale_settings.time_min:
            time_range = obj.scale_settings.time_max - obj.scale_settings.time_min
            pixels_per_second = obj.size.height() / time_range

            # Рассчитываем видимый диапазон времени
            visible_time_min = max(obj.scale_settings.time_min, 0)
            visible_time_max = min(obj.scale_settings.time_max,
                                   obj.scale_settings.time_min + obj.size.height() / pixels_per_second)

            # Находим первый и последний шаг, попадающий в видимый диапазон
            first_step = int(np.ceil((visible_time_min - obj.scale_settings.time_min) / obj.scale_settings.time_step))
            last_step = int(np.floor((visible_time_max - obj.scale_settings.time_min) / obj.scale_settings.time_step))

            # Рисуем только видимые линии
            for i in range(first_step, last_step + 1):
                time = obj.scale_settings.time_min + i * obj.scale_settings.time_step
                y = (time - obj.scale_settings.time_min) * pixels_per_second
                if 0 <= y <= obj.size.height():
                    glBegin(GL_LINES)
                    glVertex2f(0, y)
                    glVertex2f(obj.size.width(), y)
                    glEnd()

        # ШКАЛА АМПЛИТУД (вертикальные линии)
        if obj.scale_settings.amplitude_visible and obj.scale_settings.amplitude_max > obj.scale_settings.amplitude_min:
            amp_range = obj.scale_settings.amplitude_max - obj.scale_settings.amplitude_min
            pixels_per_unit = obj.size.width() / amp_range

            # Рассчитываем видимый диапазон амплитуд
            visible_amp_min = max(obj.scale_settings.amplitude_min, 0)
            visible_amp_max = min(obj.scale_settings.amplitude_max,
                                  obj.scale_settings.amplitude_min + obj.size.width() / pixels_per_unit)

            # Находим первый и последний шаг, попадающий в видимый диапазон
            first_step = int(
                np.ceil((visible_amp_min - obj.scale_settings.amplitude_min) / obj.scale_settings.amplitude_step))
            last_step = int(
                np.floor((visible_amp_max - obj.scale_settings.amplitude_min) / obj.scale_settings.amplitude_step))

            # Рисуем только видимые линии
            for i in range(first_step, last_step + 1):
                amp = obj.scale_settings.amplitude_min + i * obj.scale_settings.amplitude_step
                x = (amp - obj.scale_settings.amplitude_min) * pixels_per_unit
                if 0 <= x <= obj.size.width():
                    glBegin(GL_LINES)
                    glVertex2f(x, 0)
                    glVertex2f(x, obj.size.height())
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
            else:
                # Если ни один объект не выбран, деактивируем текущий
                if self.active_object:
                    self.active_object.is_active = False
                    self.active_object = None
                    self.objectActivated.emit(False)
                    self.update()

        if self.vectorization_mode and event.button() == Qt.LeftButton:
            self.finish_current_curve()
        else:
            super().mouseDoubleClickEvent(event)

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

        if self.vectorization_mode and event.button() == Qt.LeftButton:
            if not self.active_object:
                return

            scene_pos = self.map_to_scene(event.pos())
            # Преобразуем глобальные координаты в локальные координаты растра
            local_pos = self._scene_to_raster_local(scene_pos, self.active_object)

            if not self.current_curve:
                self.current_curve = VectorCurve(self.active_object, self.current_color)

            self.current_curve.points.append(local_pos)
            self.update()
        else:
            super().mousePressEvent(event)

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