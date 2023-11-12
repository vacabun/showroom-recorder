# showroom-recorder
一个用于录制SHOWROOM视频的脚本

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)


## Installation
1.安装python3。

2.安装python环境。

``` shell
pip install showroom-recorder
```

2.安装ffmpeg。

``` shell
sudo apt install ffmpeg
```

4.安装字体`font/msgothic.ttc` (如果需要使用字幕文件)


## Usage
使用方法为直接将成员房间名作为参数运行脚本：

``` shell
showroom-recorder -i LOVE_MAIKA_SASAKI
```

或者修改`rooms.ini`文件不加参数直接运行脚本，首次运行将会自动创建配置文件。

> showroom 直播地址为 "https://www.showroom-live.com/ROOM_URL_KEY"

> 请复制最后一段房间名并且粘贴到`rooms.ini`文件中

> 多个房间名换行输入，使用#注释

``` shell
showroom-recorder
```

录制的视频将会被存储在`save`文件夹下

保存的评论会以字幕形式保存在`comments`文件夹下

[自动上传说明](https://github.com/vacabun/showroom-recorder/blob/main/doc/autoUpBilibili.md)


