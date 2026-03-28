import json
import os

from showroom_recorder.processor import video
from showroom_recorder.services.showroom_api import ShowroomApiClient
from showroom_recorder.services.uploading import UploadFailureLog, UploadSuccessLog, UploadTask, UploaderQueue
from showroom_recorder.utils.load_config import Config


class DummyQueue:
    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


def test_recorder_download_finish_enqueues_uploaders(tmp_path):
    config = Config()
    config.webdav.upload = True
    config.webdav.url = "https://example.com/dav"
    config.webdav.username = "user"
    config.webdav.password = "pass"
    config.webdav.delete_source_file = True
    config.biliup.line = "AUTO"

    queue = DummyQueue()
    live_info = {"room_name": "Test Room", "room_id": 123}
    recorder = video.Recorder("test_room", live_info, queue, config)
    recorder.enable_uploader_bili()
    recorder.output = str(tmp_path / "video.mp4")
    recorder.time_str = "20260327_120000"
    tmp_path.joinpath("video.mp4").write_bytes(b"test")

    recorder._download_finish()

    assert len(queue.items) == 2
    assert isinstance(queue.items[0], video.UploaderBili)
    assert isinstance(queue.items[1], video.UploaderWebDav)
    assert queue.items[1].delete_source_file is True
    assert queue.items[0].expected_targets == ("bilibili", "webdav")
    assert queue.items[1].expected_targets == ("bilibili", "webdav")


class FakeApiClient:
    def __init__(self):
        self.calls = []

    def get_status_by_room_url_key(self, room_url_key):
        self.calls.append(room_url_key)
        return {"room_id": 42}

    @staticmethod
    def get_roomid_by_status(status):
        return status["room_id"]


def test_recorder_manager_caches_room_id():
    config = Config(rooms=["room_a"])
    api_client = FakeApiClient()
    manager = video.RecorderManager(config, api_client=api_client)

    assert manager._get_room_id("room_a") == 42
    assert manager._get_room_id("room_a") == 42
    assert api_client.calls == ["room_a"]


def test_showroom_api_get_online_by_liveinfo():
    assert ShowroomApiClient.get_online_by_liveinfo({"live_status": 2}) is True
    assert ShowroomApiClient.get_online_by_liveinfo({"live_status": 1}) is False


class FlakyUploader(UploadTask):
    def __init__(self, failures_before_success, max_attempts=3):
        super().__init__(max_attempts=max_attempts)
        self.failures_before_success = failures_before_success
        self.calls = 0

    def metadata(self):
        return {"target": "test", "file_path": "videos/test.mp4"}

    def upload(self):
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError(f"boom-{self.calls}")


def test_uploader_queue_retries_until_success(tmp_path):
    queue = UploaderQueue(failure_log_path=tmp_path / "upload_failures.jsonl")
    uploader = FlakyUploader(failures_before_success=2, max_attempts=3)

    queue._upload_with_retries(uploader)

    assert uploader.calls == 3
    assert uploader.status == "success"
    assert uploader.attempt_count == 3
    assert not (tmp_path / "upload_failures.jsonl").exists()


def test_bilibili_title_uses_spaces_in_timestamp():
    uploader = video.UploaderBili(
        file_path="videos/test.mp4",
        room_url_key="room",
        room_name="Room",
        time_str="20260328_120000",
    )

    assert uploader.display_time_str() == "20260328 120000"


def test_uploader_queue_records_permanent_failure(tmp_path):
    failure_log = tmp_path / "upload_failures.jsonl"
    queue = UploaderQueue(failure_log_path=failure_log)
    uploader = FlakyUploader(failures_before_success=3, max_attempts=2)

    queue._upload_with_retries(uploader)

    assert uploader.calls == 2
    assert uploader.status == "failed"
    assert uploader.attempt_count == 2

    entries = failure_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(entries) == 1

    entry = json.loads(entries[0])
    assert entry["uploader"] == "FlakyUploader"
    assert entry["status"] == "failed"
    assert entry["attempts"] == 2
    assert entry["max_attempts"] == 2
    assert entry["error"] == "boom-2"


