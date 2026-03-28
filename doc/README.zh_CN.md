# showroom-recorder

一个用于录制 SHOWROOM 直播、自动上传和手动补传失败任务的脚本。

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

典型配置步骤：

1. 复制 `config.example.json` 为 `config.json`
2. 把要监听的 SHOWROOM 房间 key 写入 `rooms`
3. 如果要自动上传到 Bilibili，把房间 key 加到 `biliup.rooms`
4. 如果要上传到 WebDAV，打开 `webdav.upload` 并填写连接信息
5. 如果要自动删除旧视频，把 `cleanup_uploaded_videos_after_hours` 设成正整数，例如 `48`

showroom 直播地址格式如下：

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

把最后一段 `ROOM_URL_KEY` 填到 `rooms` 里即可。

如果需要自动上传到 Bilibili，请把 `cookies.json` 放到运行目录，并在 `biliup.rooms` 中列出需要自动投稿的房间。

最小配置示例：

```json
{
    "interval": 10,
    "debug": false,
    "best_quality": true,
    "rooms": ["LOVE_MAIKA_SASAKI"],
    "biliup": {
        "rooms": ["LOVE_MAIKA_SASAKI"],
        "line": "AUTO"
    },
    "webdav": {
        "upload": false,
        "url": "",
        "username": "",
        "password": "",
        "delete_source_file": false
    },
    "cleanup_uploaded_videos_after_hours": 48
}
```

## 使用

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
showroom-recorder
```

## 上传行为

录制文件进入上传队列后：

- 失败任务会写入 `upload_failures.jsonl`
- 成功任务会写入 `upload_successes.jsonl`
- 单个任务会在内部自动重试一定次数
- 自动清理只会处理 `videos/` 顶层的 `.mp4` 文件
- 自动清理只会在上传成功后触发
- 只有文件超过 `cleanup_uploaded_videos_after_hours` 设定时间才会考虑删除
- 只有该文件的所有配置上传目标都成功后才会删除
- 只要该文件还存在失败记录，就不会被删除

## 手动补传

补传全部失败任务：

```bash
showroom-recorder --retry-failed-uploads
```

只补传某一个目标：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target bilibili
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target webdav
```

只补传某一个文件：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-file videos/LOVE_MAIKA_SASAKI_20260328_120000.mp4
```

录制的视频会存放在 `videos/` 下。

清理配置示例：

```json
{
    "cleanup_uploaded_videos_after_hours": 48
}
```

当这个值大于 `0` 时，程序会在上传成功后清理 `videos/` 下超过时限的顶层 `.mp4` 文件，但前提是这个文件对应的所有上传目标都已经成功。

[自动上传说明](https://github.com/vacabun/showroom-recorder/blob/main/doc/autoUpBilibili.md)
