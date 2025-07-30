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
from .uploader import UploaderQueue, UploaderWebDav, UploaderBili
import re
import m3u8

fake_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,ja;q=0.6',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}


def get_status_by_room_url_key(room_url_key):
    url = "https://www.showroom-live.com/api/room/status"
    params = {
        "room_url_key": room_url_key
    }
    response = requests.get(url=url, headers=fake_headers, params=params)
    status = response.json()
    return status


def showroom_get_roomid_by_room_url_key(room_url_key):
    webpage_url = 'https://www.showroom-live.com/r/' + room_url_key
    try:
        response = requests.get(url=webpage_url, headers=fake_headers).text
        match = re.search(r'href="/room/profile\?room_id\=(\d+)"', response)
        if match:
            room_id = match.group(1)
            return room_id
    except Exception:
        raise Exception('get room_id error.')


def get_online_by_liveinfo(liveinfo):
    if liveinfo['live_status'] == 2:
        return True
    else:
        return False


def get_liveinfo_by_roomid(room_id):
    url = "https://www.showroom-live.com/api/live/live_info"
    params = {
        "room_id": room_id
    }
    response = requests.get(url=url, headers=fake_headers, params=params)
    response = response.json()
    return response


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


def get_max_bandwidth_stream(m3u8_url):
    best_stream_url = m3u8_url
    stream_dict = {}
    max_bandwidth = 0

    try:
        playlist = m3u8.load(m3u8_url)
        for stream in playlist.playlists:
            bandwidth = stream.stream_info.bandwidth
            stream_url = stream.uri
            if not stream_url.startswith("http"):
                base_url = m3u8_url.rsplit("/", 1)[0]
                stream_url = f"{base_url}/{stream_url}"
            stream_dict[bandwidth] = stream_url
            max_bandwidth = max(stream_dict.keys())
            best_stream_url = stream_dict[max_bandwidth]
    except Exception as e:
        logging.error('Analyze m3u8 error:')
        pass
    return stream_dict, max_bandwidth, best_stream_url


class Recorder:
    def __init__(self, room_url_key, live_info, uploader_queue, config):
        self.room_url_key = room_url_key
        self.live_info = live_info
        self.room_name = live_info['room_name']
        self.room_id = live_info['room_id']
        self.uploader_queue = uploader_queue
        self.config = config
        self.is_recording = False
        self._thread = None
        self.ffmpeg_proc = None
        self.output = ''
        self.user_agent = ''
        self.upload_to_bilibili = False
        self.time_str = ''

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

    def enable_uploader_bili(self):
        self.upload_to_bilibili = True

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
        try:
            stream_url = get_stream_url_by_roomid(self.room_id)
            logging.info('{room_url_key}: stream url is {stream_url}.'.format(
                room_url_key=self.room_url_key, stream_url=stream_url))
        except Exception as e:
            raise Exception('get stream url error: ' + e)
        __, __, stream_url = get_max_bandwidth_stream(stream_url)
        logging.info('{room_url_key}: max bandwidth stream url is {stream_url}.'.format(
            room_url_key=self.room_url_key, stream_url=stream_url))

        self.time_str = get_time_now().strftime('%Y%m%d_%H%M%S')

        title = '{name}_{time}'.format(
            name=self.room_url_key,
            time=self.time_str)

        self.output = output_dir + '/' + title + '.' + 'mp4'

        kwargs_dict = {'c:v': 'copy',
                       'c:a': 'copy',
                       'bsf:a': 'aac_adtstoasc',
                       'loglevel': 'error'}
        try:
            self.ffmpeg_proc = (
                ffmpeg
                .input(stream_url, **{'rw_timeout': str(30*1000*1000)})
                .output(self.output, **kwargs_dict)
                .run()
            )
            self.ffmpeg_proc.communicate()
        except Exception as e:
            try:
                logging.info('{room_url_key}: video recording error, try to stop ffmpeg process.{e}'.format(
                    room_url_key=self.room_url_key, e=str(e)))
                self.ffmpeg_proc.stdin.write('q'.encode('utf-8'))
                self.ffmpeg_proc.stdin.flush()
            except Exception:
                pass
            self.__download_finish()
            raise Exception(e)
        return True

    def __download_finish(self):
        if os.path.exists(self.output):
            logging.info(f'{self.room_url_key}: video recording finished, saved to {self.output}.')

            if self.upload_to_bilibili:
                login_cookie = {
                    "cookies": {
                        "SESSDATA": self.config.biliup.sessdata,
                        "bili_jct": self.config.biliup.bili_jct,
                        "DedeUserID__ckMd5": self.config.biliup.DedeUserID__ckMd5,
                        "DedeUserID": self.config.biliup.DedeUserID
                    },
                    "access_token": self.config.biliup.access_token
                }
                uploader_bili = UploaderBili(file_path=self.output,
                                             room_url_key=self.room_url_key,
                                             room_name=self.room_name,
                                             time_str=self.time_str,
                                             login_cookie=login_cookie,
                                             lines=self.config.biliup.line)
                self.uploader_queue.put(uploader_bili)

            if self.config['upload_webdav']:
                uploader_webdav = UploaderWebDav(self.output,
                                                 self.output,
                                                 self.config['webdav_url'],
                                                 self.config['webdav_username'],
                                                 self.config['webdav_password'])
                if (self.config['webdav_delete_source_file']):
                    uploader_webdav.enable_delete_source_file()
                self.uploader_queue.put(uploader_webdav)


class RecroderManager:
    def __init__(self, config):
        self.room_url_key_list = config.rooms
        self.room_id_list = self.__get_room_id_list()
        self.rooms_num = len(self.room_url_key_list)
        self.recorders = [None] * self.rooms_num
        self.recorder_thread = None
        self._isQuit = False
        self.config = config
        self.uploader_queue = UploaderQueue()
        self.biliup_list = config.biliup.rooms

    def quit(self):
        self._isQuit = True
        self.recorder_thread.join()

    def start(self):
        self.recorder_thread = threading.Thread(target=self.manager)
        self.recorder_thread.daemon = True
        self.recorder_thread.start()
        return self.recorder_thread

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
                        live_info = get_liveinfo_by_roomid(room_id)
                        is_live = get_online_by_liveinfo(live_info)
                    except Exception:
                        logging.error('{room_url_key}: get online error wait 30s....'.format(
                            room_url_key=room_url_key))
                        time.sleep(30)
                    if is_live:
                        try:
                            r = Recorder(room_url_key, live_info,
                                         self.uploader_queue, self.config)
                            if room_url_key in self.biliup_list:
                                r.enable_uploader_bili()
                            r.start()
                            self.recorders[i] = r
                            continue
                        except Exception as e:
                            logging.error('{room_url_key}: {e}'.format(
                                room_url_key=room_url_key, e=str(e)))
            time.sleep(int(self.config.interval))
