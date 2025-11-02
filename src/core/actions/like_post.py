import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def like_post(driver, post_url: str) -> bool:
    print(f"[ACTION like_post] 👉 Відкриваю пост: {post_url}")

    # Перехід на пост (як у quick_like)
    driver.execute_script(f"window.location.href = '{post_url}';")
    time.sleep(3)

    # === DOM STABILIZATION ===
    print("[ACTION like_post] 🧠 Стабілізую DOM...")
    prev_html = ""
    stable_count = 0
    for _ in range(5):
        time.sleep(2)
        curr_html = driver.page_source
        if curr_html == prev_html:
            stable_count += 1
            if stable_count >= 2:
                break
        prev_html = curr_html
    print("[ACTION like_post] ✅ DOM стабілізовано.")

    # Легкий scroll вниз — щоб кнопка стала видимою
    try:
        driver.execute_script("window.scrollBy(0, 500);")
    except:
        pass
    time.sleep(1.5)

    # ФУНКЦІЯ ПОШУКУ КНОПКИ LIKE
    def find_like_button():
        selectors = [
            (By.CSS_SELECTOR, "div[aria-label='Like'][role='button']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Like']"),
            (By.CSS_SELECTOR, "div[aria-label='Вподобати'][role='button']"),
            (By.CSS_SELECTOR, "div[aria-label='Нравится'][role='button']"),
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

    # === Перевірити чи лайк вже стоїть (по aria-pressed) ===
    try:
        liked_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-pressed='true']")
        if liked_elements:
            print("[ACTION like_post] ⭐ Пост вже лайкнуто. Пропускаю.")
            return True
    except:
        pass

    print("[ACTION like_post] 👍 Пробую клікнути Like…")

    btn = find_like_button()
    if not btn:
        print("[ACTION like_post] ❌ Не знайдено кнопку Like.")
        return False

    # Навести мишку
    try:
        ActionChains(driver).move_to_element(btn).perform()
        time.sleep(random.uniform(0.8, 1.6))
    except:
        pass

    # 1) Пробуємо стандартний клік
    try:
        btn.click()
        time.sleep(2)

        # Перевіряємо чи лайк поставився
        liked_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-pressed='true']")
        if liked_elements:
            print("[ACTION like_post] ✅ Лайк поставлено (звичайний клік).")
            return True
        else:
            print("[ACTION like_post] ⚠️ Після кліку лайк не змінив статус.")
    except:
        print("[ACTION like_post] ⚠️ Стандартний клік не спрацював, пробую JS…")

    # 2) Fallback JS
    try:
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

        liked_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-pressed='true']")
        if liked_elements:
            print("[ACTION like_post] ✅ Лайк поставлено (через JS).")
            return True

        print("[ACTION like_post] ⚠️ JS клік не змінив статус.")
    except Exception as e:
        print("[ACTION like_post] ❌ Навіть JS-клік не спрацював:", e)
        return False

    print("[ACTION like_post] ❌ Не вдалося поставити лайк.")
    return False
