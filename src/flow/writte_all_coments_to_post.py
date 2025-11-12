"""Сценарій для послідовного дописування коментарів під конкретним постом."""

from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.core.bot import Bot
from src.core.ads_power import AdsPower
from src.core.actions.comments_actions.collect_comments import collect_comments
from src.core.actions.comments_actions.expand_comments import expand_comments
from src.core.actions.comments_actions.has_same_commen import has_same_comment
from src.core.actions.helpers.dom_stability import dom_stability

# Тип для впорядкування коментарів (1, 2, 2.1 тощо).
OrderTuple = Tuple[int, ...]


# Налаштування обмеження швидкості запитів до AdsPower.
_ADSPOWER_REQUEST_DELAY = 0.5
_ADSPOWER_RATE_LIMIT_DELAY = 1.0
_ADSPOWER_MAX_GENDER_ATTEMPTS = 3


def _normalize_text(value: str) -> str:
    """Повертає текст у спрощеній формі для порівняння та логів."""

    normalized = unicodedata.normalize("NFKC", (value or "")).strip()
    return " ".join(normalized.split())


def _parse_order(raw_value: object) -> Optional[OrderTuple]:
    """Перетворює рядок на кортеж чисел, придатний для сортування коментарів."""

    if raw_value is None:
        return None

    # Дозволяємо використовувати як крапку, так і кому в позначенні порядку (``5.1`` або ``5,1``).
    safe_string = str(raw_value).replace(",", ".").strip()
    if not safe_string:
        return None

    parts: List[int] = []
    for chunk in safe_string.split("."):
        if not chunk:
            continue
        try:
            parts.append(int(chunk))
        except ValueError:
            return None

    return tuple(parts) if parts else None


def _is_reply(order_tuple: OrderTuple) -> bool:
    """Визначає, чи є коментар відповіддю (має вигляд ``5.1`` тощо)."""

    return len(order_tuple) > 1


def _parent_order(order_tuple: OrderTuple) -> OrderTuple:
    """Повертає ідентифікатор батьківського коментаря для відповіді."""

    return order_tuple[:-1]


def _normalize_gender(value: Optional[str]) -> str:
    """Стандартизує стать до форматів ``Male``/``Female`` для подальших перевірок."""

    normalized = (value or "").strip().lower()
    if normalized in {"male", "m", "man", "чоловік", "ч"}:
        return "Male"
    if normalized in {"female", "f", "woman", "жінка", "ж"}:
        return "Female"
    return ""


def _fetch_gender(ads: AdsPower, serial_number: str) -> str:
    """Отримує стать профілю через AdsPower з урахуванням лімітів API."""

    last_raw_gender: Optional[str] = None

    # AdsPower допускає лише кілька запитів на секунду, тому кожну спробу супроводжуємо
    # паузою та, у разі потреби, повторюємо запит із додатковою затримкою.
    for attempt in range(1, _ADSPOWER_MAX_GENDER_ATTEMPTS + 1):
        try:
            last_raw_gender = ads.get_profil_gender_by_serial_number(serial_number)
        except Exception as exc:  # pragma: no cover - мережеві помилки лише логуються.
            print(
                f"[FLOW writte_all_coments] ⚠️ Не вдалося отримати стать для профілю {serial_number}: {exc}"
            )
            last_raw_gender = None

        # Після кожного запиту робимо невелику паузу, щоб не перевищити ліміт у ~4 запити/с.
        time.sleep(_ADSPOWER_REQUEST_DELAY)

        normalized_gender = _normalize_gender(last_raw_gender)
        if normalized_gender:
            return normalized_gender

        if last_raw_gender:
            # Якщо відповідь є, але вона не містить валідної статі — інформуємо про це одразу.
            print(
                f"[FLOW writte_all_coments] ⚠️ Профіль {serial_number} повернув невідому стать: {last_raw_gender}"
            )
            return ""

        # На цьому етапі стать не отримано — чекаємо довше та повторюємо спробу (але не більше трьох разів).
        if attempt < _ADSPOWER_MAX_GENDER_ATTEMPTS:
            print(
                "[FLOW writte_all_coments] ⏳ Не вдалося визначити стать, ймовірно AdsPower обмежив запити. "
                f"Чекаю {_ADSPOWER_RATE_LIMIT_DELAY} с та повторюю спробу {attempt + 1}/{_ADSPOWER_MAX_GENDER_ATTEMPTS}."
            )
            time.sleep(_ADSPOWER_RATE_LIMIT_DELAY)

    print(
        f"[FLOW writte_all_coments] ❌ Після {_ADSPOWER_MAX_GENDER_ATTEMPTS} спроб не вдалося визначити стать профілю {serial_number}."
    )
    return ""


