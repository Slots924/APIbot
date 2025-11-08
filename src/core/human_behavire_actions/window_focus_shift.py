"""Імітація переключення фокусу між вікнами."""

from __future__ import annotations

import random
import time

from selenium.webdriver.remote.webdriver import WebDriver


def window_focus_shift(driver: WebDriver, *, min_pause: float = 1.5, max_pause: float = 3.5) -> None:
    """Тимчасово знімає фокус із поточного вікна, ніби користувач відволікся."""
    # Ініціюємо втрату фокусу через JavaScript, щоб браузер «подумав», що користувач перемкнувся.
    driver.execute_script("window.blur();")

    # Робимо паузу — користувач ніби працює в іншій вкладці чи застосунку.
    time.sleep(random.uniform(min_pause, max_pause))

    # Повертаємо фокус на поточне вікно, щоб продовжити основний сценарій роботи.
    driver.execute_script("window.focus();")
    driver.switch_to.window(driver.current_window_handle)
