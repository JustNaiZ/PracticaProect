# Главное окно приложения
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QFileDialog, QProgressDialog,
                             QMessageBox, QApplication, QLabel, QFrame, QDialog,
                             QDialogButtonBox, QDoubleSpinBox)

from gl_widget import GLWidget

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