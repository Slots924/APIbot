"""Розкриття додаткових коментарів у стрічці (включно з реплаями)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .dom_stability import wait_dom_stable
from .human_pause import human_pause


def expand_more_comments(driver: WebDriver, max_clicks: int = 3) -> None:
    """
    Натискає кнопки:
      • “View more comments”
      • “View 1 reply” / “View replies”
    щоб завантажити верхні коментарі та вкладені відповіді.
    """

    # ---------- XPATH-и ----------

    # Кнопки "more comments"
    more_comments_xpaths = [
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//span[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'more comments')]",
        "//div[@role='button'][contains(.,'View') and contains(.,'more')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'коментар')]",
        "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'комментар')]",
    ]

    # Кнопки "View 1 reply / View replies"
    replies_xpaths = [
        "//*[(@role='button' or @role='link') "
        "and contains(translate(string(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'reply') "
        "and (contains(translate(string(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'view') "
        "or contains(translate(string(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),' replies') "
        "or contains(translate(string(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),' reply'))]",

        "//*[(@role='button' or @role='link') "
        "and .//span[@dir='auto' and "
        "contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'reply')]]",
    ]

    per_iter_limits = {
        "more_comments": 4,
        "replies": 6,
    }

    # ---------- ДОПОМІЖНІ ----------

    def visible_text(el):
        try:
            return (driver.execute_script("return arguments[0].innerText || '';", el) or "").strip()
        except Exception:
            try:
                return (el.text or "").strip()
            except Exception:
                return ""

    def looks_like_pure_reply(txt_lower: str) -> bool:
        norm = " ".join(txt_lower.split())
        return norm == "reply" or norm.startswith("reply ")

    def click_center(el):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            human_pause(0.1, 0.25)
            el.click()
            human_pause(0.2, 0.4)
            return True
        except Exception:
            return False

    def _click_visible_buttons(xpaths, per_iter_limit, group_name):
        clicked = 0
        for xp in xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xp)
            except Exception:
                buttons = []

            visible = []
            for b in buttons:
                try:
                    if b.is_displayed():
                        visible.append(b)
                except Exception:
                    continue

            for btn in visible[: max(0, per_iter_limit - clicked)]:
                txt = visible_text(btn).lower()
                if group_name == "replies" and looks_like_pure_reply(txt):
                    continue
                if click_center(btn):
                    clicked += 1
                    wait_dom_stable(driver, timeout=5.0, stable_ms=300)
                if clicked >= per_iter_limit:
                    break

            if clicked >= per_iter_limit:
                break

        return clicked

    # ---------- ОСНОВНИЙ ЦИКЛ ----------

    for step in range(1, max_clicks + 1):
        print(f"\n🔄 Ітерація #{step}")
        total_clicked = 0

        total_clicked += _click_visible_buttons(
            more_comments_xpaths,
            per_iter_limits["more_comments"],
            "more_comments",
        )

        total_clicked += _click_visible_buttons(
            replies_xpaths,
            per_iter_limits["replies"],
            "replies",
        )

        if total_clicked == 0:
            break

        wait_dom_stable(driver, timeout=8.0, stable_ms=300)

    print("\n✅ Закінчив розкривати коментарі")
