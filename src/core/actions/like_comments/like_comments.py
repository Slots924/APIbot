"""Реалізація дії, що ставить реакції на вибраних коментарях у Facebook."""

from __future__ import annotations

from typing import Iterable, Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver

from ..comments_actions import (
    collect_comments,
    expand_comments,
    react_on_single_comment,
    sort_comments_by_newest,
)
from ..helpers import (
    dom_stability,
    human_pause,
    text_extraction,
    text_normmalization,
)

CommentList = Iterable[str]


def like_comments(
    driver: WebDriver,
    comments: Optional[CommentList] = None,
    reaction: str = "like",
) -> bool:
    """Ставить реакції на коментарях, що містять передані текстові уривки."""

    print("[ACTION like_comments] 🚀 Починаю обробку коментарів.")

    comment_snippets: list[str] = []
    for raw_item in (list(comments) if comments is not None else []):
        if not (raw_item or "").strip():
            continue
        normalized_item = text_normmalization(raw_item)
        if not normalized_item:
            continue
        comment_snippets.append(normalized_item)

    if not comment_snippets:
        print(
            "[ACTION like_comments] ⚠️ Не передано жодного тексту коментаря — немає кого лайкати."
        )
        return False

    if not sort_comments_by_newest(driver):
        print("[ACTION like_comments] ❌ Не вдалося відсортувати коментарі за найновішими.")
        return False

    human_pause(0.4, 0.7)
    expand_comments(driver, max_clicks=5)
    dom_stability(driver, timeout=10.0, stable_ms=400)

    containers = collect_comments(driver)
    if not containers:
        print("[ACTION like_comments] ❌ Не знайшов жодного контейнера коментаря.")
        return False

    print(
        f"[ACTION like_comments] ℹ️ Знайдено {len(containers)} видимих коментарів. Шукаю збіги за уривками тексту."
    )

    matched: dict[str, bool] = {snippet: False for snippet in comment_snippets}

    for idx, element in enumerate(containers, start=1):
        if all(matched.values()):
            break

        dom_stability(driver, timeout=6.0, stable_ms=250)

        try:
            raw_text = text_extraction(driver, element)
        except StaleElementReferenceException:
            print(
                f"[ACTION like_comments] [{idx}] ⚠️ Контейнер оновився під час читання — пропускаю."
            )
            continue

        normalized = text_normmalization(raw_text)
        if not normalized:
            continue

        target_snippet = next(
            (snippet for snippet, done in matched.items() if not done and snippet in normalized),
            None,
        )

        if not target_snippet:
            continue

        preview = raw_text.strip().replace("\n", " ")[:80]
        print(
            f"[ACTION like_comments] [{idx}] 🎯 Збіг за уривком. Фрагмент коментаря: '{preview}'"
        )

        success = react_on_single_comment(driver, element, reaction)
        matched[target_snippet] = success

        status = "успіх" if success else "помилка"
        print(
            f"[ACTION like_comments] [{idx}] ⏱️ Завершено обробку уривка '{target_snippet[:30]}' → {status}."
        )

        human_pause(0.3, 0.6)

    all_done = all(matched.values())
    processed = sum(1 for value in matched.values() if value)

    if all_done:
        print(
            f"[ACTION like_comments] ✅ Всі {processed} цільові коментарі опрацьовано успішно."
        )
    else:
        missing = len(matched) - processed
        print(
            f"[ACTION like_comments] ❌ Успішно опрацював {processed} коментарів. {missing} залишились без реакції."
        )

    return all_done
