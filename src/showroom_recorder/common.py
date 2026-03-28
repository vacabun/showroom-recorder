#!/usr/bin/env python3

import argparse
import logging

from .processor.video import RecorderManager
from .utils.load_config import Config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download SHOWROOM live streams.")
    parser.add_argument(
        "-i",
        "--id",
        dest="room_id",
        metavar="SHOWROOM_ID",
        help='Only monitor one SHOWROOM room URL key. For multiple rooms, edit "config.json".',
    )
    return parser


def configure_logging(debug: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    return logging.getLogger()


def resolve_rooms(config: Config, room_id: str | None, log: logging.Logger) -> list[str]:
    if room_id:
        config.rooms = [room_id]
        log.info("Monitoring %s ...", room_id)
        return config.rooms

    if not config.rooms:
        log.info("No rooms to monitor.")
        return []

    log.info("Monitoring %s rooms...", len(config.rooms))
    return config.rooms


def command_loop(manager: RecorderManager, log: logging.Logger) -> None:
    help_text = (
        "Commands:\n"
        '- Type "h" or "help" for help.\n'
        '- Type "q", "quit", or "exit" to quit.'
    )

    while True:
        try:
            line = input().strip().lower()
        except EOFError:
            break
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            break

        if line in {"q", "quit", "exit"}:
            break
        if line in {"h", "help"}:
            log.info(help_text)
            continue
        if line:
            log.info('Unknown command. Type "h" or "help" for help.')

    log.info("quitting jobs...")
    manager.quit()
    log.info("bye")


def main() -> None:
    config = Config().load_config("config.json")
    args = build_parser().parse_args()
    log = configure_logging(config.debug)

    rooms = resolve_rooms(config, args.room_id, log)
    if not rooms:
        return

    recorder_manager = RecorderManager(config)
    recorder_manager.start()
    command_loop(recorder_manager, log)
