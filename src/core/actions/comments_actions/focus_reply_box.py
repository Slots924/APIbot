"""Фокусування поля відповіді на коментар."""

import time

from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def focus_reply_box(
    driver: WebDriver, comment_element: Optional[WebElement] = None
) -> bool:
    """Активує поле введення відповіді у вибраному коментарі."""

    selectors = [
        "//div[@contenteditable='true' and @role='textbox']",
        "//div[@contenteditable='true']",
    ]

    scope = comment_element if comment_element is not None else driver

    # Робимо декілька спроб, адже після натискання кнопки Reply поле може з'явитися із затримкою.
    for _ in range(5):
        for xpath in selectors:
            try:
                elements = scope.find_elements(By.XPATH, xpath)
            except Exception:
                elements = []
            for element in elements:
                try:
                    if not element.is_displayed():
                        continue
                    # Аналогічно до фокусу основного поля: пробуємо клік, а за потреби докручуємо.
                    try:
                        element.click()
                    except Exception:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", element
                        )
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", element)
                    time.sleep(0.5)
                    return True
                except Exception:
                    continue
        time.sleep(0.6)

    return False
