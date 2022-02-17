from PySide6.QtCore import Qt, QObject, QEvent, Signal, Slot
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

        self.label_picker.fetching_urls.connect(self.load_tag)
        self.label_picker.urls_ready.connect(self.handle_new_urls)
        # Removed because it would load 4 or 5 times (stalling the ui) when the user scrolled to the bottom
        # self.thumbnail_scroll.reached_bottom.connect(self.label_picker.fetch_next_ten_urls_for_tag)
        self.thumbnail_gallery.thumbnails_ready.connect(self.label_picker.loading.hide)

    @Slot()
    def load_tag(self, tag):
        self.thumbnail_gallery.begin_loading_tag(tag)

    @Slot()
    def handle_new_urls(self, urls):
        self.thumbnail_gallery.add_thumbnails_from_urls(urls)


class VerticalScrollArea(QScrollArea):
    reached_bottom = Signal()

    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def eventFilter(self, o: QObject, e: QEvent) -> bool:
        if o == self.widget() and e.type() == QEvent.Resize:
            self.setMinimumWidth(
                self.widget().minimumSizeHint().width() + self.verticalScrollBar().width()
            )

        # Signal to fetch more thumbnails when user scrolls to bottom
        if (
            e.type() == QEvent.Wheel
            and self.verticalScrollBar().value() == self.verticalScrollBar().maximum()
        ):
            self.reached_bottom.emit()

        return super().eventFilter(o, e)
