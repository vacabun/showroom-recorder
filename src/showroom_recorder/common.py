#!/usr/bin/env python3

import logging
import argparse
import time

from .utils import load_config
from .processor import video


def main():
    config = load_config.Config()
    config.LoadConfig("config.json")

    # config logging
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    consoleFmt = logging.Formatter(
        fmt='%(asctime)s %(message)s', datefmt='%H:%M:%S')
    consoleHandler.setFormatter(consoleFmt)
    if config.debug:
        consoleHandler.setLevel(logging.DEBUG)
    else:
        consoleHandler.setLevel(logging.INFO)
    log.addHandler(consoleHandler)

    # config ArgumentParser
    parser = argparse.ArgumentParser(
        description='download showroom video.')
    parser.add_argument('-i', '--id', help='Only monitor this one showroom id. \
                For more rooms, please edit file "config.json".', metavar='SHOWROOM_ID', dest='roomId')

    # handle args
    args = parser.parse_args()
    if args.roomId:
        roomNum = 1
        config.rooms = [args.roomId]
        log.info(f'Monitoring {args.roomId} ...')
    else:
        roomNum = len(config.rooms)
        if roomNum == 0:
            log.info('No rooms to monitor')
        else:
            log.info(f'Monitoring {roomNum} rooms...')

    videoRecroderManager = video.RecroderManager(config)
    videoRecroderManager.start()

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
    videoRecroderManager.quit()
    log.info("bye")
