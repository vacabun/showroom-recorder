#!/usr/bin/env python3
import os
import time

from you_get.extractors import showroom

current_directory = os.path.dirname(os.path.abspath(__file__))

url_header = "https://www.showroom-live.com/"

name = "miyu_kishi"
# name = 'momona_matsumoto'

os.makedirs(path)

while True:
    dir = current_directory + '/save/'+name+'_'+ str(time.time())
    showroom.showroom_download(url_header + name, output_dir= dir)
