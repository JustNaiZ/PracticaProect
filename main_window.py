# Главное окно приложения

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QFileDialog, QProgressDialog,
                             QMessageBox, QApplication, QLabel, QFrame)

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

    # В методе _create_tool_panel() добавим новые кнопки:
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

        self.rotate_180_btn = QPushButton("180°")
        buttons_layout.addWidget(self.rotate_180_btn)

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
        self.rotate_180_btn.clicked.connect(lambda: self.gl_widget.rotate(180))

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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Добавить изображение", "",
            "Images (*.bmp *.tif *.tiff *.png *.jpg *.jpeg)"
        )
        if file_path:
            try:
                progress_dialog = QProgressDialog("Добавление изображения...", "Отмена", 0, 100, self)
                progress_dialog.setWindowTitle("Прогресс")
                progress_dialog.setWindowModality(True)
                progress_dialog.setAutoClose(True)
                progress_dialog.setValue(0)

                def progress_callback(percent):
                    progress_dialog.setValue(percent)
                    QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        raise Exception("Добавление отменено пользователем")

                self.gl_widget.add_image(file_path, progress_callback)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить изображение:\n{str(e)}")

    def _open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть изображение", "",
            "Images (*.bmp *.tif *.tiff *.png *.jpg *.jpeg)"
        )
        if file_path:
            try:
                progress_dialog = QProgressDialog("Загрузка изображения...", "Отмена", 0, 100, self)
                progress_dialog.setWindowTitle("Прогресс")
                progress_dialog.setWindowModality(True)
                progress_dialog.setAutoClose(True)
                progress_dialog.setValue(0)

                def progress_callback(percent):
                    progress_dialog.setValue(percent)
                    QApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        raise Exception("Загрузка отменена пользователем")

                self.gl_widget.load_image(file_path, progress_callback)

                self.add_action.setVisible(True)
                self.mode_panel.setVisible(True)
                self._activate_move_mode()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")