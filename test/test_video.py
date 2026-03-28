from showroom_recorder.processor import video
from showroom_recorder.services.showroom_api import ShowroomApiClient
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
