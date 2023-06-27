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


    args = parser.parse_args()
    time_str  = args.input_file[-19:-4]

    uploader = UploaderBili(file_path=args.input_file,
                            room_url_key=args.room_url_key,
                            room_name=args.room_url_key,
                            time_str=time_str,
                            login_cookie=get_bili_cookie('bili_cookie.json'))
    uploader.upload()


if __name__ == '__main__':
    main()
