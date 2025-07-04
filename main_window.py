# Главное окно приложения

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from gl_widget import GLWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Аналоговые сейсмограммы")
        self.setGeometry(100, 100, 1024, 768)

        self.gl_widget = GLWidget(self)
        self.setCentralWidget(self.gl_widget)

        self._create_menu()
        self._create_tools_menu()

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        open_action = file_menu.addAction("Открыть изображение")
        open_action.triggered.connect(self._open_image)

    def _create_tools_menu(self):
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("Инструменты")

        # Стандартные повороты
        rotate_menu = tools_menu.addMenu(QIcon("rotate.png"), "Поворот")

        rotate_left = QAction(QIcon("rotate_left.png"), "На 90° влево", self)
        rotate_left.triggered.connect(lambda: self.gl_widget.rotate(-90))
        rotate_menu.addAction(rotate_left)

        rotate_right = QAction(QIcon("rotate_right.png"), "На 90° вправо", self)
        rotate_right.triggered.connect(lambda: self.gl_widget.rotate(90))
        rotate_menu.addAction(rotate_right)

        rotate_180 = QAction("На 180°", self)
        rotate_180.triggered.connect(lambda: self.gl_widget.rotate(180))
        rotate_menu.addAction(rotate_180)

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
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")