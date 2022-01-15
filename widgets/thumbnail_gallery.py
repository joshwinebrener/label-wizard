from typing import Union

from PySide6.QtGui import QPixmap, QImage, QResizeEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

THUMBNAIL_WIDTH_PX = 8 * 16
THUMBNAIL_HEIGHT_PX = 8 * 9
THUMBNAIL_MARGIN_PX = 5


class ThumbnailGallery(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setSpacing(THUMBNAIL_MARGIN_PX)
        self.vertical_layout.setContentsMargins(
            THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX
        )
        self.setLayout(self.vertical_layout)
        self.thumbnails = []
        self.num_columns = 1

        for _ in range(50):
            self.add_thumbnail(QPixmap("puppy.jpeg"))
        self.render_thumbnails()

    def render_thumbnails(self, columns=None):
        if columns == self.num_columns:
            return
        elif columns is not None:
            self.num_columns = columns

        # Clear main layout
        while item := self.vertical_layout.takeAt(0):
            del item

        for i, thumbnail in enumerate(self.thumbnails):
            if i % self.num_columns == 0:
                row = ThumbnailRow()
                self.vertical_layout.addWidget(row)
            row.add_thumbnail(thumbnail)

    def add_thumbnail(self, pixmap: Union[QPixmap, QImage]):
        thumbnail = QLabel()
        thumbnail.setPixmap(pixmap)
        thumbnail.setScaledContents(True)
        thumbnail.setFixedWidth(THUMBNAIL_WIDTH_PX)
        thumbnail.setFixedHeight(THUMBNAIL_HEIGHT_PX)
        self.thumbnails.append(thumbnail)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # There is more tolerance on the minimum, because the QScrollArea stops resizing its child
        # at the true minimum
        min_width_before_rerender = 2 * THUMBNAIL_MARGIN_PX + (self.num_columns) * (
            THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX
        )
        max_width_before_rerender = THUMBNAIL_MARGIN_PX + (self.num_columns + 1) * (
            THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX
        )
        w = event.size().width()

        if not (min_width_before_rerender < event.size().width() < max_width_before_rerender):
            columns = (w - 2 * THUMBNAIL_MARGIN_PX) // (THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX)
            self.render_thumbnails(max(columns, 1))

        return super().resizeEvent(event)


class ThumbnailRow(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.setSpacing(THUMBNAIL_MARGIN_PX)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.horizontal_layout)

    def add_thumbnail(self, widget: QWidget):
        self.horizontal_layout.addWidget(widget)
