from queue import Queue
import logging
import threading
import time
from webdav4.client import Client


class UploaderWebDav:
    def __init__(self, from_path, to_path, url, username='', password=''):
        self.from_path = from_path
        self.to_path = to_path
        self.url = url
        self.username = username
        self.password = password

    def upload(self):
        logging.info('upload by webdav.')
        client = Client(base_url=self.url, auth=(self.username, self.password))
        try:
            client.upload_file(from_path=self.from_path, to_path=self.to_path)
        except Exception as e:
            logging.error('webdav upload error: ' + e)


class UploaderQueue:
    def __init__(self):
        self.uploader_queue = Queue()

    def start(self):
        self._thread = threading.Thread(target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def put(self, uploader):
        self.uploader_queue.put(uploader)

    def run(self):
        while True:
            if not self.uploader_queue.empty():
                try:
                    uploader = self.uploader_queue.get()
                    uploader.upload()
                except Exception as e:
                    logging.error('upload error:' + e)
            time.sleep(10)
