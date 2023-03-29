# showroom-recorder
A Script for Recording Showroom Streaming Video

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

> It is recommended to use it in the `linux` or `macOS` environment.

> If you are the `windows` user. Please use `cygwin` or use on the `wsl (Windows Subsystem for Linux)`.

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

## Usage

The basic usage is to directly input the member room name as a parameter:

```
python3 download.py LOVE_MAIKA_SASAKI
```

Or modify the default member name in the script:

```
name = "LOVE_MAIKA_SASAKI"
```
And run the script directly:

```
python3 download.py LOVE_MAIKA_SASAKI
```

The script will recorder streaming video in the data directory (./save) 
