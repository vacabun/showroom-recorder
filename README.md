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

The SHOWROOM live URL format is:

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

Use the last path segment as the room key.

For Bilibili uploads, place your exported `cookies.json` next to `config.json`. Sensitive tokens and cookies should stay in local files, not in Git.

## Usage

Monitor a single room directly:

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
```

Or run with the rooms configured in `config.json`:

```bash
showroom-recorder
```

Recorded videos are written to `videos/`.

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
