from showroom_recorder.processor.uploader import UploaderBili
from showroom_recorder.utils.config import get_bili_cookie
import argparse


upload_info_list = [
    {'file': '~/workspace/showroom/videos/LOVE_HANA_OBA_20230627_173116.mp4',
     'room_url_key': 'LOVE_HANA_OBA'},
    {'file': '~/workspace/showroom/videos/LOVE_HITOMI_TAKAMATSU_20230627_200125.mp4',
     'room_url_key': 'LOVE_HITOMI_TAKAMATSU'},
    {'file': '~/workspace/showroom/videos/LOVE_IORI_NOGUCHI_20230627_173001.mp4',
     'room_url_key': 'LOVE_IORI_NOGUCHI'},
    {'file': '~/workspace/showroom/videos/LOVE_KIARA_SAITO_20230627_173101.mp4',
     'room_url_key': 'LOVE_KIARA_SAITO'},
    {'file': '~/workspace/showroom/videos/LOVE_MAIKA_SASAKI_20230627_195633.mp4',
     'room_url_key': 'LOVE_MAIKA_SASAKI'},
    {'file': '~/workspace/showroom/videos/LOVE_RISA_OTOSHIMA_20230627_200111.mp4',
     'room_url_key': 'LOVE_RISA_OTOSHIMA'},
    {'file': '~/workspace/showroom/videos/LOVE_RISA_OTOSHIMA_20230627_234433.mp4',
     'room_url_key': 'LOVE_RISA_OTOSHIMA'},
    {'file': '~/workspace/showroom/videos/LOVE_SANA_MOROHASHI_20230627_200154.mp4',
     'room_url_key': 'LOVE_SANA_MOROHASHI'},
    {'file': '~/workspace/showroom/videos/LOVE_SHOKO_TAKIWAKI_20230627_173017.mp4',
     'room_url_key': 'LOVE_SHOKO_TAKIWAKI'},
    {'file': '~/workspace/showroom/videos/ME_HITOMI_SUZUKI_20230627_225816.mp4',
     'room_url_key': 'ME_HITOMI_SUZUKI'},

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
                                login_cookie=get_bili_cookie('bili_cookie.json'))
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
