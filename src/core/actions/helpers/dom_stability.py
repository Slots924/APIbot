"""Очікування стабільності DOM після завантаження коментарів."""

import time

from selenium.common.exceptions import JavascriptException
from selenium.webdriver.remote.webdriver import WebDriver

from .human_pause import human_pause


def dom_stability(driver: WebDriver, timeout: float = 15.0, stable_ms: int = 600) -> bool:
    """Очікує, доки розмітка сторінки перестане активно змінюватися."""

    # Фіксуємо кінцевий момент очікування, щоб не зависнути назавжди.
    end_time = time.time() + timeout
    last_length: int | None = None
    stable_since: float | None = None

    while time.time() < end_time:
        try:
            # Отримуємо довжину HTML-документа. Якщо вона не змінюється,
            # то DOM стабілізувався і можна працювати далі.
            html_length = int(
                driver.execute_script(
                    "return document.documentElement.outerHTML.length || 0;"
                )
            )
        except JavascriptException:
            # Якщо JS виклик не вдався, робимо невелику паузу і повторюємо.
            human_pause(0.2, 0.4)
            continue

        now = time.time()
        if last_length == html_length:
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) * 1000 >= stable_ms:
                return True
        else:
            last_length = html_length
            stable_since = None

        human_pause(0.12, 0.25)

    return False
