# app/core/logger.py

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple, Any

import pytz
from pytz import timezone, UTC

# Timezone and paths
TZ: timezone = pytz.timezone('US/Eastern')
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
LOGS_DIR: Path = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Logger setup
logger: logging.Logger = logging.getLogger("tao_service")
logger.setLevel(logging.DEBUG)

log_fmt: str = '%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] ' \
          '[%(levelname)s] %(name)s: %(message)s'
date_fmt: str = '%Y-%m-%d %H:%M:%S'
formatter: logging.Formatter = logging.Formatter(fmt=log_fmt, datefmt=date_fmt)


# Time converter for formatter
def customTime(*args: Any) -> time.struct_time:
    utc_dt: datetime = pytz.utc.localize(datetime.utcnow())
    converted: datetime = utc_dt.astimezone(TZ)
    return converted.timetuple()


logging.Formatter.converter = customTime

# Handlers
file_handler: logging.FileHandler = logging.FileHandler(
    LOGS_DIR / f'{datetime.now(TZ).date()}_tao_service.log'
)
file_handler.setFormatter(formatter)

stream_handler: logging.StreamHandler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)