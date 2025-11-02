import time
import random
from selenium.webdriver.common.by import By


def like_post(driver, post_url: str) -> bool:
    print(f"[ACTION like_post] 👉 Відкриваю пост: {post_url}")

    # Переходимо так, як у quick_like
    try:
        driver.execute_script(f"window.location.href = '{post_url}';")
        time.sleep(4 + 5)  # +5сек для повільного проксі
    except:
        pass

    # --- Скролимо вниз, щоб з'явився блок з лайком ---
    try:
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
    except:
        pass

    def find_like_button():
        selectors = [
            (By.CSS_SELECTOR, "div[aria-label='Like'][role='button']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Like']"),
            (By.CSS_SELECTOR, "[aria-label*='Like']"),
            (By.CSS_SELECTOR, "div[aria-label='Нравится'][role='button']"),
            (By.CSS_SELECTOR, "div[aria-label='Вподобати'][role='button']"),
        ]
        for by, sel in selectors:
            try:
                els = driver.find_elements(by, sel)
                if els:
                    return els[0]
            except:
                pass
        return None

    btn = find_like_button()
    if not btn:
        print("[ACTION like_post] 😕 Не знайдено кнопку Like.")
        return False

    print("[ACTION like_post] 👍 Пробую клікнути Like…")

    # 1️⃣ Спроба нормального кліку
    try:
        btn.click()
        time.sleep(1.8 + 5)
        print("[ACTION like_post] ✅ Лайк поставлено (звичайний клік).")
        return True
    except:
        print("[ACTION like_post] ⚠️ Стандартний клік не спрацював, пробую JS…")

    # 2️⃣ Спроба через JS
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.8 + 5)
        print("[ACTION like_post] ✅ Лайк поставлено (через JS).")
        return True
    except Exception as e2:
        print(f"[ACTION like_post] ❌ Не вдалося поставити лайк навіть через JS: {e2}")
        return False
