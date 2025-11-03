#!/usr/bin/env python3
# Facebook Like test for AdsPower — using aria-label + like_button marker only
# + Post-click verification

import time
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# ------------ CONFIG ------------
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"
POST_URL = "https://www.facebook.com/photo/?fbid=817298384343945&set=a.137234542350336"
# --------------------------------

API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"


def ads_start_profile(sn: str) -> dict:
    return requests.get(
        f"{API_BASE}/api/v1/browser/start",
        params={"serial_number": sn},
        timeout=30
    ).json()


def ads_stop_profile(sn: str) -> dict:
    return requests.get(
        f"{API_BASE}/api/v1/browser/stop",
        params={"serial_number": sn},
        timeout=15
    ).json()


def attach_to_debugger(debug_port: str, chromedriver_path: str = None):
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    opts.page_load_strategy = "none"

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(2)
    return driver


# --------- CORE FB LIKE LOGIC (BASED ON YOUR HTML) ---------

def find_like_button(driver):
    """
    Повертає саме головну кнопку Like, всередині якої є data-ad-rendering-role='like_button'.
    Ігнорує кнопку 'Change Like reaction'.
    """
    markers = driver.find_elements(By.CSS_SELECTOR, "[data-ad-rendering-role='like_button']")
    for marker in markers:
        try:
            btn = marker.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
            aria = (btn.get_attribute("aria-label") or "").lower()
            if "like" in aria:  # ловить 'like' та 'remove like'
                return btn
        except:
            pass
    return None


def is_liked(driver):
    """
    True  → лайк стоїть
    False → лайку немає
    None  → кнопку не знайдено
    """
    btn = find_like_button(driver)
    if not btn:
        return None

    aria = (btn.get_attribute("aria-label") or "").lower()
    if "remove like" in aria:
        return True
    if "like" in aria:
        return False
    return None


def click_like(driver):
    btn = find_like_button(driver)
    if not btn:
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.3)
        btn.click()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", btn)
            return True
        except:
            return False


# --------------------------- MAIN ---------------------------

def main():
    print("[*] START")

    driver = None
    started = False

    try:
        print("[*] Starting AdsPower profile...")
        resp = ads_start_profile(SERIAL_NUMBER)
        print(resp)

        if resp.get("code") != 0:
            raise RuntimeError(resp)

        data = resp["data"]
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")

        driver = attach_to_debugger(debug_port, chromedriver_path)
        started = True

        # go to post
        driver.execute_script(f"window.location.href = '{POST_URL}';")
        time.sleep(4)

        driver.execute_script("window.scrollBy(0, 350)")
        time.sleep(1)

        state_before = is_liked(driver)
        print(f"[i] BEFORE state: {state_before}")

        if state_before is True:
            print("👍 Like already exists — skipping")

        elif state_before is False:
            print("[*] Trying to like...")
            for attempt in range(3):
                ok = click_like(driver)
                time.sleep(1.2)

                # ---- POST-CLICK RECHECK ----
                post_state = is_liked(driver)
                print(f"Attempt {attempt+1} → after click: {post_state}")

                if post_state is True:
                    print("✅ LIKE CONFIRMED")
                    break
            else:
                print("❌ FAILED to set like after 3 attempts")

        else:
            print("⚠️ Could not detect like status at start (None)")

        # final double-check
        time.sleep(1)
        final_state = is_liked(driver)
        print(f"[i] FINAL state after full flow: {final_state}")

    except Exception as e:
        print("❌ ERROR:", e)
        traceback.print_exc()

    finally:
        if started:
            try:
                ads_stop_profile(SERIAL_NUMBER)
            except:
                pass

        try:
            if driver:
                driver.quit()
        except:
            pass

        print("[*] END")


if __name__ == "__main__":
    main()
