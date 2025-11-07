"""Визначення встановленої реакції у межах коментаря."""

from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


REACTION_MAP = {
    "like": "Like",
    "love": "Love",
    "care": "Care",
    "haha": "Haha",
    "wow": "Wow",
    "sad": "Sad",
    "angry": "Angry",
}


def comment_reaction_button_state(comment_element: WebElement) -> Optional[str]:
    """Повертає назву реакції (у нижньому регістрі) або None, якщо її немає."""

    candidates = [
        ".//*[@aria-pressed='true']",
        ".//*[starts-with(@aria-label,'Remove ')]",
        ".//*[@aria-checked='true']",
    ]

    # Перевіряємо кілька різних селекторів, бо верстка може змінюватися залежно від типу реакції.
    for xpath in candidates:
        try:
            elements = comment_element.find_elements(By.XPATH, xpath)
        except StaleElementReferenceException:
            return None
        except Exception:
            elements = []

        for element in elements:
            try:
                aria_label = (element.get_attribute("aria-label") or "").strip().lower()
                aria_pressed = (element.get_attribute("aria-pressed") or "").strip().lower()
            except StaleElementReferenceException:
                continue

            if not aria_label:
                continue

            # Якщо aria-label починається з "Remove ..." — Facebook дозволяє зняти
            # вже встановлену реакцію, тому повертаємо її назву.
            if aria_label.startswith("remove "):
                return aria_label.replace("remove ", "", 1).strip()

            # Другий сценарій: кнопка має aria-pressed="true" із назвою реакції.
            # У цьому випадку підбираємо відповідне ключове слово зі словника.
            if aria_pressed == "true":
                for key, value in REACTION_MAP.items():
                    if value.lower() == aria_label:
                        return key

    return None
