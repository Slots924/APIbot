"""Встановлення реакції на пості."""

from selenium.webdriver.remote.webdriver import WebDriver

from .reaction_tools import set_reaction


def apply_reaction(driver: WebDriver, reaction: str) -> bool:
    """Пробує встановити реакцію та повертає результат операції."""

    # Інформуємо у логах, що намагаємося поставити нову реакцію.
    print(f"[ACTION like_post] 👍 Жодної реакції не знайдено. Ставлю '{reaction}'.")

    if not set_reaction(driver, reaction):
        print("[ACTION like_post] ❌ Не вдалося встановити реакцію. Завершую з помилкою.")
        return False

    return True
