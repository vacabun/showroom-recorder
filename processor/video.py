#!/usr/bin/env python3
import os
import time
import logging
import threading
import ffmpeg
import streamlink
import json
from you_get.common import get_content, match1

use_streamlink = True


def showroom_download(room_url_key, output_dir='.'):
    url = 'https://www.showroom-live.com/{room_url_key}'.format(
        room_url_key=room_url_key)
    if use_streamlink:
        stream_quality = "best"
        streams = streamlink.streams(url)
        available_qualities = streams.keys()
        if stream_quality not in available_qualities:
            raise Exception('stream quality {q} is not available.'.format(
                q=stream_quality))

        stream_url = streams[stream_quality].url
    else:
        room_id = showroom_get_roomid_by_room_url_key(room_url_key)
        timestamp = str(int(time.time() * 1000))
        api_header = 'https://www.showroom-live.com/api/live/streaming_url'
        api_endpoint = api_header + '?room_id={room_id}&_={timestamp}'.format(
            room_id=room_id, timestamp=timestamp)
        html = get_content(api_endpoint)
        html = json.loads(html)
        if len(html) == 0:
            raise BaseException('The live show is currently offline.')
        stream_url = [i['url'] for i in html['streaming_url_list']
                      if i['is_default'] and i['type'] == 'hls'][0]

    title = '{room_url_key}_{time}'.format(
        room_url_key=room_url_key,
        time=time.strftime("%Y%m%d_%H%M%S", time.localtime()))
    output = output_dir + '/' + title + '.' + 'mp4'

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


def showroom_get_roomid_by_room_url_key(room_url_key):
    """str->str"""
    fake_headers_mobile = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36'
    }
    webpage_url = 'https://www.showroom-live.com/' + room_url_key
    html = get_content(webpage_url, headers=fake_headers_mobile)
    roomid = match1(html, r'room\?room_id\=(\d+)')
    assert roomid
    return roomid


def get_online(room_url_key):
    url = 'https://www.showroom-live.com/{room_url_key}'.format(
        room_url_key=room_url_key)
    if use_streamlink:
        streams = streamlink.streams(url)
        if not streams:
            return False
        else:
            return True
    else:
        room_id = showroom_get_roomid_by_room_url_key(room_url_key)
        timestamp = str(int(time.time() * 1000))
        api_endpoint = 'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&_={timestamp}'.format(
            room_id=room_id, timestamp=timestamp)
        html = get_content(api_endpoint)
        html = json.loads(html)
        if len(html) >= 1:
            return True
        else:
            return False


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

        logging.debug('start record video.')
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
                        if get_online(room_url_key):
                            vr = VideoRecorder(room_url_key, self.settings)
                            vr.start()
                            self.vRecords[i] = vr
                            continue
                    except Exception as e:
                        logging.debug('{room_url_key}: {e}'.format(
                            room_url_key=room_url_key, e=e))
            time.sleep(1)
        # end while


class VideoRecorder:
    def __init__(self, room_url_key, settings):
        self.room_url_key = room_url_key
        self.settings = settings
        self.isRecording = False
        self._thread_main = None

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
            showroom_download(self.room_url_key, output_dir='videos')
        except Exception:
            self.isRecording = False
            logging.info('{room_url_key}: record video finished.'.format(
                room_url_key=self.room_url_key))

