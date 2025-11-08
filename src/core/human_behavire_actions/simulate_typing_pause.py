"""Пауза перед початком введення тексту."""

from __future__ import annotations

import random
import time

from selenium.webdriver.remote.webdriver import WebDriver


def simulate_typing_pause(driver: WebDriver, *, min_delay: float = 0.4, max_delay: float = 1.2) -> None:
    """Створює невелику паузу перед набором тексту."""
    # Пауза імітує роздум користувача перед тим, як щось надрукувати.
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

    # Повертаємо фокус до активного елемента, щоб уникнути втрати контексту під час паузи.
    _ = driver.switch_to.active_element
