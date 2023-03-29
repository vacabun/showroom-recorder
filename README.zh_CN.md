# showroom-recorder
一个用于录制SHOWROOM视频的脚本

- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## Installation
1.安装python3。

2.安装python环境。

```
sudo pip install -r requirements.txt
```

2.安装ffmpeg。

```
sudo apt install ffmpeg
```

4.安装字体`font/msgothic.ttc`


## Usage
使用方法为直接将成员房间名作为参数运行脚本：

```
python3 main.py -i LOVE_MAIKA_SASAKI
```
或者修改`rooms.ini`文件，首次运行将会自动创建配置文件。

> showroom 直播地址为 "https://www.showroom-live.com/ROOM_URL_KEY"
> 请复制最后一段房间名并且粘贴到`rooms.ini`文件中
> 多个房间名换行输入，使用#注释

录制的视频将会被存储在`save`文件夹下

保存的评论会以字幕形式保存在`comments`文件夹下


