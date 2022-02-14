import sys
import glob
import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QSplitter, QHBoxLayout, QWidget
from widgets.video_selection_panel import VideoSelectionPanel
from widgets.video_player import VideoPlayer, FNAME_PREFIX

from youtube_8m import YouTube8mClient


class MyWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.yt8m_client = YouTube8mClient()

        self.video_selection_panel = VideoSelectionPanel(self.yt8m_client, self)
        self.frame_sweeper = VideoPlayer(self)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.video_selection_panel)
        self.splitter.addWidget(self.frame_sweeper)

        # Only stretch the left side when the window is resized
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.splitter)

        self.video_selection_panel.thumbnail_gallery.video_selected.connect(
            self.frame_sweeper.load_video
        )

    def sizeHint(self) -> QSize:
        return QSize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MyWidget()
    widget.show()

    return_value = app.exec()

    for fname in glob.glob(f"./{FNAME_PREFIX}*.mp4"):
        os.remove(fname)

    sys.exit(return_value)
