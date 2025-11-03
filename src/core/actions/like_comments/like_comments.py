"""Реалізація дії, що ставить реакції на вибраних коментарях у Facebook."""

from __future__ import annotations

import random
import time
from typing import Iterable, List, Optional

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    JavascriptException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Імпортуємо готову функцію сортування, яка доводить список коментарів до стану «Найновіші».
from .like_comments_sort import sort_comments_by_newest


# Визначаємо підтримувані реакції. Реально імплементовано лише "like",
# але структура дозволяє з часом додати решту без зміни основної логіки.
SUPPORTED_REACTIONS = {"like", "love", "care", "haha", "wow", "sad", "angry"}

# Визначаємо тип для масиву коментарів, щоб було зрозуміло, які дані очікуємо.
CommentList = Iterable[str]

# Список XPath-селекторів, що допомагає знайти кнопку реакції всередині коментаря.
COMMENT_LIKE_SELECTORS = [
    "./descendant::div[@role='button' and (@aria-label='Like' or @aria-label='Подобається' or @aria-label='Нравится' or @aria-label='Me gusta' or @aria-label='J’aime')]",
    "./descendant::span[@role='button' and (text()='Like' or text()='Подобається' or text()='Нравится' or text()='Me gusta' or text()='J’aime')]",
    "./descendant::div[@role='button'][.//span[text()='Like' or text()='Подобається' or text()='Нравится' or text()='Me gusta' or text()='J’aime']]",
]

# XPath шаблони для контейнерів коментарів. Дублюємо підходи з R&D-скрипта, щоб покрити різні версії DOM.
COMMENT_CONTAINER_PATTERNS = [
    "//div[@role='article'][.//div[@role='button']]",
    "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
    "//div[contains(@data-ad-preview,'comment') or @data-visualcompletion='ignore-dynamic'][.//*[@role='button']]",
]

# Патерни для кнопок "View more comments" / "Показати більше".
EXPAND_COMMENTS_PATTERNS = [
    "//div[@role='button'][.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas')]]",
    "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas')]",
    "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
]


def _normalize_text(text: str) -> str:
    """Повертає текст у форматі «все в один рядок та в нижньому регістрі».

    Це дозволяє виконувати порівняння за префіксом незалежно від регістру та
    зайвих пробілів. Ми робимо саме префіксний пошук, оскільки в більшості кейсів
    користувач вводить перші слова коментаря.
    """

    return " ".join((text or "").strip().split()).lower()


def _get_inner_text(driver: WebDriver, element) -> str:
    """Зчитує видимий текст коментаря через JavaScript з обробкою виключень."""

    try:
        return (
            driver.execute_script(
                "return arguments[0].innerText || arguments[0].textContent || '';",
                element,
            )
            or ""
        )
    except JavascriptException:
        try:
            return element.text or ""
        except Exception:
            return ""


def _human_pause(min_seconds: float, max_seconds: float) -> None:
    """Імітує невеличку паузу користувача між діями."""

    time.sleep(random.uniform(min_seconds, max_seconds))


def _wait_dom_stable(driver: WebDriver, timeout: float = 15.0, stable_ms: int = 600) -> bool:
    """Очікує стабілізацію DOM за допомогою порівняння довжини outerHTML."""

    end_time = time.time() + timeout
    last_length: Optional[int] = None
    stable_since: Optional[float] = None

    while time.time() < end_time:
        try:
            html_length = int(
                driver.execute_script("return document.documentElement.outerHTML.length || 0;")
            )
        except JavascriptException:
            _human_pause(0.2, 0.4)
            continue

        now = time.time()
        if last_length == html_length:
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) * 1000 >= stable_ms:
                return True
        else:
            last_length = html_length
            stable_since = None

        _human_pause(0.12, 0.25)

    return False


def _expand_more_comments(driver: WebDriver, max_clicks: int = 3) -> None:
    """Поступово натискає кнопки «Показати більше коментарів», щоб підвантажити треди."""

    for step in range(1, max_clicks + 1):
        clicked_any = False
        for xpath in EXPAND_COMMENTS_PATTERNS:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
            except Exception:
                buttons = []

            for button in buttons[:2]:  # беремо максимум дві кнопки на ітерацію, щоб уникнути хаосу
                try:
                    if not button.is_displayed():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
                    _human_pause(0.2, 0.4)
                    driver.execute_script("arguments[0].click();", button)
                    clicked_any = True
                    print(
                        f"[ACTION like_comments] 🔁 Розкриваю додаткові коментарі (крок {step})."
                    )
                    _human_pause(0.4, 0.8)
                except Exception:
                    continue

        if not clicked_any:
            break

        _wait_dom_stable(driver, timeout=8.0, stable_ms=300)


def _collect_comment_containers(driver: WebDriver) -> List:
    """Шукає всі помітні контейнери коментарів, де в наявності є кнопки реакцій."""

    containers: List = []
    seen_ids = set()

    for xpath in COMMENT_CONTAINER_PATTERNS:
        try:
            candidates = driver.find_elements(By.XPATH, xpath)
        except Exception:
            candidates = []

        for element in candidates:
            try:
                if not element.is_displayed():
                    continue
                element_id = getattr(element, "id", None)
                if element_id in seen_ids:
                    continue
                seen_ids.add(element_id)
                containers.append(element)
            except StaleElementReferenceException:
                continue

    return containers


def _find_like_button(comment_element) -> Optional[object]:
    """Повертає кнопку лайка всередині конкретного коментаря або None, якщо її не видно."""

    for xpath in COMMENT_LIKE_SELECTORS:
        try:
            buttons = comment_element.find_elements(By.XPATH, xpath)
        except StaleElementReferenceException:
            return None
        except Exception:
            buttons = []

        for button in buttons:
            try:
                if button.is_displayed():
                    return button
            except StaleElementReferenceException:
                return None

    return None


