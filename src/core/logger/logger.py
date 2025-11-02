import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Папка для логів
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Створює та повертає логер з консольним та файловим виводом.
    Формат:
    2025-11-02 12:01:35 | INFO | bot | Запуск профілю...

    Логи зберігаються в logs/app.log (ротація до 5 файлів по 1MB)
    """

    logger = logging.getLogger(name)

    # Якщо логер уже налаштований — не дублюємо хендлери
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # ---- Console handler ----
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # ---- File handler (rotate 1MB x 5 files) ----
    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger