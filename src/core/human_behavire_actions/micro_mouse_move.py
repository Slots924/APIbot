"""Модуль з дією для короткого мікроруху курсора."""

from __future__ import annotations

import random
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver


def micro_mouse_move(driver: WebDriver) -> None:
    """Робить короткий майже непомітний рух курсора у межах 20–40 пікселів."""
    # Випадково визначаємо напрямок руху по осях X та Y у межах 20-40 пікселів.
    offset_x = random.randint(20, 40) * random.choice([-1, 1])
    offset_y = random.randint(20, 40) * random.choice([-1, 1])

    # Для природності залишаємо курсор у кінцевій точці лише на частку секунди.
    pause_duration = random.uniform(0.15, 0.35)

    # Виконуємо плавне переміщення курсора за допомогою ActionChains.
    ActionChains(driver).move_by_offset(offset_x, offset_y).perform()
    time.sleep(pause_duration)

    # Щоб не спричинити небажаних кліків, повертаємо курсор у початкову позицію.
    ActionChains(driver).move_by_offset(-offset_x, -offset_y).perform()
