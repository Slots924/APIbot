"""Перевірка стану кнопки лайка."""

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement


def is_button_liked(button: WebElement) -> bool:
    """Визначає, чи вже встановлено реакцію «Подобається» на кнопці."""

    try:
        aria_state = (
            (button.get_attribute("aria-pressed") or button.get_attribute("aria-checked") or "").lower()
        )
        if aria_state == "true":
            return True
    except StaleElementReferenceException:
        return False

    try:
        class_state = (button.get_attribute("class") or "").lower()
        if any(keyword in class_state for keyword in ["active", "liked", "press"]):
            return True
    except StaleElementReferenceException:
        return False

    try:
        aria_label = (button.get_attribute("aria-label") or "").lower()
        if any(flag in aria_label for flag in ["remove like", "liked", "reaction"]):
            return True
    except StaleElementReferenceException:
        return False

    return False
