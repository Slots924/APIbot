"""Інструменти для підготовки реакції перед запуском дії."""

from typing import Optional


def prepare_requested_reaction(reaction: Optional[str]) -> str:
    """Нормалізує назву реакції та одразу виводить службове повідомлення."""

    # Якщо користувач не передав реакцію, то обираємо лайк як дефолтний варіант.
    normalized = (reaction or "like").strip().lower()
    if not normalized:
        normalized = "like"

    # Повідомляємо у логах, яку реакцію намагаємося встановити.
    print(f"[ACTION like_post] ℹ️ Запитана реакція: '{normalized}'.")
    return normalized
