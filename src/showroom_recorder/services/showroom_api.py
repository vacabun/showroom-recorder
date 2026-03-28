import datetime
import logging
import re
import time

import m3u8
import pytz
import requests

FAKE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,ja;q=0.6",
    "Accept-Charset": "UTF-8,*;q=0.5",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
}
REQUEST_TIMEOUT = 20
SHOWROOM_TZ = pytz.timezone("Asia/Tokyo")


class ShowroomApiClient:
    def __init__(self, timeout=REQUEST_TIMEOUT, headers=None):
        self.timeout = timeout
        self.headers = headers or FAKE_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_status_by_room_url_key(self, room_url_key):
        return self._get_json(
            "https://www.showroom-live.com/api/room/status",
            params={"room_url_key": room_url_key},
        )

    def get_liveinfo_by_roomid(self, room_id):
        return self._get_json(
            "https://www.showroom-live.com/api/live/live_info",
            params={"room_id": room_id},
        )

    def get_stream_url_by_roomid(self, room_id):
        response = self._get_json(
            "https://www.showroom-live.com/api/live/streaming_url",
            params={
                "room_id": room_id,
                "_": str(int(time.time() * 1000)),
                "abr_available": 1,
            },
        )

        stream_url_list = response.get("streaming_url_list") or []
        if not stream_url_list:
            raise RuntimeError("get stream url error: no streaming url found")

        stream_url = stream_url_list[0]["url"]
        for streaming_url in stream_url_list:
            if streaming_url.get("type") == "hls_all":
                stream_url = streaming_url["url"]
                break
        return stream_url

    def showroom_get_roomid_by_room_url_key(self, room_url_key):
        try:
            response_text = self._get_text(f"https://www.showroom-live.com/r/{room_url_key}")
        except requests.RequestException as exc:
            raise RuntimeError("get room_id error") from exc

        match = re.search(r'href="/room/profile\?room_id\=(\d+)"', response_text)
        if match:
            return match.group(1)
        raise RuntimeError("get room_id error")

    @staticmethod
    def get_online_by_liveinfo(liveinfo):
        live_status = liveinfo["live_status"]
        if live_status == 2:
            return True
        if live_status == 1:
            return False

        logging.error("Unknown live status: %s", live_status)
        return False

    @staticmethod
    def get_room_url_key_by_status(status):
        return status["room_url_key"]

    @staticmethod
    def get_roomid_by_status(status):
        return status["room_id"]

    @staticmethod
    def get_online_by_status(status):
        return status["is_live"]

    @staticmethod
    def get_room_name_by_status(status):
        return status["room_name"]

    @staticmethod
    def get_start_time_by_status(status):
        return datetime.datetime.fromtimestamp(status["started_at"], tz=SHOWROOM_TZ)

    @staticmethod
    def get_time_now():
        return datetime.datetime.now(tz=SHOWROOM_TZ)

    @staticmethod
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

            if stream_dict:
                max_bandwidth = max(stream_dict)
                best_stream_url = stream_dict[max_bandwidth]
        except Exception as exc:
            logging.error("Analyze m3u8 error: %s", exc)

        return stream_dict, max_bandwidth, best_stream_url

    def _get_json(self, url, params=None):
        response = self.session.get(url=url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _get_text(self, url, params=None):
        response = self.session.get(url=url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text
