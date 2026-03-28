#!/usr/bin/env python3

import logging
import threading

from ..services.recording import Recorder
from ..services.showroom_api import ShowroomApiClient
from ..services.uploading import UploaderBili, UploaderQueue, UploaderWebDav


class RecorderManager:
    def __init__(self, config, api_client=None, recorder_cls=Recorder, uploader_queue=None):
        self.room_url_key_list = list(config.rooms)
        self.recorders = {room_url_key: None for room_url_key in self.room_url_key_list}
        self.room_id_map = {}
        self.recorder_thread = None
        self._stop_event = threading.Event()
        self.config = config
        self.api_client = api_client or ShowroomApiClient()
        self.recorder_cls = recorder_cls
        self.uploader_queue = uploader_queue or UploaderQueue()
        self.biliup_set = set(config.biliup.rooms)

    def start(self):
        if self.recorder_thread and self.recorder_thread.is_alive():
            return self.recorder_thread

        self.recorder_thread = threading.Thread(
            target=self.manager,
            name="recorder-manager",
            daemon=True,
        )
        self.recorder_thread.start()
        return self.recorder_thread

    def quit(self):
        self._stop_event.set()
        for recorder in self.recorders.values():
            if recorder is not None:
                recorder.quit()

        if self.recorder_thread:
            self.recorder_thread.join(timeout=self.config.interval + 5)

        for recorder in self.recorders.values():
            if recorder is not None:
                recorder.join(timeout=5)

        self.uploader_queue.stop(timeout=5)

    def _get_room_id(self, room_url_key):
        if room_url_key in self.room_id_map:
            return self.room_id_map[room_url_key]

        status = self.api_client.get_status_by_room_url_key(room_url_key)
        room_id = self.api_client.get_roomid_by_status(status)
        self.room_id_map[room_url_key] = room_id
        return room_id

    def manager(self):
        self.uploader_queue.start()
        while not self._stop_event.is_set():
            for room_url_key in self.room_url_key_list:
                if self._stop_event.is_set():
                    break

                recorder = self.recorders[room_url_key]
                if recorder is not None and recorder.is_recording:
                    continue
                if recorder is not None and not recorder.is_recording:
                    self.recorders[room_url_key] = None
                    logging.info("%s: delete recorder.", room_url_key)

                try:
                    room_id = self._get_room_id(room_url_key)
                    live_info = self.api_client.get_liveinfo_by_roomid(room_id)
                except Exception as exc:
                    logging.error("%s: failed to fetch live info: %s", room_url_key, exc)
                    continue

                if not self.api_client.get_online_by_liveinfo(live_info):
                    continue

                try:
                    recorder = self.recorder_cls(
                        room_url_key,
                        live_info,
                        self.uploader_queue,
                        self.config,
                        api_client=self.api_client,
                    )
                    if room_url_key in self.biliup_set:
                        recorder.enable_uploader_bili()
                    recorder.start()
                    self.recorders[room_url_key] = recorder
                except Exception as exc:
                    logging.error("%s: %s", room_url_key, exc)

            self._stop_event.wait(self.config.interval)


_DEFAULT_API_CLIENT = ShowroomApiClient()


def get_status_by_room_url_key(room_url_key):
    return _DEFAULT_API_CLIENT.get_status_by_room_url_key(room_url_key)


def showroom_get_roomid_by_room_url_key(room_url_key):
    return _DEFAULT_API_CLIENT.showroom_get_roomid_by_room_url_key(room_url_key)


def get_online_by_liveinfo(liveinfo):
    return _DEFAULT_API_CLIENT.get_online_by_liveinfo(liveinfo)


def get_liveinfo_by_roomid(room_id):
    return _DEFAULT_API_CLIENT.get_liveinfo_by_roomid(room_id)


def get_room_url_key_by_status(status):
    return _DEFAULT_API_CLIENT.get_room_url_key_by_status(status)


def get_roomid_by_status(status):
    return _DEFAULT_API_CLIENT.get_roomid_by_status(status)


def get_online_by_status(status):
    return _DEFAULT_API_CLIENT.get_online_by_status(status)


def get_room_name_by_status(status):
    return _DEFAULT_API_CLIENT.get_room_name_by_status(status)


def get_start_time_by_status(status):
    return _DEFAULT_API_CLIENT.get_start_time_by_status(status)


def get_time_now():
    return _DEFAULT_API_CLIENT.get_time_now()


def get_stream_url_by_roomid(room_id):
    return _DEFAULT_API_CLIENT.get_stream_url_by_roomid(room_id)


def get_max_bandwidth_stream(m3u8_url):
    return _DEFAULT_API_CLIENT.get_max_bandwidth_stream(m3u8_url)


RecroderManager = RecorderManager

__all__ = [
    "Recorder",
    "RecorderManager",
    "RecroderManager",
    "UploaderBili",
    "UploaderQueue",
    "UploaderWebDav",
    "get_status_by_room_url_key",
    "showroom_get_roomid_by_room_url_key",
    "get_online_by_liveinfo",
    "get_liveinfo_by_roomid",
    "get_room_url_key_by_status",
    "get_roomid_by_status",
    "get_online_by_status",
    "get_room_name_by_status",
    "get_start_time_by_status",
    "get_time_now",
    "get_stream_url_by_roomid",
    "get_max_bandwidth_stream",
]
