"""Допоміжні утиліти для перевірки та встановлення реакцій на пості Facebook."""

import time
from typing import Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

        # Кнопка може мати різні підписи («Like», «React», «Change Love reaction»).
        # Вистачає перевірки ключових фраз, щоб впевнитися, що ми працюємо саме з тригером меню.
        if any(keyword in aria for keyword in ("like", "react", "change")):
            return button

    # Якщо жоден маркер не відпрацював (Facebook міг змінити структуру DOM),
    # пробуємо знайти кнопку безпосередньо за aria-label, як радить документація з селекторами.
    fallback_selectors = [
        "div[role='button'][aria-label^='Change '][aria-label$=' reaction']",
        "div[role='button'][aria-label='React']",
    ]

    for selector in fallback_selectors:
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            candidates = []

        if candidates:
            return candidates[0]

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


def _match_known_reaction(raw_value: str) -> Optional[str]:
    """Повертає ключ реакції за її текстовим підписом у aria-label."""

    normalized_value = (raw_value or "").strip().lower()
    if not normalized_value:
        return None

    for reaction, labels in REACTION_LABELS.items():
        for label in labels:
            if normalized_value == label.lower():
                return reaction

    return None


def _extract_reaction_from_label(aria_label: str) -> Optional[str]:
    """Аналізує aria-label кнопки та повертає назву активної реакції."""

    label = (aria_label or "").strip()
    if not label:
        return None

    lower_label = label.lower()

    # Формат «Change Love reaction» (основна кнопка під постом).
    if lower_label.startswith("change ") and lower_label.endswith(" reaction"):
        reaction_part = label[7:-9].strip()
        return _match_known_reaction(reaction_part)

    # Формат «Remove Love» (кнопка у відкритому меню реакцій).
    if lower_label.startswith("remove "):
        reaction_part = label[7:].strip()
        return _match_known_reaction(reaction_part)

    return None


def check_reaction_state(driver: WebDriver) -> Optional[str]:
    """Визначає, яка реакція зараз активна на пості (якщо така є)."""

    button = _find_like_button(driver)
    if button is None:
        return None

    try:
        aria_label = button.get_attribute("aria-label") or ""
    except Exception:
        return None

    reaction_from_button = _extract_reaction_from_label(aria_label)
    if reaction_from_button:
        return reaction_from_button

    # Якщо головна кнопка повідомляє лише «React», відкритої реакції немає.
    if aria_label and aria_label.strip().lower() == "react":
        return None

    # На випадок, коли назва реакції прихована, додатково шукаємо кнопку зняття реакції у меню.
    if _open_reaction_menu(driver, button):
        try:
            remove_button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div[role='button'][aria-label^='Remove ']",
                    )
                )
            )
            reaction = _extract_reaction_from_label(remove_button.get_attribute("aria-label") or "")
            return reaction
        except TimeoutException:
            return None
        finally:
            # Невелика пауза, щоб меню встигло сховатися перед подальшими кроками.
            time.sleep(0.2)

    return None


def _open_reaction_menu(driver: WebDriver, button: WebElement) -> bool:
    """Пробує відкрити меню реакцій через наведення на кнопку з повторними спробами."""

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
    except Exception:
        pass

    for attempt in range(3):
        try:
            # Наводимо курсор на кнопку, даючи Facebook час підготувати меню.
            ActionChains(driver).move_to_element(button).pause(0.6).perform()
        except Exception:
            try:
                # Якщо наведенню щось завадило, клікаємо по кнопці як запасний варіант.
                button.click()
            except Exception:
                pass

        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='button'][aria-label='Like']")
                )
            )
            return True
        except TimeoutException:
            time.sleep(0.3)

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
        element = _wait_for_reaction_option(driver, label)
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


def _wait_for_reaction_option(driver: WebDriver, label: str) -> Optional[WebElement]:
    """Шукає кнопку реакції у відкритому меню, використовуючи рекомендовані селектори."""

    selectors = [
        (By.CSS_SELECTOR, f"div[role='button'][aria-label='{label}']"),
        (
            By.XPATH,
            f"//*[@aria-label='{label}' and (@role='button' or @role='menuitem' or @role='menuitemradio')]",
        ),
        (By.XPATH, f"//*[contains(@aria-label, '{label}')]")
    ]

    for by, value in selectors:
        try:
            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            continue

    return None

