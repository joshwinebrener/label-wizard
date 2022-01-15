import os
from typing import Union, List
from concurrent.futures import ThreadPoolExecutor
import requests

from PySide6.QtGui import QPixmap, QImage, QResizeEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from pytube import YouTube

THUMBNAIL_WIDTH_PX = 8 * 16
THUMBNAIL_HEIGHT_PX = 8 * 9
THUMBNAIL_MARGIN_PX = 5


def get_thumbnail_url(yt: YouTube) -> str:
    """
    YouTube.thumbnail_url takes about 3 seconds on my machine to complete the first time.
    This function allows it to be put in a thread pool.
    """
    return yt.thumbnail_url


class ThumbnailGallery(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.current_tag = ""

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
            w = item.widget()
            del w
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

    def add_thumbnails_from_urls(self, urls: List[str]) -> None:
        with ThreadPoolExecutor(max_workers=min(10, len(urls))) as p:
            youtubes = [YouTube(url) for url in urls]
            thumbnail_urls = p.map(get_thumbnail_url, youtubes)
            thumbnails = p.map(self._download_thumbnail, thumbnail_urls)
        for thumbnail in thumbnails:
            self.add_thumbnail(thumbnail)

    def _download_thumbnail(self, url: str) -> QPixmap:
        YOUTUBE_LOGO_FNAME = "yt_logo.jpg"
        try:
            r = requests.get(url)
            fname = url.split("/")[-1]
            open(fname, "wb").write(r.content)
            pix = QPixmap(fname)
            os.remove(fname)
        except Exception as e:
            print(e)
            pix = QPixmap(YOUTUBE_LOGO_FNAME)
        return pix

    def clear_thumbnails(self):
        self.thumbnails = []

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
