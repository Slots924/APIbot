"""Накладання реакції на конкретний коментар."""

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from .button_state import is_button_liked
from .click_like_button import click_like_button
from .find_like_button import find_like_button


def like_single_comment(driver: WebDriver, comment_element: WebElement, reaction: str) -> bool:
    """Пробує поставити реакцію на переданому елементі коментаря."""

    # Визначаємо підтримувані реакції локально, щоб уникнути глобальних змінних.
    supported_reactions = {"like", "love", "care", "haha", "wow", "sad", "angry"}

    normalized_reaction = (reaction or "like").strip().lower()
    if normalized_reaction not in supported_reactions:
        print(
            f"[ACTION like_comments] ⚠️ Реакція '{normalized_reaction}' поки не підтримується. Застосовую 'like'."
        )
        normalized_reaction = "like"

    # Поки реалізовано лише класичний лайк. Інші реакції залишаються на майбутнє.
    if normalized_reaction != "like":
        print(
            f"[ACTION like_comments] ⚠️ Реакція '{normalized_reaction}' ще не реалізована. Повертаю False."
        )
        return False

    button = find_like_button(comment_element)
    if not button:
        print("[ACTION like_comments] ❌ Не знайшов кнопку лайка в межах коментаря.")
        return False

    if is_button_liked(button):
        print("[ACTION like_comments] ℹ️ Лайк вже стоїть — пропускаю клік.")
        return True

    if not click_like_button(driver, button):
        print("[ACTION like_comments] ❌ Не вдалося натиснути кнопку лайка.")
        return False

    updated_button = find_like_button(comment_element) or button
    if is_button_liked(updated_button):
        print("[ACTION like_comments] ✅ Лайк успішно встановлено.")
        return True

    print("[ACTION like_comments] ❌ Не вдалося підтвердити встановлення лайка.")
    return False
