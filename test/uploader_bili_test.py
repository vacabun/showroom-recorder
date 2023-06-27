from showroom_recorder.processor.uploader import UploaderBili
from showroom_recorder.utils.config import get_bili_cookie
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--input',
                        dest='input_file')
    parser.add_argument('-k',
                        '--room_url_key',
                        dest='room_url_key')
    parser.add_argument('-t',
                        '--time_str',
                        dest='time_str')

    args = parser.parse_args()

    uploader = UploaderBili(file_path=args.input_file,
                            room_url_key=args.room_url_key,
                            time_str=args.time_str,
                            login_cookie=get_bili_cookie('bili_cookie.json'))
    uploader.upload()


if __name__ == '__main__':
    main()
