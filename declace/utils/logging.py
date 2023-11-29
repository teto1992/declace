from typing import List
from loguru import logger
import sys


def enable_logging_channels(channels: List[str]):
    logger.remove()
    logger.add(sys.stderr, filter=lambda record: record["level"].name in channels)
