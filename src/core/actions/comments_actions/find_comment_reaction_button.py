"""Пошук кнопки реакції всередині конкретного коментаря."""

from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def find_comment_reaction_button(comment_element: WebElement) -> Optional[WebElement]:
    """Знаходить кнопку відкриття реакцій або прямий лайк у коментарі."""

    # Підтримуємо як класичну кнопку "React", так і спрощені варіанти з написом "Like".
    button_selectors = [
        ".//div[@role='button' and @aria-label='React']",
        ".//span[@role='button' and @aria-label='React']",
        ".//*[@aria-label='React' and (@role='button' or @role='menuitem' or @role='menuitemradio')]",
        ".//div[@role='button' and (@aria-label='Like' or @aria-label='Подобається' or @aria-label='Нравится')]",
        ".//span[@role='button' and (text()='Like' or text()='Подобається' or text()='Нравится')]",
    ]

    # Перебираємо селектори від найточніших до запасних, щоб охопити всі локалізації.
    for xpath in button_selectors:
        try:
            buttons = comment_element.find_elements(By.XPATH, xpath)
        except StaleElementReferenceException:
            return None
        except Exception:
            buttons = []

        for button in buttons:
            try:
                # Обираємо лише видимі елементи, інакше клік просто не спрацює.
                if button.is_displayed():
                    return button
            except StaleElementReferenceException:
                return None

    return None
