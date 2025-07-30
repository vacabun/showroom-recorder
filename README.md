# showroom-recorder
A Script for Recording Showroom Streaming Video

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## Installation

1. Install the python3.

2. Install requirements.

``` shell
pip install showroom-recorder
```

3. Install ffmpeg

``` shell
sudo apt install ffmpeg
```

## Usage

Directly input the member room name as a parameter:

``` shell
showroom-recorder -i LOVE_MAIKA_SASAKI
```

Or modify the config.json file，and run without parameter. 

The configuration file will be automatically created on the first run.

> The SHOWROOM live address is "https://www.showroom-live.com/ROOM_URL_KEY".

> Please copy the last segment of the room name and paste it into the rooms list.


``` shell
showroom-recorder
```

The recorded video will be stored in the videos folder.

