from PyQt5.QtWidgets import QMainWindow, QFileDialog, QVBoxLayout, QWidget, QPushButton
from tiled_raster_widget import TiledRasterWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сейсмограмма - Тайловая визуализация")
        self.resize(1200, 800)

        self.viewer = TiledRasterWidget()

        open_btn = QPushButton("Загрузить растр")
        open_btn.clicked.connect(self.open_image)

        layout = QVBoxLayout()
        layout.addWidget(open_btn)
        layout.addWidget(self.viewer)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", "Изображения (*.png *.jpg *.bmp *.tif *.tiff)")
        if file_path:
            self.viewer.load_image(file_path)
