from queue import Queue
import logging
import threading
import time
import os
from webdav4.client import Client
from biliup.plugins.bili_webup import BiliBili, Data


class UploaderBili:
    def __init__(self, file_path, room_url_key, room_name, time_str, login_cookie, lines='AUTO'):
        self.file_path = file_path
        self.room_url_key = room_url_key
        self.room_name = room_name
        self.time_str = time_str
        self.login_cookie = login_cookie
        self.lines = lines

    def upload(self):
        logging.info('upload by biliup.')
        video = Data()
        video.title = self.room_name + ' showroom ' + self.time_str
        video.desc = ''
        video.source = 'https://www.showroom-live.com/' + self.room_url_key
        video.tid = 137
        video.set_tag(['showroom'])
        video.copyright = 2
        lines = self.lines
        tasks = 32
        dtime = 0
        try:
            with BiliBili(video) as bili:
                bili.login("bili_cookie.json", self.login_cookie)
                # bili.login_by_password("username", "password")
                video_part = bili.upload_file(self.file_path, lines=lines, tasks=tasks)
                video.append(video_part)
                video.delay_time(dtime)
                bili.submit(submit_api="web")
        except Exception as e:
            logging.error('bilibili upload error: ' + str(e))
            raise Exception('bilibili upload error.')


class UploaderWebDav:
    def __init__(self, from_path, to_path, url, username='', password=''):
        self.from_path = from_path
        self.to_path = to_path
        self.url = url
        self.username = username
        self.password = password
        self.delete_source_file = False
        
    def enable_delete_source_file(self):
        self.delete_source_file = True

    def upload(self):
        logging.info('upload by webdav.')
        client = Client(base_url=self.url, auth=(self.username, self.password))
        try:
            client.upload_file(from_path=self.from_path, to_path=self.to_path)
        except Exception as e:
            logging.error('webdav upload error: ' + str(e))
            raise Exception('webdav upload error.')
        if self.delete_source_file:
            os.remove(self.from_path)


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
                    logging.error('upload error:' + str(e))
            time.sleep(10)
