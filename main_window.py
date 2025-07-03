from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressDialog, QApplication
from gl_widget import GLWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Аналоговые сейсмограммы")
        self.setGeometry(100, 100, 1024, 768)

        self.gl_widget = GLWidget(self)
        self.setCentralWidget(self.gl_widget)

        self._create_menu()

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        open_action = file_menu.addAction("Открыть изображение")
        open_action.triggered.connect(self._open_image)

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