def test_failure_log_retry_all_removes_successful_entries(tmp_path):
    class RetryableUploader(FlakyUploader):
        def __init__(self, max_attempts=3):
            super().__init__(failures_before_success=0, max_attempts=max_attempts)

    failure_log = UploadFailureLog(tmp_path / "upload_failures.jsonl")
    uploader = RetryableUploader(max_attempts=2)
    failure_log.write_entries([failure_log.build_entry(uploader)])

    original_build_uploader = failure_log.build_uploader

    def fake_build_uploader(entry):
        if entry["uploader"] == "RetryableUploader":
            return RetryableUploader(max_attempts=entry["max_attempts"])
        return original_build_uploader(entry)

    failure_log.build_uploader = fake_build_uploader

    result = failure_log.retry_all()

    assert result == {"total": 1, "retried": 1, "succeeded": 1, "remaining": 0, "skipped": 0}
    assert not (tmp_path / "upload_failures.jsonl").exists()


def test_failure_log_retry_all_keeps_failed_entries(tmp_path):
    class AlwaysFailUploader(FlakyUploader):
        def __init__(self, max_attempts=2):
            super().__init__(failures_before_success=10, max_attempts=max_attempts)

    failure_log = UploadFailureLog(tmp_path / "upload_failures.jsonl")
    uploader = AlwaysFailUploader(max_attempts=2)
    failure_log.write_entries([failure_log.build_entry(uploader)])

    original_build_uploader = failure_log.build_uploader

    def fake_build_uploader(entry):
        if entry["uploader"] == "AlwaysFailUploader":
            return AlwaysFailUploader(max_attempts=entry["max_attempts"])
        return original_build_uploader(entry)

    failure_log.build_uploader = fake_build_uploader

    result = failure_log.retry_all()

    assert result == {"total": 1, "retried": 1, "succeeded": 0, "remaining": 1, "skipped": 0}
    entries = failure_log.read_entries()
    assert len(entries) == 1
    assert entries[0]["uploader"] == "AlwaysFailUploader"
    assert entries[0]["attempts"] == 2
    assert entries[0]["status"] == "failed"


def test_upload_logs_deduplicate_same_file_and_target(tmp_path):
    failure_log = UploadFailureLog(tmp_path / "upload_failures.jsonl")
    success_log = UploadSuccessLog(tmp_path / "upload_successes.jsonl")
    uploader = video.UploaderBili(
        file_path="videos/test.mp4",
        room_url_key="room",
        room_name="Room",
        time_str="20260328_120000",
        expected_targets=["bilibili"],
    )

    uploader.status = "failed"
    uploader.attempt_count = 1
    uploader.last_error = "boom-1"
    failure_log.record(uploader)
    uploader.attempt_count = 2
    uploader.last_error = "boom-2"
    failure_log.record(uploader)

    uploader.status = "success"
    uploader.last_error = ""
    success_log.record(uploader)
    success_log.record(uploader)

    failure_entries = failure_log.read_entries()
    success_entries = success_log.read_entries()
    assert len(failure_entries) == 1
    assert failure_entries[0]["attempts"] == 2
    assert len(success_entries) == 1


def test_retry_all_supports_target_and_file_filters(tmp_path):
    failure_log = UploadFailureLog(tmp_path / "upload_failures.jsonl")
    failure_log.write_entries(
        [
            {
                "uploader": "UploaderBili",
                "target": "bilibili",
                "status": "failed",
                "attempts": 1,
                "max_attempts": 2,
                "error": "boom",
                "file_path": "videos/a.mp4",
                "room_url_key": "room_a",
                "room_name": "Room A",
                "time_str": "20260328_120000",
                "lines": "AUTO",
                "expected_targets": ["bilibili"],
            },
            {
                "uploader": "UploaderWebDav",
                "target": "webdav",
                "status": "failed",
                "attempts": 1,
                "max_attempts": 2,
                "error": "boom",
                "from_path": "videos/b.mp4",
                "to_path": "videos/b.mp4",
                "url": "https://example.com/dav",
                "username": "user",
                "password": "pass",
                "delete_source_file": False,
                "expected_targets": ["webdav"],
            },
        ]
    )

    result = failure_log.retry_all(target="bilibili", file_path="videos/missing.mp4")
    assert result == {"total": 0, "retried": 0, "succeeded": 0, "remaining": 0, "skipped": 0}

    remaining = failure_log.read_entries()
    assert len(remaining) == 2


