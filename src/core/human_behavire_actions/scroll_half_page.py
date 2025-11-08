"""Скрол сторінки на пів екрана вниз та назад."""

from __future__ import annotations

import random
import time

from selenium.webdriver.remote.webdriver import WebDriver


def scroll_half_page(driver: WebDriver) -> None:
    """Плавно скролить сторінку на пів екрана вниз і повертає назад."""
    # Отримуємо висоту видимої частини сторінки, щоб розрахувати половину екрана.
    viewport_height = driver.execute_script("return window.innerHeight;")
    half_page = int(viewport_height * random.uniform(0.45, 0.55))

    # Плавний скрол вниз із невеликою паузою — імітація читання контенту.
    driver.execute_script("window.scrollBy({top: arguments[0], behavior: 'smooth'});", half_page)
    time.sleep(random.uniform(0.6, 1.0))

    # Повертаємося назад приблизно на ту саму відстань, ніби користувач перечитує.
    driver.execute_script("window.scrollBy({top: arguments[0], behavior: 'smooth'});", -half_page)
    time.sleep(random.uniform(0.5, 0.9))
