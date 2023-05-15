# showroom-recorder
A Script for Recording Showroom Streaming Video

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## Installation

1. Install the python3.

2. Install requirements.

``` shell
pip install -r requirements.txt
```

3. Install ffmpeg

``` shell
sudo apt install ffmpeg
```

4. Install font `font/msgothic.ttc`. (If you need to use subtitle files)

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

## D0cker.

1. Create new directories `data/comments` and `data/videos`.

2. Enter the directory `data`.

3. Download the docker image

```
docker pull vacabun/showroom-recorder:latest
```

4. Create a docker container

```
docker run -v videos:/root/showroom-recorder/videos -v comments:/root/showroom-recorder/comments -it vacabun/showroom-recorder /bin/bash
```

## Build

1. Install pyinstaller

``` shell
pip install pyinstaller
```

2. Create spec file

``` shell
pyi-makespec --onefile --console "main.py"
```

3. Edit spec file

Open "main.spec" file and edit it as follows.

> My streamlink is version 2.4.0, but it also conflicts with the iso639 package, so I added it.

``` python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules  # append

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas = collect_data_files('streamlink.plugins', include_py_files=True) + collect_data_files('iso639'), # edit
    hiddenimports = collect_submodules('streamlink.plugins'),   # edit
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

3. Porting executable file

``` shell
pyinstaller --noconfirm --clean "main.spec"
```
