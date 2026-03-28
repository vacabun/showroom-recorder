# showroom-recorder 自动上传

## 1. 准备上传登录信息

使用 https://github.com/ForgQi/biliup-rs 导出登录信息，参考 [https://biliup.github.io/biliup-rs/index.html](https://biliup.github.io/biliup-rs/index.html)。

导出后得到 `cookies.json`，把它放在运行 `showroom-recorder` 的目录中。

不要把登录信息写进仓库，也不要提交 `cookies.json`。

## 2. 配置要上传的房间

只有在 `config.json` 的 `biliup.rooms` 里列出的房间，录制完成后才会自动投稿。

示例：

```json
{
    "biliup": {
        "rooms": ["LOVE_MAIKA_SASAKI"],
        "line": "AUTO"
    }
}
```

`line` 默认可以保持 `AUTO`。

## 3. 运行方式

正常运行录制程序即可：

```bash
showroom-recorder
```

当录制的房间命中 `biliup.rooms` 配置时，程序会在录制结束后尝试使用本地 `cookies.json` 上传。

如果上传连续失败，程序会把失败任务写到当前目录下的 `upload_failures.jsonl`，方便后续排查或补传。

## 4. 手动补传失败任务

补传全部失败任务：

```bash
showroom-recorder --retry-failed-uploads
```

只补传 Bilibili 失败任务：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target bilibili
```

只补传单个文件：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-file videos/LOVE_MAIKA_SASAKI_20260328_120000.mp4
```

补传成功后，对应失败记录会从 `upload_failures.jsonl` 中移除。
