"""Наведення курсора на елемент із короткою паузою."""

from __future__ import annotations

import random
import time
from typing import List

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


SELECTOR_POOL = "a, button, img, [role='button'], input, textarea, [tabindex]"


def _visible_elements(driver: WebDriver) -> List[WebElement]:
    """Повертає список відображуваних елементів, доступних для наведення."""
    elements = driver.find_elements(By.CSS_SELECTOR, SELECTOR_POOL)
    return [element for element in elements if element.is_displayed()]


def hover_pause(driver: WebDriver) -> None:
    """Наводить курсор на елемент і затримує його на 1–3 секунди."""
    # Вибираємо елемент, біля якого користувач міг би зупинитися, щоб щось прочитати.
    visible_elements = _visible_elements(driver)
    if not visible_elements:
        return

    target = random.choice(visible_elements)
    ActionChains(driver).move_to_element(target).perform()

    # Пауза створює враження, що користувач задумався або читає тултіп.
    time.sleep(random.uniform(1.0, 3.0))
