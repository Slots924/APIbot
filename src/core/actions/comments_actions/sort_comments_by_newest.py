"""Сортування коментарів за найновішими."""

import re
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def sort_comments_by_newest(driver: WebDriver) -> bool:
    """Відкриває меню сортування Facebook і обирає пункт «Найновіші»."""

    print("\n[SORT] 🚀 Починаю сортування коментарів → Найновіші")

    # ------------------ КРОК 1. ЗНАХОДИМО КНОПКУ СОРТУВАННЯ ------------------
    print("[SORT] 🔍 Шукаю кнопку сортування коментарів...")

    try:
        buttons = driver.find_elements(By.XPATH, "//*[@role='button' and @aria-haspopup='menu']")
    except Exception:
        print("[SORT] ❌ Помилка доступу до DOM. Не можу знайти кнопки.")
        return False

    sort_btn = None
    for btn in buttons:
        text = (btn.text or "").lower()
        if any(k in text for k in ["relevant", "recent", "нов", "актуал", "релевант"]):
            sort_btn = btn
            break

    if not sort_btn:
        # Якщо меню сортування відсутнє, Facebook вже показує всі коментарі у потрібному порядку.
        print(
            "[SORT] ℹ️ Кнопку сортування не знайдено — схоже, Facebook не показує її для малих стрічок. Продовжую без зміни порядку."
        )
        return True

    print("[SORT] ✅ Кнопка сортування знайдена.")

    # ------------------ КРОК 2. ВІДКРИВАЄМО МЕНЮ ------------------
    print("[SORT] 🖱️ Відкриваю меню сортування...")

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sort_btn)
        time.sleep(0.3)
        ActionChains(driver).move_to_element(sort_btn).perform()
        time.sleep(0.2)
        sort_btn.click()
        time.sleep(0.7)
    except Exception:
        print("[SORT] ⚠️ Selenium-клік не спрацював, пробую JS-клік...")
        try:
            driver.execute_script("arguments[0].click();", sort_btn)
            time.sleep(0.7)
        except Exception:
            print("[SORT] ❌ Не вдалося відкрити меню сортування.")
            return False

    print("[SORT] ✅ Меню сортування відкрито.")

    # ------------------ КРОК 3. ОБИРАЄМО “НАЙНОВІШІ” ------------------
    print("[SORT] 📑 Шукаю пункт меню 'Найновіші'...")

    keywords = [
        "most recent",
        "newest",
        "найнов",
        "нові",
        "самые новые",
        "новые",
    ]

    try:
        options = driver.find_elements(By.XPATH, "//*[@role='menuitem' or @role='option']")
    except Exception:
        print("[SORT] ❌ Не можу зчитати список опцій меню.")
        return False

    target_option = None
    for opt in options:
        text = (opt.text or "").strip().lower()
        if any(k in text for k in keywords) or re.search(r"\bnew|recent|нов", text):
            target_option = opt
            break

    if not target_option:
        print("[SORT] ❌ Пункт 'Найновіші' не знайдено у меню.")
        return False

    print(f"[SORT] ✅ Пункт знайдено  '{target_option.text.strip()}'")
    print("[SORT] 🖱️ Клікаю по пункту...")

    try:
        target_option.click()
        time.sleep(1)
    except Exception:
        print("[SORT] ⚠️ Selenium-клік не спрацював, пробую JS-клік...")
        try:
            driver.execute_script("arguments[0].click();", target_option)
            time.sleep(1)
        except Exception:
            print("[SORT] ❌ Не вдалося натиснути на пункт меню.")
            return False

    print("[SORT] ✅ Коментарі відсортовано за найновішими.\n")
    return True
