import json
import logging
import os
import random
import threading
import time
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from queue import Empty, Queue

import ffmpeg
import requests
from biliup.plugins.bili_webup import BiliBili, Data
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from webdav4.client import Client

ACFUN_TITLE_LIMIT = 50
ACFUN_DESCRIPTION_LIMIT = 1000
ACFUN_TAG_LIMIT = 6
ACFUN_CHANNEL_ID = 129
ACFUN_TAGS = ["showroom"]
ACFUN_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


def compact_text(text, max_len):
    text = " ".join(str(text or "").split())
    if not text or max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[: max_len - 3] + "..."


def format_bytes(num_bytes):
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{num_bytes}B"


class AcfunUploader:
    def __init__(self, cookie_file="ac_cookies.json"):
        self.cookie_file = cookie_file
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": ACFUN_USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Origin": "https://member.acfun.cn",
                "Referer": "https://member.acfun.cn/",
            }
        )
        self.login_status_url = "https://member.acfun.cn/video/api/getMyChannels"
        self.token_url = "https://member.acfun.cn/video/api/getKSCloudToken"
        self.fragment_url = "https://upload.kuaishouzt.com/api/upload/fragment"
        self.complete_url = "https://upload.kuaishouzt.com/api/upload/complete"
        self.finish_url = "https://member.acfun.cn/video/api/uploadFinish"
        self.create_video_url = "https://member.acfun.cn/video/api/createVideo"
        self.create_douga_url = "https://member.acfun.cn/video/api/createDouga"
        self.qiniu_url = "https://member.acfun.cn/common/api/getQiniuToken"
        self.cover_url = "https://member.acfun.cn/common/api/getUrlAfterUpload"

    def _load_netscape_cookies(self, content):
        cookie_count = 0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            self.session.cookies.set(
                name=parts[5],
                value=parts[6],
                domain=parts[0],
                path=parts[2] or "/",
                secure=parts[3].upper() == "TRUE",
            )
            cookie_count += 1
        return cookie_count

    def load_cookies(self):
        cookie_path = Path(self.cookie_file)
        if not cookie_path.is_file():
            logging.error("AcFun cookie file not found: %s", cookie_path)
            return False

        content = cookie_path.read_text(encoding="utf-8").strip()
        if not content:
            logging.error("AcFun cookie file is empty: %s", cookie_path)
            return False

        try:
            if content.startswith("[") or content.startswith("{"):
                cookie_items = json.loads(content)
                for cookie in cookie_items:
                    self.session.cookies.set(
                        cookie["name"],
                        cookie["value"],
                        domain=cookie.get("domain", ""),
                        path=cookie.get("path", "/"),
                    )
            else:
                loaded_count = self._load_netscape_cookies(content)
                if loaded_count <= 0:
                    logging.error("AcFun cookie file contains no valid Netscape cookies: %s", cookie_path)
                    return False
        except Exception as exc:
            logging.error("failed to load AcFun cookies from %s: %s", cookie_path, exc)
            return False

        return self.test_login()

    def test_login(self):
        try:
            response = self.session.get(self.login_status_url, timeout=15)
            if response.status_code != 200:
                logging.error("AcFun login check returned HTTP %s", response.status_code)
                return False

            try:
                payload = response.json()
            except ValueError:
                response_text = response.text or ""
                if "login" in response_text.lower() or "登录" in response_text:
                    logging.error("AcFun login check returned login page instead of JSON")
                    return False

                logging.info("AcFun login check returned non-JSON page, treating it as logged in")
                return True
        except Exception as exc:
            logging.error("failed to verify AcFun login: %s", exc)
            return False
        return payload.get("result") == 0

    @staticmethod
    def _build_retry_session():
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_token(self, filename, filesize):
        response = self.session.post(
            self.token_url,
            data={"fileName": filename, "size": filesize, "template": "1"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        task_id = payload.get("taskId")
        token = payload.get("token")
        upload_config = payload.get("uploadConfig", {})
        part_size = upload_config.get("partSize") if isinstance(upload_config, dict) else None
        if not task_id or not token or not part_size:
            raise RuntimeError(f"AcFun get token failed: {payload}")
        return int(task_id), token, int(part_size)

    def upload_chunk(self, block, fragment_id, upload_token):
        response = self._build_retry_session().post(
            self.fragment_url,
            params={"fragment_id": fragment_id, "upload_token": upload_token},
            data=block,
            headers={
                "Content-Type": "application/octet-stream",
                "User-Agent": ACFUN_USER_AGENT,
                "Accept": "*/*",
                "Connection": "keep-alive",
            },
            timeout=(30, 120),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("result") != 1:
            raise RuntimeError(f"AcFun fragment upload failed: {payload}")

    def complete_upload(self, fragment_count, upload_token):
        response = self._build_retry_session().post(
            self.complete_url,
            params={"fragment_count": fragment_count, "upload_token": upload_token},
            headers={
                "Content-Length": "0",
                "User-Agent": ACFUN_USER_AGENT,
                "Accept": "*/*",
                "Connection": "keep-alive",
            },
            timeout=(30, 60),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("result") != 1:
            raise RuntimeError(f"AcFun complete upload failed: {payload}")

    def upload_finish(self, task_id):
        response = self.session.post(self.finish_url, data={"taskId": task_id}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("result") != 0:
            raise RuntimeError(f"AcFun upload finish failed: {payload}")

    def create_video(self, video_key, filename):
        response = self.session.post(
            self.create_video_url,
            data={
                "videoKey": video_key,
                "fileName": filename,
                "vodType": "ksCloud",
            },
            headers={
                "Origin": "https://member.acfun.cn",
                "Referer": "https://member.acfun.cn/upload-video",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("result") != 0 or not payload.get("videoId"):
            raise RuntimeError(f"AcFun create video failed: {payload}")
        self.upload_finish(video_key)
        return int(payload["videoId"])

    def upload_cover(self, image_path):
        logging.info("AcFun cover upload started: %s", image_path)
        suffix = Path(image_path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        file_name = f"{random.getrandbits(64):016x}{'.jpg' if suffix == '.jpeg' else suffix}"
        response = self.session.post(self.qiniu_url, data={"fileName": file_name}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        token = payload.get("info", {}).get("token") if isinstance(payload, dict) else None
        if not token:
            raise RuntimeError(f"AcFun cover token failed: {payload}")

        with open(image_path, "rb") as file_obj:
            self.upload_chunk(file_obj.read(), 0, token)
        self.complete_upload(1, token)

        response = self.session.post(
            self.cover_url,
            data={"bizFlag": "web-douga-cover", "token": token},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        cover_url = payload.get("url") if isinstance(payload, dict) else None
        if not cover_url:
            raise RuntimeError(f"AcFun cover url failed: {payload}")
        logging.info("AcFun cover upload finished")
        return cover_url

    def create_douga(self, file_path, title, channel_id, cover_path, desc="", tags=None, original_url=""):
        tags = list(tags or [])
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        task_id, upload_token, part_size = self.get_token(file_name, file_size)
        fragment_count = ceil(file_size / part_size)
        logging.info(
            "AcFun video upload started: %s (%s, %s chunk%s)",
            file_name,
            format_bytes(file_size),
            fragment_count,
            "" if fragment_count == 1 else "s",
        )
        next_progress_marker = 10

        with open(file_path, "rb") as file_obj:
            for fragment_id in range(fragment_count):
                chunk_data = file_obj.read(part_size)
                if not chunk_data:
                    break
                self.upload_chunk(chunk_data, fragment_id, upload_token)
                progress = int(((fragment_id + 1) / fragment_count) * 100)
                if progress >= next_progress_marker or fragment_id + 1 == fragment_count:
                    logging.info(
                        "AcFun video upload progress: %s%% (%s/%s)",
                        progress,
                        fragment_id + 1,
                        fragment_count,
                    )
                    while progress >= next_progress_marker:
                        next_progress_marker += 10

        logging.info("AcFun video upload finishing on server")
        self.complete_upload(fragment_count, upload_token)
        video_id = self.create_video(task_id, file_name)
        cover_url = self.upload_cover(cover_path)
        logging.info("AcFun submit request started")
        payload = {
            "title": title,
            "description": desc,
            "tagNames": json.dumps(tags, ensure_ascii=False),
            "creationType": 1 if original_url else 3,
            "channelId": int(channel_id),
            "coverUrl": cover_url,
            "videoInfos": json.dumps([{"videoId": video_id, "title": title}], ensure_ascii=False),
            "isJoinUpCollege": "0",
            "isSyncKs": "0",
            "originalDeclare": "0" if original_url else "1",
        }
        if original_url:
            payload["originalLinkUrl"] = original_url

        response = self.session.post(
            self.create_douga_url,
            data=payload,
            headers={
                "Origin": "https://member.acfun.cn",
                "Referer": "https://member.acfun.cn/upload-video",
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("result") == 0 and "dougaId" in result:
            logging.info("AcFun submit succeeded: ac%s", result["dougaId"])
            return True, {"ac_number": result["dougaId"], "title": title, "cover_url": cover_url}

        error_msg = result.get("error_msg") or result.get("msg") or result.get("err_msg") or result
        return False, error_msg

    def upload_video(self, video_file_path, cover_file_path, title, description, tags, channel_id, original_url=""):
        if not self.load_cookies():
            return False, "AcFun login failed, please check your cookie file"

        if not os.path.exists(video_file_path):
            return False, f"video file not found: {video_file_path}"
        if not os.path.exists(cover_file_path):
            return False, f"cover file not found: {cover_file_path}"

        safe_title = compact_text(title, ACFUN_TITLE_LIMIT)
        safe_desc = compact_text(description, ACFUN_DESCRIPTION_LIMIT)
        safe_tags = [compact_text(tag, 20) for tag in list(tags or []) if compact_text(tag, 20)][:ACFUN_TAG_LIMIT]
        return self.create_douga(
            file_path=video_file_path,
            title=safe_title,
            channel_id=channel_id,
            cover_path=cover_file_path,
            desc=safe_desc,
            tags=safe_tags,
            original_url=original_url,
        )


class UploadTask:
    def __init__(self, max_attempts=3, expected_targets=None):
        self.max_attempts = max(1, int(max_attempts))
        self.attempt_count = 0
        self.status = "pending"
        self.last_error = ""
        self.expected_targets = tuple(sorted(set(expected_targets or [])))

    def metadata(self):
        return {}

    def describe(self):
        details = ", ".join(f"{key}={value}" for key, value in self.metadata().items() if value != "")
        return f"{self.__class__.__name__}({details})"

    def run(self):
        self.attempt_count += 1
        self.status = "running"
        try:
            self.upload()
        except Exception as exc:
            self.status = "failed"
            self.last_error = str(exc)
            raise

        self.status = "success"
        self.last_error = ""


class UploaderBili(UploadTask):
    def __init__(
        self,
        file_path,
        room_url_key,
        room_name,
        time_str,
        lines="AUTO",
        max_attempts=3,
        expected_targets=None,
    ):
        super().__init__(max_attempts=max_attempts, expected_targets=expected_targets)
        self.file_path = file_path
        self.room_url_key = room_url_key
        self.room_name = room_name
        self.time_str = time_str
        self.lines = lines

    def metadata(self):
        return {
            "target": "bilibili",
            "file_path": self.file_path,
            "room_url_key": self.room_url_key,
            "room_name": self.room_name,
            "time_str": self.time_str,
            "lines": self.lines,
        }

    def display_time_str(self):
        return self.time_str.replace("_", " ")

    def upload(self):
        logging.info("upload by biliup.")
        video = Data()
        video.title = f"{self.room_name} showroom {self.display_time_str()}"
        video.desc = ""
        video.source = f"https://www.showroom-live.com/{self.room_url_key}"
        video.tid = 137
        video.set_tag(["showroom"])
        video.copyright = 2
        try:
            with BiliBili(video) as bili:
                bili.login(persistence_path="", user_cookie="cookies.json")
                video_part = bili.upload_file(self.file_path, lines=self.lines, tasks=32)
                video.append(video_part)
                video.delay_time(0)
                bili.submit(submit_api="web")
        except Exception as exc:
            logging.error("bilibili upload error: %s", exc)
            raise RuntimeError("bilibili upload error") from exc


class UploaderAcfun(UploadTask):
    def __init__(
        self,
        file_path,
        room_url_key,
        room_name,
        time_str,
        cookie_file="ac_cookies.json",
        max_attempts=3,
        expected_targets=None,
    ):
        super().__init__(max_attempts=max_attempts, expected_targets=expected_targets)
        self.file_path = file_path
        self.room_url_key = room_url_key
        self.room_name = room_name
        self.time_str = time_str
        self.cookie_file = cookie_file
        self.channel_id = str(ACFUN_CHANNEL_ID)
        self.tags = list(ACFUN_TAGS)

    def metadata(self):
        return {
            "target": "acfun",
            "file_path": self.file_path,
            "room_url_key": self.room_url_key,
            "room_name": self.room_name,
            "time_str": self.time_str,
            "cookie_file": self.cookie_file,
            "channel_id": self.channel_id,
            "tags": self.tags,
        }

    def display_time_str(self):
        return self.time_str.replace("_", " ")

    def _build_cover_path(self):
        return str(Path(self.file_path).with_suffix(".acfun-cover.jpg"))

    def _generate_cover(self):
        cover_path = self._build_cover_path()
        for seek_seconds in (5, 0):
            kwargs = {"ss": seek_seconds} if seek_seconds else {}
            try:
                (
                    ffmpeg.input(self.file_path, **kwargs)
                    .output(cover_path, vframes=1, **{"q:v": 2})
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
                    return cover_path
            except ffmpeg.Error as exc:
                logging.warning("failed to generate AcFun cover for %s: %s", self.file_path, exc)
        raise RuntimeError("failed to generate AcFun cover image")

    def upload(self):
        logging.info("upload by acfun.")
        cover_path = self._generate_cover()
        try:
            uploader = AcfunUploader(cookie_file=self.cookie_file)
            success, result = uploader.upload_video(
                video_file_path=self.file_path,
                cover_file_path=cover_path,
                title=f"{self.room_name} showroom {self.display_time_str()}",
                description="",
                tags=self.tags,
                channel_id=int(self.channel_id),
                original_url=f"https://www.showroom-live.com/{self.room_url_key}",
            )
            if not success:
                raise RuntimeError(str(result))
        except Exception as exc:
            logging.error("acfun upload error: %s", exc)
            raise RuntimeError(f"acfun upload error: {exc}") from exc
        finally:
            Path(cover_path).unlink(missing_ok=True)


class UploaderWebDav(UploadTask):
    def __init__(
        self,
        from_path,
        to_path,
        url,
        username="",
        password="",
        max_attempts=3,
        expected_targets=None,
    ):
        super().__init__(max_attempts=max_attempts, expected_targets=expected_targets)
        self.from_path = from_path
        self.to_path = to_path
        self.url = url
        self.username = username
        self.password = password
        self.delete_source_file = False

    def metadata(self):
        return {
            "target": "webdav",
            "from_path": self.from_path,
            "to_path": self.to_path,
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "delete_source_file": self.delete_source_file,
        }

    def enable_delete_source_file(self):
        self.delete_source_file = True

    def upload(self):
        logging.info("upload by webdav.")
        client = Client(base_url=self.url, auth=(self.username, self.password))
        try:
            client.upload_file(from_path=self.from_path, to_path=self.to_path)
        except Exception as exc:
            logging.error("webdav upload error: %s", exc)
            raise RuntimeError("webdav upload error") from exc

        if self.delete_source_file:
            os.remove(self.from_path)


class UploadTaskLog:
    def __init__(self, path="upload_failures.jsonl"):
        self.path = Path(path)
        self._lock = threading.Lock()

    @staticmethod
    def entry_key(entry):
        source_path = entry.get("file_path") or entry.get("from_path") or ""
        target = entry.get("target", "")
        return source_path, target

    def build_entry(self, uploader):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uploader": uploader.__class__.__name__,
            "status": uploader.status,
            "attempts": uploader.attempt_count,
            "max_attempts": uploader.max_attempts,
            "error": uploader.last_error,
            "expected_targets": list(uploader.expected_targets),
            **uploader.metadata(),
        }

    def record(self, uploader):
        self.upsert_entry(self.build_entry(uploader))

    def upsert_entry(self, entry):
        entries = self.read_entries()
        new_key = self.entry_key(entry)
        updated = False
        for index, existing in enumerate(entries):
            if self.entry_key(existing) == new_key:
                entries[index] = entry
                updated = True
                break
        if not updated:
            entries.append(entry)
        self.write_entries(entries)

    def remove_entry(self, uploader):
        self.remove_by_key(self.entry_key(self.build_entry(uploader)))

    def remove_by_key(self, entry_key):
        entries = [entry for entry in self.read_entries() if self.entry_key(entry) != entry_key]
        self.write_entries(entries)

    def prune(self, predicate):
        entries = [entry for entry in self.read_entries() if not predicate(entry)]
        self.write_entries(entries)

    def read_entries(self):
        if not self.path.exists():
            return []

        entries = []
        with self.path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def write_entries(self, entries):
        if not entries:
            self.path.unlink(missing_ok=True)
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("w", encoding="utf-8") as file_obj:
                for entry in entries:
                    json.dump(entry, file_obj, ensure_ascii=False)
                    file_obj.write("\n")

    def build_uploader(self, entry):
        uploader_type = entry.get("uploader")
        max_attempts = entry.get("max_attempts", 3)
        expected_targets = entry.get("expected_targets", [])

        if uploader_type == "UploaderBili":
            return UploaderBili(
                file_path=entry["file_path"],
                room_url_key=entry["room_url_key"],
                room_name=entry.get("room_name", entry["room_url_key"]),
                time_str=entry.get("time_str", ""),
                lines=entry.get("lines", "AUTO"),
                max_attempts=max_attempts,
                expected_targets=expected_targets,
            )

        if uploader_type == "UploaderAcfun":
            return UploaderAcfun(
                file_path=entry["file_path"],
                room_url_key=entry["room_url_key"],
                room_name=entry.get("room_name", entry["room_url_key"]),
                time_str=entry.get("time_str", ""),
                cookie_file=entry.get("cookie_file", "ac_cookies.json"),
                max_attempts=max_attempts,
                expected_targets=expected_targets,
            )

        if uploader_type == "UploaderWebDav":
            uploader = UploaderWebDav(
                from_path=entry["from_path"],
                to_path=entry["to_path"],
                url=entry["url"],
                username=entry.get("username", ""),
                password=entry.get("password", ""),
                max_attempts=max_attempts,
                expected_targets=expected_targets,
            )
            if entry.get("delete_source_file", False):
                uploader.enable_delete_source_file()
            return uploader

        return None

    def retry_all(self, target=None, file_path=None):
        entries = self.read_entries()
        if target:
            entries = [entry for entry in entries if entry.get("target") == target]
        if file_path:
            entries = [entry for entry in entries if (entry.get("file_path") or entry.get("from_path")) == file_path]
        if not entries:
            return {"total": 0, "retried": 0, "succeeded": 0, "remaining": 0, "skipped": 0}

        queue = UploaderQueue(failure_log_path=self.path)
        remaining_entries = []
        retried = 0
        succeeded = 0
        skipped = 0
        retried_keys = {self.entry_key(entry) for entry in entries}

        for entry in entries:
            uploader = self.build_uploader(entry)
            if uploader is None:
                skipped += 1
                remaining_entries.append(entry)
                logging.warning("skipping unsupported failure entry: %s", entry.get("uploader"))
                continue

            retried += 1
            success = queue._upload_with_retries(uploader, record_failure=False)
            if success:
                succeeded += 1
                continue

            remaining_entries.append(self.build_entry(uploader))

        untouched_entries = [entry for entry in self.read_entries() if self.entry_key(entry) not in retried_keys]
        self.write_entries(untouched_entries + remaining_entries)
        return {
            "total": len(entries),
            "retried": retried,
            "succeeded": succeeded,
            "remaining": len(remaining_entries),
            "skipped": skipped,
        }


class UploadFailureLog(UploadTaskLog):
    pass


class UploadSuccessLog(UploadTaskLog):
    pass


class UploaderQueue:
    def __init__(
        self,
        failure_log_path="upload_failures.jsonl",
        success_log_path="upload_successes.jsonl",
        cleanup_after_hours=0,
        cleanup_dir="videos",
    ):
        self.uploader_queue = Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self.failure_log = UploadFailureLog(failure_log_path)
        self.success_log = UploadSuccessLog(success_log_path)
        self.cleanup_after_hours = max(0, int(cleanup_after_hours))
        self.cleanup_dir = Path(cleanup_dir)
        self.success_count = 0
        self.failure_count = 0
        self.deleted_count = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self.run, name="uploader-queue", daemon=True)
        self._thread.start()

    def stop(self, timeout=None):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def put(self, uploader):
        self.uploader_queue.put(uploader)

    @staticmethod
    def _source_path_from_entry(entry):
        return entry.get("file_path") or entry.get("from_path") or ""

    @staticmethod
    def _target_from_entry(entry):
        return entry.get("target", "")

    @staticmethod
    def _expected_targets_from_entries(entries):
        expected_targets = set()
        for entry in entries:
            expected_targets.update(entry.get("expected_targets", []))
        return expected_targets

    def summary(self):
        return {
            "succeeded": self.success_count,
            "failed": self.failure_count,
            "deleted": self.deleted_count,
        }

    def _cleanup_uploaded_videos(self):
        if self.cleanup_after_hours <= 0 or not self.cleanup_dir.is_dir():
            return 0

        success_entries = self.success_log.read_entries()
        failure_entries = self.failure_log.read_entries()
        cutoff = time.time() - (self.cleanup_after_hours * 3600)
        deleted_count = 0

        success_by_path = {}
        for entry in success_entries:
            success_by_path.setdefault(self._source_path_from_entry(entry), []).append(entry)
        failure_by_path = {}
        for entry in failure_entries:
            failure_by_path.setdefault(self._source_path_from_entry(entry), []).append(entry)

        for file_path in self.cleanup_dir.glob("*.mp4"):
            normalized_path = str(file_path)
            path_success_entries = success_by_path.get(normalized_path, [])
            if not path_success_entries:
                continue
            if file_path.stat().st_mtime > cutoff:
                continue

            path_failure_entries = failure_by_path.get(normalized_path, [])
            if path_failure_entries:
                continue

            expected_targets = self._expected_targets_from_entries(path_success_entries)
            if not expected_targets:
                continue

            success_targets = {self._target_from_entry(entry) for entry in path_success_entries}
            if not expected_targets.issubset(success_targets):
                continue

            file_path.unlink(missing_ok=True)
            self.success_log.prune(lambda entry: self._source_path_from_entry(entry) == normalized_path)
            deleted_count += 1
            logging.info("deleted old uploaded video: %s", normalized_path)

        return deleted_count

    def _upload_with_retries(self, uploader, record_failure=True):
        while uploader.attempt_count < uploader.max_attempts:
            try:
                uploader.run()
            except Exception as exc:
                if uploader.attempt_count < uploader.max_attempts:
                    logging.warning(
                        "upload failed, retrying %s (%s/%s): %s",
                        uploader.describe(),
                        uploader.attempt_count,
                        uploader.max_attempts,
                        exc,
                    )
                    continue

                logging.error(
                    "upload failed permanently after %s attempts: %s",
                    uploader.attempt_count,
                    uploader.describe(),
                )
                self.failure_count += 1
                if record_failure:
                    self.success_log.remove_entry(uploader)
                    self.failure_log.record(uploader)
                    logging.error("failure details written to %s", self.failure_log.path)
                return False

            logging.info(
                "upload succeeded after %s attempt(s): %s",
                uploader.attempt_count,
                uploader.describe(),
            )
            self.success_count += 1
            self.failure_log.remove_entry(uploader)
            self.success_log.record(uploader)
            deleted_count = self._cleanup_uploaded_videos()
            if deleted_count:
                self.deleted_count += deleted_count
                logging.info("deleted %s old uploaded video(s).", deleted_count)
            return True

        return False

    def run(self):
        while not self._stop_event.is_set() or not self.uploader_queue.empty():
            try:
                uploader = self.uploader_queue.get(timeout=1)
            except Empty:
                continue

            try:
                self._upload_with_retries(uploader)
            finally:
                self.uploader_queue.task_done()
