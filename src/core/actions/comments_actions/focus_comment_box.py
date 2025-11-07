"""Фокусування основного поля введення коментаря."""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def focus_comment_box(driver: WebDriver) -> bool:
    """Шукає і активує поле для нового коментаря."""

    selectors = [
        (By.CSS_SELECTOR, "div[aria-label='Leave a comment'][contenteditable='true']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"),
        (By.XPATH, "//div[@contenteditable='true']"),
    ]

    # Виконуємо кілька ітерацій, щоб пережити можливі перерендери поля на сторінці.
    for _ in range(5):
        for by, sel in selectors:
            try:
                elems = driver.find_elements(by, sel)
            except Exception:
                elems = []
            for el in elems:
                try:
                    if not el.is_displayed():
                        continue
                    # Спочатку пробуємо звичайний клік, а якщо не вийшло — прокручуємо до поля.
                    try:
                        el.click()
                    except Exception:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", el)
                    time.sleep(1.0)
                    return True
                except Exception:
                    continue
        time.sleep(1)

    return False
