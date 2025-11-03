# -*- coding: utf-8 -*-
"""
React to target comments under a Facebook post (AdsPower serial_number + debugger attach).
- Header: account id, post_url, targets
- Args: (post_url, comment_prefixes, reaction='like')
- Prefix matching (case-insensitive)
- Like implemented with pre/post checks; other reactions = stubs
"""

import time
import json
import random
import requests
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    JavascriptException,
)

# ===================== YOUR ENV (as in your working file) =====================
ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"

SERIAL_NUMBER = "214"  # <-- як у твоєму прикладі
ACCOUNT_ID = 214       # для шапки

# Твої вимоги для демо
POST_URL = "https://www.facebook.com/share/p/1CwNcFNiuD/"
COMMENTS_TO_LIKE = [
    "I’m honestly shocked by their relationship dynamics. It’s wild how everything turned out!",
    "Похуй",
]

# ===================== FB/UX tunables =====================
DOM_STABLE_TIMEOUT = 25
DOM_STABLE_MIN_TICKS = 3
DOM_STABLE_INTERVAL = 0.6

SCROLL_ONCE_PX = 540

GENERIC_LIKE_SELECTORS = [
    "//div[@role='button' and (@aria-label='Like' or @aria-label='J’aime' or @aria-label='Me gusta' or @aria-label='Подобається' or @aria-label='Нравится')]",
    "//div[@role='button'][.//span[text()='Like' or text()='J’aime' or text()='Me gusta' or text()='Подобається' or text()='Нравится']]",
    "//span[@role='button'][.='Like' or .='J’aime' or .='Me gusta' or .='Подобається' or .='Нравится']",
]

LIKED_STATE_XP = [
    ".//*[@aria-pressed='true']",
    ".//*[@aria-checked='true']",
    ".//*[contains(@class,'active') or contains(@class,'liked')]",
]

SUPPORTED_REACTIONS = {"like", "love", "care", "haha", "wow", "sad", "angry"}

# ===================== AdsPower: start/stop like your sample =====================
def ads_start_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/start",
                        params={"serial_number": sn}, timeout=30).json()

def ads_stop_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/stop",
                        params={"serial_number": sn}, timeout=15).json()

def attach_to_debugger(debug_port: str, chromedriver_path: str | None = None):
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    try:
        opts.page_load_strategy = "none"  # не чекаємо повного лоаду — працюємо через JS
    except Exception:
        pass
    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(2)
    return driver

# ===================== Helpers (враховано твої поради) =====================
def human_sleep(a: float, b: float):
    time.sleep(random.uniform(a, b))

def dom_stable(driver, timeout=DOM_STABLE_TIMEOUT, interval=DOM_STABLE_INTERVAL, min_ticks=DOM_STABLE_MIN_TICKS):
    last = None
    stable = 0
    start = time.time()
    while time.time() - start < timeout:
        html = driver.page_source
        if html == last:
            stable += 1
            if stable >= min_ticks:
                return True
        else:
            stable = 0
            last = html
        time.sleep(interval)
    return False

def navigate_via_js(driver, url: str):
    driver.execute_script(f"window.location.href = {json.dumps(url)}")

def soft_scroll_once(driver, px=SCROLL_ONCE_PX):
    try:
        driver.execute_script(f"window.scrollBy(0,{int(px)});")
    except JavascriptException:
        pass
    human_sleep(0.25, 0.55)

