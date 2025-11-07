"""Пошук елементів коментарів на сторінці."""

from typing import List

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def collect_comments(driver: WebDriver) -> List[WebElement]:
    """Повертає список видимих контейнерів коментарів (включно з реплаями)."""

    container_patterns = [
        "//div[@role='article'][.//a[contains(@href,'comment_id=')]]",
        "//div[@role='article'][.//a[contains(@href,'reply_comment_id=')]]",
        "//div[@role='article'][.//div[@role='button']]",
        "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
        "//div[contains(@data-ad-preview,'comment') or @data-visualcompletion='ignore-dynamic'][.//*[@role='button']]",
    ]

    containers: List[WebElement] = []
    seen_keys: set[str] = set()

    # Перебираємо набір селекторів, щоб підтримувати різні версії DOM Facebook.
    for xpath in container_patterns:
        try:
            candidates = driver.find_elements(By.XPATH, xpath)
        except Exception:
            continue

        for element in candidates:
            try:
                if not element.is_displayed():
                    continue

                aria = element.get_attribute("aria-label") or ""
                key = aria.strip()

                if not key:
                    # Якщо aria-label відсутній, беремо частину тексту елемента для унікальності.
                    key = (element.text or "")[:50]

                if key in seen_keys:
                    continue

                # Запам'ятовуємо ключ, щоб не додавати дублікати у фінальний список.
                seen_keys.add(key)
                containers.append(element)

            except StaleElementReferenceException:
                continue

    return containers
