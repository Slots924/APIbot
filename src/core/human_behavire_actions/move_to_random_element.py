"""Переміщення курсора до випадкового видимого елемента."""

from __future__ import annotations

import random
import time
from typing import List

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


SELECTOR_POOL = "a, button, img, [role='button'], input, textarea, [tabindex]"


def _collect_visible_elements(driver: WebDriver) -> List[WebElement]:
    """Повертає список елементів, які відображаються на екрані."""
    candidates = driver.find_elements(By.CSS_SELECTOR, SELECTOR_POOL)
    visible = [element for element in candidates if element.is_displayed()]
    return visible


def move_to_random_element(driver: WebDriver) -> None:
    """Наводить курсор на випадковий видимий елемент сторінки."""
    # Збираємо всі потенційні елементи, на які користувач міг би навести курсор.
    visible_elements = _collect_visible_elements(driver)
    if not visible_elements:
        return

    # Обираємо випадковий елемент і плавно наводимо на нього курсор.
    target = random.choice(visible_elements)
    ActionChains(driver).move_to_element(target).perform()

    # Затримуємо курсор, наче користувач уважно розглядає елемент.
    time.sleep(random.uniform(0.6, 1.2))
