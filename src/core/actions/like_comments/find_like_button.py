"""Пошук кнопки реакції всередині конкретного коментаря."""

from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def find_like_button(comment_element: WebElement) -> Optional[WebElement]:
    """Шукає доступну кнопку лайка і повертає її, якщо вона видима."""

    # Для різних мовних локалізацій Facebook використовуємо кілька XPath-виразів.
    button_selectors = [
        "./descendant::div[@role='button' and (@aria-label='Like' or @aria-label='Подобається' or @aria-label='Нравится' or @aria-label='Me gusta' or @aria-label='J’aime')]",
        "./descendant::span[@role='button' and (text()='Like' or text()='Подобається' or text()='Нравится' or text()='Me gusta' or text()='J’aime')]",
        "./descendant::div[@role='button'][.//span[text()='Like' or text()='Подобається' or text()='Нравится' or text()='Me gusta' or text()='J’aime']]",
    ]

    for xpath in button_selectors:
        try:
            buttons = comment_element.find_elements(By.XPATH, xpath)
        except StaleElementReferenceException:
            return None
        except Exception:
            buttons = []

        for button in buttons:
            try:
                if button.is_displayed():
                    return button
            except StaleElementReferenceException:
                return None

    return None
