import time
import random
import requests
from typing import Optional, List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, JavascriptException

# ===================== CONFIG =====================
ADSPOWER_HOST = "127.0.0.1"
ADSPOWER_PORT = 50325
SERIAL = "214"
BASE = f"http://{ADSPOWER_HOST}:{ADSPOWER_PORT}"

POST_URL = "https://www.facebook.com/photo/?fbid=815878634634705&set=a.115800767975832"

DOM_STABLE_FOR_SEC = 1.8
DOM_STABLE_TIMEOUT = 45
OPEN_TAB_TIMEOUT = 30
OVERLAY_APPEAR_TIMEOUT = 10
FIND_ITEM_TIMEOUT = 8

# Підписи для пункту "Найновіші"
NEWEST_EXACT = [
    "most recent", "newest",
    "найновіші", "нові спочатку",
    "новые", "самые новые", "новейшие"
]
NEWEST_PARTS = [
    "recent", "newest", "новей", "найнов", "нові", "новые"
]

# ===================== AdsPower API =====================
def ads_start(serial: str):
    return requests.get(f"{BASE}/api/v1/browser/start", params={"serial_number": serial}).json()

def ads_stop(serial: str):
    return requests.get(f"{BASE}/api/v1/browser/stop", params={"serial_number": serial}).json()

# ===================== Driver attach =====================
def attach(debug_port: str, driver_path: str) -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    # FB — SPA; не чекаємо повне завантаження кожної навігації
    opts.page_load_strategy = "none"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(2)
    return driver

# ===================== Helpers =====================
def human_pause(a=0.25, b=0.6):
    time.sleep(random.uniform(a, b))

def js(driver, script, *args):
    return driver.execute_script(script, *args)

def dom_stabilized(driver, timeout=DOM_STABLE_TIMEOUT, still_for=DOM_STABLE_FOR_SEC) -> bool:
    """
    Стабілізація DOM: вимірюємо довжину outerHTML кореня; вважаємо стабільним,
    якщо не змінюється ≥ still_for секунд, але не довше timeout.
    """
    end = time.time() + timeout
    last_len = None
    stable_since = None

    while time.time() < end:
        try:
            cur_len = js(driver, "return document.documentElement.outerHTML.length")
        except JavascriptException:
            human_pause(0.2, 0.4)
            continue

        if last_len is None or cur_len != last_len:
            last_len = cur_len
            stable_since = time.time()
        else:
            if time.time() - stable_since >= still_for:
                return True
        human_pause(0.15, 0.35)
    return False

def wait_ready(driver, timeout=35):
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
    except TimeoutException:
        pass
    # Додатково – стабілізація DOM
    dom_stabilized(driver, timeout=max(8, timeout), still_for=DOM_STABLE_FOR_SEC)

def open_in_new_tab_via_cdp(driver, url: str, timeout=OPEN_TAB_TIMEOUT) -> Optional[str]:
    """
    Відкриває нову вкладку через CDP Target.createTarget і повертає її handle.
    """
    before = set(driver.window_handles)
    driver.execute_cdp_cmd("Target.createTarget", {"url": "about:blank"})
    # Чекаємо появи нового handle
    end = time.time() + timeout
    while time.time() < end:
        now = set(driver.window_handles)
        diff = list(now - before)
        if diff:
            new_handle = diff[0]
            driver.switch_to.window(new_handle)
            # Навігація через driver.get — ок, але одразу після цього додамо стабілізацію
            driver.get(url)
            wait_ready(driver)
            return new_handle
        human_pause(0.2, 0.4)
    return None

def move_cursor_away_and_clear_popups(driver):
    """
    Перед взаємодією з основною сторінкою — відвести мишу і закрити випадкові підказки/попапи.
    УВАГА: НЕ використовувати цю функцію після відкриття меню сортування, інакше ESC закриє меню.
    """
    try:
        ActionChains(driver).move_by_offset(-800, 0).perform()
        human_pause(0.1, 0.2)
        ActionChains(driver).send_keys("\ue00c").perform()  # ESC
    except Exception:
        pass

