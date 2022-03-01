import os
import pwd
import time
from threading import Thread
import math

from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QSize, QTimer
from PySide6.QtGui import QPainter, QResizeEvent, QKeyEvent, QIcon, QMouseEvent, QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsRectItem,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QGraphicsTextItem,
    QLabel,
    QGraphicsSceneMouseEvent,
    QWidget,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QProgressBar,
    QGraphicsView,
    QGraphicsScene,
)

import cv2
import yaml
from pytube import YouTube


FNAME_PREFIX = "yt_download_"


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class VideoPlayer(QWidget):
    file_size_changed = Signal(int)
    video_downloaded = Signal(str)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.custom_data_yaml_file = None
        self.output_folder = None

        # Theme names from here:
        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        self.load_labels_button = QPushButton(
            QIcon.fromTheme("system-file-manager"), "load labels file"
        )
        self.label_selector = QComboBox()
        self.open_folder_button = QPushButton(
            QIcon.fromTheme("system-file-manager"), "load output folder"
        )
        self.save_button = QPushButton(QIcon.fromTheme("document-save"), "save bounding boxes")
        self.help_button = QPushButton(QIcon.fromTheme("help-about"), "help")
        self.video_window = VideoWindow()
        self.seek_backward_button = QPushButton(QIcon.fromTheme("media-seek-backward"), "")
        self.play_button = QPushButton(QIcon.fromTheme("media-playback-start"), "")
        self.seek_forward_button = QPushButton(QIcon.fromTheme("media-seek-forward"), "")
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.loading = QProgressBar(self)
        self.loading.setRange(0, 0)
        self.loading.hide()

        self.menu_bar = QHBoxLayout()
        self.menu_bar.addWidget(self.load_labels_button)
        self.menu_bar.addWidget(self.label_selector)
        self.menu_bar.addStretch()
        self.menu_bar.addWidget(self.save_button)
        self.menu_bar.addWidget(self.help_button)
        self.playhead_layout = QHBoxLayout()
        self.playhead_layout.addWidget(self.seek_backward_button)
        self.playhead_layout.addWidget(self.play_button)
        self.playhead_layout.addWidget(self.seek_forward_button)
        self.playhead_layout.addWidget(self.slider)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.menu_bar)
        self.main_layout.addWidget(self.video_window)
        self.main_layout.addLayout(self.playhead_layout)
        self.main_layout.addWidget(self.loading)
        self.setLayout(self.main_layout)

        self.timer = QTimer()
        self.timer.setInterval(15)
        self.timer.start()

        self.yaml_dialog = QFileDialog(filter="YAML files (*.yaml *.yml)")
        self.help_dialog = QMessageBox(
            text="""j: back 10s
k/SPACE: play/pause
l: forward 10s
<: back 1 frame
>: forward 1 frame

Left-click to place a bounding box
Right-click to remove a bounding box"""
        )

        self.timer.timeout.connect(self._update_playhead)
        self.file_size_changed.connect(self._file_size_change)
        self.video_downloaded.connect(self.set_video_source)
        self.slider.sliderMoved.connect(self._jump_to_position)
        self.seek_backward_button.clicked.connect(self.seek_backward)
        self.play_button.clicked.connect(self.pause_play)
        self.seek_forward_button.clicked.connect(self.seek_forward)
        self.load_labels_button.clicked.connect(self.yaml_dialog.show)
        self.yaml_dialog.fileSelected.connect(self.load_labels_file)
        self.label_selector.currentTextChanged.connect(self.set_current_label)
        self.help_button.clicked.connect(self.help_dialog.show)
        self.save_button.clicked.connect(self.save_bounding_boxes)

        self.current_video = None

    @Slot()
    def set_current_label(self, label):
        for i in range(self.label_selector.count()):
            if label == self.label_selector.itemText(i):
                self.video_window.scene.current_label = label
                break

    @Slot()
    def load_labels_file(self, fname):
        self.custom_data_yaml_file = fname
        custom_data = None
        with open(fname, "r") as f:
            custom_data = yaml.safe_load(f)
        if custom_data is not None and "names" in custom_data:
            self.label_selector.clear()
            self.label_selector.addItems(custom_data["names"])

    @Slot()
    def save_bounding_boxes(self):
        if self.current_video is None:
            return

        if self.output_folder is None:
            self.output_folder = str(QFileDialog.getExistingDirectory(self, "Select Output Folder"))

        labels = []
        for i in range(self.label_selector.count()):
            labels.append(self.label_selector.itemText(i))

        video = cv2.VideoCapture(self.video_window.fname)
        video.set(cv2.CAP_PROP_POS_MSEC, self.video_window.position)
        success, image = video.read()
        fname = f"{self.output_folder}/{self.current_video}_{self.video_window.position}"
        if success:
            cv2.imwrite(fname + ".png", image)
        with open(fname + ".txt", "w") as f:
            for label in self.video_window.scene.rectangles:
                label_id = -1
                if label in labels:
                    label_id = labels.index(label)
                else:
                    continue
                for rect in self.video_window.scene.rectangles[label]:
                    l = min(rect.rect().x(), rect.rect().x() + rect.rect().width())
                    r = max(rect.rect().x(), rect.rect().x() + rect.rect().width())
                    t = min(rect.rect().y(), rect.rect().y() + rect.rect().height())
                    b = max(rect.rect().y(), rect.rect().y() + rect.rect().height())
                    f.writelines([f"{label_id} {l} {t} {r} {b}\n"])

    def pause_play(self):
        if self.video_window.paused:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-pause"))
            self.video_window.play()
        else:
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
            self.video_window.pause()

    def seek_forward(self):
        self.video_window.set_position(self.video_window.position + 10_000)

    def seek_backward(self):
        self.video_window.set_position(self.video_window.position - 10_000)

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
        except Exception as e:
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

        self.current_video = yt.watch_url.split("=")[1]
        fname = f"{os.getcwd()}/{FNAME_PREFIX}{self.current_video}.mp4"
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

        # Show the first frame, but keep the video paused
        self.video_window.play()
        self.video_window.pause()

    @Slot()
    def _file_size_change(self, size: int):
        self.loading.setValue(size)

    def load_video(self, yt: YouTube):
        self.loading.setRange(0, 0)
        t = Thread(target=self._load_video, args=(yt,))
        t.start()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.text() == " ":
            self.pause_play()
        elif event.text() == "j":
            self.seek_backward()
        elif event.text() == "k":
            self.pause_play()
        elif event.text() == "l":
            self.seek_forward()
        elif event.text() == "<":
            # Skip backward 30ms, or about one frame
            self.video_window.set_position(self.video_window.position - 15)
        elif event.text() == ">":
            # Skip forward 30ms, or about one frame
            self.video_window.set_position(self.video_window.position + 15)

        return super().keyPressEvent(event)


