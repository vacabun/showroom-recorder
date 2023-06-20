#!/usr/bin/env python3

import logging
import argparse
import time

from .utils import config
from .processor import danmaku
from .processor import video

def main():
    room_url_keys = config.readRoomsFile('rooms.ini')
    danmaku_settings = config.readSettingsFile('config.ini')

    # build logging
    log = logging.getLogger()
    log.setLevel(logging.INFO)

    consoleHandler = logging.StreamHandler()
    consoleFmt = logging.Formatter(
        fmt='%(asctime)s %(message)s', datefmt='%H:%M:%S')
    consoleHandler.setFormatter(consoleFmt)
    if danmaku_settings['program_settings']['show_debug_message'] > 0:
        consoleHandler.setLevel(logging.DEBUG)
    else:
        consoleHandler.setLevel(logging.INFO)
    log.addHandler(consoleHandler)

    if danmaku_settings['program_settings']['save_program_debug_log'] > 0:
        fileHandler = logging.handlers.TimedRotatingFileHandler(
            'sr_danmaku.log', when='midnight', backupCount=7, encoding='utf-8')
        fileFmt = logging.Formatter(fmt='%(asctime)s [%(threadName)s][%(levelname)s][%(name)s] %(message)s',
                                    datefmt='%y%m%d %H:%M:%S')
        fileHandler.setFormatter(fileFmt)
        fileHandler.setLevel(logging.DEBUG)
        log.addHandler(fileHandler)

    # build ArgumentParser
    parser = argparse.ArgumentParser(
        description='download showroom video and  comments')
    parser.add_argument('-i', '--id', help='Only monitor this one showroom id. \
                For more rooms, please edit file "romms.ini".', metavar='SHOWROOM_ID', dest='sr_id')

    log.debug('program_settings = {}'.format(danmaku_settings['program_settings']))
    log.debug('danmaku_settings = {}'.format(danmaku_settings['danmaku_settings']))

    # handle args
    args = parser.parse_args()

    nRoom = len(room_url_keys)
    if args.sr_id:
        room_url_key = args.sr_id
        room_url_keys = [room_url_key]
        log.info('Monitoring {} ...'.format(room_url_key))

    else:
        # remove duplicates
        nRoomPre = nRoom
        room_url_keys = list(dict.fromkeys(room_url_keys))
        nRoom = len(room_url_keys)
        if nRoomPre != nRoom:
            log.info('Removed duplicate {} room(s)'.format(nRoomPre - nRoom))
        log.info('Monitoring {} rooms...'.format(len(room_url_keys)))

    if len(room_url_keys) == 0:
        log.info('No rooms to monitor')
    else:
        if danmaku_settings['program_settings']['show_comments'] > 0:
            log.info('Comments on')
        else:
            log.info('Comments off')
        # start monitoring room

    danmaku_rm = danmaku.RoomMonitor(room_url_keys, danmaku_settings)
    danmaku_rm.start()
    video_rm = video.RoomMonitor(room_url_keys, danmaku_settings)
    video_rm.start()

    helptxt = '''
    Commands:
    - Type "h" or "help" for help.
    - Type "q" or "quit" to quit.
    '''

    while True:
        try:
            line = input().strip().lower()
        except KeyboardInterrupt:  # Ctrl-C is pressed
            log.info('KeyboardInterrupt')
            break
        if line == 'q' or line == 'quit' or line == 'exit':
            break
        elif line == 'h' or line == 'help':
            log.info(helptxt)
        else:
            log.info('Unknown command. Type "h" or "help" for help.')
        time.sleep(0.1)

    log.info('quitting jobs...')
    danmaku_rm.quit()
    log.info("bye")
    # handle arguments
