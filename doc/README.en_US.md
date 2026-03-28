# showroom-recorder
Record SHOWROOM live streams from the command line.

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## Installation

```bash
pip install showroom-recorder
sudo apt install ffmpeg
```

## Configuration

The app reads `config.json` from the current working directory. A clean example is available in `config.example.json`.

The SHOWROOM room key comes from the last segment of:

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

Put the room keys in `rooms`. For automatic Bilibili uploads, place `cookies.json` next to `config.json` and list the upload targets in `biliup.rooms`.

## Usage

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
showroom-recorder
```

Recorded videos are stored in `videos/`.
