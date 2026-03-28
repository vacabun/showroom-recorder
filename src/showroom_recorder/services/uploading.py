import logging
import os
import threading
from queue import Empty, Queue

from biliup.plugins.bili_webup import BiliBili, Data
from webdav4.client import Client


class UploaderBili:
    def __init__(self, file_path, room_url_key, room_name, time_str, lines="AUTO"):
        self.file_path = file_path
        self.room_url_key = room_url_key
        self.room_name = room_name
        self.time_str = time_str
        self.lines = lines

    def upload(self):
        logging.info("upload by biliup.")
        video = Data()
        video.title = f"{self.room_name} showroom {self.time_str}"
        video.desc = ""
        video.source = f"https://www.showroom-live.com/{self.room_url_key}"
        video.tid = 137
        video.set_tag(["showroom"])
        video.copyright = 2
        try:
            with BiliBili(video) as bili:
                bili.login(persistence_path="", user_cookie="cookies.json")
                video_part = bili.upload_file(self.file_path, lines=self.lines, tasks=32)
                video.append(video_part)
                video.delay_time(0)
                bili.submit(submit_api="web")
        except Exception as exc:
            logging.error("bilibili upload error: %s", exc)
            raise RuntimeError("bilibili upload error") from exc


class UploaderWebDav:
    def __init__(self, from_path, to_path, url, username="", password=""):
        self.from_path = from_path
        self.to_path = to_path
        self.url = url
        self.username = username
        self.password = password
        self.delete_source_file = False

    def enable_delete_source_file(self):
        self.delete_source_file = True

    def upload(self):
        logging.info("upload by webdav.")
        client = Client(base_url=self.url, auth=(self.username, self.password))
        try:
            client.upload_file(from_path=self.from_path, to_path=self.to_path)
        except Exception as exc:
            logging.error("webdav upload error: %s", exc)
            raise RuntimeError("webdav upload error") from exc

        if self.delete_source_file:
            os.remove(self.from_path)


class UploaderQueue:
    def __init__(self):
        self.uploader_queue = Queue()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self.run, name="uploader-queue", daemon=True)
        self._thread.start()

    def stop(self, timeout=None):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def put(self, uploader):
        self.uploader_queue.put(uploader)

    def run(self):
        while not self._stop_event.is_set() or not self.uploader_queue.empty():
            try:
                uploader = self.uploader_queue.get(timeout=1)
            except Empty:
                continue

            try:
                uploader.upload()
            except Exception as exc:
                logging.error("upload error: %s", exc)
            finally:
                self.uploader_queue.task_done()