def _is_button_liked(button) -> bool:
    """Перевіряє стан кнопки лайка через aria-атрибути та CSS-класи."""

    try:
        aria_state = (
            (button.get_attribute("aria-pressed") or button.get_attribute("aria-checked") or "").lower()
        )
        if aria_state == "true":
            return True
    except StaleElementReferenceException:
        return False

    try:
        class_state = (button.get_attribute("class") or "").lower()
        if any(keyword in class_state for keyword in ["active", "liked", "press"]):
            return True
    except StaleElementReferenceException:
        return False

    try:
        aria_label = (button.get_attribute("aria-label") or "").lower()
        if any(flag in aria_label for flag in ["remove like", "liked", "reaction" ]):
            return True
    except StaleElementReferenceException:
        return False

    return False


def _click_like_button(driver: WebDriver, button) -> bool:
    """Робить безпечний клік по кнопці лайка з запасними сценаріями."""

    for attempt in range(1, 4):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
            _human_pause(0.1, 0.25)
            button.click()
            _human_pause(0.25, 0.45)
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", button)
                _human_pause(0.25, 0.45)
                return True
            except Exception:
                pass
        except Exception:
            pass

        print(
            f"[ACTION like_comments] ⚠️ Не вдалося натиснути кнопку лайка (спроба {attempt})."
        )
        _human_pause(0.25, 0.5)

    return False


def _like_single_comment(driver: WebDriver, comment_element, reaction: str) -> bool:
    """Накладає реакцію на конкретному коментарі і повертає успіх/помилку."""

    reaction = (reaction or "like").strip().lower()
    if reaction not in SUPPORTED_REACTIONS:
        print(
            f"[ACTION like_comments] ⚠️ Реакція '{reaction}' поки не підтримується. Застосовую 'like'."
        )
        reaction = "like"

    if reaction != "like":
        print(
            f"[ACTION like_comments] ⚠️ Реакція '{reaction}' ще не реалізована. Повертаю False."
        )
        return False

    button = _find_like_button(comment_element)
    if not button:
        print("[ACTION like_comments] ❌ Не знайшов кнопку лайка в межах коментаря.")
        return False

    if _is_button_liked(button):
        print("[ACTION like_comments] ℹ️ Лайк вже стоїть — пропускаю клік.")
        return True

    if not _click_like_button(driver, button):
        print("[ACTION like_comments] ❌ Не вдалося натиснути кнопку лайка.")
        return False

    # Після кліку перепошук кнопки для надійності — Facebook часто перерендерює DOM.
    updated_button = _find_like_button(comment_element) or button
    if _is_button_liked(updated_button):
        print("[ACTION like_comments] ✅ Лайк успішно встановлено.")
        return True

    print("[ACTION like_comments] ❌ Не вдалося підтвердити встановлення лайка.")
    return False


def like_comments(
    driver: WebDriver,
    comments: Optional[CommentList] = None,
    reaction: str = "like",
) -> bool:
    """Ставить реакції на коментарях, що починаються з вказаних текстових префіксів."""

    print("[ACTION like_comments] 🚀 Починаю обробку коментарів.")

    # Переконуємося, що список цілей існує й не порожній.
    comment_prefixes = [
        _normalize_text(item)
        for item in (list(comments) if comments is not None else [])
        if (item or "").strip()
    ]

    if not comment_prefixes:
        print(
            "[ACTION like_comments] ⚠️ Не передано жодного тексту коментаря — немає кого лайкати."
        )
        return False

    if not sort_comments_by_newest(driver):
        print("[ACTION like_comments] ❌ Не вдалося відсортувати коментарі за найновішими.")
        return False

    _human_pause(0.4, 0.7)
    _expand_more_comments(driver, max_clicks=3)
    _wait_dom_stable(driver, timeout=10.0, stable_ms=400)

    containers = _collect_comment_containers(driver)
    if not containers:
        print("[ACTION like_comments] ❌ Не знайшов жодного контейнера коментаря.")
        return False

    print(
        f"[ACTION like_comments] ℹ️ Знайдено {len(containers)} видимих коментарів. Шукаю збіги за префіксами."
    )

    matched: dict[str, bool] = {prefix: False for prefix in comment_prefixes}

    for idx, element in enumerate(containers, start=1):
        if all(matched.values()):
            break

        _wait_dom_stable(driver, timeout=6.0, stable_ms=250)

        try:
            raw_text = _get_inner_text(driver, element)
        except StaleElementReferenceException:
            print(
                f"[ACTION like_comments] [{idx}] ⚠️ Контейнер оновився під час читання — пропускаю."
            )
            continue

        normalized = _normalize_text(raw_text)
        if not normalized:
            continue

        target_prefix = next(
            (prefix for prefix, done in matched.items() if not done and normalized.startswith(prefix)),
            None,
        )

        if not target_prefix:
            continue

        preview = raw_text.strip().replace("\n", " ")[:80]
        print(
            f"[ACTION like_comments] [{idx}] 🎯 Збіг за префіксом. Фрагмент коментаря: '{preview}'"
        )

        success = _like_single_comment(driver, element, reaction)
        matched[target_prefix] = success

        status = "успіх" if success else "помилка"
        print(
            f"[ACTION like_comments] [{idx}] ⏱️ Завершено обробку префікса '{target_prefix[:30]}' → {status}."
        )

        _human_pause(0.3, 0.6)

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
