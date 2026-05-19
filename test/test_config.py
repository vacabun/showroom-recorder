import json

from showroom_recorder.utils.load_config import Config


def test_load_config_applies_defaults_and_filters_empty_rooms(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "interval": 0,
                "debug": True,
                "rooms": ["room_a", "", " room_b "],
                "best_quality": False,
                "webdav": {
                    "upload": True,
                    "url": "https://example.com/dav",
                    "username": "user",
                    "password": "pass",
                },
                "biliup": {
                    "rooms": [" bili_room ", ""],
                },
                "acfun": {
                    "rooms": [" ac_room ", ""],
                    "cookie_file": "cookies/acfun.json",
                },
                "cleanup_uploaded_videos_after_hours": 48,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = Config().load_config("config.json")

    assert config.interval == 1
    assert config.debug is True
    assert config.rooms == ["room_a", "room_b"]
    assert config.best_quality is False
    assert config.webdav.upload is True
    assert config.webdav.delete_source_file is False
    assert config.biliup.rooms == ["bili_room"]
    assert config.biliup.line == "AUTO"
    assert config.acfun.rooms == ["ac_room"]
    assert config.acfun.cookie_file == "cookies/acfun.json"
    assert config.cleanup_uploaded_videos_after_hours == 48


def test_load_config_creates_default_file_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = Config().load_config("config.json")

    assert (tmp_path / "config.json").exists()
    assert config.interval == 10
    assert config.rooms == []
    assert config.biliup.rooms == []
    assert config.acfun.rooms == []
    assert config.acfun.cookie_file == "ac_cookies.json"
    assert config.cleanup_uploaded_videos_after_hours == 0
