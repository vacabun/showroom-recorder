import m3u8

# M3U8文件的URL
m3u8_url = "https://hls-css.live.showroom-live.com/live/40acb124ff82e95b4882495ae83838be7a6b3631ed960cf32b1e6eaf2712d6d5_default.m3u8"

# 使用m3u8库加载M3U8文件
playlist = m3u8.load(m3u8_url)

# 初始化一个字典来存储带宽和相应的视频流URL
stream_dict = {}

# 遍历播放列表中的所有流
for stream in playlist.playlists:
    # 获取带宽
    bandwidth = stream.stream_info.bandwidth
    # 获取视频流的URL
    # 需要检查URL是否完整
    stream_url = stream.uri
    if not stream_url.startswith("http"):
        # 如果不是完整的URL，则尝试拼接
        base_url = m3u8_url.rsplit("/", 1)[0]
        stream_url = f"{base_url}/{stream_url}"
    
    # 将带宽和视频流URL添加到字典中
    stream_dict[bandwidth] = stream_url

# 打印结果
print("不同带宽的视频流地址:")
for bandwidth, url in stream_dict.items():
    print(f"带宽: {bandwidth}, URL: {url}")