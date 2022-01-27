import os
import random
import time
from threading import Thread

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QSlider, QVBoxLayout, QProgressBar

from pytube import YouTube

from widgets.aspect_ratio_pixmap_label import AspectRatioPixmapLabel


class VideoPlayer(QWidget):
    file_size_changed = Signal(int)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.img = AspectRatioPixmapLabel(self)
        self.img.setPixmap(QPixmap("puppy2.jpg"))
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.loading = QProgressBar(self)
        self.loading.setRange(0, 0)
        self.loading.hide()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.img)
        self.main_layout.addWidget(self.slider)
        self.main_layout.addWidget(self.loading)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

        self.file_size_changed.connect(self._file_size_change)

    def _load_video(self, yt: YouTube):
        audio_video_streams = yt.streams.filter(progressive=True)
        max_resolution = 0
        chosen_stream = None
        for stream in audio_video_streams:
            res = int(stream.resolution.replace("p", ""))
            if max_resolution < res < 1440:
                max_resolution = res
                chosen_stream = stream

        if chosen_stream is None:
            print("No available stream")
            return

        fname = "./selected_video.mp4"
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

    @Slot()
    def _file_size_change(self, size: int):
        self.loading.setValue(size)

    def load_video(self, yt: YouTube):
        self.loading.setRange(0, 0)
        self.loading.show()
        t = Thread(target=self._load_video, args=(yt,))
        t.start()
