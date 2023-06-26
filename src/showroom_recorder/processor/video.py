#!/usr/bin/env python3
import os
import time
import logging
import threading
import ffmpeg
import json
import requests
import datetime
import pytz
from .uploader import UploaderQueue, UploaderWebDav


fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36'
}


def get_status_by_room_url_key(room_url_key):
    url = "https://www.showroom-live.com/api/room/status"
    params = {
        "room_url_key": room_url_key,
    }
    response = requests.get(url=url, headers=fake_headers, params=params)
    status = response.json()
    return status


def get_online_by_roomid(room_id):
    url = "https://www.showroom-live.com/api/live/live_info"
    params = {
        "room_id": room_id,
    }
    response = requests.get(url=url, headers=fake_headers, params=params)
    response = response.json()
    if response['live_status'] == 2:
        return True
    else:
        return False


def get_room_url_key_by_status(status):
    return status['room_url_key']


def get_roomid_by_status(status):
    return status['room_id']


def get_online_by_status(status):
    return status['is_live']


def get_room_name_by_status(status):
    return status['room_name']


def get_start_time_by_status(status):
    t = status['started_at']
    dt = datetime.datetime.utcfromtimestamp(t)
    tz = pytz.timezone('Asia/Tokyo')
    dt = dt.astimezone(tz)
    return dt


def get_time_now():
    dt = datetime.datetime.now()
    tz = pytz.timezone('Asia/Tokyo')
    dt = dt.astimezone(tz)
    return dt


def get_stream_url_by_roomid(room_id):
    stream_url = ''
    api_endpoint = 'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&_={timestamp}&abr_available=1'.format(
        room_id=room_id, timestamp=str(int(time.time() * 1000)))
    try:
        response = requests.get(url=api_endpoint, headers=fake_headers).text
        response = json.loads(response)
        stream_url = response['streaming_url_list'][0]['url']
        for streaming_url in response['streaming_url_list']:
            if streaming_url['type'] == 'hls_all':
                stream_url = streaming_url['url']
    except Exception as e:
        raise Exception('get stream url error: ' + e)
    return stream_url


class Recorder:
    def __init__(self, status, uploader_queue, config):
        self.room_url_key = status['room_url_key']
        self.config = config
        self.is_recording = False
        self._thread = None
        self.status = status
        self.ffmpeg_proc = None
        self.output = ''
        self.uploader_queue = uploader_queue

    def start(self):
        self._thread = threading.Thread(target=self.record)
        self._thread.daemon = True
        self._thread.start()

    def quit(self):
        try:
            self.ffmpeg_proc.stdin.write('q'.encode('utf-8'))
        except Exception:
            pass
        # self._thread.join()

    def record(self):
        self.is_recording = True
        logging.info('{room_url_key}: is on live, start recording video.'.format(
            room_url_key=self.room_url_key))
        try:
            if not os.path.isdir('videos'):
                os.makedirs('videos')
            self.download(output_dir='videos')
        except Exception:
            self.is_recording = False
            logging.error('{room_url_key}: record video finished.'.format(
                room_url_key=self.room_url_key))

    def download(self, output_dir='.'):
        status = self.status
        try:
            stream_url = get_stream_url_by_roomid(get_roomid_by_status(status))
        except Exception as e:
            raise Exception('get stream url error: ' + e)

        title = '{name}_{time}'.format(
            name=self.room_url_key,
            time=get_time_now().strftime('%Y%m%d_%H%M%S'))

        self.output = output_dir + '/' + title + '.' + 'mp4'

        kwargs_dict = {'c:v': 'copy',
                       'c:a': 'copy',
                       'bsf:a': 'aac_adtstoasc',
                       'loglevel': 'error'}
        try:
            self.ffmpeg_proc = (
                ffmpeg
                .input(stream_url)
                .output(self.output, **kwargs_dict)
                .run()
            )
            self.ffmpeg_proc.communicate()
        except Exception as e:
            try:
                self.ffmpeg_proc.stdin.write('q'.encode('utf-8'))
            except Exception:
                pass
            self.__download_finish()
            raise Exception(e)
        return True

    def __download_finish(self):
        if os.path.exists(self.output):
            logging.info('{room_url_key}: video recording finished, saved to {output}.'.format(
                                room_url_key=self.room_url_key, output=self.output))
            if self.config['upload_webdav']:
                uploader = UploaderWebDav(self.output, 
                                          self.output, 
                                          self.config['webdav_url'], 
                                          self.config['webdav_username'], 
                                          self.config['webdav_password'])
                self.uploader_queue.put(uploader)


class RecroderManager:
    def __init__(self, room_url_key_list, config):
        self.room_url_key_list = room_url_key_list
        self.room_id_list = self.__get_room_id_list()
        self.rooms_num = len(self.room_url_key_list)
        self.recorders = [None] * self.rooms_num
        self.t = None
        self._isQuit = False
        self.config = config
        self.uploader_queue = UploaderQueue()

    def quit(self):
        self._isQuit = True
        self.t.join()

    def start(self):
        self.t = threading.Thread(target=self.manager)
        self.t.daemon = True
        self.t.start()
        return self.t

    def __get_room_id_list(self):
        room_id_list = []
        for room_url_key in self.room_url_key_list:
            status = get_status_by_room_url_key(room_url_key)
            room_id = get_roomid_by_status(status)
            room_id_list.append(room_id)
        return room_id_list

    def manager(self):
        self.uploader_queue.start()
        while True:
            for i in range(self.rooms_num):
                room_url_key = self.room_url_key_list[i]
                room_id = self.room_id_list[i]
                if self.recorders[i] is not None:
                    if self.recorders[i].is_recording:
                        continue
                    else:
                        self.recorders[i] = None
                        logging.info('{room_url_key}: delete recorder.'.format(
                            room_url_key=room_url_key))
                if self.recorders[i] is None:
                    try:
                        if get_online_by_roomid(room_id):
                            status = get_status_by_room_url_key(room_url_key)
                            r = Recorder(status, self.uploader_queue, self.config)
                            r.start()
                            self.recorders[i] = r
                            continue
                    except Exception as e:
                        logging.error('{room_url_key}: {e}'.format(
                            room_url_key=room_url_key, e=e))
            time.sleep(1)
