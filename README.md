# showroom-recorder
A Script for Recording Showroom Streaming Video

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

> Only tested On Ubuntu-22.04-x86_64

## Installation

Install requirements

```
pip install -r requirements.txt
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