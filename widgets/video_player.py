import os
import time
from threading import Thread

from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QSize, QTimer
from PySide6.QtGui import QPainter, QResizeEvent
from PySide6.QtWidgets import (
    QWidget,
    QSlider,
    QVBoxLayout,
    QSizePolicy,
    QProgressBar,
    QGraphicsView,
    QGraphicsScene,
)

from pytube import YouTube
from pytube.exceptions import VideoPrivate


FNAME_PREFIX = "yt_download_"


class VideoPlayer(QWidget):
    file_size_changed = Signal(int)
    video_downloaded = Signal(str)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.video_window = VideoWindow()
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.loading = QProgressBar(self)
        self.loading.setRange(0, 0)
        self.loading.hide()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.video_window)
        self.main_layout.addWidget(self.slider)
        self.main_layout.addWidget(self.loading)
        self.setLayout(self.main_layout)

        self.timer = QTimer()
        self.timer.setInterval(15)
        self.timer.start()

        self.timer.timeout.connect(self._update_playhead)
        self.file_size_changed.connect(self._file_size_change)
        self.video_downloaded.connect(self.set_video_source)
        self.slider.sliderMoved.connect(self._jump_to_position)

    @Slot()
    def _jump_to_position(self, val):
        current_pos = self.video_window.position
        dur = self.video_window.duration
        new_pos = val / 1000 * dur
        increment = dur / 1000
        if not -increment < current_pos - new_pos < increment:
            self.video_window.set_position(new_pos)

    @Slot()
    def _update_playhead(self):
        pos = self.video_window.position
        dur = self.video_window.duration
        playhead = int(1000 * pos / dur if dur else 0)
        self.slider.setValue(playhead)

    def _load_video(self, yt: YouTube):
        self.loading.show()

        try:
            audio_video_streams = yt.streams.filter(progressive=True)
        except (AttributeError, VideoPrivate) as e:
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

        fname = f"{os.getcwd()}/{FNAME_PREFIX}{yt.watch_url.split('=')[1]}.mp4"
        if not os.path.exists(fname):
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
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.fname = None

        self.video_graphics = QGraphicsVideoItem()
        self.video_graphics.setAspectRatioMode(Qt.KeepAspectRatio)
        self.scene = QGraphicsScene(self)
        self.scene.addItem(self.video_graphics)
        self.scene.setBackgroundBrush(Qt.white)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_graphics)

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.view)
        self.setLayout(self.vertical_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @property
    def duration(self):
        return self.media_player.duration()

    @property
    def position(self):
        return self.media_player.position()

    def set_position(self, new_pos):
        self.media_player.setPosition(new_pos)

    def load(self, fname: str):
        self.fname = fname
        if self.media_player.playbackState == QMediaPlayer.PlayingState:
            self.stop()
        url = QUrl.fromLocalFile(fname)
        self.media_player.setSource(url)
        self.resizeEvent(QResizeEvent(QSize(self.size()), QSize(self.size())))

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()

    def clear(self):
        pass

    # def sizeHint(self) -> QSize:
    #     aspect_ratio = self.video_graphics.size().width() / self.video_graphics.size().height()
    #     w = self.size().width()
    #     h = w / aspect_ratio
    #     return QSize(w, h)
    #     # return super().sizeHint()

    def resizeEvent(self, event):
        self.view.fitInView(self.video_graphics, Qt.KeepAspectRatio)
        # print(self.view.size())
        # aspect_ratio = self.video_graphics.size().width() / self.video_graphics.size().height()
        # delta = max(
        #     abs(event.oldSize().width() - event.size().width()),
        #     abs(event.oldSize().height() - event.size().height()),
        # )
        # self.setMinimumSize(
        #     event.size().width() - delta, event.size().width() / aspect_ratio - delta
        # )
        # self.setMaximumSize(
        #     event.size().width() + delta, event.size().width() / aspect_ratio + delta
        # )
        return super().resizeEvent(event)
