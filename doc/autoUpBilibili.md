# showroom-recorder自动上传

## 1. 设置上传的cookie和token

使用 https://github.com/ForgQi/biliup-rs 导出cookie和token，参考[https://biliup.github.io/biliup-rs/index.html](https://biliup.github.io/biliup-rs/index.html)。

获得cookie.json文件。

```json
{
    "cookies": {
        "SESSDATA": "",
        "bili_jct": "",
        "DedeUserID__ckMd5": "",
        "DedeUserID": ""
    },
    "access_token": ""
}
```

在启动showroom-recorder的目录新建一个文件bili.cookie。把上面获取的cookie和token按照下面的格式填进去并且保存。

```json
{
    "SESSDATA": "",
    "bili_jct": "",
    "DedeUserID__ckMd5": "",
    "DedeUserID": "",
    "access_token": "",
    "refresh_token": null
}
```

## 2. 配置showroom-recorder

修改config.ini文件。

``` ini
[program_settings]
interval = 10                    # seconds, time interval to check rooms are on live or not
show_comments = 0                # 1: enable, 0: disable
show_debug_message = 0           # 1: enable, 0: disable
save_program_debug_log = 0       # 1: enable, 0: disable
save_comments_debug_log = 0      # 1: enable, 0: disable

[danmaku_settings]
width = 640
height = 360
font_name = MS PGothic
font_size = 18
alpha = 10                       # transparency percentage, a number between 0 and 100

[video_settings]
interval = 20
upload_webdav = 1
webdav_delete_source_file = 1
webdav_url = 
webdav_username = 
webdav_password =
biliup_lines = AUTO
```

这几个是需要修改的参数。

``` ini
upload_webdav = 1
webdav_delete_source_file = 1
webdav_url =
webdav_username =
webdav_password =
biliup_lines = AUTO
```

upload_webdav = 1，表示开启自从上传到webdav网盘。

webdav_delete_source_file = 1，表示成功上传到webdav之后会在原本录制的位置删除原文件。

webdav_url，webdav_username，webdav_password，根据实际填写。

如果不想上传到webdav可以upload_webdav = 0，或者直接不写这几个参数。

biliup_lines = AUTO参数表示上传到b站的线路。线路选择说明[https://biliup.github.io/upload-systems-analysis.html](https://biliup.github.io/upload-systems-analysis.html)，也可以直接AUTO，会自动选择。

## 3. 配置想要上传的房间

上面的都设置了也不会开始上传，还需要指定上传的房间名，（为了设置部分房间投稿部分不投稿）。

在启动showroom-recorder的目录新建一个文件biliup.list，按照room.ini每一行写一个房间名，写到这个文件里面的房间才会上传。
