import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings

def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if logger.handlers:
        return

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # 파일 로깅
    file_handler = RotatingFileHandler(
        settings.LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # 콘솔 로깅
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)