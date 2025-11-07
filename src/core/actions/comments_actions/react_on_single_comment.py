"""Накладання реакції на конкретний коментар."""

from __future__ import annotations

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from ..helpers import dom_stability, human_pause
from .comment_reaction_button_state import REACTION_MAP, comment_reaction_button_state
from .find_comment_reaction_button import find_comment_reaction_button


def react_on_single_comment(
    driver: WebDriver, comment_element: WebElement, reaction: str = "like"
) -> bool:
    """Пробує поставити потрібну реакцію на переданому елементі коментаря."""

    # Приводимо реакцію до нижнього регістру, щоб працювати з єдиним форматом.
    normalized_reaction = (reaction or "like").strip().lower()
    if normalized_reaction not in REACTION_MAP:
        print(
            f"[ACTION comments] ⚠️ Реакція '{normalized_reaction}' не підтримується. Застосовую 'like'."
        )
        normalized_reaction = "like"

    current_reaction = comment_reaction_button_state(comment_element)
    if current_reaction == normalized_reaction:
        print(
            f"[ACTION comments] ℹ️ Реакція '{REACTION_MAP[normalized_reaction]}' вже встановлена — пропускаю."
        )
        return True

    button = find_comment_reaction_button(comment_element)
    if not button:
        print("[ACTION comments] ❌ Не знайшов кнопку реакцій у коментарі.")
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
    except Exception:
        pass

    button_label = (button.get_attribute("aria-label") or button.text or "").lower()
    has_reaction_menu = "react" in button_label

    # Якщо меню з реакціями недоступне, то можемо поставити тільки стандартний лайк.
    if not has_reaction_menu and normalized_reaction != "like":
        print(
            "[ACTION comments] ❌ Меню реакцій недоступне, тому можу поставити лише звичайний лайк."
        )
        return False

    if not has_reaction_menu:
        if current_reaction:
            print("[ACTION comments] 🔄 Скидаю поточну реакцію повторним натисканням на кнопку лайка.")
        try:
            button.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                print("[ACTION comments] ❌ Не вдалося натиснути кнопку лайка.")
                return False
        dom_stability(driver, timeout=3.0, stable_ms=200)
        human_pause(0.25, 0.4)
        final_state = comment_reaction_button_state(comment_element)
        if final_state == "like":
            print("[ACTION comments] ✅ Реакцію 'Like' встановлено успішно.")
            return True
        print("[ACTION comments] ❌ Не вдалося підтвердити встановлення лайка.")
        return False

    def _open_reaction_menu() -> bool:
        """Допоміжна функція, що відкриває попап з реакціями."""
        try:
            button.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                print("[ACTION comments] ❌ Не вдалося відкрити меню реакцій.")
                return False
        dom_stability(driver, timeout=3.0, stable_ms=200)
        human_pause(0.2, 0.35)
        return True

    def _click_reaction(name: str) -> bool:
        """Натискає потрібну реакцію у глобальному меню."""
        xpath = f"//div[@role='button' and @aria-label='{REACTION_MAP[name]}']"
        try:
            target = driver.find_element(By.XPATH, xpath)
        except Exception:
            print(
                f"[ACTION comments] ❌ Не знайшов опцію реакції '{REACTION_MAP[name]}' у меню."
            )
            return False

        try:
            target.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", target)
            except Exception:
                print(
                    f"[ACTION comments] ❌ Не вдалося натиснути реакцію '{REACTION_MAP[name]}'."
                )
                return False

        dom_stability(driver, timeout=3.0, stable_ms=200)
        human_pause(0.25, 0.4)
        return True

    def _remove_current_reaction(active: str) -> bool:
        """Знімає вже встановлену реакцію перед вибором нової."""
        if not _open_reaction_menu():
            return False

        remove_xpath = "//div[@role='button' and starts-with(@aria-label,'Remove ')]"
        try:
            options = driver.find_elements(By.XPATH, remove_xpath)
        except Exception:
            options = []

        for option in options:
            try:
                aria_label = (option.get_attribute("aria-label") or "").strip().lower()
            except StaleElementReferenceException:
                continue

            if not aria_label.startswith("remove "):
                continue

            if aria_label.split("remove ", 1)[-1] == active:
                try:
                    option.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", option)
                    except Exception:
                        continue
                dom_stability(driver, timeout=3.0, stable_ms=200)
                human_pause(0.25, 0.4)
                return True
        return False

    if current_reaction and current_reaction != normalized_reaction:
        print(
            f"[ACTION comments] 🔄 Виявив реакцію '{current_reaction}'. Спершу знімаю її."
        )
        if not _remove_current_reaction(current_reaction):
            print(
                "[ACTION comments] ❌ Не вдалося зняти наявну реакцію перед встановленням нової."
            )
            return False
        human_pause(0.2, 0.35)

    if not _open_reaction_menu():
        return False

    print(f"[ACTION comments] 👍 Ставлю реакцію '{REACTION_MAP[normalized_reaction]}'.")
    if not _click_reaction(normalized_reaction):
        return False

    final_state = comment_reaction_button_state(comment_element)
    if final_state == normalized_reaction:
        print(
            f"[ACTION comments] ✅ Реакцію '{REACTION_MAP[normalized_reaction]}' встановлено успішно."
        )
        return True

    print("[ACTION comments] ❌ Не вдалося підтвердити встановлення вибраної реакції.")
    return False
