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


def download(status, output_dir='.'):
    try:
        stream_url = get_stream_url_by_roomid(get_roomid_by_status(status))
    except Exception as e:
        raise Exception('get stream url error: ' + e)
    try:
        title = '{name}_{time}'.format(
            name=get_room_url_key_by_status(status),
            time=get_time_now().strftime('%Y%m%d_%H%M%S'))
        output = output_dir + '/' + title + '.' + 'mp4'
    except Exception as e:
        raise Exception('get title error: ' + e)

    kwargs_dict = {'c:v': 'copy',
                   'c:a': 'copy',
                   'bsf:a': 'aac_adtstoasc',
                   'loglevel': 'error'}
    try:
        proc = (
            ffmpeg
            .input(stream_url)
            .output(output, **kwargs_dict)
            .run()
        )
        proc.communicate()
    except KeyboardInterrupt as e:
        try:
            proc.stdin.write('q'.encode('utf-8'))
        except Exception:
            pass
        raise Exception(e)
    except Exception as e:
        try:
            proc.stdin.write('q'.encode('utf-8'))
        except Exception:
            pass
        raise Exception(e)
    return True


class RoomMonitor:
    def __init__(self, room_url_keys, settings):
        self.room_url_keys = room_url_keys
        self.t = None
        self.nRooms = 0
        self.cRecords = []
        self.settings = settings
        self.interval = settings['program_settings']['interval']
        self._isQuit = False

    def quit(self):
        self._isQuit = True
        self.t.join()

    def start(self):
        self.t = threading.Thread(target=self.monitor)
        self.t.daemon = True
        self.t.start()
        return self.t

    def monitor(self):
        self.nRooms = len(self.room_url_keys)
        self.vRecords = [None] * self.nRooms
        while True:
            for i in range(self.nRooms):
                if self.vRecords[i] is not None:
                    if self.vRecords[i].isRecording:
                        # logging.debug('already recording...')
                        continue
                    else:
                        self.vRecords[i] = None
                        logging.debug('{k}:delete recording...'
                                      .format(k=self.room_url_keys[i]))
                if self.vRecords[i] is None:
                    room_url_key = self.room_url_keys[i]
                    try:
                        status = get_status_by_room_url_key(room_url_key)
                        if get_online_by_status(status):
                            vr = VideoRecorder(status, self.settings)
                            vr.start()
                            self.vRecords[i] = vr
                            continue
                    except Exception as e:
                        logging.error('{room_url_key}: {e}'.format(
                            room_url_key=room_url_key, e=e))
            time.sleep(1)
        # end while


class VideoRecorder:
    def __init__(self, status, settings):
        self.room_url_key = status['room_url_key']
        self.settings = settings
        self.isRecording = False
        self._thread_main = None
        self.status = status

    def start(self):
        self._thread_main = threading.Thread(target=self.record)
        self._thread_main.daemon = True
        self._thread_main.start()

    def record(self):
        self.isRecording = True
        logging.info('{room_url_key}: is on live, start recording video.'.format(
            room_url_key=self.room_url_key))
        try:
            if not os.path.isdir('videos'):
                os.makedirs('videos')
            download(self.status, output_dir='videos')
        except Exception:
            self.isRecording = False
            logging.error('{room_url_key}: record video finished.'.format(
                room_url_key=self.room_url_key))
