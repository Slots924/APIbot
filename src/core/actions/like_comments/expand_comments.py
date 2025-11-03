"""Розкриття додаткових коментарів у стрічці."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .dom_stability import wait_dom_stable
from .human_pause import human_pause


def expand_more_comments(driver: WebDriver, max_clicks: int = 3) -> None:
    """Натискає кнопки на кшталт «Показати більше коментарів», щоб завантажити тред."""

    # Визначаємо шаблони кнопок лише у межах функції, щоб не створювати глобальні
    # змінні у модулі. Це полегшує підтримку та тестування.
    expand_patterns = [
        "//div[@role='button'][.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas')]]",
        "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas')]",
        "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
    ]

    for step in range(1, max_clicks + 1):
        clicked_any = False
        for xpath in expand_patterns:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
            except Exception:
                buttons = []

            # Працюємо максимум з двома кнопками за ітерацію, щоб не спричинити хаос.
            for button in buttons[:2]:
                try:
                    if not button.is_displayed():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
                    human_pause(0.2, 0.4)
                    driver.execute_script("arguments[0].click();", button)
                    clicked_any = True
                    print(
                        f"[ACTION like_comments] 🔁 Розкриваю додаткові коментарі (крок {step})."
                    )
                    human_pause(0.4, 0.8)
                except Exception:
                    continue

        if not clicked_any:
            break

        wait_dom_stable(driver, timeout=8.0, stable_ms=300)
