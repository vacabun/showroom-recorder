# showroom-recorder
A Script for Recording Showroom Streaming Video

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## Installation

1.Install the python3.

2.Install requirements.

```
pip install -r requirements.txt
```

3.Install ffmpeg

```
sudo apt install ffmpeg
```

4.Install font `font/msgothic.ttc`.

## Usage

Directly input the member room name as a parameter:

```
python3 download.py -i LOVE_MAIKA_SASAKI
```

Or modify the rooms.ini file. 

The configuration file will be automatically created on the first run.

> The SHOWROOM live address is "https://www.showroom-live.com/ROOM_URL_KEY".
> Please copy the last segment of the room name and paste it into the rooms.ini file.
> Enter multiple room names separated by line breaks and use "#" for comments.

The recorded video will be stored in the save folder, and the comments will be saved in the comments folder as subtitles.
