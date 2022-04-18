import random
import time
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import requests

from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QResizeEvent, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from pytube import YouTube

THUMBNAIL_WIDTH_PX = 8 * 16
THUMBNAIL_HEIGHT_PX = 8 * 9
THUMBNAIL_MARGIN_PX = 5


class ThumbnailGallery(QWidget):
    video_selected = Signal(YouTube)
    thumbnails_ready = Signal()

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.current_tag = ""
        self.busy = False

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setSpacing(THUMBNAIL_MARGIN_PX)
        self.vertical_layout.setContentsMargins(
            THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX, THUMBNAIL_MARGIN_PX
        )
        self.vertical_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(self.vertical_layout)
        self.thumbnails = []
        self.num_columns = 1

        self.render_thumbnails()

        random.seed(int(time.time()))

        self.thumbnails_ready.connect(self.render_thumbnails)

    @Slot()
    def render_thumbnails(self, columns=None):
        if columns == self.num_columns:
            return
        elif columns is not None:
            self.num_columns = columns

        # Clear main layout
        while item := self.vertical_layout.takeAt(0):
            w = item.widget()
            w.hide()
            del w, item

        for i, (pixmap, yt) in enumerate(self.thumbnails):
            thumbnail = Thumbnail(pixmap, yt)
            # yt=thumbnail.yt is a hack to prevent yt from referring to the last yt value
            thumbnail.clicked.connect(lambda *_, yt=thumbnail.yt: self.video_selected.emit(yt))

            if i % self.num_columns == 0:
                row = ThumbnailRow()
                self.vertical_layout.addWidget(row)
            row.add_thumbnail(thumbnail)

    def _add_thumbnails_from_urls(self, urls: List[str]) -> None:
        youtubes = [YouTube(url) for url in urls]
        with ThreadPoolExecutor(max_workers=min(10, len(urls))) as p:
            thumbnail_imgs = p.map(self._download_thumbnail, youtubes)

        self.thumbnails.extend(list(zip(thumbnail_imgs, youtubes)))
        self.thumbnails_ready.emit()

    def add_thumbnails_from_urls(self, urls: List[str]) -> None:
        t = Thread(target=self._add_thumbnails_from_urls, args=(urls,))
        t.start()

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
            print(f"error retrieving video: {e}")
            pix = QPixmap(YOUTUBE_LOGO_FNAME)
        return pix

    def clear_thumbnails(self):
        self.thumbnails = []
        self.render_thumbnails()

    def begin_loading_tag(self, tag: str):
        if not tag or tag != self.current_tag:
            self.clear_thumbnails()
            self.current_tag = tag

    def resizeEvent(self, event: QResizeEvent) -> None:
        min_width_before_rerender = (
            THUMBNAIL_MARGIN_PX
            + (self.num_columns) * (THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX)
            + 1
        )
        max_width_before_rerender = THUMBNAIL_MARGIN_PX + (self.num_columns + 1) * (
            THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX
        )
        w = event.size().width()

        if not (min_width_before_rerender < w < max_width_before_rerender):
            columns = (w - 2 * THUMBNAIL_MARGIN_PX) // (THUMBNAIL_WIDTH_PX + THUMBNAIL_MARGIN_PX)
            self.render_thumbnails(max(columns, 1))

        return super().resizeEvent(event)


class Thumbnail(QPushButton):
    def __init__(self, pixmap: QPixmap, yt: YouTube, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)

        self.yt = yt

        icon = QIcon(pixmap)
        self.setIcon(icon)
        self.setFlat(True)
        # Set the icon bigger than the button, and it will be downscaled to exactly the right size
        self.setIconSize(QSize(2 * THUMBNAIL_WIDTH_PX, 2 * THUMBNAIL_HEIGHT_PX))
        self.setFixedSize(QSize(THUMBNAIL_WIDTH_PX, THUMBNAIL_HEIGHT_PX))


class ThumbnailRow(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.setSpacing(THUMBNAIL_MARGIN_PX)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.horizontal_layout)

    def add_thumbnail(self, widget: QWidget):
        self.horizontal_layout.addWidget(widget)
