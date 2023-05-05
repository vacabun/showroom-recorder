#!/usr/bin/env python3
import os
import time
import logging
import threading
import ffmpeg
import streamlink

from utils import config

os.chdir(os.path.dirname(__file__))


def showroom_download(room_url_key, output_dir='.'):

    url = 'https://www.showroom-live.com/r/{room_url_key}'.format(
        room_url_key=room_url_key)
    stream_quality = "best"
    streams = streamlink.streams(url)
    available_qualities = streams.keys()
    if stream_quality not in available_qualities:
        raise BaseException('stream quality {stream_quality} is not available.'.format(
            stream_quality=stream_quality))

    stream_url = streams[stream_quality].url

    title = '{room_url_key}_{time}'.format(
        room_url_key=room_url_key, time=time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime()))

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
        stdout, stderr = proc.communicate()


    except KeyboardInterrupt:
        try:
            proc.stdin.write('q'.encode('utf-8'))
        except:
            pass
    except Exception as e:
        # logging.error(e)
        try:
            proc.stdin.write('q'.encode('utf-8'))
        except:
            pass
        raise BaseException('ffmpeg finish.')

    return True


def get_online(room_url_key):
    url = 'https://www.showroom-live.com/r/{room_url_key}'.format(
        room_url_key=room_url_key)
    streams = streamlink.streams(url)
    if not streams:
        return False
    else:
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
                        logging.debug('delete recording...')
                if self.vRecords[i] is None:
                    room_url_key = self.room_url_keys[i]
                    try:
                        if get_online(room_url_key):
                            vr = VideoRecorder(room_url_key, self.settings)
                            vr.start()
                            self.vRecords[i] = vr
                            continue
                    except BaseException as e:
                        # logging.error(e)
                        pass

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
        except BaseException as e:
            # logging.error(e)
            self.isRecording = False
            logging.info('{room_url_key}: record video finished.'.format(
                room_url_key=self.room_url_key))
