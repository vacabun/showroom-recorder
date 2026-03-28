#!/usr/bin/env python3

import logging
import os
import threading

import ffmpeg

from .showroom_api import ShowroomApiClient
from .uploading import UploaderBili, UploaderWebDav


class Recorder:
    def __init__(self, room_url_key, live_info, uploader_queue, config, api_client=None):
        self.room_url_key = room_url_key
        self.live_info = live_info
        self.room_name = live_info["room_name"]
        self.room_id = live_info["room_id"]
        self.uploader_queue = uploader_queue
        self.config = config
        self.api_client = api_client or ShowroomApiClient()
        self.is_recording = False
        self._thread = None
        self._stop_event = threading.Event()
        self.ffmpeg_proc = None
        self.output = ""
        self.upload_to_bilibili = False
        self.time_str = ""

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(
            target=self.record,
            name=f"recorder-{self.room_url_key}",
            daemon=True,
        )
        self._thread.start()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout=timeout)

    def quit(self):
        self._stop_event.set()
        if self.ffmpeg_proc and self.ffmpeg_proc.poll() is None:
            try:
                self.ffmpeg_proc.stdin.write(b"q")
                self.ffmpeg_proc.stdin.flush()
            except Exception:
                pass

    def enable_uploader_bili(self):
        self.upload_to_bilibili = True

    def record(self):
        self.is_recording = True
        logging.info("%s: is live, start recording video.", self.room_url_key)
        try:
            os.makedirs("videos", exist_ok=True)
            self.download(output_dir="videos")
        except Exception as exc:
            if not self._stop_event.is_set():
                logging.error("%s: record video error: %s", self.room_url_key, exc)
        finally:
            self.is_recording = False
            self._download_finish()
            logging.info("%s: record video finished.", self.room_url_key)

    def download(self, output_dir="."):
        stream_url = self.api_client.get_stream_url_by_roomid(self.room_id)
        logging.info("%s: stream url is %s.", self.room_url_key, stream_url)

        if self.config.best_quality:
            _, _, best_stream_url = self.api_client.get_max_bandwidth_stream(stream_url)
            stream_url = best_stream_url or stream_url
            logging.info("%s: max bandwidth stream url is %s.", self.room_url_key, stream_url)

        self.time_str = self.api_client.get_time_now().strftime("%Y%m%d_%H%M%S")
        self.output = os.path.join(output_dir, f"{self.room_url_key}_{self.time_str}.mp4")

        try:
            self.ffmpeg_proc = (
                ffmpeg.input(stream_url, rw_timeout=str(30 * 1000 * 1000))
                .output(
                    self.output,
                    **{
                        "c:v": "copy",
                        "c:a": "copy",
                        "bsf:a": "aac_adtstoasc",
                        "loglevel": "error",
                    },
                )
                .overwrite_output()
                .run_async(pipe_stdin=True)
            )
            return_code = self.ffmpeg_proc.wait()
            if return_code != 0 and not self._stop_event.is_set():
                raise RuntimeError(f"ffmpeg exited with code {return_code}")
        except Exception:
            self.quit()
            raise

    def _download_finish(self):
        if not self.output or not os.path.exists(self.output):
            return

        logging.info("%s: video saved to %s.", self.room_url_key, self.output)
        expected_targets = []
        if self.upload_to_bilibili:
            expected_targets.append("bilibili")
        if self.config.webdav.upload:
            expected_targets.append("webdav")

        if self.upload_to_bilibili:
            self.uploader_queue.put(
                UploaderBili(
                    file_path=self.output,
                    room_url_key=self.room_url_key,
                    room_name=self.room_name,
                    time_str=self.time_str,
                    lines=self.config.biliup.line,
                    expected_targets=expected_targets,
                )
            )

        if self.config.webdav.upload:
            uploader_webdav = UploaderWebDav(
                from_path=self.output,
                to_path=self.output,
                url=self.config.webdav.url,
                username=self.config.webdav.username,
                password=self.config.webdav.password,
                expected_targets=expected_targets,
            )
            if self.config.webdav.delete_source_file:
                uploader_webdav.enable_delete_source_file()
            self.uploader_queue.put(uploader_webdav)
