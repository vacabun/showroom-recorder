# showroom-recorder
A Script for Recording Showroom Streaming Video

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

