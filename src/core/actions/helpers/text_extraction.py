"""Утиліта для зчитування тексту з елементів інтерфейсу."""

from selenium.common.exceptions import JavascriptException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def text_extraction(driver: WebDriver, element: WebElement) -> str:
    """Читає текст коментаря через JavaScript з запасним варіантом Selenium."""

    # Спочатку пробуємо витягнути текст за допомогою JavaScript, бо він краще
    # обробляє приховані переносі рядків та вкладені теги.
    try:
        return (
            driver.execute_script(
                "return arguments[0].innerText || arguments[0].textContent || '';",
                element,
            )
            or ""
        )
    except JavascriptException:
        # Якщо браузер блокує JS-запит, використовуємо стандартне поле text.
        try:
            return element.text or ""
        except Exception:
            # На крайній випадок повертаємо порожній рядок, щоб не зламати цикл.
            return ""
