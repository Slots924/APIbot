"""Логіка відкриття нової вкладки через CDP з очікуванням стабільності DOM.

Файл створено на основі робочого прикладу з ``testing_fille/open_new_tabe.py``.
Містить допоміжні утиліти для комплексної перевірки завантаження сторінки
та сам екшен ``open_new_tab``. Всі коментарі та логи українською мовою,
щоб пояснити кроки новачку.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# --------- Константи часу (підібрані під повільні SPA на кшталт Facebook) ---------
PAGE_LOAD_TIMEOUT = 45            # максимальний час очікування готовності сторінки, сек
NEW_TAB_APPEAR_TIMEOUT = 12       # таймаут очікування появи нового window handle, сек
DOM_STABLE_WINDOW = 1.8           # скільки секунд DOM має бути стабільним
DOM_POLL_INTERVAL = 0.25          # інтервал опитування DOM під час стабілізації, сек
DOM_NODES_TOLERANCE = 50          # допустима зміна кількості DOM-вузлів
HTML_LEN_TOLERANCE = 800          # допустима зміна довжини innerHTML
RES_COUNT_TOLERANCE = 5           # допустима зміна кількості завантажених ресурсів


# ====================== Допоміжні утиліти для DOM-стабілізації ======================

def _safe_exec(driver: WebDriver, script: str, default=None):
    """Виконати JS-скрипт і гарантовано повернути значення, навіть якщо сталася помилка."""

    try:
        return driver.execute_script(script)
    except Exception:
        return default


def _snapshot_dom_and_perf(driver: WebDriver) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Зібрати «снапшот» DOM: кількість вузлів, довжину body.innerHTML та число ресурсів."""

    dom_nodes = _safe_exec(driver, "return document.getElementsByTagName('*').length", None)
    html_len = _safe_exec(
        driver,
        "return document.body ? document.body.innerHTML.length : 0",
        None,
    )
    res_count = _safe_exec(
        driver,
        "return performance.getEntriesByType('resource').length",
        None,
    )
    return dom_nodes, html_len, res_count


def _is_stable(
    prev: Tuple[Optional[int], Optional[int], Optional[int]],
    cur: Tuple[Optional[int], Optional[int], Optional[int]],
) -> bool:
    """Перевірити, що різниця між снапшотами лежить у межах толерантності."""

    p_nodes, p_html, p_res = prev
    c_nodes, c_html, c_res = cur

    nodes_ok = (p_nodes is None or c_nodes is None) or abs(c_nodes - p_nodes) <= DOM_NODES_TOLERANCE
    html_ok = (p_html is None or c_html is None) or abs(c_html - p_html) <= HTML_LEN_TOLERANCE
    res_ok = (p_res is None or c_res is None) or abs(c_res - p_res) <= RES_COUNT_TOLERANCE
    return nodes_ok and html_ok and res_ok


def wait_for_full_page_ready(
    driver: WebDriver,
    timeout: int = PAGE_LOAD_TIMEOUT,
    stable_window: float = DOM_STABLE_WINDOW,
    require_selector: Optional[Tuple[By, str]] = None,
) -> bool:
    """Комплексно перевірити, що сторінка повністю завантажилася й стабілізувалася."""

    deadline = time.time() + timeout

    # 1. Очікуємо document.readyState == 'complete'.
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: _safe_exec(d, "return document.readyState", "") == "complete"
        )
    except TimeoutException:
        print("[ACTION open_new_tab] ❌ Не дочекався стану document.readyState == 'complete'.")
        return False

    # 2. За потреби перевіряємо появу опорного селектора.
    if require_selector is not None:
        by, selector = require_selector
        try:
            WebDriverWait(driver, min(timeout, 12)).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            print(
                "[ACTION open_new_tab] ⚠️ Опорний селектор не з'явився: "
                f"{selector}. Продовжую перевірку стабільності DOM."
            )

    # 3. Чекаємо стабільності DOM протягом stable_window секунд.
    last_snapshot = _snapshot_dom_and_perf(driver)
    stable_since = time.time()

    while time.time() < deadline:
        time.sleep(DOM_POLL_INTERVAL)
        current_snapshot = _snapshot_dom_and_perf(driver)

        if _is_stable(last_snapshot, current_snapshot):
            if time.time() - stable_since >= stable_window:
                return True
        else:
            # Якщо DOM змінився — перезапускаємо відлік стабільності.
            stable_since = time.time()
            last_snapshot = current_snapshot

    print("[ACTION open_new_tab] ⚠️ DOM не стабілізувався у відведений час.")
    return False


# =========================== Основна дія відкриття вкладки ===========================

def open_new_tab(
    driver: WebDriver,
    target_url: str,
    require_selector: Optional[Tuple[By, str]] = None,
) -> bool:
    """Відкрити нову вкладку, перейти на ``target_url`` та дочекатися стабілізації сторінки."""

    print(f"[ACTION open_new_tab] 🔄 Створюю нову вкладку для: {target_url}")

    # Запам'ятовуємо існуючі дескриптори, щоб визначити нову вкладку.
    existing_handles = set(driver.window_handles)
    print(f"[ACTION open_new_tab] ℹ️ Кількість вкладок до створення: {len(existing_handles)}")

    # Крок 1. Через CDP створюємо about:blank і активуємо її.
    try:
        result = driver.execute_cdp_cmd("Target.createTarget", {"url": "about:blank"})
        target_id = result.get("targetId")
        if not target_id:
            print(
                "[ACTION open_new_tab] ❌ Target.createTarget не повернув targetId."
            )
            return False

        driver.execute_cdp_cmd("Target.activateTarget", {"targetId": target_id})
        driver.execute_cdp_cmd("Page.bringToFront", {})
        print(f"[ACTION open_new_tab] ✨ Вкладку створено й активовано (targetId={target_id}).")
    except WebDriverException as error:
        print(f"[ACTION open_new_tab] ❌ Помилка CDP при створенні вкладки: {error}")
        return False

    # Крок 2. Чекаємо появи нового Selenium window handle.
    new_handle: Optional[str] = None
    deadline = time.time() + NEW_TAB_APPEAR_TIMEOUT
    while time.time() < deadline:
        current_handles = set(driver.window_handles)
        diff = current_handles - existing_handles
        if diff:
            new_handle = diff.pop()
            break
        time.sleep(0.2)

    if not new_handle:
        print("[ACTION open_new_tab] ❌ Selenium не побачив нову вкладку.")
        return False

    # Крок 3. Перемикаємося на вкладку і виконуємо навігацію.
    try:
        driver.switch_to.window(new_handle)
        print("[ACTION open_new_tab] 🔀 Перейшов у нову вкладку. Починаю навігацію…")
        driver.get(target_url)
    except Exception as navigation_error:
        print(f"[ACTION open_new_tab] ❌ Не вдалося перейти за посиланням: {navigation_error}")
        return False

    # Крок 4. DOM-стабілізація + перевірка готовності.
    loaded = wait_for_full_page_ready(
        driver,
        timeout=PAGE_LOAD_TIMEOUT,
        stable_window=DOM_STABLE_WINDOW,
        require_selector=require_selector,
    )

    if loaded:
        print("[ACTION open_new_tab] ✅ Сторінка повністю завантажена та стабільна.")
    else:
        print("[ACTION open_new_tab] ⚠️ Сторінка не вийшла на стабільний стан за таймаутом.")

    return loaded


__all__ = ["open_new_tab", "wait_for_full_page_ready"]

