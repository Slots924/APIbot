# -*- coding: utf-8 -*-
"""
Like reactions on target comments under a Facebook post (AdsPower + Selenium 4).
- Prints header with account id, post url, and target prefixes
- Matches comments by prefix (case-insensitive, trimmed, normalized spaces)
- Sets 'Like' reaction (others: stubs ready)
- Verifies state before & after; detailed console logs
"""

import json
import random
import time
import typing as t
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    JavascriptException,
)

# ===================== CONFIG / HEADER =====================
ACCOUNT_ID = 214
POST_URL = "https://www.facebook.com/share/p/1CwNcFNiuD/"
COMMENTS_TO_LIKE = ["I’m honestly shocked by their relationship dynamics. It’s wild how everything turned out!", "Похуй"]  # префікси коментарів

ADSP_POWER_BASE = "http://localhost:50325"
DOM_STABLE_MIN_MS = 800
DOM_STABLE_TIMEOUT_S = 25
SCROLL_ONCE_PX = 540

GENERIC_LIKE_SELECTORS = [
    # aria-label на кнопці
    "//div[@role='button' and (@aria-label='Like' or @aria-label='J’aime' or @aria-label='Me gusta' or @aria-label='Подобається' or @aria-label='Нравится')]",
    # кнопка в блоці дій коментаря з текстом
    "//div[@role='button'][.//span[text()='Like' or text()='J’aime' or text()='Me gusta' or text()='Подобається' or text()='Нравится']]",
    # інколи кнопка — <span role="button">...
    "//span[@role='button'][.='Like' or .='J’aime' or .='Me gusta' or .='Подобається' or .='Нравится']",
]

LIKED_STATE_XP = [
    ".//*[@aria-pressed='true']",
    ".//*[@aria-checked='true']",
    ".//*[contains(@class,'active') or contains(@class,'liked')]",
]

# ===================== AdsPower helpers =====================
def _adspower_start_profile(profile_id: str) -> dict:
    resp = requests.get(f"{ADSP_POWER_BASE}/api/v1/browser/start", params={"user_id": profile_id}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"AdsPower start error: {data}")
    return data["data"]

def _adspower_stop_profile(profile_id: str) -> None:
    try:
        requests.get(f"{ADSP_POWER_BASE}/api/v1/browser/stop", params={"user_id": profile_id}, timeout=30)
    except Exception:
        pass

def _start_driver_via_adspower(profile_id: str) -> WebDriver:
    info = _adspower_start_profile(profile_id)
    if "webdriver" in info and info["webdriver"]:
        return webdriver.Remote(command_executor=info["webdriver"], options=webdriver.ChromeOptions())
    elif "ws" in info and info["ws"]:
        opts = webdriver.ChromeOptions()
        opts.debugger_address = info["ws"].replace("ws://", "").replace("wss://", "")
        return webdriver.Chrome(options=opts)
    else:
        raise RuntimeError(f"Unknown AdsPower start response: {info}")

# ===================== Low-level utils (узгоджені зі стилем у твоєму коді) =====================
def _human_sleep(a: float, b: float):
    time.sleep(random.uniform(a, b))

def _wait_dom_stable(driver: WebDriver, timeout_s=DOM_STABLE_TIMEOUT_S, min_ms=DOM_STABLE_MIN_MS) -> bool:
    end = time.time() + timeout_s
    last_len = None
    stable_since = None
    while time.time() < end:
        try:
            html_len = driver.execute_script("return document.documentElement.outerHTML.length")
        except Exception:
            _human_sleep(0.2, 0.5)
            continue
        now = time.time()
        if last_len == html_len:
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) * 1000 >= min_ms:
                return True
        else:
            last_len = html_len
            stable_since = None
        _human_sleep(0.12, 0.28)
    return False

def _navigate_via_js(driver: WebDriver, url: str):
    driver.execute_script(f"window.location.href = {json.dumps(url)}")

def _soft_scroll_once(driver: WebDriver, px=SCROLL_ONCE_PX):
    try:
        driver.execute_script(f"window.scrollBy(0,{int(px)});")
    except JavascriptException:
        pass
    _human_sleep(0.25, 0.55)

def _normalize_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()

