# showroom-recorder
一个用于录制SHOWROOM视频的脚本

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

> 仅在 Ubuntu-22.04-x86_64 执行过测试

## Installation

安装依赖

```
pip install -r requirements.txt
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