def _ensure_comments_scanned(driver: WebDriver) -> List[WebElement]:
    """Розгортає блок коментарів і повертає зібрані контейнери."""

    print("[FLOW writte_all_coments] 🔄 Оновлюю список коментарів на сторінці…")
    expand_comments(driver, max_clicks=4)
    dom_stability(driver, timeout=8.0, stable_ms=300)
    containers = collect_comments(driver)
    print(
        f"[FLOW writte_all_coments] ℹ️ Знайдено {len(containers)} контейнерів коментарів для аналізу."
    )
    return containers


def writte_all_coments_to_post(
    bot: Bot,
    url: str,
    user_serial_numbers: Iterable[int | str],
    comments_json_path: str,
    like_post_reaction: str = "none",
) -> None:
    """Виконує повний цикл написання коментарів згідно з JSON-конфігом.

    Параметр ``like_post_reaction`` дозволяє задати реакцію, яку потрібно поставити перед
    написанням коментаря. Якщо передано ``"none"`` (значення за замовчуванням), реакція не
    встановлюється.
    """

    print("[FLOW writte_all_coments] 🚀 Стартую сценарій масового публікування коментарів.")
    print(f"[FLOW writte_all_coments] 🔗 Цільовий допис: {url}")

    # Шлях до JSON може містити як відносні, так і абсолютні адреси, тому одразу конвертуємо його у ``Path``.
    path = Path(str(comments_json_path))
    if not path.exists():
        print(f"[FLOW writte_all_coments] ❌ JSON-файл з коментарями не знайдено: {path}")
        return

    try:
        # Читаємо файл як UTF-8, щоб коректно обробляти емодзі та інші спецсимволи.
        raw_comments = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(
            f"[FLOW writte_all_coments] ❌ Не вдалося прочитати файл {path}: {exc}"
        )
        return

    if not isinstance(raw_comments, list):
        print("[FLOW writte_all_coments] ❌ JSON має містити список об'єктів-коментарів.")
        return

    # На цьому етапі формуємо допоміжний список із впорядкованими та очищеними коментарями.
    prepared: List[Dict[str, object]] = []
    for entry in raw_comments:
        if not isinstance(entry, dict):
            print(
                f"[FLOW writte_all_coments] ⚠️ Пропускаю елемент незнайомого формату: {entry}"
            )
            continue

        # ``order`` визначає черговість виконання та ієрархію відповідей.
        order_tuple = _parse_order(entry.get("order"))
        if not order_tuple:
            print(
                f"[FLOW writte_all_coments] ⚠️ Пропуск без валідного порядку: {entry}"
            )
            continue

        gender = _normalize_gender(entry.get("gender"))
        text = _normalize_text(str(entry.get("text", "")))
        if not text:
            print(
                f"[FLOW writte_all_coments] ⚠️ Коментар #{'.'.join(map(str, order_tuple))} порожній — пропускаю."
            )
            continue

        prepared.append(
            {
                "__order_tuple": order_tuple,
                "order": ".".join(map(str, order_tuple)),
                "gender": gender,
                "text": str(entry.get("text", "")),
            }
        )

    if not prepared:
        print("[FLOW writte_all_coments] ⚠️ У файлі немає жодного валідного коментаря.")
        return

    # Сортуємо за кортежем порядку, щоб відповіді завжди виконувалися після своїх батьків.
    prepared.sort(key=lambda item: item["__order_tuple"])  # type: ignore[index]
    lookup: Dict[OrderTuple, Dict[str, object]] = {
        item["__order_tuple"]: item for item in prepared  # type: ignore[index]
    }

    # Серійні номери зберігаємо у вигляді рядків, щоб збігатися з форматами AdsPower API.
    available_serials = [str(serial) for serial in user_serial_numbers]
    print(f"[FLOW writte_all_coments] 🧾 Доступні профілі: {available_serials}")

    posted_orders: List[str] = []
    skipped_orders: List[str] = []
    failed_orders: List[Tuple[str, str]] = []

    # ``like_post_reaction`` дозволяє задати реакцію, яку слід поставити перед написанням
    # коментаря. Значення ``none`` використовується як прапорець, що реакцію не потрібно ставити.
    normalized_reaction = (like_post_reaction or "none").strip().lower()

    for comment in prepared:
        # Кожен коментар обробляємо окремо, поступово зменшуючи пул доступних профілів.
        order_tuple = comment["__order_tuple"]  # type: ignore[assignment]
        order_label = str(comment["order"])
        target_gender = str(comment["gender"])
        original_text = str(comment["text"])

        print("\n" + "-" * 80)
        print(f"[FLOW writte_all_coments] ▶️ Обробка коментаря #{order_label}")
        print(
            f"[FLOW writte_all_coments] ℹ️ Очікувана стать: {target_gender or 'невідома'} | Текст: {original_text}"
        )

        if not target_gender:
            print(
                f"[FLOW writte_all_coments] ❌ Для коментаря #{order_label} не вказано стать — не знаю, який профіль обрати."
            )
            failed_orders.append((order_label, "Не вказано стать коментаря"))
            continue

        # Якщо коментар має вигляд "5.1" — це означає, що потрібно готувати відповідь.
        parent_text = ""
        if _is_reply(order_tuple):
            parent_tuple = _parent_order(order_tuple)
            parent_entry = lookup.get(parent_tuple)
            if not parent_entry:
                print(
                    "[FLOW writte_all_coments] ❌ Не знайдено батьківський коментар для відповіді."
                )
                failed_orders.append(
                    (order_label, "Відсутній батьківський коментар у джерелі")
                )
                continue
            parent_text = str(parent_entry.get("text", ""))
            print(
                f"[FLOW writte_all_coments] ↪️ Потрібно відповісти на #{parent_entry.get('order')}"
            )

        # Вибір профілю відбувається по першому збігу статі у доступному списку.
        chosen_serial: Optional[str] = None
        for serial in list(available_serials):
            gender = _fetch_gender(bot.ads, serial)
            print(
                f"[FLOW writte_all_coments] 🔍 Перевіряю профіль {serial}: стать = {gender or 'невідома'}"
            )
            if gender == target_gender:
                chosen_serial = serial
                break

        if chosen_serial is None:
            print(
                f"[FLOW writte_all_coments] ❌ Немає вільного профілю статі {target_gender} для #{order_label}."
            )
            failed_orders.append(
                (order_label, f"Немає профілю статі {target_gender}")
            )
            continue

        print(
            f"[FLOW writte_all_coments] ✅ Вибрано профіль {chosen_serial} для написання коментаря."
        )

        driver_started = False
        remove_serial_from_pool = False
        try:
            # Запускаємо профіль AdsPower і створюємо WebDriver для подальших дій.
            bot.start(chosen_serial)
            driver_started = True

            # Одразу переходимо у нову вкладку з потрібним постом. Якщо сторінка не відкрилась —
            # немає сенсу продовжувати роботу з цим профілем.
            if not bot.open_tab(chosen_serial, url):
                print(
                    f"[FLOW writte_all_coments] ❌ Не вдалося відкрити вкладку з постом для профілю {chosen_serial}."
                )
                failed_orders.append((order_label, "Не відкрився пост"))
            else:
                # Доступ до драйвера беремо через службовий метод бота. Так ми не дублюємо логіку
                # підключення та користуємося вже відкритою сесією Selenium.
                driver: WebDriver = bot._ensure_driver(chosen_serial)  # type: ignore[attr-defined]
                # Невелика стабілізація DOM дозволяє переконатися, що сторінка повністю готова
                # до наступних дій (пошуку елементів, встановлення реакції тощо).
                dom_stability(driver, timeout=8.0, stable_ms=300)

                if normalized_reaction and normalized_reaction != "none":
                    print(
                        f"[FLOW writte_all_coments] ❤️ Ставлю реакцію '{normalized_reaction}' перед коментуванням."
                    )
                    liked = bot.like_post(chosen_serial, normalized_reaction)
                    if liked:
                        print(
                            "[FLOW writte_all_coments] 🟢 Реакцію під постом успішно встановлено."
                        )
                    else:
                        print(
                            "[FLOW writte_all_coments] ⚠️ Не вдалося поставити реакцію, продовжую без неї."
                        )

                containers = _ensure_comments_scanned(driver)

                # Перевіряємо, чи немає на сторінці ідентичного тексту. Якщо він є —
                # просто фіксуємо факт у логах і не витрачаємо зайвих дій.
                _, already_exists = has_same_comment(
                    driver,
                    original_text,
                    containers=containers,
                )
                if already_exists:
                    print(
                        f"[FLOW writte_all_coments] 🟡 Коментар вже присутній на сторінці. Пропускаю написання."
                    )
                    skipped_orders.append(order_label)
                    remove_serial_from_pool = True
                else:
                    # Для відповідей додатково переконуємося, що батьківський коментар присутній у DOM.
                    if parent_text:
                        _, parent_present = has_same_comment(
                            driver,
                            parent_text,
                            containers=containers,
                        )
                        if not parent_present:
                            print(
                                "[FLOW writte_all_coments] ❌ Не знайшов батьківський коментар на сторінці, не можу відповісти."
                            )
                            failed_orders.append(
                                (order_label, "Батьківський коментар відсутній на сторінці")
                            )
                        else:
                            success = bool(bot.writte_replay(chosen_serial, parent_text, original_text))
                            if success:
                                print(
                                    f"[FLOW writte_all_coments] 🟢 Профіль {chosen_serial} завершив коментар #{order_label}."
                                )
                                posted_orders.append(order_label)
                                remove_serial_from_pool = True
                                dom_stability(driver, timeout=6.0, stable_ms=350)
                            else:
                                print(
                                    f"[FLOW writte_all_coments] ❌ Не вдалося підтвердити публікацію коментаря #{order_label}."
                                )
                                failed_orders.append((order_label, "Екшен повернув помилку"))
                    else:
                        success = bool(bot.writte_comment(chosen_serial, original_text))
                        if success:
                            print(
                                f"[FLOW writte_all_coments] 🟢 Профіль {chosen_serial} завершив коментар #{order_label}."
                            )
                            posted_orders.append(order_label)
                            remove_serial_from_pool = True
                            dom_stability(driver, timeout=6.0, stable_ms=350)
                        else:
                            print(
                                f"[FLOW writte_all_coments] ❌ Не вдалося підтвердити публікацію коментаря #{order_label}."
                            )
                            failed_orders.append((order_label, "Екшен повернув помилку"))

        except Exception as exc:
            print(
                f"[FLOW writte_all_coments] ❌ Неочікувана помилка під час коментування #{order_label}: {exc}"
            )
            failed_orders.append((order_label, f"Виключення: {exc}"))
        finally:
            if driver_started:
                try:
                    bot.stop(chosen_serial)
                except Exception as stop_exc:  # pragma: no cover - логування для стабільності.
                    print(
                        f"[FLOW writte_all_coments] ⚠️ Не вдалося коректно зупинити профіль {chosen_serial}: {stop_exc}"
                    )
            if remove_serial_from_pool and chosen_serial in available_serials:
                available_serials.remove(chosen_serial)
            print(
                f"[FLOW writte_all_coments] 📉 Залишилось профілів: {available_serials}"
            )

    print("\n" + "=" * 80)
    print("[FLOW writte_all_coments] 📊 Підсумки виконання сценарію:")
    if failed_orders:
        print(
            f"[FLOW writte_all_coments] ❌ Не вдалося опрацювати {len(failed_orders)} коментар(ів)."
        )
        for order_label, reason in failed_orders:
            print(
                f"[FLOW writte_all_coments]   • #{order_label}: {reason}"
            )
    else:
        print("[FLOW writte_all_coments] ✅ Усі коментарі опрацьовано успішно.")

    if skipped_orders:
        print(
            f"[FLOW writte_all_coments] ℹ️ Пропущено через наявність на сторінці: {skipped_orders}"
        )

    if posted_orders:
        print(
            f"[FLOW writte_all_coments] 🟢 Успішно опубліковано: {posted_orders}"
        )

    print("[FLOW writte_all_coments] 🏁 Сценарій завершено.")
