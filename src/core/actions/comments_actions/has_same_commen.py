"""Перевірка наявності дубліката коментаря у стрічці."""

from __future__ import annotations

from typing import Iterable

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..helpers import text_extraction, text_normmalization
from .collect_comments import collect_comments


def has_same_comment(
    driver: WebDriver,
    target_text: str,
    containers: Iterable[WebElement] | None = None,
) -> tuple[str, bool]:
    """Повертає нормалізований текст і факт наявності такого коментаря."""

    # Нормалізуємо текст, щоб порівняння було нечутливим до регістру та пробілів.
    normalized_target = text_normmalization(target_text)
    if not normalized_target:
        # Якщо після нормалізації текст порожній — немає сенсу шукати збігів.
        return "", False

    # Робимо список з переданої колекції або збираємо коментарі самостійно,
    # щоб мати можливість багаторазово проходити по елементах.
    comment_containers = list(containers or collect_comments(driver))

    for element in comment_containers:
        try:
            # Витягуємо сирий текст коментаря навіть із вкладеної розмітки.
            existing_text = text_extraction(driver, element)
        except StaleElementReferenceException:
            # Якщо DOM оновився і елемент застарів — пропускаємо його.
            continue

        # Приводимо поточний текст до такої самої нормалізованої форми.
        normalized_existing = text_normmalization(existing_text)
        if normalized_existing == normalized_target:
            # Як тільки знайшли повний збіг — повертаємо успіх.
            return normalized_target, True

    # Якщо жоден коментар не співпав із цільовим текстом — повідомляємо про відсутність.
    return normalized_target, False
