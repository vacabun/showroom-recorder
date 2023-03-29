# showroom-recorder
A Script for Recording Showroom Streaming Video

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## Installation

1.Install the python3.

2.Install requirements.

``` shell
pip install -r requirements.txt
```

3.Install ffmpeg

``` shell
sudo apt install ffmpeg
```

4.Install font `font/msgothic.ttc`. (If you need to use subtitle files)

## Usage

Directly input the member room name as a parameter:

``` shell
python3 main.py -i LOVE_MAIKA_SASAKI
```

Or modify the rooms.ini file，and run without parameter. 

The configuration file will be automatically created on the first run.

> The SHOWROOM live address is "https://www.showroom-live.com/ROOM_URL_KEY".

> Please copy the last segment of the room name and paste it into the rooms.ini file.

> Enter multiple room names separated by line breaks and use "#" for comments.

``` shell
python3 main.py
```

The recorded video will be stored in the save folder.

And the comments will be saved in the comments folder as subtitles.
