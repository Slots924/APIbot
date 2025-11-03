"""Пошук елементів коментарів на сторінці."""

from typing import List

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def collect_comment_containers(driver: WebDriver) -> List[WebElement]:
    """Повертає список видимих контейнерів коментарів з кнопками реакцій."""

    # Шаблони розташування коментарів різняться залежно від версії Facebook,
    # тому підбираємо декілька XPath, які покривають найпопулярніші DOM-структури.
    container_patterns = [
        "//div[@role='article'][.//div[@role='button']]",
        "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
        "//div[contains(@data-ad-preview,'comment') or @data-visualcompletion='ignore-dynamic'][.//*[@role='button']]",
    ]

    containers: List[WebElement] = []
    seen_ids: set[str | None] = set()

    for xpath in container_patterns:
        try:
            candidates = driver.find_elements(By.XPATH, xpath)
        except Exception:
            candidates = []

        for element in candidates:
            try:
                if not element.is_displayed():
                    continue
                element_id = getattr(element, "id", None)
                if element_id in seen_ids:
                    continue
                seen_ids.add(element_id)
                containers.append(element)
            except StaleElementReferenceException:
                continue

    return containers