class VideoWindow(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.fname = None

        self.video_graphics = QGraphicsVideoItem()
        self.video_graphics.setAspectRatioMode(Qt.KeepAspectRatio)
        self.scene = DrawableGraphicsScene(self)
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
        self.view.fitInView(self.video_graphics, Qt.KeepAspectRatio)

    def play(self):
        self.media_player.play()

    @property
    def paused(self):
        return self.media_player.playbackState() in [
            QMediaPlayer.PausedState,
            QMediaPlayer.StoppedState,
        ]

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()

    def clear(self):
        pass

    def resizeEvent(self, event):
        self.view.fitInView(self.video_graphics, Qt.KeepAspectRatio)
        return super().resizeEvent(event)


class DrawableGraphicsScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        QGraphicsScene.__init__(self, *args, **kwargs)
        self.rectangles = {}
        self.markers = {}
        self.click_point = None
        self.current_label = "?"
        self.unique_color = None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.click_point = event.scenePos()
            next_rect = QGraphicsRectItem(self.click_point.x(), self.click_point.y(), 0, 0)
            r = sigmoid(hash(self.current_label) / (1 << 63)) * 255
            g = sigmoid(hash(self.current_label[1:] + self.current_label[0]) / (1 << 63)) * 255
            b = sigmoid(hash(self.current_label[2:] + self.current_label[0:2]) / (1 << 63)) * 255
            brightness = math.sqrt(r * r + g * g + b * b)
            self.unique_color = QColor(
                r / brightness * 255,
                g / brightness * 255,
                b / brightness * 255,
                255,
            )
            next_rect.setPen(self.unique_color)
            if self.current_label not in self.rectangles or not self.rectangles[self.current_label]:
                self.rectangles[self.current_label] = []
            self.rectangles[self.current_label].append(next_rect)
            self.addItem(self.rectangles[self.current_label][-1])

        elif event.button() == Qt.RightButton:
            to_remove = []
            for label in self.rectangles:
                for i, rect in enumerate(self.rectangles[label]):
                    br = rect.boundingRect()
                    x = event.scenePos().x()
                    y = event.scenePos().y()
                    l = min(br.x(), br.x() + br.width())
                    r = max(br.x(), br.x() + br.width())
                    t = min(br.y(), br.y() + br.height())
                    b = max(br.y(), br.y() + br.height())
                    if l < x < r and t < y < b:
                        to_remove.append((label, i))
            to_remove.reverse()
            for (label, i) in to_remove:
                self.removeItem(self.rectangles[label][i])
                self.rectangles[label].pop(i)
                self.removeItem(self.markers[label][i])
                self.markers[label].pop(i)

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.click_point is not None:
            self.rectangles[self.current_label][-1].setRect(
                self.click_point.x(),
                self.click_point.y(),
                event.scenePos().x() - self.click_point.x(),
                event.scenePos().y() - self.click_point.y(),
            )

        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            if (
                abs(event.scenePos().x() - self.click_point.x()) < 10
                and abs(event.scenePos().y() - self.click_point.y()) < 10
            ):
                self.removeItem(self.rectangles[self.current_label][-1])
                self.rectangles[self.current_label].pop(-1)
            else:
                if self.current_label not in self.markers or not self.markers[self.current_label]:
                    self.markers[self.current_label] = []
                top_left_x = min(
                    self.rectangles[self.current_label][-1].rect().x(),
                    self.rectangles[self.current_label][-1].rect().x()
                    + self.rectangles[self.current_label][-1].rect().width(),
                )
                top_left_y = min(
                    self.rectangles[self.current_label][-1].rect().y(),
                    self.rectangles[self.current_label][-1].rect().y()
                    + self.rectangles[self.current_label][-1].rect().height(),
                )
                text = QGraphicsTextItem(self.current_label)
                self.markers[self.current_label].append(text)
                self.markers[self.current_label][-1].setDefaultTextColor(self.unique_color)
                self.markers[self.current_label][-1].setPos(top_left_x, top_left_y)
                self.markers[self.current_label][-1].setFont(QFont("Roboto", 3))
                self.addItem(self.markers[self.current_label][-1])

        self.click_point = None

        return super().mouseReleaseEvent(event)
