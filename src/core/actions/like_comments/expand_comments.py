"""Розкриття додаткових коментарів у стрічці (включно з реплаями)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .dom_stability import wait_dom_stable
from .human_pause import human_pause


def expand_more_comments(driver: WebDriver, max_clicks: int = 3) -> None:
    """
    Натискає кнопки на кшталт:
      • “View more comments” / локалізовані варіанти
      • “View all X replies” / “View replies” / “See replies” / локалізовані варіанти
      • “See more” у довгих коментарях
    щоб завантажити і верхні коментарі, і вкладені відповіді.
    """

    # Для case-insensitive contains використовуємо translate(...) всередині XPath.
    # Окремі групи: треди, реплаї, довгі тексти
    more_comments_xpaths = [
        # Англ: more comments / view more
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
        # Деякі локалі (укр/рос/фр/ісп)
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'коментар')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'комментар')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'réponses')]",  # fr
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'respuestas')]",  # es
    ]

    replies_xpaths = [
        # Англ: replies
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'view all') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'replies')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'view replies')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'see replies')]",
        "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'replies')]",
        # Поширені локалі: укр/рос/фр/ісп/нім/італ/порт
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'відповід')]",   # укр: відповіді/відповідей
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'ответ')]",      # рус: ответы
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'réponses')]",   # fr
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'respuestas')]", # es
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'antworten')]",  # de
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'risposte')]",   # it
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'respostas')]",  # pt
    ]

    see_more_text_xpaths = [
        # Довгий текст комента/реплая
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'see more')]",
        "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'see more')]",
        # Можливі локалізації (мінімальний набір)
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'показати більше')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'показать ещё')]",
    ]

    # Скільки кнопок пробуємо натискати за одну ітерацію кожної групи
    per_iter_limits = {
        "more_comments": 4,
        "replies": 6,
        "see_more": 6,
    }

    def _click_visible_buttons(xpaths, per_iter_limit, log_label):
        clicked = 0
        for xp in xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xp)
            except Exception:
                buttons = []

            # Відфільтруємо тільки видимі
            visible = []
            for b in buttons:
                try:
                    if b.is_displayed():
                        visible.append(b)
                except Exception:
                    continue

            if not visible:
                continue

            for btn in visible[: max(0, per_iter_limit - clicked)]:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    human_pause(0.15, 0.3)
                    driver.execute_script("arguments[0].click();", btn)
                    clicked += 1
                    print(f"[ACTION like_comments] 🔁 Розкриваю {log_label}.")
                    human_pause(0.25, 0.5)
                    if clicked >= per_iter_limit:
                        break
                except Exception:
                    continue

            if clicked >= per_iter_limit:
                break

        return clicked

    for step in range(1, max_clicks + 1):
        total_clicked = 0

        # 1) Більше коментарів у треді
        total_clicked += _click_visible_buttons(more_comments_xpaths, per_iter_limits["more_comments"], f"коментарі (крок {step})")

        # 2) РЕПЛАЇ (головне для твого кейсу)
        total_clicked += _click_visible_buttons(replies_xpaths, per_iter_limits["replies"], f"реплаї (крок {step})")

        # 3) “See more” у довгих коментах/реплаях
        total_clicked += _click_visible_buttons(see_more_text_xpaths, per_iter_limits["see_more"], f"довгий текст (крок {step})")

        if total_clicked == 0:
            break

        wait_dom_stable(driver, timeout=8.0, stable_ms=300)
