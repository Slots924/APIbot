"""Допоміжна пауза для імітації поведінки живої людини."""

import random
import time


def human_pause(min_seconds: float, max_seconds: float) -> None:
    """Виконує випадкову паузу між діями, щоб не виглядати як бот."""

    # Обираємо випадкову тривалість паузи в заданому діапазоні та засинаємо.
    # Такий підхід повторює звичну затримку реального користувача між кліками.
    time.sleep(random.uniform(min_seconds, max_seconds))
