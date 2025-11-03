"""Логіка встановлення лайка на пості Facebook."""

import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


# ----------------- ХЕЛПЕРИ -----------------


def _find_like_button(driver) -> Optional[WebElement]:
    """Повертає головну кнопку лайка на основі маркера `data-ad-rendering-role`."""

    # Використовуємо ту ж саму вибірку, що і у `quick_like2`,
    # адже вона надійно знаходить саме потрібну кнопку без промахів по контейнерах.
    try:
        markers = driver.find_elements(By.CSS_SELECTOR, "[data-ad-rendering-role='like_button']")
    except Exception:
        return None

    for marker in markers:
        try:
            button = marker.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
            aria = (button.get_attribute("aria-label") or "").lower()
            if "like" in aria:
                return button
        except Exception:
            # Якщо для конкретного маркера щось пішло не так — пропускаємо його.
            continue

    return None


def _read_like_state(driver) -> Optional[bool]:
    """Зчитує стан лайка так само, як у `quick_like2.is_liked`."""

    button = _find_like_button(driver)
    if button is None:
        return None

    try:
        aria = (button.get_attribute("aria-label") or "").lower()
    except Exception:
        return None

    if "remove like" in aria:
        return True
    if "like" in aria:
        return False
    return None


def _click_like_button(driver) -> bool:
    """Викликає натискання кнопки з плавною прокруткою, як у `quick_like2.click_like`."""

    button = _find_like_button(driver)
    if button is None:
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        time.sleep(0.3)
        button.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", button)
            return True
        except Exception:
            return False


# ----------------- ГОЛОВНА ФУНКЦІЯ -----------------


def like_post(driver, attempts: int = 3) -> bool:
    """Перевіряє стан лайка, за потреби ставить його та підтверджує результат."""

    print("[ACTION like_post] 🚀 Починаю перевірку кнопки лайка.")

    initial_state = _read_like_state(driver)
    if initial_state is None:
        print("[ACTION like_post] ❌ Не вдалося знайти кнопку лайка в DOM.")
        return False

    if initial_state is True:
        print("[ACTION like_post] ⭐ Лайк вже стоїть — додаткові дії не потрібні.")
        return True

    print("[ACTION like_post] 👍 Лайка ще немає — ставлю реакцію.")

    for attempt in range(1, attempts + 1):
        if not _click_like_button(driver):
            print(f"[ACTION like_post] ❌ Не вдалося натиснути кнопку лайка (спроба {attempt}).")
            continue

        time.sleep(1.2)
        state_after_click = _read_like_state(driver)
        print(f"[ACTION like_post] 🔁 Перевіряю стан після кліку: {state_after_click} (спроба {attempt}).")

        if state_after_click is True:
            print("[ACTION like_post] ✅ Лайк успішно поставлено.")
            return True

        if state_after_click is None:
            print("[ACTION like_post] ⚠️ Кнопка тимчасово недоступна, пробую ще раз.")

    print("[ACTION like_post] ❌ Не вдалося підтвердити, що лайк стоїть.")
    return False
