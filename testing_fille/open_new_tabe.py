# -*- coding: utf-8 -*-
"""
AdsPower + Selenium: відкриття вкладок через CDP і перевірка повного завантаження сторінки
(readyState + DOM-стабілізація + стабілізація мережевих ресурсів)

Працює на Windows. Попап-блокер не заважає, бо вкладки створюються через DevTools-протокол.
"""

import time
import traceback
from typing import Optional, List, Tuple

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# -------------------- Налаштування --------------------
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"  # <-- твій профіль AdsPower
API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"

# Часові константи (підібрані під важкі SPA як Facebook)
PAGE_LOAD_TIMEOUT = 45            # загальний таймаут очікування готовності сторінки, сек
NEW_TAB_APPEAR_TIMEOUT = 12       # очікування появи нового window_handle, сек
DOM_STABLE_WINDOW = 1.8           # скільки секунду DOM/мережа мають бути стабільні
DOM_POLL_INTERVAL = 0.25          # інтервал опитування DOM, сек
DOM_NODES_TOLERANCE = 50          # допустима зміна кількості нод у вікні стабільності
HTML_LEN_TOLERANCE = 800          # допустима зміна довжини innerHTML у вікні стабільності
RES_COUNT_TOLERANCE = 5           # допустима зміна кількості ресурсів у вікні стабільності
# ------------------------------------------------------


# =============== AdsPower API helpers =================

def ads_start_profile(serial_number: str) -> dict:
    return requests.get(
        f"{API_BASE}/api/v1/browser/start",
        params={"serial_number": serial_number},
        timeout=30,
    ).json()


def ads_stop_profile(serial_number: str) -> dict:
    return requests.get(
        f"{API_BASE}/api/v1/browser/stop",
        params={"serial_number": serial_number},
        timeout=15,
    ).json()


# =============== Selenium attach ======================

def attach_to_debugger(debug_port: str, chromedriver_path: Optional[str] = None) -> webdriver.Chrome:
    """Attach до вже запущеного профілю AdsPower через DevTools debug-порт."""
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    # Швидше підключення; готовність сторінки перевіряємо власною логікою
    opts.page_load_strategy = "none"

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(2)
    return driver


# =============== Очікування повного завантаження =======

def _safe_exec(driver, script: str, default=None):
    """Виконати JS і завжди повертати значення (не падати)."""
    try:
        return driver.execute_script(script)
    except Exception:
        return default


