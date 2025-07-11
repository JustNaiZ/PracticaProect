# Главное окно приложения
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QFileDialog, QProgressDialog,
                             QMessageBox, QApplication, QLabel, QFrame, QDialog,
                             QDialogButtonBox, QDoubleSpinBox, QCheckBox, QFormLayout, QGroupBox)
from gl_widget import GLWidget

class ScaleSettingsDialog(QDialog):
    def __init__(self, scale_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка шкалы")
        self.scale_settings = scale_settings

        layout = QVBoxLayout()

        # Временная шкала
        time_group = QGroupBox("Временная шкала (горизонтальные линии)")
        time_layout = QFormLayout()

        self.time_visible = QCheckBox()
        self.time_visible.setChecked(scale_settings.time_visible)
        time_layout.addRow("Показывать временную шкалу:", self.time_visible)

        self.time_min = QDoubleSpinBox()
        self.time_min.setRange(-1e6, 1e6)
        self.time_min.setValue(scale_settings.time_min)
        time_layout.addRow("Минимальное время (с):", self.time_min)

        self.time_max = QDoubleSpinBox()
        self.time_max.setRange(-1e6, 1e6)
        self.time_max.setValue(scale_settings.time_max)
        time_layout.addRow("Максимальное время (с):", self.time_max)

        self.time_step = QDoubleSpinBox()
        self.time_step.setRange(0.001, 1e6)
        self.time_step.setValue(scale_settings.time_step)
        time_layout.addRow("Шаг времени (с):", self.time_step)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Шкала амплитуд
        amp_group = QGroupBox("Шкала амплитуд (вертикальные линии)")
        amp_layout = QFormLayout()

        self.amp_visible = QCheckBox()
        self.amp_visible.setChecked(scale_settings.amplitude_visible)
        amp_layout.addRow("Показывать шкалу амплитуд:", self.amp_visible)

        self.amp_min = QDoubleSpinBox()
        self.amp_min.setRange(-1e6, 1e6)
        self.amp_min.setValue(scale_settings.amplitude_min)
        amp_layout.addRow("Минимальная амплитуда:", self.amp_min)

        self.amp_max = QDoubleSpinBox()
        self.amp_max.setRange(-1e6, 1e6)
        self.amp_max.setValue(scale_settings.amplitude_max)
        amp_layout.addRow("Максимальная амплитуда:", self.amp_max)

        self.amp_step = QDoubleSpinBox()
        self.amp_step.setRange(0.001, 1e6)
        self.amp_step.setValue(scale_settings.amplitude_step)
        amp_layout.addRow("Шаг амплитуды:", self.amp_step)

        amp_group.setLayout(amp_layout)
        layout.addWidget(amp_group)

        # Кнопки
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.validate_and_accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        # Подключаем сигналы валидации
        self.time_min.valueChanged.connect(self.validate_values)
        self.time_max.valueChanged.connect(self.validate_values)
        self.amp_min.valueChanged.connect(self.validate_values)
        self.amp_max.valueChanged.connect(self.validate_values)

        # Первоначальная валидация
        self.validate_values()

    def validate_values(self):
        """Проверка корректности введенных значений"""
        time_valid = self.time_max.value() > self.time_min.value()
        amp_valid = self.amp_max.value() > self.amp_min.value()

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(time_valid and amp_valid)

        if not time_valid:
            self.time_max.setStyleSheet("background-color: #ffdddd;")
        else:
            self.time_max.setStyleSheet("")

        if not amp_valid:
            self.amp_max.setStyleSheet("background-color: #ffdddd;")
        else:
            self.amp_max.setStyleSheet("")

    def validate_and_accept(self):
        """Проверка значений перед принятием"""
        if self.time_max.value() <= self.time_min.value():
            QMessageBox.warning(self, "Ошибка", "Максимальное время должно быть больше минимального")
            return

        if self.amp_max.value() <= self.amp_min.value():
            QMessageBox.warning(self, "Ошибка", "Максимальная амплитуда должна быть больше минимальной")
            return

        self.accept()

    def accept(self):
        """Сохраняем настройки перед закрытием"""
        self.scale_settings.time_visible = self.time_visible.isChecked()
        self.scale_settings.time_min = self.time_min.value()
        self.scale_settings.time_max = self.time_max.value()
        self.scale_settings.time_step = self.time_step.value()

        self.scale_settings.amplitude_visible = self.amp_visible.isChecked()
        self.scale_settings.amplitude_min = self.amp_min.value()
        self.scale_settings.amplitude_max = self.amp_max.value()
        self.scale_settings.amplitude_step = self.amp_step.value()

        super().accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Аналоговые сейсмограммы")

        self.gl_widget = GLWidget(self)
        self.setCentralWidget(self.gl_widget)

        # Создаём панели
        self.mode_panel = self._create_mode_panel()
        self.selection_panel = self._create_selection_panel()
        self.tool_panel = self._create_tool_panel()

        # Скрываем панели по умолчанию
        self.mode_panel.setVisible(False)
        self.selection_panel.setVisible(False)
        self.tool_panel.setVisible(False)

        self.add_action = None  # Добавляем инициализацию атрибута

        # Позиционируем панели поверх gl_widget, не используя layout для них
        self._position_panels()

        self._create_menu()
        self._connect_signals()

        self.gl_widget.objectActivated.connect(self._on_object_activated)

        # Меню шкалы (изначально полностью неактивно)
        self.scale_menu = self.menuBar().addMenu("Шкала")
        self.scale_settings_action = self.scale_menu.addAction("Настроить шкалу")
        self.scale_settings_action.triggered.connect(self._show_scale_settings)
        self.scale_toggle_action = self.scale_menu.addAction("Показать шкалу")
        self.scale_toggle_action.setEnabled(False)  # Изначально недоступна
        self.scale_toggle_action.triggered.connect(self._toggle_scale)
        self.scale_menu.setEnabled(False)

        # Меню векторизации (изначально неактивно)
        self._create_vectorization_menu()
        self.vectorization_menu.setEnabled(False)

    def _position_panels(self):
        x = 20
        y = 20
        spacing = 10

        for panel in [self.mode_panel, self.selection_panel, self.tool_panel]:
            panel.adjustSize()
            panel.move(x, y)
            y += panel.height() + spacing

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        open_action = file_menu.addAction("Открыть изображение")
        open_action.triggered.connect(self._open_image)

        self.add_action = file_menu.addAction("Добавить изображение")
        self.add_action.setVisible(False)
        self.add_action.triggered.connect(self._add_image)

    def _create_mode_panel(self):
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Режим работы")
        title.setStyleSheet("color: gray; font-weight: normal; background: transparent; border: none;")
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bbb;")
        layout.addWidget(line)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        self.move_mode_btn = QPushButton("Режим движения")
        self.move_mode_btn.setCheckable(True)
        buttons_layout.addWidget(self.move_mode_btn)

        self.raster_mode_btn = QPushButton("Работа с растром")
        self.raster_mode_btn.setCheckable(True)
        buttons_layout.addWidget(self.raster_mode_btn)

        layout.addLayout(buttons_layout)

        return panel

    def _create_selection_panel(self):
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Выделение растра")
        title.setStyleSheet("color: gray; font-weight: normal; background: transparent; border: none;")
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bbb;")
        layout.addWidget(line)

        self.select_raster_btn = QPushButton("Выделить растр")
        self.select_raster_btn.setCheckable(True)  # Делаем кнопку переключаемой
        layout.addWidget(self.select_raster_btn)

        return panel

    def _create_tool_panel(self):
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Инструменты")
        title.setStyleSheet("color: gray; font-weight: normal; background: transparent; border: none;")
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bbb;")
        layout.addWidget(line)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        self.rotate_left_btn = QPushButton("↺ 90°")
        buttons_layout.addWidget(self.rotate_left_btn)

        self.rotate_right_btn = QPushButton("↻ 90°")
        buttons_layout.addWidget(self.rotate_right_btn)

        self.rotate_custom_btn = QPushButton("Ввести угол")
        buttons_layout.addWidget(self.rotate_custom_btn)

        layout.addLayout(buttons_layout)

        return panel

    def _create_vectorization_menu(self):
        """Создание меню векторизации"""
        self.vectorization_menu = self.menuBar().addMenu("Векторизация")

        self.start_vector_action = self.vectorization_menu.addAction("Начать векторизацию")
        self.start_vector_action.triggered.connect(self._start_vectorization)
        self.start_vector_action.setEnabled(False)  # Изначально недоступно

        self.finish_vector_action = self.vectorization_menu.addAction("Завершить векторизацию")
        self.finish_vector_action.setEnabled(False)
        self.finish_vector_action.triggered.connect(self._finish_vectorization)

        self.finish_curve_action = self.vectorization_menu.addAction("Завершить текущую кривую")
        self.finish_curve_action.setEnabled(False)
        self.finish_curve_action.triggered.connect(self._finish_current_curve)

        self.color_menu = self.vectorization_menu.addMenu("Цвет кривой")
        self.color_menu.setEnabled(False)

        # Создаем действия для каждого цвета
        self.color_actions = []
        colors = [
            ("Красный", (1.0, 0.0, 0.0, 1.0)),
            ("Зеленый", (0.0, 1.0, 0.0, 1.0)),
            ("Синий", (0.0, 0.0, 1.0, 1.0)),
            ("Пурпурный", (1.0, 0.0, 1.0, 1.0)),
            ("Желтый", (1.0, 1.0, 0.0, 1.0)),
            ("Голубой", (0.0, 1.0, 1.0, 1.0)),
            ("Черный", (0.0, 0.0, 0.0, 1.0))
        ]

        for name, color in colors:
            try:
                action = self.color_menu.addAction(name)
                action.setCheckable(True)

                # Создаем иконку с цветом
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))
                action.setIcon(QIcon(pixmap))

                # Сохраняем цвет в данных действия
                action.setData(color)

                # Безопасное подключение
                action.triggered.connect(lambda checked, c=color: self._set_curve_color(c))

                self.color_actions.append(action)
            except Exception as e:
                print(f"Ошибка создания цветового действия {name}: {str(e)}")

            # Выбираем первый цвет по умолчанию
        if self.color_actions:
            self.color_actions[0].setChecked(True)
            self._current_color = colors[0][1]

        self.clear_curves_action = self.vectorization_menu.addAction("Очистить все кривые")
        self.clear_curves_action.setEnabled(False)
        self.clear_curves_action.triggered.connect(self._clear_all_curves)

    def _start_vectorization(self):
        if not hasattr(self.gl_widget, 'active_object') or not self.gl_widget.active_object:
            QMessageBox.warning(self, "Ошибка",
                                "Нет активного растрового объекта.\n"
                                "Выберите растр двойным кликом перед началом векторизации.")
            return

        try:
            # Проверяем успешность запуска
            if not self.gl_widget.start_vectorization():
                raise Exception("Ошибка! Не удалось начать векторизацию!")

            # Обновляем интерфейс
            self.start_vector_action.setEnabled(False)
            self.finish_vector_action.setEnabled(True)
            self.finish_curve_action.setEnabled(True)
            self.color_menu.setEnabled(True)
            self.clear_curves_action.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка начала векторизации:\n{str(e)}")
            # Восстанавливаем состояние
            self.gl_widget.vectorization_mode = False
            self.gl_widget.setCursor(Qt.ArrowCursor)

    def _finish_vectorization(self):
        """Завершение режима векторизации"""
        try:
            if not hasattr(self.gl_widget, 'finish_vectorization'):
                return

            # Сохраняем текущее состояние перед завершением
            had_curve = hasattr(self.gl_widget, 'current_curve') and self.gl_widget.current_curve

            self.gl_widget.finish_vectorization()

            # Обновляем UI только после успешного завершения
            self.start_vector_action.setEnabled(True)
            self.finish_vector_action.setEnabled(False)
            self.finish_curve_action.setEnabled(False)
            self.color_menu.setEnabled(False)
            self.clear_curves_action.setEnabled(had_curve)

        except Exception as e:
            print(f"Критическая ошибка при завершении векторизации: {str(e)}")
            # Восстанавливаем состояние
            if hasattr(self.gl_widget, 'vectorization_mode'):
                self.gl_widget.vectorization_mode = False
            if hasattr(self.gl_widget, 'current_curve'):
                self.gl_widget.current_curve = None
            self.gl_widget.unsetCursor()
            self.gl_widget.update()

    def _finish_current_curve(self):
        self.gl_widget.finish_current_curve()

    def _set_curve_color(self, color):
        """Установка цвета кривой"""
        if not hasattr(self, '_current_color'):
            self._current_color = (1.0, 0.0, 0.0, 1.0)  # Красный по умолчанию

        try:
            # Проверяем корректность цвета
            if not color or len(color) != 4 or not all(0.0 <= c <= 1.0 for c in color):
                color = (1.0, 0.0, 0.0, 1.0)  # Красный при ошибке

            self._current_color = color

            # Устанавливаем цвет в виджете
            if hasattr(self.gl_widget, 'current_color'):
                self.gl_widget.current_color = color

            # Обновляем текущую кривую, если она есть
            if (hasattr(self.gl_widget, 'current_curve') and
                    self.gl_widget.current_curve and
                    hasattr(self.gl_widget.current_curve, 'color')):
                self.gl_widget.current_curve.color = color

            # Снимаем выделение с других цветов
            if hasattr(self, 'color_actions'):
                for action in self.color_actions:
                    if hasattr(action, 'isChecked') and hasattr(action, 'setChecked'):
                        action.setChecked(False)
                        if hasattr(action, 'data') and action.data() == color:
                            action.setChecked(True)

            # Обновляем отображение
            if hasattr(self.gl_widget, 'update'):
                self.gl_widget.update()

        except Exception as e:
            print(f"Ошибка установки цвета: {str(e)}")
            # Пытаемся восстановить работоспособность
            self._current_color = (1.0, 0.0, 0.0, 1.0)
            if hasattr(self.gl_widget, 'current_color'):
                self.gl_widget.current_color = self._current_color

    def _clear_all_curves(self):
        self.gl_widget.clear_all_curves()

    def _panel_style(self):
        return """
            QWidget {
                background: rgba(240, 240, 240, 0.9);
                border: 1px solid #aaa;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                padding: 5px 10px;
                min-width: 120px;
                border: 1px solid #888;
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f6f7fa, stop:1 #dadbde);
            }
            QPushButton:checked {
                background: #b0d0ff;
            }
        """

    def _connect_signals(self):
        self.move_mode_btn.clicked.connect(self._activate_move_mode)
        self.raster_mode_btn.clicked.connect(self._activate_raster_mode)
        self.select_raster_btn.clicked.connect(self._enable_raster_selection)

        self.rotate_left_btn.clicked.connect(lambda: self.gl_widget.rotate(-90))
        self.rotate_right_btn.clicked.connect(lambda: self.gl_widget.rotate(90))
        self.rotate_custom_btn.clicked.connect(self._show_angle_dialog)

    def _show_scale_settings(self):
        if not hasattr(self.gl_widget, 'active_object') or not self.gl_widget.active_object:
            QMessageBox.warning(self, "Ошибка",
                                "Нет активного растрового объекта.\n"
                                "Дважды кликните по растру, чтобы активировать его.")
            return

        dialog = ScaleSettingsDialog(self.gl_widget.active_object.scale_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # Только после успешной настройки делаем кнопку доступной
            self.scale_toggle_action.setEnabled(True)
            self.gl_widget.update()

    def _toggle_scale(self):
        if not self.gl_widget.active_object:
            return

        scale = self.gl_widget.active_object.scale_settings
        if scale.time_visible or scale.amplitude_visible:
            scale.time_visible = False
            scale.amplitude_visible = False
            self.scale_toggle_action.setText("Показать шкалу")
        else:
            scale.time_visible = True
            scale.amplitude_visible = True
            self.scale_toggle_action.setText("Убрать шкалу")

        self.gl_widget.update()

    def _show_angle_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Точный поворот")
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(dialog)

        # Создаем контейнер для ввода угла
        angle_layout = QHBoxLayout()
        angle_label = QLabel("Угол (°):")
        angle_layout.addWidget(angle_label)

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(-360.0, 360.0)
        self.angle_spin.setDecimals(2)  # Две цифры после запятой
        self.angle_spin.setValue(0.0)
        self.angle_spin.setSingleStep(0.01)  # Шаг изменения 0.01
        angle_layout.addWidget(self.angle_spin)

        # Кнопки для быстрого изменения сотых долей
        btn_layout = QVBoxLayout()
        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(1)
        up_btn.clicked.connect(lambda: self.angle_spin.setValue(
            round(self.angle_spin.value() + 0.01, 2)))
        down_btn = QPushButton("▼")
        down_btn.setFixedWidth(1)
        down_btn.clicked.connect(lambda: self.angle_spin.setValue(
            round(self.angle_spin.value() - 0.01, 2)))
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        angle_layout.addLayout(btn_layout)

        layout.addLayout(angle_layout)

        # Кнопки подтверждения/отмены
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._apply_rotation(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()

    def _apply_rotation(self, dialog):
        angle = self.angle_spin.value()
        self.gl_widget.rotate(angle)
        dialog.accept()

    def _activate_move_mode(self):
        self.raster_mode_btn.setChecked(False)
        self.move_mode_btn.setChecked(True)
        self.move_mode_btn.setEnabled(False)
        self.raster_mode_btn.setEnabled(True)

        self.gl_widget.set_mode_move(True)
        self.gl_widget.set_selection_enabled(False)  # Отключаем выделение
        self.select_raster_btn.setChecked(False)  # Сбрасываем состояние кнопки

        self.gl_widget.setCursor(Qt.ArrowCursor)
        self.selection_panel.setVisible(False)

    def _activate_raster_mode(self):
        self.move_mode_btn.setChecked(False)
        self.raster_mode_btn.setChecked(True)
        self.raster_mode_btn.setEnabled(False)
        self.move_mode_btn.setEnabled(True)

        self.selection_panel.setVisible(True)
        self.tool_panel.setVisible(False)

        self.gl_widget.set_mode_move(False)
        self.gl_widget.set_selection_enabled(False)
        # self.gl_widget.center_camera_on_raster() - оставляем там, где пользователь изволит

    def _enable_raster_selection(self):
        self.gl_widget.set_selection_enabled(self.select_raster_btn.isChecked())

    def _on_object_activated(self, active):
        self.tool_panel.setVisible(active)
        self.scale_menu.setEnabled(active)  # Меню шкалы доступно только при активном растре
        self.vectorization_menu.setEnabled(active)  # Меню векторизации доступно только при активном растре
        self.color_menu.setEnabled(active)  # Активируем меню цветов
        if active:
            # При активации объекта всегда выключаем кнопку показа шкалы
            self.scale_toggle_action.setEnabled(False)
            self.scale_toggle_action.setText("Показать шкалу")
            self.start_vector_action.setEnabled(True)
        else:
            # Если объект деактивирован, выключаем режим векторизации
            if self.gl_widget.vectorization_mode:
                self._finish_vectorization()

    def _add_image(self):
        """Добавление нового изображения к текущей сцене"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Добавить изображение",
            "",
            "Images (*.bmp *.tif *.tiff *.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        try:
            # Закрываем предыдущие уведомления перед операцией
            if hasattr(self, '_current_toast'):
                try:
                    self._current_toast.hide()
                except RuntimeError:
                    pass  # Игнорируем ошибки удаленного объекта

            # Добавляем изображение
            success = self.gl_widget.add_image(file_path, self._progress_callback)

            if success:
                # Формируем сообщение после успешного добавления
                try:
                    last_obj = self.gl_widget.raster_objects[-1]
                    self.show_toast(
                        f"Добавлено изображение: {file_path.split('/')[-1]}\n"
                        f"Размер: {last_obj.size.width():.0f}×{last_obj.size.height():.0f} px\n"
                        f"Физический размер: "
                        f"{last_obj.get_physical_size_mm().width():.1f}×"
                        f"{last_obj.get_physical_size_mm().height():.1f} мм"
                    )
                except (IndexError, AttributeError, RuntimeError) as e:
                    print(f"Ошибка при показе уведомления: {str(e)}")

        except Exception as e:
            # Сначала скрываем прогресс-диалог, если он есть
            if hasattr(self, '_progress_dialog'):
                try:
                    self._progress_dialog.hide()
                except RuntimeError:
                    pass

            QMessageBox.critical( self, "Ошибка", f"Не удалось добавить изображение:\n{str(e)}")

    def _open_image(self):
        """Загрузка нового изображения (очищает предыдущее)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть изображение",
            "",
            "Images (*.bmp *.tif *.tiff *.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        try:
            # Закрываем предыдущие уведомления
            if hasattr(self, '_current_toast'):
                try:
                    self._current_toast.hide()
                except RuntimeError:
                    pass

            # Загружаем изображение
            self.gl_widget.load_image(file_path, self._progress_callback)

            # Формируем информационное сообщение
            try:
                img_info = (
                    f"Загружено изображение: {file_path.split('/')[-1]}\n"
                    f"Размер: {self.gl_widget.image_loader.width}×{self.gl_widget.image_loader.height} px\n"
                    f"Физический размер: "
                    f"{self.gl_widget.raster_objects[0].get_physical_size_mm().width():.1f}×"
                    f"{self.gl_widget.raster_objects[0].get_physical_size_mm().height():.1f} мм"
                )
                self.show_toast(img_info, timeout=5000)  # Увеличиваем время показа
            except (IndexError, AttributeError, RuntimeError) as e:
                print(f"Ошибка при формировании информации: {str(e)}")

            # Активируем интерфейс
            self.add_action.setVisible(True)
            self.scale_menu.setEnabled(False)  # Меню шкалы неактивно
            self.vectorization_menu.setEnabled(False)  # Меню векторизации неактивно
            self.mode_panel.setVisible(True)
            self._activate_move_mode()

        except Exception as e:
            # Скрываем прогресс-диалог при ошибке
            if hasattr(self, '_progress_dialog'):
                try:
                    self._progress_dialog.hide()
                except RuntimeError:
                    pass

            QMessageBox.critical( self, "Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")

    def _progress_callback(self, percent):
        """Обработчик прогресса операций загрузки"""
        # Инициализация диалога только при начале операции (percent == 0)
        if percent == 0:
            if hasattr(self, '_progress_dialog'):
                self._progress_dialog.deleteLater()

            self._progress_dialog = QProgressDialog("Обработка изображения...", "Отмена", 0, 100, self)
            self._progress_dialog.setWindowTitle("Прогресс")
            self._progress_dialog.setWindowModality(True)
            self._progress_dialog.setAutoClose(True)  # Автоматически закрывать при завершении
            self._progress_dialog.show()

        # Обновляем прогресс только если диалог существует
        if hasattr(self, '_progress_dialog'):
            self._progress_dialog.setValue(percent)
            QApplication.processEvents()

            if self._progress_dialog.wasCanceled():
                self._progress_dialog.deleteLater()
                del self._progress_dialog
                raise Exception("Операция отменена пользователем")

    def show_toast(self, message, timeout=7000):
        """Всплывающее уведомление с автоисчезновением"""
        # Удаляем предыдущее уведомление безопасным способом
        if hasattr(self, '_current_toast'):
            try:
                if self._current_toast:
                    self._current_toast.deleteLater()
            except RuntimeError:
                pass  # Объект уже был удален

        # Создаем новое уведомление
        self._current_toast = QLabel(message, self)
        self._current_toast.setObjectName("ToastNotification")
        self._current_toast.setStyleSheet("""
            QLabel#ToastNotification {
                background: rgba(50, 50, 50, 220);
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font: 12px;
                border: 1px solid #444;
            }
        """)
        self._current_toast.setAlignment(Qt.AlignCenter)
        self._current_toast.adjustSize()

        # Позиционируем
        x = (self.width() - self._current_toast.width()) // 2
        y = self.height() - self._current_toast.height() - 30
        self._current_toast.move(x, y)
        self._current_toast.show()

        # Автоудаление с проверкой
        def safe_delete():
            if hasattr(self, '_current_toast'):
                try:
                    self._current_toast.deleteLater()
                    del self._current_toast
                except RuntimeError:
                    pass

        QTimer.singleShot(timeout, safe_delete) # Удаление через timeout миллисекунд