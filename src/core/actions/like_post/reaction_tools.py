"""Допоміжні утиліти для перевірки та встановлення реакцій на пості Facebook."""

import time
from typing import Optional

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


# Словник з відомими реакціями та можливими aria-лейблами меню.
# Підтримуємо базові реакції, які найчастіше використовуються у Facebook.
REACTION_LABELS = {
    "like": ["Like"],
    "love": ["Love"],
    "care": ["Care"],
    "haha": ["Haha"],
    "wow": ["Wow"],
    "sad": ["Sad"],
    "angry": ["Angry"],
}


def _find_like_button(driver: WebDriver) -> Optional[WebElement]:
    """Повертає головну кнопку реакцій під постом."""

    # Шукаємо усі маркери з data-атрибутом, який Facebook навішує на контейнер лайка.
    try:
        markers = driver.find_elements(By.CSS_SELECTOR, "[data-ad-rendering-role='like_button']")
    except Exception:
        return None

    # Для кожного маркера намагаємося знайти найближчий предок-кнопку з role="button".
    for marker in markers:
        try:
            button = marker.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
        except Exception:
            continue

        try:
            aria = (button.get_attribute("aria-label") or "").lower()
        except Exception:
            aria = ""

        # Якщо aria-label містить слово "like", то це саме потрібна кнопка.
        if "like" in aria:
            return button

    return None


def check_like_state(driver: WebDriver) -> Optional[bool]:
    """Зчитує стан класичного лайка (натиснуто / не натиснуто)."""

    button = _find_like_button(driver)
    if button is None:
        return None

    try:
        aria_pressed = button.get_attribute("aria-pressed")
        aria_label = (button.get_attribute("aria-label") or "").lower()
    except Exception:
        return None

    # Якщо aria-pressed є валідним булевим значенням — використовуємо його напряму.
    if aria_pressed in {"true", "false"}:
        return aria_pressed == "true"

    # Якщо Facebook в aria-label дозволяє «Remove Like», вважаємо, що лайк встановлено.
    if "remove like" in aria_label:
        return True

    # Якщо бачимо лише «Like» без «Remove» — лайк ще не поставлено.
    if "like" in aria_label:
        return False

    return None


def check_reaction_state(driver: WebDriver) -> Optional[str]:
    """Визначає, яка реакція зараз активна на пості (якщо така є)."""

    button = _find_like_button(driver)
    if button is None:
        return None

    try:
        aria_label = (button.get_attribute("aria-label") or "").lower()
    except Exception:
        return None

    # Якщо aria-label містить слово "remove", Facebook повідомляє про активну реакцію.
    if "remove" not in aria_label:
        return None

    for reaction in REACTION_LABELS:
        if reaction in aria_label:
            return reaction

    return None


def _open_reaction_menu(driver: WebDriver, button: WebElement) -> bool:
    """Пробує відкрити меню реакцій через наведення на кнопку."""

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
    except Exception:
        pass

    try:
        ActionChains(driver).move_to_element(button).pause(0.6).perform()
        time.sleep(0.6)
        return True
    except Exception:
        return False


def _click_via_js(driver: WebDriver, element: WebElement) -> bool:
    """Fallback-клік через JavaScript на випадок, якщо звичайний click не спрацює."""

    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception:
        return False


def set_reaction(driver: WebDriver, reaction: str) -> bool:
    """Встановлює потрібну реакцію на пості."""

    normalized_reaction = (reaction or "like").strip().lower()
    if normalized_reaction not in REACTION_LABELS:
        print(
            f"[ACTION like_post] ⚠️ Реакція '{normalized_reaction}' не підтримується. Використовую 'like'."
        )
        normalized_reaction = "like"

    button = _find_like_button(driver)
    if button is None:
        print("[ACTION like_post] ❌ Не вдалося знайти кнопку реакцій для встановлення.")
        return False

    # Якщо потрібен звичайний лайк — достатньо кліку по кнопці.
    if normalized_reaction == "like":
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
            time.sleep(0.3)
            button.click()
            print("[ACTION like_post] 🖱️ Натиснув кнопку лайка для встановлення реакції.")
            return True
        except Exception:
            if _click_via_js(driver, button):
                print("[ACTION like_post] 🖱️ Застосував JS-клік для натискання кнопки лайка.")
                return True
            return False

    print(
        f"[ACTION like_post] 🧭 Відкриваю меню реакцій для встановлення '{normalized_reaction}'."
    )

    if not _open_reaction_menu(driver, button):
        print("[ACTION like_post] ❌ Не вдалося відкрити меню реакцій.")
        return False

    possible_labels = REACTION_LABELS[normalized_reaction]
    for label in possible_labels:
        # Шукаємо реакцію в меню за aria-label. Використовуємо contains для підстраховки.
        xpath_exact = f"//div[@role='menu']//div[@aria-label='{label}']"
        xpath_partial = f"//div[@role='menu']//div[contains(@aria-label, '{label}')]"

        try:
            element = driver.find_element(By.XPATH, xpath_exact)
        except Exception:
            try:
                element = driver.find_element(By.XPATH, xpath_partial)
            except Exception:
                element = None

        if not element:
            continue

        try:
            element.click()
            print(
                f"[ACTION like_post] 🖱️ Обрав реакцію '{normalized_reaction}' у меню."
            )
            return True
        except Exception:
            if _click_via_js(driver, element):
                print(
                    f"[ACTION like_post] 🖱️ Обрав реакцію '{normalized_reaction}' через JS-клік."
                )
                return True

    print(
        f"[ACTION like_post] ❌ Не вдалося знайти елемент реакції '{normalized_reaction}' у меню."
    )
    return False

