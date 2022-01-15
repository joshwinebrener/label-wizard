import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplitter, QHBoxLayout, QWidget
from widgets.video_selection_panel import VideoSelectionPanel
from widgets.video_player import VideoPlayer

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

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.splitter)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
