#!/usr/bin/env python3
# quick_like.py — тест лайку в AdsPower профілі (перехід через JS, без driver.get)

import time
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ---------- Налаштування ----------
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"  # SN профілю AdsPower
POST_URL = "https://www.facebook.com/photo/?fbid=1669832114466241&set=pcb.1669832301132889"
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
    opts.page_load_strategy = "none"  # щоб не чекати повного лоду

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(3)
    return driver


def find_like_button(driver):
    selectors = [
        (By.CSS_SELECTOR, "div[aria-label='Like'][role='button']"),
        (By.XPATH, "//div[@role='button' and @aria-label='Like']"),
        (By.CSS_SELECTOR, "div[aria-label='Нравится'][role='button']"),  # RU
        (By.CSS_SELECTOR, "div[aria-label='Вподобати'][role='button']"), # UA
        (By.CSS_SELECTOR, "[aria-label*='Like']"),
    ]
    for by, sel in selectors:
        try:
            els = driver.find_elements(by, sel)
            if els:
                return els[0]
        except:
            pass
    return None


def main():
    print("[*] Старт тесту лайку…")

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

        # ------- ПЕРЕХІД НА ПОСТ ЧЕРЕЗ JS -------
        print("[*] Переходжу на пост через JS…")
        driver.execute_script(f"window.location.href = '{POST_URL}';")
        time.sleep(4)  # дати FB завантажитись

        # Легкий скрол, щоб кнопка з’явилась
        try:
            driver.execute_script("window.scrollBy(0, 400);")
        except:
            pass
        time.sleep(1)

        btn = find_like_button(driver)
        if not btn:
            print("😕 Не знайдено кнопку Like.")
            return

        print("[*] Пробую клікнути Like…")

        # 1) Спроба звичайного кліку
        try:
            btn.click()
            time.sleep(1)
            print("✅ Лайк поставлено (звичайний клік).")
        except Exception:
            print("⚠️ Стандартний клік не спрацював, пробую JS...")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.4)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                print("✅ Лайк поставлено (через JavaScript).")
            except Exception as e2:
                print("❌ Навіть JS-клік не спрацював:", e2)
                return

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
