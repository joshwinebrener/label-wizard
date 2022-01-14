import sys

from PySide6.QtCore import QLine, Qt, Slot
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QWidget,
)


from youtube_8m import YouTube8mClient


class MyWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.yt8m_client = YouTube8mClient()

        self.completer = QCompleter(self.yt8m_client.labels.keys())
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.label_picker = QLineEdit()
        self.label_picker.setCompleter(self.completer)
        self.label_picker.setPlaceholderText("YouTube video label")
        self.submit_button = QPushButton("submit")

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.label_picker)
        self.layout.addWidget(self.submit_button)

        self.label_picker.returnPressed.connect(self.submit_label)
        self.submit_button.clicked.connect(self.submit_label)

    @Slot()
    def submit_label(self):
        label = self.label_picker.text()
        if label in self.yt8m_client.labels:
            tag = self.yt8m_client.labels[label][0]
            self.yt8m_client.fetch_next_ten_urls_for_tag(tag)
        else:
            print("not a valid label")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