def _get_inner_text(driver: WebDriver, el) -> str:
    try:
        return driver.execute_script("return arguments[0].innerText || arguments[0].textContent || '';", el) or ""
    except Exception:
        try:
            return el.text or ""
        except Exception:
            return ""

def _element_is_liked(el) -> bool:
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

def _find_like_button_within_comment(comment_el):
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

def _click_like_safely(driver: WebDriver, btn) -> bool:
    for _ in range(2):
        try:
            _ = btn.location_once_scrolled_into_view
            _human_sleep(0.08, 0.18)
            btn.click()
            _human_sleep(0.15, 0.3)
            return True
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", btn)
                _human_sleep(0.12, 0.25)
                return True
            except Exception:
                pass
        except Exception:
            pass
        _human_sleep(0.18, 0.35)
    return False

def _expand_more_comments(driver: WebDriver, max_clicks: int = 3):
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
                        print(f"[react_comments] ▶️  expand_more_comments: clicked '{_normalize_text(b.text)[:40]}'")
                        _human_sleep(0.45, 0.9)
                except Exception:
                    continue
        if not clicked:
            break
        _wait_dom_stable(driver, timeout_s=10, min_ms=400)

def _collect_comment_containers(driver: WebDriver) -> list:
    xpaths = [
        "//div[@role='article'][.//div[@role='button']]",  # часто весь коментар
        "//ul[contains(@class,'comment')]/li//div[.//div[@role='button']]",
        "//div[.//*[@aria-label='Like' or @aria-label='J’aime' or @aria-label='Me gusta' or @aria-label='Подобається' or @aria-label='Нравится']]",
    ]
    seen, results = set(), []
    for xp in xpaths:
        try:
            els = driver.find_elements(By.XPATH, xp)
        except Exception:
            els = []
        for el in els:
            try:
                key = el.id
                if key not in seen and el.is_displayed():
                    seen.add(key)
                    results.append(el)
            except StaleElementReferenceException:
                continue
    return results

# ===================== Reaction layer =====================
SUPPORTED_REACTIONS = {"like", "love", "care", "haha", "wow", "sad", "angry"}

def _set_reaction_on_comment(driver: WebDriver, comment_el, reaction: str) -> bool:
    """
    Реально ставить реакцію на коментар.
    Зараз повна реалізація для 'like', для решти — заглушки (місце для твого коду).
    """
    reaction = (reaction or "like").lower().strip()
    if reaction not in SUPPORTED_REACTIONS:
        print(f"[react_comments] ⚠️  unknown reaction '{reaction}', fallback -> 'like'")
        reaction = "like"

    # === LIKE (реалізовано) ===
    if reaction == "like":
        btn = _find_like_button_within_comment(comment_el)
        if not btn:
            print("[react_comments] ❌ like button not found in comment container")
            return False

        if _element_is_liked(btn):
            print("[react_comments] ℹ️  already liked (pre-check)")
            return True

        if not _click_like_safely(driver, btn):
            print("[react_comments] ❌ failed to click like button")
            return False

        # підтвердження після кліку
        try:
            btn2 = _find_like_button_within_comment(comment_el) or btn
            if _element_is_liked(btn2):
                print("[react_comments] ✅ like applied (post-check)")
                return True
        except StaleElementReferenceException:
            # FB часто перерендерить у liked-стан
            print("[react_comments] ✅ like assumed (stale after click)")
            return True

        print("[react_comments] ❌ like not confirmed after click")
        return False

    # === OTHER REACTIONS (STUBS) ===
    # тут залишив структуровані заглушки — підключиш свій код відкриття реакційного палітри і вибору іконки:
    try:
        print(f"[react_comments] ▶️  set reaction stub: '{reaction}' (TODO implement palette hover + select)")
        # TODO:
        # 1) знайти базову кнопку реакцій (ту ж кнопку дій біля коментаря)
        # 2) навести курсор (hover) ~600–900 мс, дочекатися палітри
        # 3) клікнути по відповідній іконці (aria-label='Love'/'Haha'/'Wow'/...)
        # 4) підтвердити стан (текст/іконка/aria-pressed)
        return False  # поки що повертаємо False, щоб у логах було видно "заглушку"
    except Exception as e:
        print(f"[react_comments] ❌ reaction stub error: {e}")
        return False