def _snapshot_dom_and_perf(driver) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Знімаємо міні-снапшот стану:
    - кількість DOM-нод
    - довжина body.innerHTML
    - кількість завантажених ресурсів за performance API
    """
    dom_nodes = _safe_exec(driver, "return document.getElementsByTagName('*').length", None)
    html_len = _safe_exec(driver, "return document.body ? document.body.innerHTML.length : 0", None)
    res_count = _safe_exec(driver, "return performance.getEntriesByType('resource').length", None)
    return dom_nodes, html_len, res_count


def _is_stable(prev: Tuple[Optional[int], Optional[int], Optional[int]],
               cur: Tuple[Optional[int], Optional[int], Optional[int]]) -> bool:
    """Перевіряємо, що зміни в межах толерантності."""
    (p_nodes, p_html, p_res) = prev
    (c_nodes, c_html, c_res) = cur

    nodes_ok = (p_nodes is None or c_nodes is None) or abs(c_nodes - p_nodes) <= DOM_NODES_TOLERANCE
    html_ok  = (p_html  is None or c_html  is None) or abs(c_html  - p_html ) <= HTML_LEN_TOLERANCE
    res_ok   = (p_res   is None or c_res   is None) or abs(c_res   - p_res  ) <= RES_COUNT_TOLERANCE
    return nodes_ok and html_ok and res_ok


def wait_for_full_page_ready(
    driver,
    timeout: int = PAGE_LOAD_TIMEOUT,
    stable_window: float = DOM_STABLE_WINDOW,
    require_selector: Optional[Tuple[By, str]] = None,
) -> bool:
    """
    Комплексна перевірка “сторінка повністю завантажена”:
      1) document.readyState == 'complete'
      2) DOM/мережа стабільні >= stable_window секунд (із толерантністю)
      3) (опційно) з'явився опорний селектор (наприклад, головний контейнер контенту)

    Повертає True/False.
    """

    t_end = time.time() + timeout

    # Крок 1: readyState == 'complete'
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: _safe_exec(d, "return document.readyState", "") == "complete"
        )
    except TimeoutException:
        print("[wait] ❌ Не дочекався document.readyState == 'complete'.")
        return False

    # (опційний) чек на селектор
    if require_selector is not None:
        by, selector = require_selector
        try:
            WebDriverWait(driver, min(12, timeout)).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            print(f"[wait] ⚠️ Опорний селектор не з'явився: {selector}")

    # Крок 2: стабілізація DOM/мережі
    # DOM/мережа мають бути стабільні безперервно stable_window секунд
    last_snapshot = _snapshot_dom_and_perf(driver)
    stable_since = time.time()

    while time.time() < t_end:
        time.sleep(DOM_POLL_INTERVAL)
        cur = _snapshot_dom_and_perf(driver)

        if _is_stable(last_snapshot, cur):
            # якщо стабільно достатньо довго — готово
            if time.time() - stable_since >= stable_window:
                return True
        else:
            # відкот стабільного відліку
            stable_since = time.time()
            last_snapshot = cur

    print("[wait] ⚠️ DOM/мережа не вийшли на стабільний стан у відведений час.")
    # все ж, якщо readyState був 'complete', можна повернути True/False за політикою:
    # обираю False, щоб не маскувати реальні затримки у важких сторінках
    return False


# =============== Відкриття нової вкладки =================

def open_new_tab_and_wait(
    driver,
    target_url: str,
    require_selector: Optional[Tuple[By, str]] = None,
) -> bool:
    """
    Створює НОВУ вкладку через CDP (обхід попап-блокера),
    перемикається на неї, відкриває target_url і чекає повного завантаження.
    """

    print(f"[tab] 🔄 Відкриваю нову вкладку для: {target_url}")

    # Запам’ятовуємо існуючі хендли
    before_handles: List[str] = driver.window_handles
    before_set = set(before_handles)
    print(f"[tab] ℹ️ Вкладок до: {len(before_handles)}")

    # 1) Створити about:blank, щоб гарантовано отримати handle → потім вже driver.get(target_url)
    try:
        res = driver.execute_cdp_cmd("Target.createTarget", {"url": "about:blank"})
        target_id = res.get("targetId")
        if not target_id:
            print(f"[tab] ❌ Target.createTarget не повернув targetId: {res}")
            return False
        # активуємо нову вкладку
        driver.execute_cdp_cmd("Target.activateTarget", {"targetId": target_id})
        driver.execute_cdp_cmd("Page.bringToFront", {})  # на всяк випадок
        print(f"[tab] ✨ Створив і активував вкладку (targetId={target_id}).")
    except WebDriverException as e:
        print(f"[tab] ❌ Помилка CDP при створенні вкладки: {e}")
        return False

    # 2) Дочекаємось появи Selenium-handle
    new_handle: Optional[str] = None
    deadline = time.time() + NEW_TAB_APPEAR_TIMEOUT
    while time.time() < deadline:
        handles = set(driver.window_handles)
        diff = handles - before_set
        if diff:
            new_handle = diff.pop()
            break
        time.sleep(0.2)

    if not new_handle:
        print("[tab] ❌ Selenium не побачив новий дескриптор вкладки.")
        return False

    # 3) Перемикаємось на нову вкладку, навігуємо
    try:
        driver.switch_to.window(new_handle)
        print("[tab] 🔀 Перейшов у нову вкладку, навігую...")
        driver.get(target_url)
    except Exception as nav_err:
        print(f"[tab] ❌ Помилка навігації: {nav_err}")
        return False

    # 4) Комплексне очікування “повністю завантажено”
    loaded = wait_for_full_page_ready(
        driver,
        timeout=PAGE_LOAD_TIMEOUT,
        stable_window=DOM_STABLE_WINDOW,
        require_selector=require_selector,  # можна передати None або (By.CSS_SELECTOR, "..."),
    )

    if loaded:
        print("[tab] ✅ Сторінка повністю завантажена й стабільна.")
    else:
        print("[tab] ⚠️ Сторінка не досягла стабільного стану за таймаутом.")
    return loaded


# =============== main ==================================

def main():
    print("[main] 🚀 Старт сценарію відкриття вкладок через AdsPower + Selenium")

    driver = None
    profile_started = False

    try:
        print("[main] ▶️ Запускаю профіль AdsPower…")
        start_resp = ads_start_profile(SERIAL_NUMBER)
        print(f"[main] ↩️ Відповідь AdsPower: {start_resp}")

        if start_resp.get("code") != 0:
            raise RuntimeError(f"Помилка запуску профілю: {start_resp}")

        data = start_resp.get("data", {})
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")

        if not debug_port:
            raise RuntimeError("Не отримав debug_port — не можу під’єднатися до профілю.")

        print(f"[main] 🛠️ Debug port: {debug_port}")
        print("[main] 🔌 Підключаюсь до існуючого браузера…")
        driver = attach_to_debugger(debug_port, chromedriver_path)
        profile_started = True
        print("[main] ✅ Підключення успішне.")

        # Тестові посилання (Facebook)
        links = [
            "https://www.facebook.com/photo/?fbid=850312507680833&set=a.561033343275419",
            "https://www.facebook.com/photo/?fbid=814649828090919&set=a.115800767975832",
            "https://www.facebook.com/photo/?fbid=1353897506100628&set=a.363229598500762",
        ]

        # (опційно) опорний селектор — наприклад, головний контейнер контенту fb
        # Якщо не хочеш чекати конкретний елемент — передай require_selector=None нижче
        fb_anchor: Optional[Tuple[By, str]] = None
        # Приклад: fb_anchor = (By.CSS_SELECTOR, "div[role='main']")

        for i, url in enumerate(links, start=1):
            print(f"\n[main] 📄 Обробляю посилання #{i}: {url}")
            ok = open_new_tab_and_wait(driver, url, require_selector=fb_anchor)
            print(f"[main] ➤ Результат: {'OK' if ok else 'FAIL'}")
            time.sleep(3)

        print("\n[main] 🏁 Готово.")

    except Exception as e:
        print(f"[main] 💥 Критична помилка: {e}")
        traceback.print_exc()

    finally:
        if profile_started:
            print("[main] ⛔ Зупиняю профіль AdsPower…")
            try:
                stop_resp = ads_stop_profile(SERIAL_NUMBER)
                print(f"[main] ↩️ Відповідь на stop: {stop_resp}")
            except Exception as stop_err:
                print(f"[main] ⚠️ Не вдалося коректно зупинити профіль: {stop_err}")

        if driver:
            print("[main] ❎ Закриваю драйвер Selenium…")
            try:
                driver.quit()
            except Exception as quit_err:
                print(f"[main] ⚠️ Помилка при закритті драйвера: {quit_err}")

        print("[main] 👋 Кінець сценарію.")


if __name__ == "__main__":
    main()
