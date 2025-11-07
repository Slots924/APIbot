"""Перевірка присутності коментаря у DOM."""

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement


def check_comment_exist(comment_element: WebElement) -> bool:
    """Повертає True, якщо коментар все ще існує та відображається."""

    try:
        # Доступ до tag_name дозволяє швидко виявити, чи елемент вже видалений із DOM.
        _ = comment_element.tag_name
        return comment_element.is_displayed()
    except StaleElementReferenceException:
        return False
    except Exception:
        return False
