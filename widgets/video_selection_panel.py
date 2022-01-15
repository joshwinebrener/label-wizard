from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import (
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from widgets.label_picker import LabelPicker
from widgets.thumbnail_gallery import ThumbnailGallery


class VideoSelectionPanel(QWidget):
    def __init__(self, yt8m_client, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.label_picker = LabelPicker(yt8m_client)
        self.thumbnail_gallery = ThumbnailGallery()
        self.thumbnail_gallery.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.thumbnail_scroll = VerticalScrollArea()
        self.thumbnail_scroll.setWidget(self.thumbnail_gallery)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.label_picker)
        self.vertical_layout.addWidget(self.thumbnail_scroll)


class VerticalScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def eventFilter(self, o: QObject, e: QEvent) -> bool:
        if o == self.widget() and e.type() == QEvent.Resize:
            self.setMinimumWidth(
                self.widget().minimumSizeHint().width() + self.verticalScrollBar().width()
            )
        return super().eventFilter(o, e)