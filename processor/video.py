#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
import json
import re

from you_get.common import match1, get_content, url_info, print_info, download_url_ffmpeg


from utils import config

os.chdir(os.path.dirname(__file__))


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


def showroom_download_by_room_id(room_id, output_dir='.', merge=False, info_only=False, **kwargs):
    '''Source: Android mobile'''
    while True:
        timestamp = str(int(time.time() * 1000))
        api_endpoint = 'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&_={timestamp}'.format(
            room_id=room_id, timestamp=timestamp)
        html = get_content(api_endpoint)
        html = json.loads(html)
        if len(html) >= 1:
            break
        logging.w('The live show is currently offline.')
        sleep(1)

    stream_url = [i['url'] for i in html['streaming_url_list']
                  if i['is_default'] and i['type'] == 'hls'][0]

    assert stream_url

    # title
    # title = ''
    # profile_api = 'https://www.showroom-live.com/api/room/profile?room_id={room_id}'.format(room_id = room_id)
    # html = json.loads(get_content(profile_api))
    # try:
    #     title = html['main_name']
    # except KeyError:
    #     title = 'Showroom_{room_id}'.format(room_id = room_id)
    
    title = 'Showroom_{room_id}_{time}'.format(
        room_id=room_id, time=time.strftime("%Y_%m_%d_%X_%H_%M_%S", time.localtime()))
    
    logging.info(title)

    if info_only:
        type_, ext, size = url_info(stream_url)
        print_info("showroom", title, type_, size)
    if not info_only:
        download_url_ffmpeg(url=stream_url, title=title,
                            # params={'-v':  'quiet'},
                            ext='mp4', output_dir=output_dir)


# ----------------------------------------------------------------------
def showroom_download(url, output_dir='.', merge=False, info_only=False, **kwargs):
    """"""
    if re.match(r'(\w+)://www.showroom-live.com/([-\w]+)', url):
        room_url_key = match1(url, r'\w+://www.showroom-live.com/([-\w]+)')
        room_id = showroom_get_roomid_by_room_url_key(room_url_key)
        showroom_download_by_room_id(room_id, output_dir, merge,
                                     info_only)


def get_online(url):
    room_url_key = match1(url, r'\w+://www.showroom-live.com/([-\w]+)')
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

        count = self.interval
        logging.debug('start record video.')
        while True:

            for i in range(self.nRooms):

                if self.vRecords[i] is not None:
                    if self.vRecords[i].isRecording:
                        # logging.debug('already recording...')
                        continue
                    else:
                        self.vRecords[i] = None

                if self.vRecords[i] is None:
                    room_url_key = self.room_url_keys[i]
                    try:
                        if get_online("https://www.showroom-live.com/"+room_url_key):
                            vr = VideoRecorder(room_url_key, self.settings)
                            vr.start()
                            self.vRecords[i] = vr
                            continue
                    except BaseException as e:
                        logging.error(e)

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
        try:
            url = "https://www.showroom-live.com/" + self.room_url_key

            logging.info(self.room_url_key +
                         "\'s live show is currently online.")

            if not os.path.isdir('videos'):
                os.makedirs('videos')

            showroom_download(url, output_dir='videos')

        except BaseException as e:
            logging.error(e)
            self.isRecording = False
