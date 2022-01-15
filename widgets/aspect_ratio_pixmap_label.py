from typing import Union

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QResizeEvent
from PySide6.QtWidgets import QLabel


class AspectRatioPixmapLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)

        self.setMinimumSize(1, 1)
        self.full_size_pixmap = None

    def setPixmap(self, pix: Union[QPixmap, QImage]) -> None:
        self.full_size_pixmap = pix
        return super().setPixmap(self.scaled_pixmap())

    def scaled_pixmap(self) -> Union[QPixmap, QImage]:
        return self.full_size_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.FastTransformation)

    def heightForWidth(self, width):
        if self.full_size_pixmap:
            return self.full_size_pixmap.height() * width / self.full_size_pixmap.width()
        else:
            return self.height()

    def sizeHint(self):
        w = self.width()
        return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.full_size_pixmap:
            self.setPixmap(self.full_size_pixmap)
        return super().resizeEvent(event)
