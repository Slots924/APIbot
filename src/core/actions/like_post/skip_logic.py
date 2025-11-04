"""Правила прийняття рішення щодо пропуску дії лайкування."""

from typing import Optional


def should_skip_action(like_state: Optional[bool], reaction_state: Optional[str]) -> bool:
    """Визначає, чи потрібно пропустити подальші кроки, якщо реакція вже є."""

    # Якщо лайк вже стоїть, то зайвих дій не виконуємо.
    if like_state:
        print("[ACTION like_post] ✅ Лайк вже стоїть. Додаткові дії не потрібні.")
        return True

    # Якщо існує будь-яка реакція (наприклад, love або wow) — лишаємо її без змін.
    if reaction_state:
        print("[ACTION like_post] ✅ На пості вже є реакція — залишаю як є.")
        return True

    return False
