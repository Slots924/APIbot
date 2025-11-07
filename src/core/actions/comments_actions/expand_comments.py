"""Розкриття додаткових коментарів у стрічці (включно з реплаями)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from ..helpers import dom_stability, human_pause


def expand_comments(driver: WebDriver, max_clicks: int = 5) -> None:
    """Скролить стрічку коментарів, доки не покаже всі елементи."""

    print("\n=== 🧩 Починаю розкриття коментарів ===")

    more_comments_xpaths = [
        "//div[@role='button'][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//span[@role='button'][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
        "//div[@role='button'][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'коментар')]",
        "//div[@role='button'][contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'комментар')]",
    ]

    replies_candidate_xpath = "//*[(@role='button' or @role='link') and string-length(normalize-space(string(.)))>0]"

    per_iter_limits = {"more_comments": 4, "replies": 8}

    def _normalize_text(s: str) -> str:
        if not s:
            return ""
        s = s.replace("\u00A0", " ")
        s = " ".join(s.split())
        return s.lower()

    REPLY_KEYS = ("repl", "відпов", "ответ")
    VIEW_KEYS = ("view", "перегля", "показ", "посмотр", "показать")
    HIDE_KEYS = ("hide", "схов", "скрыт")

    def _text_has_any(text: str, keys: tuple) -> bool:
        return any(k in text for k in keys)

    def _looks_like_expand_replies(text_raw: str) -> bool:
        """Визначає, чи це кнопка розгортання реплаїв."""

        t = _normalize_text(text_raw)
        if not t:
            return False
        if _text_has_any(t, HIDE_KEYS):
            return False
        if not _text_has_any(t, REPLY_KEYS):
            return False

        if t.strip() in ("reply", "відповісти", "ответить"):
            return False

        if _text_has_any(t, VIEW_KEYS):
            return True

        if any(ch.isdigit() for ch in t):
            return True

        return False

    def element_has_size(el) -> bool:
        try:
            r = el.rect
            return r.get("width", 0) > 0 and r.get("height", 0) > 0
        except Exception:
            return False

    def inner_text(el) -> str:
        try:
            return (driver.execute_script("return arguments[0].innerText || '';", el) or "").strip()
        except Exception:
            try:
                return (el.text or "").strip()
            except Exception:
                return ""

    def click_element(el) -> bool:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            human_pause(0.1, 0.25)
            el.click()
            human_pause(0.25, 0.4)
            return True
        except Exception:
            return False

    def scan_scroll(step_px: int = 450, repeats: int = 2):
        try:
            for _ in range(repeats):
                driver.execute_script(f"window.scrollBy(0, {step_px});")
                human_pause(0.2, 0.35)
                driver.execute_script(f"window.scrollBy(0, {-step_px//2});")
                human_pause(0.2, 0.35)
        except Exception:
            pass

    def _click_more_comments(xpaths, limit):
        clicked = 0
        for xp in xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xp)
            except Exception:
                buttons = []
            for btn in buttons:
                if clicked >= limit:
                    break
                try:
                    if not btn.is_displayed() or not element_has_size(btn):
                        continue
                    if click_element(btn):
                        clicked += 1
                        dom_stability(driver, timeout=5.0, stable_ms=300)
                except Exception:
                    continue
        return clicked

    def _click_replies(limit):
        clicked = 0
        try:
            candidates = driver.find_elements(By.XPATH, replies_candidate_xpath)
        except Exception:
            candidates = []
        for el in candidates:
            if clicked >= limit:
                break
            try:
                if not el.is_displayed() or not element_has_size(el):
                    continue
                txt_raw = inner_text(el)
                if not _looks_like_expand_replies(txt_raw):
                    continue
                target = el
                try:
                    inner_span = el.find_element(By.XPATH, ".//span[@dir='auto']")
                    if inner_span and element_has_size(inner_span):
                        target = inner_span
                except Exception:
                    pass
                if click_element(target):
                    clicked += 1
                    dom_stability(driver, timeout=5.0, stable_ms=300)
            except Exception:
                continue
        return clicked

    for step in range(1, max_clicks + 1):
        print(f"\n🔄 Ітерація #{step}")
        total_clicked = 0
        total_clicked += _click_more_comments(more_comments_xpaths, per_iter_limits["more_comments"])
        total_clicked += _click_replies(per_iter_limits["replies"])
        if total_clicked == 0:
            scan_scroll()
            more = _click_replies(per_iter_limits["replies"])
            if more == 0:
                break
        dom_stability(driver, timeout=8.0, stable_ms=300)

    print("\n✅ Закінчив розкривати коментарі\n")
