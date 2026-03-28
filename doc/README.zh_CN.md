# showroom-recorder
一个用于录制 SHOWROOM 直播视频的脚本。

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## 安装

```bash
pip install showroom-recorder
sudo apt install ffmpeg
```

## 配置

程序会读取当前目录下的 `config.json`。仓库里提供了干净的 `config.example.json` 作为参考。

showroom 直播地址格式如下：

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

把最后一段 `ROOM_URL_KEY` 填到 `rooms` 里即可。

如果需要自动上传到 Bilibili，请把 `cookies.json` 放到运行目录，并在 `biliup.rooms` 中列出需要自动投稿的房间。

## 使用

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
showroom-recorder
```

录制的视频会存放在 `videos/` 下。

[自动上传说明](https://github.com/vacabun/showroom-recorder/blob/main/doc/autoUpBilibili.md)

