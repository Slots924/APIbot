"""Короткий сценарій швидкого скролу сторінки."""

from __future__ import annotations

import random
import time

from selenium.webdriver.remote.webdriver import WebDriver


def scroll_up_down_short(driver: WebDriver) -> None:
    """Імітує швидкий короткий скрол вниз і трохи вгору."""
    # Визначаємо довжину скролу у пікселях, щоб рух виглядав природно.
    scroll_distance = random.randint(200, 400)

    # Скролимо сторінку вниз — користувач ніби шукає потрібний блок.
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_distance)
    time.sleep(random.uniform(0.2, 0.4))

    # Повертаємо сторінку трохи вгору, ніби користувач зупинився на потрібному місці.
    driver.execute_script("window.scrollBy(0, arguments[0]);", -int(scroll_distance * random.uniform(0.3, 0.6)))
    time.sleep(random.uniform(0.2, 0.4))
