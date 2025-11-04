"""Накладання реакції на конкретний коментар."""

from __future__ import annotations

from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from .dom_stability import wait_dom_stable
from .human_pause import human_pause


def like_single_comment(driver: WebDriver, comment_element: WebElement, reaction: str) -> bool:
    """Пробує поставити потрібну реакцію на переданому елементі коментаря."""

    # Дозволений перелік реакцій з відображенням у офіційних aria-label Facebook.
    reaction_map = {
        "like": "Like",
        "love": "Love",
        "care": "Care",
        "haha": "Haha",
        "wow": "Wow",
        "sad": "Sad",
        "angry": "Angry",
    }

    normalized_reaction = (reaction or "like").strip().lower()
    if normalized_reaction not in reaction_map:
        # Якщо користувач вказав щось не зі списку, обираємо дефолтний «лайк».
        print(
            f"[ACTION like_comments] ⚠️ Реакція '{normalized_reaction}' не підтримується. Застосовую 'like'."
        )
        normalized_reaction = "like"

    # Допоміжна функція знаходить кнопку відкриття меню реакцій у межах коментаря.
    def _find_react_button() -> Optional[WebElement]:
        selectors = [
            ".//div[@role='button' and @aria-label='React']",
            ".//span[@role='button' and @aria-label='React']",
            ".//*[@aria-label='React' and (@role='button' or @role='menuitem' or @role='menuitemradio')]",
        ]

        for xpath in selectors:
            try:
                buttons = comment_element.find_elements(By.XPATH, xpath)
            except StaleElementReferenceException:
                return None

            for button in buttons:
                try:
                    if button.is_displayed():
                        return button
                except StaleElementReferenceException:
                    return None
        return None

    # Функція визначає, яка реакція вже стоїть під коментарем.
    def _detect_current_reaction() -> Optional[str]:
        candidates = [
            ".//*[@aria-pressed='true']",
            ".//*[starts-with(@aria-label,'Remove ')]",
        ]

        for xpath in candidates:
            try:
                elements = comment_element.find_elements(By.XPATH, xpath)
            except StaleElementReferenceException:
                return None

            for element in elements:
                try:
                    aria_label = (element.get_attribute("aria-label") or "").strip()
                    aria_pressed = (element.get_attribute("aria-pressed") or "").strip().lower()
                except StaleElementReferenceException:
                    continue

                if not aria_label:
                    continue

                if aria_label.lower().startswith("remove "):
                    return aria_label[7:].strip().lower()

                # Якщо aria-pressed=true та label збігається з назвою реакції — теж повертаємо її.
                if aria_pressed == "true":
                    lowered = aria_label.lower()
                    for key, value in reaction_map.items():
                        if value.lower() == lowered:
                            return key

        return None

    # Універсальний клік по кнопці відкриття меню реакцій.
    def _open_reaction_menu() -> Optional[WebElement]:
        button = _find_react_button()
        if not button:
            print("[ACTION like_comments] ❌ Не знайшов кнопку 'React' у коментарі.")
            return None

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        except Exception:
            pass

        try:
            button.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                print("[ACTION like_comments] ❌ Не вдалося відкрити меню реакцій.")
                return None

        # DOM може перебудовуватися після натискання, тож очікуємо стабілізації.
        wait_dom_stable(driver, timeout=3.0, stable_ms=200)
        human_pause(0.2, 0.35)
        return button

    # Метод клікає по конкретній реакції у глобальному меню.
    def _click_reaction(name: str) -> bool:
        xpath = f"//div[@role='button' and @aria-label='{reaction_map[name]}']"
        try:
            target = driver.find_element(By.XPATH, xpath)
        except Exception:
            print(
                f"[ACTION like_comments] ❌ Не знайшов опцію реакції '{reaction_map[name]}' у меню."
            )
            return False

        try:
            target.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", target)
            except Exception:
                print(
                    f"[ACTION like_comments] ❌ Не вдалося натиснути реакцію '{reaction_map[name]}'."
                )
                return False

        wait_dom_stable(driver, timeout=3.0, stable_ms=200)
        human_pause(0.25, 0.4)
        return True

    # Перевіряємо, чи стоїть вже потрібна реакція, щоб не виконувати зайвих кроків.
    current_reaction = _detect_current_reaction()
    if current_reaction == normalized_reaction:
        print(
            f"[ACTION like_comments] ℹ️ Реакція '{reaction_map[normalized_reaction]}' вже встановлена — пропускаю."
        )
        return True

    # Якщо є інша реакція, спочатку намагаємося її зняти.
    if current_reaction and current_reaction != normalized_reaction:
        print(
            f"[ACTION like_comments] 🔄 Виявив реакцію '{current_reaction}'. Спершу знімаю її."
        )
        if not _open_reaction_menu():
            return False

        remove_xpath = "//div[@role='button' and starts-with(@aria-label,'Remove ')]"
        try:
            options = driver.find_elements(By.XPATH, remove_xpath)
        except Exception:
            options = []

        removed = False
        for option in options:
            try:
                aria_label = (option.get_attribute("aria-label") or "").strip().lower()
            except StaleElementReferenceException:
                continue

            if not aria_label.startswith("remove "):
                continue

            if aria_label.split("remove ", 1)[-1] == current_reaction:
                try:
                    option.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", option)
                    except Exception:
                        continue

                wait_dom_stable(driver, timeout=3.0, stable_ms=200)
                human_pause(0.25, 0.4)
                removed = True
                break

        if not removed:
            print(
                "[ACTION like_comments] ❌ Не вдалося знайти кнопку видалення поточної реакції."
            )
            return False

        current_reaction = _detect_current_reaction()
        if current_reaction:
            print(
                "[ACTION like_comments] ❌ Після спроби зняти реакцію вона все ще активна."
            )
            return False

        print("[ACTION like_comments] ✅ Поточну реакцію успішно знято.")
        human_pause(0.2, 0.35)

    # Відкриваємо меню реакцій та пробуємо встановити потрібний варіант.
    if not _open_reaction_menu():
        return False

    print(
        f"[ACTION like_comments] 👍 Ставлю реакцію '{reaction_map[normalized_reaction]}'."
    )
    if not _click_reaction(normalized_reaction):
        return False

    # Після кліку перевіряємо, що реакція дійсно з'явилася під коментарем.
    final_state = _detect_current_reaction()
    if final_state == normalized_reaction:
        print(
            f"[ACTION like_comments] ✅ Реакцію '{reaction_map[normalized_reaction]}' встановлено успішно."
        )
        return True

    print(
        "[ACTION like_comments] ❌ Не вдалося підтвердити встановлення вибраної реакції."
    )
    return False
