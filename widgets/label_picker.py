from threading import Thread

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QCompleter,
    QProgressBar,
)

from youtube_8m import YouTube8mClient


class LabelPicker(QWidget):
    urls_ready = Signal(list)
    fetching_urls = Signal(str)
    labels_fetched = Signal()

    def __init__(self, yt8m_client: YouTube8mClient, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.yt8m_client = yt8m_client
        self.tag = ""

        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.label_picker = QLineEdit()
        self.label_picker.setPlaceholderText("YouTube video label")
        self.label_picker.setCompleter(self.completer)
        self.submit_button = QPushButton("submit")

        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.addWidget(self.label_picker)
        self.horizontal_layout.addWidget(self.submit_button)

        self.loading = QProgressBar()
        self.loading.setRange(0, 0)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addWidget(self.loading)
        self.setLayout(self.vertical_layout)

        self.label_picker.returnPressed.connect(self.submit_label)
        self.label_picker.textEdited.connect(self.check_labels_fetched)
        self.submit_button.clicked.connect(self.submit_label)
        self.labels_fetched.connect(self._show_popup_if_text_entered)

        self.fetch_thread = Thread(target=self._fetch_labels)
        self.fetch_thread.start()

    def _fetch_labels(self):
        self.loading.show()
        self.yt8m_client.fetch_labels()
        self.labels_fetched.emit()
        self.loading.hide()

    def _show_popup_if_text_entered(self):
        self.label_picker.completer().model().setStringList(self.yt8m_client.labels)
        if self.label_picker.text() != "":
            self.label_picker.completer().complete()

    def fetch_next_ten_urls_for_tag(self, tag=None):
        self.loading.show()

        if tag is None:
            if self.tag:
                tag = self.tag
            else:
                return
        else:
            self.tag = tag

        self.fetching_urls.emit(tag)
        urls = self.yt8m_client.fetch_next_ten_urls_for_tag(tag)
        self.urls_ready.emit(urls)

    @Slot()
    def check_labels_fetched(self):
        if self.fetch_thread.is_alive():
            return

        if self.completer is None:
            self.label_picker.completer().model().setStringList(self.yt8m_client.labels)

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