def test_uploader_queue_cleanup_deletes_old_uploaded_video_when_all_targets_succeeded(tmp_path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    old_file = videos_dir / "uploaded.mp4"
    old_file.write_bytes(b"video")
    old_timestamp = 1_700_000_000
    os.utime(old_file, (old_timestamp, old_timestamp))

    queue = UploaderQueue(
        failure_log_path=tmp_path / "upload_failures.jsonl",
        success_log_path=tmp_path / "upload_successes.jsonl",
        cleanup_after_hours=48,
        cleanup_dir=videos_dir,
    )
    queue.success_log.write_entries(
        [
            {
                "uploader": "UploaderBili",
                "target": "bilibili",
                "status": "success",
                "attempts": 1,
                "max_attempts": 3,
                "error": "",
                "file_path": str(old_file),
                "expected_targets": ["bilibili", "webdav"],
            },
            {
                "uploader": "UploaderWebDav",
                "target": "webdav",
                "status": "success",
                "attempts": 1,
                "max_attempts": 3,
                "error": "",
                "from_path": str(old_file),
                "to_path": str(old_file),
                "url": "https://example.com/dav",
                "expected_targets": ["bilibili", "webdav"],
            }
        ]
    )

    deleted_count = queue._cleanup_uploaded_videos()

    assert deleted_count == 1
    assert not old_file.exists()


def test_uploader_queue_cleanup_keeps_old_video_when_not_all_targets_succeeded(tmp_path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    old_file = videos_dir / "uploaded.mp4"
    old_file.write_bytes(b"video")
    old_timestamp = 1_700_000_000
    os.utime(old_file, (old_timestamp, old_timestamp))

    queue = UploaderQueue(
        failure_log_path=tmp_path / "upload_failures.jsonl",
        success_log_path=tmp_path / "upload_successes.jsonl",
        cleanup_after_hours=48,
        cleanup_dir=videos_dir,
    )
    queue.success_log.write_entries(
        [
            {
                "uploader": "UploaderBili",
                "target": "bilibili",
                "status": "success",
                "attempts": 1,
                "max_attempts": 3,
                "error": "",
                "file_path": str(old_file),
                "expected_targets": ["bilibili", "webdav"],
            }
        ]
    )
    deleted_count = queue._cleanup_uploaded_videos()

    assert deleted_count == 0
    assert old_file.exists()


def test_uploader_queue_cleanup_keeps_old_video_with_pending_failures(tmp_path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    old_file = videos_dir / "uploaded.mp4"
    old_file.write_bytes(b"video")
    old_timestamp = 1_700_000_000
    os.utime(old_file, (old_timestamp, old_timestamp))

    queue = UploaderQueue(
        failure_log_path=tmp_path / "upload_failures.jsonl",
        success_log_path=tmp_path / "upload_successes.jsonl",
        cleanup_after_hours=48,
        cleanup_dir=videos_dir,
    )
    queue.success_log.write_entries(
        [
            {
                "uploader": "UploaderBili",
                "target": "bilibili",
                "status": "success",
                "attempts": 1,
                "max_attempts": 3,
                "error": "",
                "file_path": str(old_file),
                "expected_targets": ["bilibili", "webdav"],
            },
            {
                "uploader": "UploaderWebDav",
                "target": "webdav",
                "status": "success",
                "attempts": 1,
                "max_attempts": 3,
                "error": "",
                "from_path": str(old_file),
                "to_path": str(old_file),
                "url": "https://example.com/dav",
                "expected_targets": ["bilibili", "webdav"],
            },
        ]
    )
    queue.failure_log.write_entries(
        [
            {
                "uploader": "UploaderWebDav",
                "target": "webdav",
                "status": "failed",
                "attempts": 3,
                "max_attempts": 3,
                "error": "boom",
                "from_path": str(old_file),
                "expected_targets": ["bilibili", "webdav"],
            }
        ]
    )

    deleted_count = queue._cleanup_uploaded_videos()

    assert deleted_count == 0
    assert old_file.exists()
