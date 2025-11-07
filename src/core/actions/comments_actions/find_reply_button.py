"""Пошук кнопки відповіді під коментарем."""

from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


REPLY_TEXTS = [
    "reply",
    "відповісти",
    "ответить",
    "відповідь",
]


def find_reply_button(comment_element: WebElement) -> Optional[WebElement]:
    """Повертає видиму кнопку «Reply» для переданого коментаря."""

    selectors = [
        ".//span[@role='button']",
        ".//div[@role='button']",
        ".//a[@role='link']",
    ]

    # Перебираємо кілька типів кнопок, оскільки Facebook змінює верстку залежно від контексту.
    for xpath in selectors:
        try:
            candidates = comment_element.find_elements(By.XPATH, xpath)
        except StaleElementReferenceException:
            return None
        except Exception:
            candidates = []

        for candidate in candidates:
            try:
                if not candidate.is_displayed():
                    continue
                # Порівнюємо текст та aria-label, щоб підтримувати різні локалізації.
                text = (candidate.text or candidate.get_attribute("aria-label") or "").strip().lower()
            except StaleElementReferenceException:
                continue

            if not text:
                continue

            if any(key in text for key in REPLY_TEXTS):
                return candidate

    return None
