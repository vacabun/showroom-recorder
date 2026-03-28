import argparse

from showroom_recorder.processor.uploader import UploaderBili


UPLOAD_INFO_LIST = [
    {
        "file": "/home/vacabun/workspace/showroom/videos/LOVE_SHOKO_TAKIWAKI_20230629_225937.mp4",
        "room_url_key": "LOVE_SHOKO_TAKIWAKI",
    },
]


def build_uploader(file_path, room_url_key):
    time_str = file_path[-19:-4]
    return UploaderBili(
        file_path=file_path,
        room_url_key=room_url_key,
        room_name=room_url_key,
        time_str=time_str,
        lines="AUTO",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input_file")
    parser.add_argument("-k", "--room_url_key", dest="room_url_key")
    args = parser.parse_args()

    if args.input_file and args.room_url_key:
        build_uploader(args.input_file, args.room_url_key).upload()
        return

    for upload_info in UPLOAD_INFO_LIST:
        build_uploader(upload_info["file"], upload_info["room_url_key"]).upload()


if __name__ == "__main__":
    main()
