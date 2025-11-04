"""Перевірка результатів встановлення реакції."""

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from .reaction_tools import check_like_state, check_reaction_state


def _is_like_confirmed(updated_like_state: Optional[bool], updated_reaction_state: Optional[str]) -> bool:
    """Допоміжна перевірка для сценарію з класичним лайком."""

    # Якщо aria-pressed показав true — лайк поставлено.
    if updated_like_state:
        print("[ACTION like_post] ✅ Лайк успішно підтверджено після встановлення.")
        return True

    # Іноді Facebook не оновлює aria-pressed, але реакція переходить у стан 'like'.
    if updated_reaction_state == "like":
        print("[ACTION like_post] ✅ Отримав підтвердження через стан реакції 'like'.")
        return True

    return False


def verify_reaction_result(driver: WebDriver, reaction: str) -> bool:
    """Повторно перевіряє стан реакцій після спроби встановлення."""

    updated_like_state = check_like_state(driver)
    updated_reaction_state = check_reaction_state(driver)

    if reaction == "like":
        if _is_like_confirmed(updated_like_state, updated_reaction_state):
            return True
    else:
        if updated_reaction_state == reaction:
            print(
                f"[ACTION like_post] ✅ Реакція '{reaction}' успішно підтверджена."
            )
            return True

    print("[ACTION like_post] ❌ Не вдалося підтвердити встановлену реакцію після перевірки.")
    return False