def try_click(driver, el) -> bool:
    try:
        js(driver, "arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
        human_pause()
        ActionChains(driver).move_to_element(el).perform()
        human_pause()
        el.click()
        return True
    except ElementClickInterceptedException:
        # JS fallback
        try:
            js(driver, "arguments[0].click();", el)
            return True
        except Exception as e:
            print("[click] JS fallback failed:", e)
            return False
    except Exception as e:
        print("[click] failed:", e)
        return False

def visible(e) -> bool:
    try:
        return e.is_displayed() and e.size.get("height", 0) > 0 and e.size.get("width", 0) > 0
    except Exception:
        return False

# ===================== Sorting controls =====================
def find_sort_button(driver):
    """
    Пошук кнопки сортування коментарів:
    орієнтуємось на aria-меню: role='button' і aria-haspopup='menu' / aria-expanded.
    Далі — якоримося на тексті поруч (не обов'язково), але без жорстких залежностей.
    """
    candidates: List = driver.find_elements(
        By.XPATH,
        "//*[@role='button' and (@aria-haspopup='menu' or @aria-expanded or @aria-controls)]"
    )
    candidates = [c for c in candidates if visible(c)]

    if not candidates:
        return None

    # Спроба відсортувати за “ймовірністю”: ті, що мають у тексті згадки про коменти/сортування.
    def score_button(b) -> int:
        t = (b.get_attribute("innerText") or "").strip().lower()
        score = 0
        if any(x in t for x in ["most", "recent", "newest", "comments", "all comments", "коментар", "комментар"]):
            score += 2
        # ближче до середини екрана — краще
        try:
            rect = js(driver, "const r=arguments[0].getBoundingClientRect(); return [r.top, r.left];", b)
            if rect:
                top = rect[0]
                # ціль — десь у середині екрана
                score += max(0, 3 - abs(top - 400)//150)
        except Exception:
            pass
        return score

    candidates.sort(key=score_button, reverse=True)
    return candidates[0] if candidates else None

def wait_overlay_menu(driver, timeout=OVERLAY_APPEAR_TIMEOUT):
    """
    Чекаємо появи активного overlay-меню (role='menu' або 'dialog'),
    що реально видиме (не aria-hidden) і має розміри.
    """
    end = time.time() + timeout
    while time.time() < end:
        menus = driver.find_elements(By.XPATH, "//*[@role='menu' or @role='dialog']")
        menus = [m for m in menus if visible(m)]
        # Деякі меню — без ролей: пробуємо типові overlay-контейнери Facebook
        if not menus:
            overlays = driver.find_elements(By.XPATH, "//*[contains(@style,'z-index') or contains(@class,'layer') or contains(@class,'overlay')]")
            menus = [o for o in overlays if visible(o)]
        if menus:
            # Виберемо той, що найвище (грубо — найбільший zIndex)
            try:
                best = max(
                    menus,
                    key=lambda m: int(js(driver, "return parseInt(getComputedStyle(arguments[0]).zIndex)||0;", m))
                )
            except Exception:
                best = menus[0]
            return best
        human_pause(0.2, 0.35)
    return None

def find_newest_item_in_menu(driver, menu) -> Optional[object]:
    """
    Пошук пункту 'Most recent / Newest / Найновіші / Новые / Новейшие'.
    Без чутливості до регістру, працює навіть якщо текст фрагментований.
    """
    # 1) радіо/меню айтеми
    items = menu.find_elements(By.XPATH, ".//*[@role='menuitem' or @role='menuitemradio' or @role='option' or @role='button']")
    items = [i for i in items if visible(i)]
    if not items:
        # інколи потрібні “глибші” елементи
        items = menu.find_elements(By.XPATH, ".//*")
        items = [i for i in items if visible(i)]

    def is_newest(el) -> bool:
        text = (el.get_attribute("innerText") or "").lower()
        # нормалізуємо пробіли
        text = " ".join(text.split())
        if not text:
            return False
        if any(text == v for v in NEWEST_EXACT):
            return True
        if any(part in text for part in NEWEST_PARTS):
            # уникаємо “news”
            if "news" in text and "newest" not in text:
                return False
            return True
        return False

    for it in items:
        try:
            if is_newest(it):
                return it
        except Exception:
            continue
    return None

# ===================== MAIN FLOW =====================
def sort_comments_newest_on_post(driver, url: str) -> bool:
    """
    Відкриває пост у новій вкладці, вмикає сортування коментарів на "Найновіші",
    чекає 10 секунд і закриває цю вкладку.
    """
    print("[flow] Відкриваю пост у новій вкладці через CDP…")
    new_handle = open_in_new_tab_via_cdp(driver, url)
    if not new_handle:
        print("[flow] ❌ Не вдалося відкрити вкладку")
        return False

    print("[flow] Стабілізую DOM…")
    wait_ready(driver)

    print("[flow] Очищаю випадкові попапи (до взаємодії)…")
    move_cursor_away_and_clear_popups(driver)

    print("[flow] Шукаю кнопку сортування коментарів…")
    btn = find_sort_button(driver)
    if not btn:
        print("[flow] ❌ Не знайшов кнопку сортування")
        driver.close()
        return False

    print("[flow] Клікаю по кнопці сортування…")
    if not try_click(driver, btn):
        print("[flow] ❌ Не вдалося натиснути кнопку сортування")
        driver.close()
        return False

    print("[flow] Чекаю появу overlay-меню…")
    menu = wait_overlay_menu(driver, timeout=OVERLAY_APPEAR_TIMEOUT)
    if not menu:
        print("[flow] ❌ Меню не зʼявилось")
        driver.close()
        return False

    print("[flow] Шукаю пункт 'Найновіші/Most recent/Newest'…")
    item = find_newest_item_in_menu(driver, menu)
    if not item:
        print("[flow] ❌ Пункт 'Найновіші' не знайдено")
        driver.close()
        return False

    print("[flow] Клікаю 'Найновіші'…")
    if not try_click(driver, item):
        print("[flow] ❌ Не вдалося натиснути 'Найновіші'")
        driver.close()
        return False

    # Невелика стабілізація після вибору
    human_pause(0.6, 1.2)
    dom_stabilized(driver, timeout=10, still_for=1.0)

    print("[flow] ⏳ Чекаю 10 секунд…")
    time.sleep(10)

    print("[flow] Закриваю вкладку…")
    try:
        driver.close()
    except Exception:
        pass

    print("[flow] ✅ Готово")
    return True

def main():
    print("[main] 🚀 START")
    driver = None
    try:
        start = ads_start(SERIAL)
        print("[main] AdsPower start:", start.get("code"), start.get("msg"))

        data = start.get("data", {}) or {}
        debug = data.get("debug_port")
        path = data.get("webdriver")
        if not (debug and path):
            print("[main] ❌ Немає debug_port або webdriver у відповіді AdsPower")
            return

        driver = attach(debug, path)
        print("[main] ✅ Attached")

        ok = sort_comments_newest_on_post(driver, POST_URL)
        print("[main] flow result:", ok)

    finally:
        print("[main] 🧹 Зупиняю профіль…")
        try:
            ads_stop(SERIAL)
        except Exception:
            pass
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        print("[main] ✅ DONE")

if __name__ == "__main__":
    main()
