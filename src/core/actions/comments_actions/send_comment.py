"""Надсилання написаного коментаря або відповіді."""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver


def send_comment(
    driver: WebDriver,
    expected_text: str | None = None,
    label: str = "коментар",
) -> bool:
    """Відправляє коментар через Enter або явну кнопку."""

    print(f"[ACTION comments] 📩 Відправляю {label}...")

    def _is_posted() -> bool:
        """Перевіряє, що текст реально з'явився в розмітці сторінки."""
        if not expected_text:
            return True
        try:
            return expected_text[:8] in driver.page_source
        except Exception:
            return False

    try:
        # Найнадійніший спосіб — симулювати натискання клавіші Enter через CDP.
        driver.execute_cdp_cmd(
            "Input.dispatchKeyEvent",
            {
                "type": "keyDown",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            },
        )
        driver.execute_cdp_cmd(
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                "key": "Enter",
                "code": "Enter",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
            },
        )
        time.sleep(2)
        if _is_posted():
            print(
                f"[ACTION comments] ✅ {label.capitalize()} надіслано через CDP Enter."
            )
            return True
    except Exception:
        pass

    try:
        # Якщо CDP недоступний, дублюємо поведінку через активний елемент Selenium.
        active = driver.switch_to.active_element
        active.send_keys(Keys.ENTER)
        time.sleep(2)
        if _is_posted():
            print(
                f"[ACTION comments] ✅ {label.capitalize()} надіслано через Selenium Enter."
            )
            return True
    except Exception:
        pass

    button_selectors = [
        "//div[@role='button' and (text()='Post' or text()='Comment' or text()='Опублікувати' or text()='Коментувати' or text()='Надіслати')]",
        "//div[@role='button' and (@aria-label='Post' or @aria-label='Comment' or @aria-label='Опублікувати' or @aria-label='Коментувати' or @aria-label='Надіслати')]",
        "//div[@role='button'][contains(@aria-label,'Post')]",
        "//div[@role='button'][contains(@aria-label,'Comment')]",
    ]

    for xpath in button_selectors:
        try:
            buttons = driver.find_elements(By.XPATH, xpath)
        except Exception:
            buttons = []
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                # На крайній випадок клікаємо по кнопці відправки, якщо клавіатура не спрацювала.
                try:
                    button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
                if _is_posted():
                    print(
                        f"[ACTION comments] ✅ {label.capitalize()} надіслано через кнопку."
                    )
                    return True
            except Exception:
                continue

    print(
        f"[ACTION comments] ❌ Не вдалося надіслати {label} жодним зі способів."
    )
    return False
