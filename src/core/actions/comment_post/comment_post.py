"""Дія для публікації коментаря під постом Facebook."""

import time

from selenium.webdriver.remote.webdriver import WebDriver

from ..comments_actions import (
    comment_human_behavire_writting,
    focus_comment_box,
    send_comment,
)


def comment_post(driver: WebDriver, text: str) -> bool:
    """Повноцінно пише та відправляє коментар під постом Facebook."""

    print("[ACTION comment_post] 🚀 Починаю взаємодію з уже відкритим постом.")

    print("[ACTION comment_post] 🟦 Фокусую поле коментаря…")
    if not focus_comment_box(driver):
        print("[ACTION comment_post] ❌ Не вдалося знайти/активувати поле коментаря.")
        return False

    print("[ACTION comment_post] ✍️ Ввожу текст…")
    comment_human_behavire_writting(driver, text)

    # Робимо коротку паузу, щоб Facebook встиг зафіксувати введений текст.
    time.sleep(1.2)

    if send_comment(driver, expected_text=text):
        print("[ACTION comment_post] ✅ Коментар опубліковано.")
        return True

    print("[ACTION comment_post] ❌ Коментар не знайдено після всіх спроб.")
    return False
