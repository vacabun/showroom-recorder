from showroom_recorder.processor.uploader import UploaderBili
import argparse


upload_info_list = [
    # {'file': '/home/vacabun/workspace/showroom/videos/LOVE_ANNA_YAMAMOTO_20230629_212751.mp4',
    #  'room_url_key': 'LOVE_ANNA_YAMAMOTO'},
    {'file': '/home/vacabun/workspace/showroom/videos/LOVE_SHOKO_TAKIWAKI_20230629_225937.mp4',
     'room_url_key': 'LOVE_SHOKO_TAKIWAKI'},
    # {'file': '/home/vacabun/workspace/showroom/videos/ME_HITOMI_SUZUKI_20230629_233110.mp4',
    #  'room_url_key': 'ME_HITOMI_SUZUKI'},
    # {'file': '/home/vacabun/workspace/showroom/videos/ME_SAYA_TANIZAKI_20230629_232055.mp4',
    #  'room_url_key': 'ME_SAYA_TANIZAKI'},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--input',
                        dest='input_file')
    parser.add_argument('-k',
                        '--room_url_key',
                        dest='room_url_key')

    args = parser.parse_args()

    if args.input_file:
        time_str = args.input_file[-19:-4]

        uploader = UploaderBili(file_path=args.input_file,
                                room_url_key=args.room_url_key,
                                room_name=args.room_url_key,
                                time_str=time_str,
                                login_cookie=get_bili_cookie('bili_cookie.json'),
                                lines='AUTO')
        uploader.upload()
    else:
        for upload_info in upload_info_list:
            time_str = upload_info['file'][-19:-4]

            uploader = UploaderBili(file_path=upload_info['file'],
                                    room_url_key=upload_info['room_url_key'],
                                    room_name=upload_info['room_url_key'],
                                    time_str=time_str,
                                    login_cookie=get_bili_cookie('bili_cookie.json'))
            uploader.upload()


if __name__ == '__main__':
    main()
