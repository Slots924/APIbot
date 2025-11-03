import time
import traceback
from typing import List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

# -------------------- Базові налаштування --------------------
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"  # Вказуємо конкретний профіль AdsPower
API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"
PAGE_LOAD_TIMEOUT = 40  # сек, скільки чекаємо на повне завантаження вкладки
# --------------------------------------------------------------


def ads_start_profile(serial_number: str) -> dict:
    """Запускає профіль AdsPower і повертає відповідь API."""
    return requests.get(
        f"{API_BASE}/api/v1/browser/start",
        params={"serial_number": serial_number},
        timeout=30,
    ).json()


def ads_stop_profile(serial_number: str) -> dict:
    """Зупиняє профіль AdsPower (щоб після тесту не висів зайвий процес)."""
    return requests.get(
        f"{API_BASE}/api/v1/browser/stop",
        params={"serial_number": serial_number},
        timeout=15,
    ).json()


def attach_to_debugger(debug_port: str, chromedriver_path: str = None):
    """Під'єднує Selenium до вже запущеного браузера AdsPower через debug-порт."""
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    opts.page_load_strategy = "none"  # Підключаємось швидше, ніж вкладка встигне завантажитися

    # Якщо AdsPower повернув шлях до chromedriver — використовуємо його, інакше стандартний.
    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(3)
    return driver


def wait_for_page_ready(driver, timeout: int = PAGE_LOAD_TIMEOUT) -> bool:
    """Очікує, поки document.readyState стане 'complete'."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState == 'complete';")
        )
        return True
    except TimeoutException:
        return False


def open_new_tab(driver, target_url: str) -> bool:
    """Відкриває нову вкладку з потрібною адресою та чекає повного завантаження."""
    print(f"[open_new_tab] 🔄 Починаю відкривати нову вкладку для {target_url}")

    existing_handles: List[str] = driver.window_handles
    print(f"[open_new_tab] ℹ️ Поточна кількість вкладок: {len(existing_handles)}")

    try:
        # Спершу відкриваємо порожнє вікно через JS, щоб обійти блокування pop-up.
        driver.execute_script("window.open('about:blank', '_blank');")
        print("[open_new_tab] ✨ Створив нову порожню вкладку через window.open().")
    except Exception as create_err:
        print(f"[open_new_tab] ❌ Не вдалося створити вкладку: {create_err}")
        return False

    # Фіксуємо новий дескриптор вкладки, коли він з'явиться.
    new_handle: Optional[str] = None
    for _ in range(20):
        handles = driver.window_handles
        if len(handles) > len(existing_handles):
            new_handle = list(set(handles) - set(existing_handles))[0]
            print(f"[open_new_tab] ✅ Отримав новий дескриптор вкладки: {new_handle}")
            break
        time.sleep(0.3)

    if not new_handle:
        print("[open_new_tab] ❌ Не побачив нову вкладку у списку дескрипторів.")
        return False

    # Переключаємось на нову вкладку.
    driver.switch_to.window(new_handle)
    print("[open_new_tab] 🔁 Перейшов у нову вкладку.")

    try:
        # Через driver.get() відкриваємо лінк, таким чином обходимо обмеження фейсбуку/гугла.
        driver.get(target_url)
        print("[open_new_tab] 🌐 Надіслав запит на завантаження сторінки.")
    except Exception as nav_err:
        print(f"[open_new_tab] ❌ Помилка при навігації: {nav_err}")
        return False

    fully_loaded = wait_for_page_ready(driver)
    if fully_loaded:
        print("[open_new_tab] ✅ Сторінка повністю завантажена.")
    else:
        print("[open_new_tab] ⚠️ Сторінка не встигла повністю завантажитися за таймаутом.")

    return fully_loaded


def main():
    """Точка входу до тесту: стартує профіль, відкриває кілька вкладок і завершує роботу."""
    print("[main] 🚀 Старт тесту відкриття вкладок через AdsPower…")

    driver = None
    profile_started = False

    try:
        print("[main] ▶️ Запускаю профіль AdsPower…")
        start_resp = ads_start_profile(SERIAL_NUMBER)
        print(f"[main] ↩️ Відповідь AdsPower: {start_resp}")

        if start_resp.get("code") != 0:
            raise RuntimeError(f"AdsPower повернув помилку: {start_resp}")

        data = start_resp.get("data", {})
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")

        if not debug_port:
            raise RuntimeError("Не отримав debug_port від AdsPower, не можу під'єднатися.")

        print(f"[main] 🛠️ Debug port: {debug_port}")
        print("[main] 🔌 Підключаюсь до браузера…")
        driver = attach_to_debugger(debug_port, chromedriver_path)
        profile_started = True
        print("[main] ✅ Підключення успішне.")

        links = [
            "https://www.facebook.com/photo/?fbid=850312507680833&set=a.561033343275419",
            "https://www.facebook.com/photo/?fbid=814649828090919&set=a.115800767975832",
            "https://www.facebook.com/photo/?fbid=1353897506100628&set=a.363229598500762",
        ]

        for index, link in enumerate(links, start=1):
            print(f"[main] 📄 Обробляю посилання #{index}: {link}")
            success = open_new_tab(driver, link)
            print(f"[main] ⏱️ Чекаю 5 секунд перед наступною спробою… (успіх={success})")
            time.sleep(5)

        print("[main] 🏁 Тест завершено.")

    except Exception as main_err:
        print(f"[main] 💥 Виникла помилка: {main_err}")
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

        print("[main] 👋 Кінець тесту.")


if __name__ == "__main__":
    main()
