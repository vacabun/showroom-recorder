from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_TEMPLATE = {
    "interval": 10,
    "debug": False,
    "webdav": {
        "upload": False,
        "url": "",
        "username": "",
        "password": "",
        "delete_source_file": False,
    },
    "best_quality": True,
    "rooms": [""],
    "biliup": {
        "rooms": [""],
        "line": "AUTO",
    },
    "cleanup_uploaded_videos_after_hours": 0,
}


def _normalize_room_list(rooms: list[Any] | None) -> list[str]:
    if not rooms:
        return []
    return [str(room).strip() for room in rooms if str(room).strip()]


@dataclass
class WebdavConfig:
    upload: bool = False
    url: str = ""
    username: str = ""
    password: str = ""
    delete_source_file: bool = False

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "WebdavConfig":
        payload = payload or {}
        return cls(
            upload=bool(payload.get("upload", False)),
            url=str(payload.get("url", "")),
            username=str(payload.get("username", "")),
            password=str(payload.get("password", "")),
            delete_source_file=bool(payload.get("delete_source_file", False)),
        )


@dataclass
class BiliupConfig:
    rooms: list[str] = field(default_factory=list)
    line: str = "AUTO"

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "BiliupConfig":
        payload = payload or {}
        return cls(
            rooms=_normalize_room_list(payload.get("rooms")),
            line=str(payload.get("line", "AUTO") or "AUTO"),
        )


@dataclass
class Config:
    interval: int = 10
    debug: bool = False
    webdav: WebdavConfig = field(default_factory=WebdavConfig)
    rooms: list[str] = field(default_factory=list)
    biliup: BiliupConfig = field(default_factory=BiliupConfig)
    best_quality: bool = True
    cleanup_uploaded_videos_after_hours: int = 0

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Config":
        return cls(
            interval=max(1, int(payload.get("interval", 10))),
            debug=bool(payload.get("debug", False)),
            webdav=WebdavConfig.from_mapping(payload.get("webdav")),
            rooms=_normalize_room_list(payload.get("rooms")),
            biliup=BiliupConfig.from_mapping(payload.get("biliup")),
            best_quality=bool(payload.get("best_quality", True)),
            cleanup_uploaded_videos_after_hours=max(
                0, int(payload.get("cleanup_uploaded_videos_after_hours", 0))
            ),
        )

    def load_config(self, file_name: str) -> "Config":
        file_path = Path.cwd() / file_name
        self._ensure_config_exists(file_path)

        with file_path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)

        loaded = self.from_mapping(payload)
        self.interval = loaded.interval
        self.debug = loaded.debug
        self.webdav = loaded.webdav
        self.rooms = loaded.rooms
        self.biliup = loaded.biliup
        self.best_quality = loaded.best_quality
        self.cleanup_uploaded_videos_after_hours = loaded.cleanup_uploaded_videos_after_hours
        return self

    def LoadConfig(self, fileName: str) -> "Config":
        return self.load_config(fileName)

    @staticmethod
    def _ensure_config_exists(file_path: Path) -> None:
        if file_path.is_file():
            return

        with file_path.open("w", encoding="utf-8") as file_obj:
            json.dump(CONFIG_TEMPLATE, file_obj, indent=4, ensure_ascii=False)
            file_obj.write("\n")
        logging.info("File %s does not exist, created with defaults.", file_path)
