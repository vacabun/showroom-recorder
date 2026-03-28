# showroom-recorder

Record SHOWROOM live streams, optionally upload finished videos, and publish releases to PyPI with GitHub Actions.

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## Installation

Install the package:

```bash
pip install showroom-recorder
```

Install `ffmpeg` separately:

```bash
sudo apt install ffmpeg
```

## Configuration

The app reads `config.json` from the current working directory. On first run it creates a default config automatically, but the repository also includes [config.example.json](./config.example.json) as a clean reference.

Typical setup:

1. Copy `config.example.json` to `config.json`.
2. Put the SHOWROOM room URL keys you want to monitor into `rooms`.
3. If you want Bilibili uploads, add the room keys to `biliup.rooms`.
4. If you want WebDAV uploads, enable `webdav.upload` and fill in the connection settings.
5. If you want old uploaded videos to be cleaned up automatically, set `cleanup_uploaded_videos_after_hours` to a positive number such as `48`.

The SHOWROOM live URL format is:

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

Use the last path segment as the room key.

For Bilibili uploads, place your exported `cookies.json` next to `config.json`. Sensitive tokens and cookies should stay in local files, not in Git.

Minimal example:

```json
{
    "interval": 10,
    "debug": false,
    "best_quality": true,
    "rooms": ["LOVE_MAIKA_SASAKI"],
    "biliup": {
        "rooms": ["LOVE_MAIKA_SASAKI"],
        "line": "AUTO"
    },
    "webdav": {
        "upload": false,
        "url": "",
        "username": "",
        "password": "",
        "delete_source_file": false
    },
    "cleanup_uploaded_videos_after_hours": 48
}
```

## Usage

Monitor a single room directly:

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
```

Or run with the rooms configured in `config.json`:

```bash
showroom-recorder
```

## Upload Behavior

When a recorded file is queued for upload:

- Failed uploads are written to `upload_failures.jsonl`
- Successful uploads are written to `upload_successes.jsonl`
- A retryable upload is attempted up to the configured internal retry limit
- Video cleanup only deletes top-level `.mp4` files in `videos/`
- Cleanup only runs after upload success
- Cleanup only deletes files older than `cleanup_uploaded_videos_after_hours`
- Cleanup only deletes a file after all configured upload targets for that file have succeeded
- Cleanup never deletes a file that still has a pending failure record

## Manual Retry

Retry all failed uploads and exit:

```bash
showroom-recorder --retry-failed-uploads
```

Retry only one target:

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target bilibili
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target webdav
```

Retry only one file:

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-file videos/LOVE_MAIKA_SASAKI_20260328_120000.mp4
```

Recorded videos are written to `videos/`.

Cleanup config example:

```json
{
    "cleanup_uploaded_videos_after_hours": 48
}
```

When this value is greater than `0`, the uploader deletes old top-level `.mp4` files in `videos/` after upload success, but only when all expected upload targets have already succeeded for that file.

## Development

Common commands:

```bash
make clean
make build
make reinstall
make release VERSION=0.7.16
```

Development notes and release flow are documented in [doc/DEVELOPMENT.md](./doc/DEVELOPMENT.md).

## Documentation

- Chinese: [doc/README.zh_CN.md](./doc/README.zh_CN.md)
- English: [doc/README.en_US.md](./doc/README.en_US.md)
- Japanese: [doc/README.ja_JP.md](./doc/README.ja_JP.md)
- Bilibili upload notes: [doc/autoUpBilibili.md](./doc/autoUpBilibili.md)
