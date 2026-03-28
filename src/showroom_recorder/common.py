#!/usr/bin/env python3

import argparse
import logging

from .processor.video import RecorderManager
from .services.uploading import UploadFailureLog
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
    parser.add_argument(
        "--retry-failed-uploads",
        action="store_true",
        help="Retry tasks recorded in upload_failures.jsonl, remove succeeded entries, then exit.",
    )
    parser.add_argument(
        "--retry-failed-uploads-target",
        choices=["bilibili", "webdav"],
        help="Only retry failed uploads for one target. Use with --retry-failed-uploads.",
    )
    parser.add_argument(
        "--retry-failed-uploads-file",
        metavar="FILE",
        help="Only retry failed uploads for one source file. Use with --retry-failed-uploads.",
    )
    return parser


def configure_logging(debug: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    third_party_level = logging.INFO if debug else logging.WARNING
    logging.getLogger("urllib3").setLevel(third_party_level)
    logging.getLogger("requests").setLevel(third_party_level)
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
    summary = manager.uploader_queue.summary()
    if any(summary.values()):
        log.info(
            "upload summary: %s succeeded, %s failed, %s old video(s) deleted.",
            summary["succeeded"],
            summary["failed"],
            summary["deleted"],
        )
    log.info("bye")


def main() -> None:
    args = build_parser().parse_args()
    if args.retry_failed_uploads:
        log = configure_logging(False)
        result = UploadFailureLog().retry_all(
            target=args.retry_failed_uploads_target,
            file_path=args.retry_failed_uploads_file,
        )
        if result["total"] == 0:
            log.info("No failed uploads to retry.")
            return

        log.info(
            "Retried %s failed upload(s): %s succeeded, %s remaining, %s skipped.",
            result["retried"],
            result["succeeded"],
            result["remaining"],
            result["skipped"],
        )
        return
    if args.retry_failed_uploads_target or args.retry_failed_uploads_file:
        raise SystemExit("Use --retry-failed-uploads together with retry filters.")

    config = Config().load_config("config.json")
    log = configure_logging(config.debug)

    rooms = resolve_rooms(config, args.room_id, log)
    if not rooms:
        return

    recorder_manager = RecorderManager(config)
    recorder_manager.start()
    command_loop(recorder_manager, log)
