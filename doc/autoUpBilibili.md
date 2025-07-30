# showroom-recorder自动上传

## 1. 设置上传的cookie和token

使用 https://github.com/ForgQi/biliup-rs 导出cookie和token，参考[https://biliup.github.io/biliup-rs/index.html](https://biliup.github.io/biliup-rs/index.html)。

获得cookie.json文件。

把cookie.json文件放在启动showroom-recorder的目录

## 2. 配置想要上传的房间

上面的都设置了也不会开始上传，还需要指定上传的房间名，（为了设置部分房间投稿部分不投稿）。

和配置录制房间的方法一样，在config.json配置文件中的biliup.rooms里面添加想要上传的房间

