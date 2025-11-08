"""Екшен для написання відповіді на конкретний коментар."""

from __future__ import annotations

import time
from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..comments_actions import (
    collect_comments,
    comment_human_behavire_writting,
    expand_comments,
    find_reply_button,
    focus_reply_box,
    has_same_comment,
    press_reply_button,
    send_reply,
)
from ..helpers import dom_stability, human_pause, text_extraction, text_normmalization


def writte_replay(
    driver: WebDriver,
    comment_snippet: str,
    reply_text: str,
) -> bool:
    """Шукає коментар за уривком і залишає під ним відповідь без дублікатів."""

    print("[ACTION writte_replay] 🚀 Починаю пошук цільового коментаря для відповіді.")

    if not text_normmalization(reply_text):
        print("[ACTION writte_replay] ❌ Текст відповіді порожній після нормалізації.")
        return False

    print("[ACTION writte_replay] 🔄 Розкриваю всі коментарі для аналізу.")
    # Відкриваємо всі коментарі та реплаї, щоб не пропустити потрібний елемент у прихованому блоці.
    expand_comments(driver, max_clicks=4)
    dom_stability(driver, timeout=8.0, stable_ms=300)

    containers = collect_comments(driver)
    if not containers:
        print("[ACTION writte_replay] ❌ Не знайшов жодного коментаря на сторінці.")
        return False

    # Перевіряємо, чи немає вже відповіді з таким самим текстом серед будь-яких коментарів.
    _, already_posted = has_same_comment(
        driver,
        reply_text,
        containers=containers,
    )
    if already_posted:
        print(
            "[ACTION writte_replay] ✅ Така відповідь вже існує у стрічці — повторно не надсилаю."
        )
        return True

    normalized_snippet = text_normmalization(comment_snippet)
    if not normalized_snippet:
        print(
            "[ACTION writte_replay] ❌ Уривок коментаря порожній після нормалізації — не знаю, куди відповідати."
        )
        return False

    target_element: Optional[WebElement] = None

    print(
        "[ACTION writte_replay] 🔍 Перебираю коментарі в пошуках збігу з переданим уривком."
    )
    for element in containers:
        # Послідовно шукаємо коментар, в якому присутній заданий уривок тексту.
        try:
            raw_text = text_extraction(driver, element)
        except StaleElementReferenceException:
            continue

        normalized_comment = text_normmalization(raw_text)
        if normalized_snippet in normalized_comment:
            target_element = element
            break

    if target_element is None:
        print(
            "[ACTION writte_replay] ❌ Не вдалося знайти коментар із таким уривком тексту."
        )
        return False

    print("[ACTION writte_replay] 🛎️ Знаходжу кнопку відповіді…")
    reply_button = find_reply_button(target_element)
    if not reply_button:
        print("[ACTION writte_replay] ❌ Кнопку відповіді не знайдено в цільовому коментарі.")
        return False

    # Натискаємо на кнопку, щоб Facebook відобразив поле введення для реплаю.
    if not press_reply_button(driver, reply_button):
        print("[ACTION writte_replay] ❌ Не вдалося натиснути кнопку відповіді.")
        return False

    dom_stability(driver, timeout=5.0, stable_ms=250)

    print("[ACTION writte_replay] 📝 Фокусую поле для відповіді…")
    # Після натискання Reply поле може з'явитися не одразу, тому терпляче чекаємо на нього в межах коментаря.
    if not focus_reply_box(driver, comment_element=target_element):
        print("[ACTION writte_replay] ❌ Поле відповіді не з'явилося або недоступне.")
        return False

    print("[ACTION writte_replay] ✍️ Імітую друк відповіді…")
    # Вводимо текст по символах, щоб поведінка виглядала максимально природньо.
    comment_human_behavire_writting(driver, reply_text)
    # Невелика пауза гарантує, що React встигне зафіксувати весь текст відповіді.
    time.sleep(1.0)
    human_pause(0.3, 0.6)

    # Надсилаємо відповідь через уніфікований механізм send_reply із валідацією по тексту.
    if send_reply(driver, expected_text=reply_text):
        print("[ACTION writte_replay] ✅ Відповідь успішно опубліковано.")
        return True

    print("[ACTION writte_replay] ❌ Відповідь не підтвердилася після всіх спроб надсилання.")
    return False
