"""Отримання поточного стану реакцій під постом."""

from typing import Optional, Tuple

from selenium.webdriver.remote.webdriver import WebDriver

from .reaction_tools import check_like_state, check_reaction_state


def evaluate_current_state(driver: WebDriver) -> Tuple[Optional[bool], Optional[str]]:
    """Зчитує та логує стан звичайного лайка і додаткових реакцій."""

    # Знімаємо інформацію про класичний лайк, щоб розуміти чи потрібні дії взагалі.
    like_state = check_like_state(driver)
    if like_state is None:
        print("[ACTION like_post] ⚠️ Не вдалося однозначно визначити стан лайка.")
    else:
        print(
            f"[ACTION like_post] 🔍 Результат перевірки лайка: {'стоїть' if like_state else 'ще немає'}."
        )

    # Дізнаємося чи активна будь-яка інша реакція, щоб уникнути повторної установки.
    reaction_state = check_reaction_state(driver)
    if reaction_state:
        print(f"[ACTION like_post] 🔍 Виявлено реакцію: '{reaction_state}'.")
    else:
        print("[ACTION like_post] 🔍 Активних реакцій не знайдено.")

    return like_state, reaction_state
