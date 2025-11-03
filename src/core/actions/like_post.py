"""Логіка встановлення лайка на пості Facebook."""

import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


# ----------------- ХЕЛПЕРИ -----------------


def _find_like_button(driver, timeout: float = 12.0) -> Optional[WebElement]:
    """Повертає головну кнопку лайка, яка містить маркер data-ad-rendering-role."""

    finish_time = time.time() + timeout
    has_scrolled = False

    while time.time() < finish_time:
        try:
            markers = driver.find_elements(By.CSS_SELECTOR, "[data-ad-rendering-role='like_button']")
        except Exception:
            markers = []

        for marker in markers:
            try:
                button = marker.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
                aria = (button.get_attribute("aria-label") or "").lower()
                if "like" in aria:
                    return button
            except Exception:
                continue

        if not has_scrolled:
            try:
                driver.execute_script("window.scrollBy(0, 450);")
            except Exception:
                pass
            has_scrolled = True

        time.sleep(0.4)

    return None


def _read_like_state(button: WebElement) -> Optional[bool]:
    """Зчитує стан лайка з aria-label кнопки."""

    try:
        aria = (button.get_attribute("aria-label") or "").lower()
    except Exception:
        return None

    if "remove like" in aria:
        return True
    if "like" in aria:
        return False
    return None


def _click_like_button(driver, button: WebElement) -> bool:
    """Плавно клікає по кнопці лайка з прокруткою та JS-фолбеком."""

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.3)
    except Exception:
        pass

    try:
        button.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", button)
            return True
        except Exception:
            return False


# ----------------- ГОЛОВНА ФУНКЦІЯ -----------------


def like_post(driver, timeout: float = 12.0) -> bool:
    """Перевіряє стан лайка, за потреби ставить його та підтверджує результат."""

    print("[ACTION like_post] 🚀 Починаю перевірку кнопки лайка.")

    button = _find_like_button(driver, timeout=timeout)
    if button is None:
        print("[ACTION like_post] ❌ Не вдалося знайти контейнер з кнопкою лайка.")
        return False

    current_state = _read_like_state(button)
    if current_state is True:
        print("[ACTION like_post] ⭐ Лайк вже стоїть — додаткові дії не потрібні.")
    elif current_state is False:
        print("[ACTION like_post] 👍 Лайка ще немає — ставлю реакцію.")
        if not _click_like_button(driver, button):
            print("[ACTION like_post] ❌ Не вдалося натиснути кнопку лайка.")
            return False
        time.sleep(1.2)
        button = _find_like_button(driver, timeout=6.0)
        if button is None:
            print("[ACTION like_post] ❌ Після кліку не знайшов кнопку для повторної перевірки.")
            return False
    else:
        print("[ACTION like_post] ⚠️ Не зміг зчитати стан лайка одразу, пробую натиснути для синхронізації.")
        if not _click_like_button(driver, button):
            print("[ACTION like_post] ❌ Не вдалося натиснути кнопку лайка.")
            return False
        time.sleep(1.2)
        button = _find_like_button(driver, timeout=6.0)
        if button is None:
            print("[ACTION like_post] ❌ Після повторної спроби кнопка зникла з DOM.")
            return False

    final_state = _read_like_state(button)
    if final_state is True:
        print("[ACTION like_post] ✅ Лайк стоїть.")
        return True

    print("[ACTION like_post] ❌ Не вдалося підтвердити, що лайк стоїть.")
    return False
