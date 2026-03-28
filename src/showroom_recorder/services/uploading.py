import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue

from biliup.plugins.bili_webup import BiliBili, Data
from webdav4.client import Client


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
