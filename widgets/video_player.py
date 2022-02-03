import os
import time
from threading import Thread
from xml.dom.minidom import Attr

from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget, QGraphicsVideoItem
from PySide6.QtCore import Qt, Signal, Slot, QRectF, QPointF, QUrl, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QSlider,
    QVBoxLayout,
    QProgressBar,
    QGraphicsView,
    QGraphicsScene,
)

from pytube import YouTube

from widgets.aspect_ratio_pixmap_label import AspectRatioPixmapLabel


class VideoPlayer(QWidget):
    file_size_changed = Signal(int)
    video_downloaded = Signal(str)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.video_window = VideoWindow()
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.loading = QProgressBar(self)
        self.loading.setRange(0, 0)
        self.loading.hide()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.video_window)
        self.main_layout.addWidget(self.slider)
        self.main_layout.addWidget(self.loading)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

        self.file_size_changed.connect(self._file_size_change)
        self.video_downloaded.connect(self.set_video_source)

    def _load_video(self, yt: YouTube):
        self.loading.show()

        try:
            audio_video_streams = yt.streams.filter(progressive=True)
        except AttributeError as e:
            print(e)
            self.loading.hide()
            return

        max_resolution = 0
        chosen_stream = None
        for stream in audio_video_streams:
            res = int(stream.resolution.replace("p", ""))
            if max_resolution < res < 1440:
                max_resolution = res
                chosen_stream = stream

        if chosen_stream is None:
            print("No available stream")
            self.loading.hide()
            return

        i = 0
        while os.path.exists(f"{os.getcwd()}/{i}.mp4"):
            i += 1
        fname = f"{os.getcwd()}/{i}.mp4"
        fsize_mb = chosen_stream.filesize_approx // (1024 * 1024)
        self.loading.setRange(0, fsize_mb)
        t = Thread(
            target=chosen_stream.download,
            kwargs={"filename": fname, "skip_existing": False},
        )
        t.start()
        while t.is_alive():
            time.sleep(0.1)
            if os.path.exists(fname):
                self.file_size_changed.emit(os.path.getsize(fname) // (1024 * 1024))
        t.join()
        self.loading.hide()

        self.video_downloaded.emit(fname)

    @Slot()
    def set_video_source(self, fname: str):
        self.video_window.clear()
        self.video_window.load(fname)
        self.video_window.play()

    @Slot()
    def _file_size_change(self, size: int):
        self.loading.setValue(size)

    def load_video(self, yt: YouTube):
        self.loading.setRange(0, 0)
        t = Thread(target=self._load_video, args=(yt,))
        t.start()


class VideoWindow(QWidget):
    DEFAULT_FNAME = "./yt_logo.jpg"

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.fname = self.DEFAULT_FNAME

        self.video_widget = QVideoWidget()
        self.video_widget.show()
        self.video_widget.setMinimumSize(QSize(100, 100))

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.video_widget)
        self.setLayout(self.vertical_layout)

        self.load(self.fname)
        self.play()

    def load(self, fname: str):
        self.fname = fname
        if self.media_player.playbackState == QMediaPlayer.PlayingState:
            self.stop()
        url = QUrl.fromLocalFile(fname)
        self.media_player.setSource(url)

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()

    def clear(self):
        if os.path.exists(self.fname) and self.fname != self.DEFAULT_FNAME:
            os.remove(self.fname)
