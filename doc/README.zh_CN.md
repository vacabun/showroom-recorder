# showroom-recorder
一个用于录制SHOWROOM视频的脚本

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

> 推荐在`linux`或`macOS`环境下使用。

> 如果你是`windows`用户。 请使用`cygwin`或在`wsl（适用于 Linux 的 Windows 子系统）`上使用。

## Installation
1.安装python3。

2.安装python包。

```
sudo pip install -r requirements.txt
```

2.安装ffmpeg。

```
sudo apt install ffmpeg
```

## Usage
基本用法为直接将成员房间名作为参数运行脚本：

```
python3 download.py LOVE_MAIKA_SASAKI
```

或者修改脚本中默认的成员房间名:

```
name = "LOVE_MAIKA_SASAKI"
```
直接运行脚本:

```
python3 download.py LOVE_MAIKA_SASAKI
```
录制的视频将会被存储（路径为./save）

