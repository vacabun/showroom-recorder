#!/usr/bin/env python3
import os
import sys
import time
import logging
from you_get.common import match1, get_content
from json import loads
from you_get.extractors import showroom

current_directory = os.path.dirname(os.path.abspath(__file__))

url_header = "https://www.showroom-live.com/"

name = "LOVE_MAIKA_SASAKI"

def get_online(url):
    room_url_key = match1(url, r'\w+://www.showroom-live.com/([-\w]+)')
    room_id = showroom.showroom_get_roomid_by_room_url_key(room_url_key)
    timestamp = str(int(time.time() * 1000))
    api_endpoint = 'https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}&_={timestamp}'.format(
        room_id=room_id, timestamp=timestamp)
    html = get_content(api_endpoint)
    html = loads(html)
    if len(html) >= 1:
        return True
    else:
        return False
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        name = sys.argv[1]
    while True:
        try:
            url = url_header + name
            if get_online(url):
                logging.warning(name + "\'s live show is currently online.")
                dir = current_directory + '/save/'+name + \
                    '_' + str(int(time.time() * 1000))
                os.makedirs(dir)
                showroom.showroom_download(url, output_dir=dir)
            else:
                logging.warning(name + "\'s live show is currently offline.")
        except:
            time.sleep(1)
        time.sleep(1)



