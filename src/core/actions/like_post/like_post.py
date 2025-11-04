"""Головна дія для встановлення реакції на пості."""

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from .reaction_tools import check_like_state, check_reaction_state, set_reaction


def _normalize_reaction(reaction: Optional[str]) -> str:
    """Нормалізує назву реакції до нижнього регістру та підставляє значення за замовчуванням."""

    # Для стабільності прибираємо зайві пробіли та приводимо текст до нижнього регістру.
    normalized = (reaction or "like").strip().lower()
    if not normalized:
        return "like"
    return normalized


def like_post(driver: WebDriver, reaction: str = "like") -> bool:
    """Ставить реакцію на пості або завершує роботу, якщо вона вже встановлена."""

    print("[ACTION like_post] 🚀 Починаю перевірку реакцій під постом.")

    normalized_reaction = _normalize_reaction(reaction)
    print(
        f"[ACTION like_post] ℹ️ Запитана реакція: '{normalized_reaction}'."
    )

    # Крок 1. Перевіряємо стан класичного лайка через окрему функцію.
    like_state = check_like_state(driver)
    if like_state is None:
        print("[ACTION like_post] ⚠️ Не вдалося однозначно визначити стан лайка.")
    else:
        print(
            f"[ACTION like_post] 🔍 Результат перевірки лайка: {'стоїть' if like_state else 'ще немає'}."
        )

    # Крок 2. Зчитуємо, чи проставлена будь-яка інша реакція.
    reaction_state = check_reaction_state(driver)
    if reaction_state:
        print(
            f"[ACTION like_post] 🔍 Виявлено реакцію: '{reaction_state}'."
        )
    else:
        print("[ACTION like_post] 🔍 Активних реакцій не знайдено.")

    # Якщо лайк вже стоїть або існує будь-яка реакція — завершуємо дію.
    if like_state:
        print("[ACTION like_post] ✅ Лайк вже стоїть. Додаткові дії не потрібні.")
        return True

    if reaction_state:
        print("[ACTION like_post] ✅ На пості вже є реакція — залишаю як є.")
        return True

    print(
        f"[ACTION like_post] 👍 Жодної реакції не знайдено. Ставлю '{normalized_reaction}'."
    )

    # Пробуємо встановити реакцію один раз, згідно з вимогою не повторювати спроби.
    if not set_reaction(driver, normalized_reaction):
        print(
            "[ACTION like_post] ❌ Не вдалося встановити реакцію. Завершую з помилкою."
        )
        return False

    # Після встановлення знову перевіряємо стан для гарантії результату.
    updated_like_state = check_like_state(driver)
    updated_reaction_state = check_reaction_state(driver)

    if normalized_reaction == "like":
        if updated_like_state:
            print("[ACTION like_post] ✅ Лайк успішно підтверджено після встановлення.")
            return True
        if updated_reaction_state == "like":
            print(
                "[ACTION like_post] ✅ Отримав підтвердження через стан реакції 'like'."
            )
            return True
    else:
        if updated_reaction_state == normalized_reaction:
            print(
                f"[ACTION like_post] ✅ Реакція '{normalized_reaction}' успішно підтверджена."
            )
            return True

    print(
        "[ACTION like_post] ❌ Не вдалося підтвердити встановлену реакцію після перевірки."
    )
    return False