def normalize(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()

def get_inner_text(driver, el) -> str:
    try:
        return driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", el) or ""
    except Exception:
        try:
            return el.text or ""
        except Exception:
            return ""

def element_is_liked(el) -> bool:
    try:
        pressed = (el.get_attribute("aria-pressed") or el.get_attribute("aria-checked") or "").lower()
        if pressed == "true":
            return True
    except StaleElementReferenceException:
        return False
    for xp in LIKED_STATE_XP:
        try:
            if el.find_elements(By.XPATH, xp):
                return True
        except StaleElementReferenceException:
            return False
    return False

def find_like_button_within_comment(comment_el):
    for xp in GENERIC_LIKE_SELECTORS:
        try:
            found = comment_el.find_elements(By.XPATH, xp)
            for btn in found:
                try:
                    if btn.is_displayed():
                        return btn
                except StaleElementReferenceException:
                    continue
        except StaleElementReferenceException:
            return None
    return None

def click_like_safely(driver, btn) -> bool:
    for _ in range(2):
        try:
            _ = btn.location_once_scrolled_into_view
            human_sleep(0.08, 0.18)
            btn.click()
            human_sleep(0.15, 0.3)
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", btn)
                human_sleep(0.12, 0.25)
                return True
            except Exception:
                pass
        except Exception:
            pass
        human_sleep(0.18, 0.35)
    return False

def expand_more_comments(driver, max_clicks: int = 3):
    patterns = [
        "//div[@role='button'][.//span[contains(.,'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas')]]",
        "//span[@role='button' and (contains(.,'more comments') or contains(.,'коментар') or contains(.,'комментар') or contains(.,'réponses') or contains(.,'respuestas'))]",
        "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
    ]
    for step in range(max_clicks):
        clicked = False
        for xp in patterns:
            try:
                btns = driver.find_elements(By.XPATH, xp)
            except Exception:
                btns = []
            for b in btns[:2]:
                try:
                    if b.is_displayed():
                        driver.execute_script("arguments[0].click();", b)
                        clicked = True
                        print(f"[expand] ▶ click '{normalize(b.text)[:40]}'")
                        human_sleep(0.45, 0.9)
                except Exception:
                    continue
        if not clicked:
            break
        dom_stable(driver, timeout=10, interval=0.4, min_ticks=2)

def collect_comment_containers(driver) -> list:
    xpaths = [
        "//div[@role='article'][.//div[@role='button']]",           # частий випадок
        "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
        "//div[.//*[@aria-label='Like' or @aria-label='J’aime' or @aria-label='Me gusta' or @aria-label='Подобається' or @aria-label='Нравится']]",
    ]
    seen, out = set(), []
    for xp in xpaths:
        try:
            els = driver.find_elements(By.XPATH, xp)
        except Exception:
            els = []
        for el in els:
            try:
                if el.id not in seen and el.is_displayed():
                    seen.add(el.id)
                    out.append(el)
            except StaleElementReferenceException:
                continue
    return out

# ===================== Reactions =====================
def set_reaction_on_comment(driver, comment_el, reaction: str) -> bool:
    reaction = (reaction or "like").lower().strip()
    if reaction not in SUPPORTED_REACTIONS:
        print(f"[react] ⚠ unknown reaction '{reaction}', fallback -> like")
        reaction = "like"

    if reaction == "like":
        btn = find_like_button_within_comment(comment_el)
        if not btn:
            print("[react] ❌ like button not found")
            return False

        # pre-check
        if element_is_liked(btn):
            print("[react] ℹ already liked (pre-check)")
            return True

        if not click_like_safely(driver, btn):
            print("[react] ❌ click failed")
            return False

        # post-check
        try:
            btn2 = find_like_button_within_comment(comment_el) or btn
            if element_is_liked(btn2):
                print("[react] ✅ like confirmed (post-check)")
                return True
        except StaleElementReferenceException:
            print("[react] ✅ like assumed (stale after click)")
            return True

        print("[react] ❌ like not confirmed")
        return False

    # stubs for other reactions
    print(f"[react] ▶ stub for '{reaction}' — TODO: open palette (hover) and click icon by aria-label")
    return False

# ===================== MAIN FUNCTION (signature you asked) =====================
def react_comments_under_post(post_url: str, comment_prefixes: List[str], reaction: str = "like") -> dict:
    """
    Args:
        post_url: посилання на пост
        comment_prefixes: список початків коментарів (prefix-match)
        reaction: реакція (default: like). Інші реакції поки як заглушки.
    Returns:
        stats dict
    """
    # ---- HEADER
    print("============================================================")
    print(f"[HEADER] account_id: {ACCOUNT_ID}")
    print(f"[HEADER] post_url  : {post_url}")
    print(f"[HEADER] targets   : {comment_prefixes}")
    print(f"[HEADER] reaction  : {reaction}")
    print("============================================================")

    # ---- Start AdsPower profile (serial_number) and attach
    driver = None
    started = False
    stats = {"found": 0, "matched": 0, "already": 0, "reacted": 0, "failed": 0}

    try:
        print("[adspower] 🚀 start profile via serial_number…")
        resp = ads_start_profile(SERIAL_NUMBER)
        print(f"[adspower] response: {resp}")
        if resp.get("code") != 0:
            raise RuntimeError(resp)

        data = resp.get("data", {}) or {}
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")
        if not debug_port:
            raise RuntimeError("debug_port не знайдено у відповіді AdsPower.")

        print(f"[adspower] 🧩 debugger port: {debug_port}")
        driver = attach_to_debugger(debug_port, chromedriver_path)
        started = True

        # ---- Navigate via JS and stabilize
        print("[nav] 👉 go to post via JS")
        navigate_via_js(driver, post_url)
        time.sleep(2.5)
        dom_stable(driver, timeout=12)

        # ---- Minimal human behavior
        print("[ux] 🖱️ soft scroll once & expand more comments")
        soft_scroll_once(driver, SCROLL_ONCE_PX)
        expand_more_comments(driver, max_clicks=3)

        # ---- Collect comments
        print("[scan] 🔎 collecting comment containers…")
        comments = collect_comment_containers(driver)
        stats["found"] = len(comments)
        print(f"[scan] ℹ total visible containers: {stats['found']}")

        prefixes = [normalize(p) for p in comment_prefixes if (p or "").strip()]

        for idx, c in enumerate(comments, 1):
            dom_stable(driver, timeout=8, interval=0.4, min_ticks=2)
            try:
                txt = get_inner_text(driver, c)
            except StaleElementReferenceException:
                print(f"[scan] [{idx}] ⚠ stale container, skip")
                continue

            nt = normalize(txt)
            if not nt:
                continue

            matched = next((p for p in prefixes if nt.startswith(p)), None)
            if not matched:
                continue

            stats["matched"] += 1
            preview = txt.strip().replace("\n", " ")[:120]
            print(f"[match] [{idx}] 🎯 '{preview}'")

            # pre-check just for like
            if reaction.lower() == "like":
                btn = find_like_button_within_comment(c)
                if btn and element_is_liked(btn):
                    stats["already"] += 1
                    print(f"[match] [{idx}] ℹ already liked → skip")
                    human_sleep(0.15, 0.35)
                    continue

            ok = set_reaction_on_comment(driver, c, reaction)
            if ok:
                stats["reacted"] += 1
                print(f"[apply] [{idx}] ✅ reaction '{reaction}' applied")
            else:
                stats["failed"] += 1
                print(f"[apply] [{idx}] ❌ failed to apply '{reaction}'")

            human_sleep(0.25, 0.7)

        print("------------------------------------------------------------")
        print(f"[done] ✅ found={stats['found']} matched={stats['matched']} "
              f"already={stats['already']} reacted={stats['reacted']} failed={stats['failed']}")
        print("------------------------------------------------------------")
        return stats

    finally:
        # AdsPower stop + driver quit
        if started:
            print("[adspower] ⏹ stopping profile…")
            try:
                ads_stop_profile(SERIAL_NUMBER)
            except Exception:
                pass
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

# ===================== Example run (same header you asked) =====================
if __name__ == "__main__":
    react_comments_under_post(
        post_url=POST_URL,
        comment_prefixes=COMMENTS_TO_LIKE,
        reaction="like"
    )
