from ast import Load
import random
import time
import os
from typing import Union, List
from concurrent.futures import ThreadPoolExecutor
import requests

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap, QImage, QResizeEvent, QMovie
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from pytube import YouTube

THUMBNAIL_WIDTH_PX = 8 * 16
THUMBNAIL_HEIGHT_PX = 8 * 9
THUMBNAIL_MARGIN_PX = 5


class ThumbnailGallery(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.current_tag = ""

        self.loading_indicator = LoadingIndicator(self)
        self.loading_indicator.hide()

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setSpacing(THUMBNAIL_MARGIN_PX)
        self.vertical_layout.setContentsMargins(
            THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX
        )
        self.vertical_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(self.vertical_layout)
        self.thumbnails = []
        self.num_columns = 1

        # for _ in range(50):
        #     self.add_thumbnail(QPixmap("puppy.jpeg"))
        self.render_thumbnails()

        random.seed(int(time.time()))

    def render_thumbnails(self, columns=None):
        if columns == self.num_columns:
            return
        elif columns is not None:
            self.num_columns = columns

        # Clear main layout
        while item := self.vertical_layout.takeAt(0):
            w = item.widget()
            del w, item

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
        youtubes = [YouTube(url) for url in urls]
        with ThreadPoolExecutor(max_workers=min(10, len(urls))) as p:
            thumbnails = p.map(self._download_thumbnail, youtubes)

        self.vertical_layout.removeWidget(self.loading_indicator)
        self.loading_indicator.hide()

        for thumbnail in thumbnails:
            self.add_thumbnail(thumbnail)

    def _download_thumbnail(self, yt: YouTube) -> QPixmap:
        url = yt.thumbnail_url

        YOUTUBE_LOGO_FNAME = "yt_logo.jpg"
        try:
            r = requests.get(url)
            # TODO: this will collide in rare instances.  Try to find a more deterministic name.
            fname = f"{random.randint(100_000, 999_999)}.jpg"
            open(fname, "wb").write(r.content)
            pix = QPixmap(fname)
            os.remove(fname)
        except Exception as e:
            print(e)
            pix = QPixmap(YOUTUBE_LOGO_FNAME)
        return pix

    def clear_thumbnails(self):
        self.thumbnails = []
        self.render_thumbnails()

    def begin_loading_tag(self, tag: str):
        if tag != self.current_tag:
            self.clear_thumbnails()
            self.current_tag = tag

        self.vertical_layout.addWidget(self.loading_indicator)
        self.vertical_layout.setAlignment(self.loading_indicator, Qt.AlignHCenter)
        self.loading_indicator.show()

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


class LoadingIndicator(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)

        gif = QMovie("loading.gif")
        self.setMovie(gif)
        gif.start()

        self.setMaximumHeight(30)
        self.setMaximumWidth(30)

    def resizeEvent(self, event: QResizeEvent) -> None:
        rect = self.geometry()
        size = QSize(min(rect.width(), rect.height()), min(rect.width(), rect.height()))

        self.movie().setScaledSize(size)

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
