"""Натискання кнопки відповіді під коментарем."""

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from ..helpers import dom_stability, human_pause


def press_reply_button(driver: WebDriver, reply_button: WebElement) -> bool:
    """Скролить до кнопки «Reply» та натискає її кількома способами."""

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reply_button)
    except Exception:
        pass

    for attempt in range(1, 4):
        # Пробуємо натиснути кнопку кілька разів, адже інтерфейс може блокувати перші кліки.
        try:
            reply_button.click()
            dom_stability(driver, timeout=3.0, stable_ms=200)
            human_pause(0.2, 0.35)
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", reply_button)
                dom_stability(driver, timeout=3.0, stable_ms=200)
                human_pause(0.2, 0.35)
                return True
            except Exception:
                print(
                    f"[ACTION comments] ⚠️ Не вдалося натиснути кнопку відповіді (спроба {attempt})."
                )
                human_pause(0.2, 0.35)

    return False