# ===================== MAIN =====================
def react_comments_under_post(
    profile_id: str,
    post_url: str,
    comment_prefixes: t.List[str],
    reaction: str = "like",
    limit: int = 0
) -> dict:
    """
    Основна функція:
    - відкриває AdsPower профіль і пост
    - розкриває треди
    - знаходить коментарі, чиї тексти ПОЧИНАЮТЬСЯ з будь-якого з префіксів
    - ставить реакцію (default: like) з перед- і після-перевіркою стану
    - детальні логи
    """
    print("============================================================")
    print(f"[HEADER] account_id: {ACCOUNT_ID}")
    print(f"[HEADER] post_url  : {post_url}")
    print(f"[HEADER] targets   : {comment_prefixes}")
    print(f"[HEADER] reaction  : {reaction}")
    print("============================================================")

    stats = {"found": 0, "matched": 0, "already": 0, "reacted": 0, "failed": 0}

    driver = None
    try:
        print("[react_comments] 🚀 starting AdsPower profile & driver…")
        driver = _start_driver_via_adspower(profile_id)
        driver.set_page_load_timeout(120)

        print(f"[react_comments] 👉 navigate via JS to post")
        _navigate_via_js(driver, post_url)
        _wait_dom_stable(driver)
        _human_sleep(0.6, 1.0)

        print("[react_comments] 🖱️ soft scroll once + expand more comments")
        _soft_scroll_once(driver, SCROLL_ONCE_PX)
        _expand_more_comments(driver, max_clicks=3)

        print("[react_comments] 🔎 collecting comment containers…")
        comments = _collect_comment_containers(driver)
        stats["found"] = len(comments)
        print(f"[react_comments] ℹ️  total visible comment containers: {stats['found']}")

        if limit > 0:
            comments = comments[:limit]

        normalized_prefixes = [_normalize_text(p) for p in comment_prefixes if (p or "").strip()]

        for idx, c in enumerate(comments, 1):
            # ре-стабілізація між коментарями
            _wait_dom_stable(driver, timeout_s=8, min_ms=300)

            # отримати текст коментаря
            try:
                text = _get_inner_text(driver, c)
            except StaleElementReferenceException:
                print(f"[react_comments] [{idx}] ⚠️ stale container, skipping")
                continue

            norm_text = _normalize_text(text)
            if not norm_text:
                continue

            # префіксний матч
            matched_prefix = next((p for p in normalized_prefixes if norm_text.startswith(p)), None)
            if not matched_prefix:
                continue

            stats["matched"] += 1
            preview = text.strip().replace("\n", " ")[:120]
            print(f"[react_comments] [{idx}] 🎯 match: '{preview}'")

            # знайти кнопку і зробити pre-check стану для 'like'
            if reaction.lower() == "like":
                btn = _find_like_button_within_comment(c)
                if btn and _element_is_liked(btn):
                    stats["already"] += 1
                    print(f"[react_comments] [{idx}] ℹ️ already liked → skip")
                    _human_sleep(0.15, 0.35)
                    continue

            ok = _set_reaction_on_comment(driver, c, reaction)
            if ok:
                stats["reacted"] += 1
                print(f"[react_comments] [{idx}] ✅ reaction '{reaction}' applied")
            else:
                stats["failed"] += 1
                print(f"[react_comments] [{idx}] ❌ failed to apply reaction '{reaction}'")

            _human_sleep(0.25, 0.7)

        print("------------------------------------------------------------")
        print(f"[react_comments] ✅ DONE | found={stats['found']} matched={stats['matched']} "
              f"already={stats['already']} reacted={stats['reacted']} failed={stats['failed']}")
        print("------------------------------------------------------------")
        return stats

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        _adspower_stop_profile(profile_id)

# ===================== Example run =====================
if __name__ == "__main__":
    # Виклик з твоїми вимогами:
    react_comments_under_post(
        profile_id=str(ACCOUNT_ID),
        post_url=POST_URL,
        comment_prefixes=COMMENTS_TO_LIKE,
        reaction="like"  # можна "love"/"haha"/"wow"/"sad"/"angry" — зараз це заглушки
    )
