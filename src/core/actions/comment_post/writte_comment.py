"""Дія для безпечного публікування коментаря під постом Facebook."""

from __future__ import annotations

import time

from selenium.webdriver.remote.webdriver import WebDriver

from ..comments_actions import (
    collect_comments,
    comment_human_behavire_writting,
    expand_comments,
    focus_comment_box,
    has_same_comment,
    send_comment,
)
from ..helpers import dom_stability, human_pause, text_normmalization


def writte_comment(driver: WebDriver, text: str) -> bool:
    """Перевіряє відсутність дубліката та, за потреби, відправляє коментар."""

    print("[ACTION writte_comment] 🚀 Починаю взаємодію з уже відкритим постом.")

    normalized_target = text_normmalization(text)
    if not normalized_target:
        print("[ACTION writte_comment] ❌ Текст коментаря порожній після нормалізації.")
        return False

    print("[ACTION writte_comment] 🔄 Розкриваю коментарі, щоб перевірити дублікати.")
    # Попередньо показуємо всі наявні коментарі, інакше можемо пропустити вже опублікований текст.
    expand_comments(driver, max_clicks=3)
    dom_stability(driver, timeout=8.0, stable_ms=300)

    containers = collect_comments(driver)
    # Якщо знаходимо ідентичний текст, вважаємо задачу виконаною та не дублюємо коментар.
    _, already_exists = has_same_comment(
        driver,
        normalized_target,
        containers=containers,
    )
    if already_exists:
        print(
            "[ACTION writte_comment] ✅ Такий коментар вже присутній на сторінці — пропускаю повторну публікацію."
        )
        return True

    print("[ACTION writte_comment] 🟦 Фокусую поле коментаря…")
    # Шукаємо input-поле під постом і переносимо туди курсор, щоб наступне введення було успішним.
    if not focus_comment_box(driver):
        print("[ACTION writte_comment] ❌ Не вдалося знайти або активувати поле коментаря.")
        return False

    print("[ACTION writte_comment] ✍️ Імітую друк коментаря…")
    comment_human_behavire_writting(driver, text)

    # Додаємо невелику паузу, щоб Facebook точно встиг зберегти введений текст.
    time.sleep(1.2)

    human_pause(0.3, 0.5)

    if send_comment(driver, expected_text=text):
        print("[ACTION writte_comment] ✅ Коментар опубліковано.")
        return True

    print("[ACTION writte_comment] ❌ Коментар не знайдено після спроб надсилання.")
    return False
