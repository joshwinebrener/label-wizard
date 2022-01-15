import requests
import csv
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from requests.models import DEFAULT_REDIRECT_LIMIT


class YouTube8mClient(object):
    """
    NOTE: tag, id, and name mean different things
    - tag: the hash of the label/category name.  Used to fetch ids.
    - id: the hash of the YouTube video url
    - name: the 10-character or so extension on youtube.com which distinguishes each video.
    """

    LABELS_CSV_URL = "https://research.google.com/youtube8m/csv/2/train-histogram-min.csv"
    TAG_TO_LIST_URL = "https://storage.googleapis.com/data.yt8m.org/2/j/v/"
    ID_TO_VIDEO_URL = "https://storage.googleapis.com/data.yt8m.org/2/j/i/"
    YOUTUBE_TEMPLATE_URL = "https://www.youtube.com/watch?v="

    def __init__(self):
        self.requests_session = requests.Session()
        self.labels = []
        self.urls = []
        self.last_id_accessed = {}

    def fetch_labels(self):
        try:
            r = self.requests_session.get(self.LABELS_CSV_URL)
        except ConnectionError:
            print(f"{__file__} unable to connect to network to download labels")
            return {}

        reader = csv.reader(r.text.split("\n"), delimiter=",")

        labels = {}
        for row in reader:
            if row:
                labels[row[2]] = (row[1], row[0])

        self.labels = labels
        return labels

    def fetch_next_ten_urls_for_tag(self, tag):
        NUM_URLS_TO_FETCH = 10

        tag = tag.replace("/m/", "")
        r = self.requests_session.get(f"{self.TAG_TO_LIST_URL}{tag}.js")

        # Remove javascript syntax
        text = (
            r.text.strip().replace("p(", "").replace(f"[", "").replace("]);", "").replace('"', "")
        )

        # Values are comma-separated and start with the tag (which is redundant)
        ids = [id for id in text.split(",") if id != tag]

        if tag not in self.last_id_accessed:
            self.last_id_accessed[tag] = 0

        urls = []
        while len(urls) < NUM_URLS_TO_FETCH:
            remaining = NUM_URLS_TO_FETCH - len(urls)

            with ThreadPoolExecutor(max_workers=remaining) as p:
                names = p.map(
                    self.get_yt_link_from_id,
                    ids[self.last_id_accessed[tag] : self.last_id_accessed[tag] + remaining],
                )
            names = [name for name in names if name]  # Remove empty

            self.last_id_accessed[tag] += len(names)
            urls.extend([self.YOUTUBE_TEMPLATE_URL + name for name in names])

        pprint(list(zip(ids[0:10], urls)))

        return urls

    def get_yt_link_from_id(self, id):
        r = self.requests_session.get(f"{self.ID_TO_VIDEO_URL}{id[0:2]}/{id}.js")
        responses = r.text.replace("i(", "").replace(");", "").replace('"', "").split(",")

        if len(responses) > 1:
            return responses[1]
        else:
            # AccessDenied: Anonymous caller does not have storage.objects.get access to the Google Cloud Storage object
            return ""
