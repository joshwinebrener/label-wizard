from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QSlider, QVBoxLayout

from widgets.aspect_ratio_pixmap_label import AspectRatioPixmapLabel


class VideoPlayer(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.img = AspectRatioPixmapLabel(self)
        self.img.setPixmap(QPixmap("puppy2.jpg"))
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.img)
        self.main_layout.addWidget(self.slider)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)
