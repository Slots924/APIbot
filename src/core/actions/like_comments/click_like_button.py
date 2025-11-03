"""Клік по кнопці лайка з кількома сценаріями резервного доступу."""

from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from .human_pause import human_pause


def click_like_button(driver: WebDriver, button: WebElement) -> bool:
    """Пробує натиснути кнопку лайка з кількома повторними спробами."""

    for attempt in range(1, 4):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
            human_pause(0.1, 0.25)
            button.click()
            human_pause(0.25, 0.45)
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", button)
                human_pause(0.25, 0.45)
                return True
            except Exception:
                pass
        except Exception:
            pass

        print(
            f"[ACTION like_comments] ⚠️ Не вдалося натиснути кнопку лайка (спроба {attempt})."
        )
        human_pause(0.25, 0.5)

    return False
