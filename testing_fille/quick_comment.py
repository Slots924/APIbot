import time
import random
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ---------- Налаштування ----------
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"
POST_URL = "https://www.facebook.com/share/p/1CwNcFNiuD/"
COMMENT_TEXT = "I’m shocked by their relationship... 😳\nThere’s so much more going on behind the scenes!"
# -----------------------------------

API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"


def ads_start_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/start",
                        params={"serial_number": sn}, timeout=30).json()


def ads_stop_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/stop",
                        params={"serial_number": sn}, timeout=15).json()


def attach_to_debugger(debug_port: str, chromedriver_path: str = None):
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    opts.page_load_strategy = "none"  # прискорює підключення

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(3)
    return driver


def human_type(element, text, min_delay=0.04, max_delay=0.22):
    """Друкує по-символьно з паузами, як реальна людина"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))


def main():
    print("[*] Старт тесту комента…")

    driver = None
    started = False

    try:
        print("[*] Стартую профіль у AdsPower…")
        resp = ads_start_profile(SERIAL_NUMBER)
        print(resp)

        if resp.get("code") != 0:
            raise RuntimeError(resp)

        data = resp.get("data", {})
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")

        if not debug_port:
            raise RuntimeError("debug_port не знайдено у відповіді AdsPower.")

        print(f"[*] Debug port: {debug_port}")
        print("[*] Підключаюсь до браузера…")
        driver = attach_to_debugger(debug_port, chromedriver_path)
        started = True

        # Перехід на пост через JS (J1)
        print("[*] Переходжу на пост через JS…")
        driver.execute_script(f"window.location.href = '{POST_URL}';")
        time.sleep(5)

        # Скрол трохи вниз, щоб поле комента було видимо
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)

        print("[*] Шукаю поле для коментаря…")

        comment_box = None
        selectors = [
            (By.CSS_SELECTOR, "div[aria-label='Write a comment…']"),
            (By.CSS_SELECTOR, "div[aria-label='Write a comment']"),
            (By.CSS_SELECTOR, "div[aria-label='Напишите комментарий…']"),
            (By.CSS_SELECTOR, "div[aria-label='Написати коментар…']"),
            (By.CSS_SELECTOR, "div[role='textbox']"),
        ]

        for by, sel in selectors:
            try:
                els = driver.find_elements(by, sel)
                if els:
                    comment_box = els[0]
                    break
            except:
                pass

        if not comment_box:
            print("😕 Не вдалося знайти поле для коментаря.")
            return

        print("[*] Клікаю у поле…")
        comment_box.click()
        time.sleep(1)

        print("[*] Друкую коментар як людина…")
        human_type(comment_box, COMMENT_TEXT)

        time.sleep(0.6)
        comment_box.send_keys("\n")  # Enter для відправки
        time.sleep(2)

        print("✅ Коментар залишено!")

    except Exception as e:
        print("❌ ПОМИЛКА:", e)
        traceback.print_exc()

    finally:
        if started:
            print("[*] Зупиняю профіль у AdsPower…")
            try:
                ads_stop_profile(SERIAL_NUMBER)
            except:
                pass

        try:
            if driver:
                driver.quit()
        except:
            pass

        print("[*] Кінець.")


if __name__ == "__main__":
    main()