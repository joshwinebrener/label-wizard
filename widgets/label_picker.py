from threading import Thread

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QCompleter

from youtube_8m import YouTube8mClient


class LabelPicker(QWidget):
    urls_ready = Signal(str, list)

    def __init__(self, yt8m_client: YouTube8mClient, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.yt8m_client = yt8m_client

        self.completer = None
        self.label_picker = QLineEdit()
        self.label_picker.setPlaceholderText("YouTube video label")
        self.submit_button = QPushButton("submit")

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.label_picker)
        self.layout.addWidget(self.submit_button)

        self.label_picker.returnPressed.connect(self.submit_label)
        self.label_picker.textEdited.connect(self.check_labels_fetched)
        self.submit_button.clicked.connect(self.submit_label)

        self.fetch_thread = Thread(target=self.yt8m_client.fetch_labels)
        self.fetch_thread.start()

    def fetch_next_ten_urls_for_tag(self, tag):
        urls = self.yt8m_client.fetch_next_ten_urls_for_tag(tag)
        self.urls_ready.emit(tag, urls)

    @Slot()
    def check_labels_fetched(self):
        if self.fetch_thread.is_alive():
            return

        if self.completer is None:
            self.completer = QCompleter(self.yt8m_client.labels)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.label_picker.setCompleter(self.completer)

    @Slot()
    def submit_label(self):
        if self.fetch_thread.is_alive():
            self.fetch_thread.join()

        label = self.label_picker.text()
        if label in self.yt8m_client.labels:
            tag = self.yt8m_client.labels[label][0]
            self.fetch_thread = Thread(target=self.fetch_next_ten_urls_for_tag, args=(tag,))
            self.fetch_thread.start()
        else:
            print("not a valid label")
