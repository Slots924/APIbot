"""Пошук елементів коментарів на сторінці."""

from typing import List

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def collect_comment_containers(driver: WebDriver) -> List[WebElement]:
    """
    Повертає список видимих контейнерів коментарів (включно з реплаями),
    які містять comment_id або reply_comment_id.
    """

    # ✅ Нові найточніші селектори (мовонезалежні)
    container_patterns = [
        # 1) Головний: будь-який comment або reply, який має comment_id
        "//div[@role='article'][.//a[contains(@href,'comment_id=')]]",

        # 2) Реплаї, якщо Facebook раптом розділить DOM (страховка)
        "//div[@role='article'][.//a[contains(@href,'reply_comment_id=')]]",

        # 🧰 СТАРІ СЕЛЕКТОРИ — залишаємо як fallback
        "//div[@role='article'][.//div[@role='button']]",
        "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
        "//div[contains(@data-ad-preview,'comment') or @data-visualcompletion='ignore-dynamic'][.//*[@role='button']]",
    ]

    containers: List[WebElement] = []
    seen_keys: set[str] = set()  # унікальність коментів

    for xpath in container_patterns:
        try:
            candidates = driver.find_elements(By.XPATH, xpath)
        except Exception:
            candidates = []
            continue

        for element in candidates:
            try:
                if not element.is_displayed():
                    continue

                # Унікальний ключ для дедупу — беремо aria-label або href comment_id
                aria = element.get_attribute("aria-label") or ""
                key = aria.strip()

                if not key:
                    # fallback: беремо частину outerHTML як hash
                    key = (element.text or "")[:50]

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                containers.append(element)

            except StaleElementReferenceException:
                continue

    return containers
