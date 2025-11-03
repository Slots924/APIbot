# src/core/actions/comment_post/comment_post.py

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ----------------- HELPERS -----------------


def _focus_comment_box(driver):
    """Шукає і фокусує поле коментування, повертає WebElement або None."""
    selectors = [
        (By.CSS_SELECTOR, "div[aria-label='Leave a comment'][contenteditable='true']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"),
        (By.XPATH, "//div[@contenteditable='true']"),
    ]

    for _ in range(5):  # до 5 спроб на випадок перерендеру
        for by, sel in selectors:
            try:
                elems = driver.find_elements(by, sel)
                for el in elems:
                    if el.is_displayed():
                        try:
                            el.click()
                        except Exception:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", el)
                        time.sleep(1.0)
                        return True
            except Exception:
                pass
        time.sleep(1)

    return False


def _type_like_human(driver, text):
    """Вводить текст у поле, імітуючи людину, через CDP insertText."""
    for ch in text:
        try:
            driver.execute_cdp_cmd("Input.insertText", {"text": ch})
        except Exception:
            # запасний варіант — send_keys у active element
            try:
                driver.switch_to.active_element.send_keys(ch)
            except:
                pass
        time.sleep(random.uniform(0.07, 0.21))


def _press_enter_cdp(driver):
    """Реальна клавіша Enter через CDP (не символ '\n')."""
    # keyDown
    driver.execute_cdp_cmd("Input.dispatchKeyEvent", {
        "type": "keyDown",
        "key": "Enter",
        "code": "Enter",
        "windowsVirtualKeyCode": 13,
        "nativeVirtualKeyCode": 13
    })
    # keyUp
    driver.execute_cdp_cmd("Input.dispatchKeyEvent", {
        "type": "keyUp",
        "key": "Enter",
        "code": "Enter",
        "windowsVirtualKeyCode": 13,
        "nativeVirtualKeyCode": 13
    })


def _press_enter_selenium(driver):
    """Запасний Enter через Selenium у активний елемент."""
    try:
        ae = driver.switch_to.active_element
        ae.send_keys(Keys.ENTER)
        return True
    except Exception:
        return False


def _click_post_button(driver) -> bool:
    """Фінальний варіант — знайти кнопку Post/Comment і натиснути."""
    selectors = [
        # текстові
        (By.XPATH, "//div[@role='button' and (text()='Post' or text()='Comment' or text()='Опублікувати' or text()='Коментувати' or text()='Надіслати')]"),
        # aria-label
        (By.XPATH, "//div[@role='button' and (@aria-label='Post' or @aria-label='Comment' or @aria-label='Опублікувати' or @aria-label='Коментувати' or @aria-label='Надіслати')]"),
        # часткові збіги
        (By.CSS_SELECTOR, "div[role='button'][aria-label*='Post']"),
        (By.CSS_SELECTOR, "div[role='button'][aria-label*='Comment']"),
    ]

    for by, sel in selectors:
        try:
            btns = driver.find_elements(by, sel)
            for b in btns:
                if b.is_displayed():
                    try:
                        b.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", b)
                    time.sleep(2)
                    return True
        except Exception:
            continue

    return False


def _is_comment_posted(driver, text: str) -> bool:
    """Перевіряє чи з'явився коментар у DOM."""
    try:
        return text[:8] in driver.page_source  # простий, але ефективний варіант
    except Exception:
        return False


# ----------------- MAIN ACTION -----------------

def comment_post(driver, text: str) -> bool:
    """
    Повноцінно пише та відправляє коментар під постом Facebook.
    Повертає True/False.
    """

    # На цьому етапі вважаємо, що сторінка з постом уже відкрита зовнішньою логікою,
    # тому зосереджуємося на пошуку поля та надсиланні коментаря.
    print("[ACTION comment_post] 🚀 Починаю взаємодію з уже відкритим постом.")

    print("[ACTION comment_post] 🟦 Фокусую поле коментаря…")
    if not _focus_comment_box(driver):
        print("[ACTION comment_post] ❌ Не вдалося знайти/активувати поле коментаря.")
        return False

    print("[ACTION comment_post] ✍️ Ввожу текст…")
    _type_like_human(driver, text)

    # даємо FB зафіксувати введення
    time.sleep(1.2)

    print("[ACTION comment_post] 📩 Відправляю коментар...")

    # 1) CDP Enter
    try:
        _press_enter_cdp(driver)
        time.sleep(2)
        if _is_comment_posted(driver, text):
            print("[ACTION comment_post] ✅ Коментар опубліковано (CDP Enter).")
            return True
    except Exception:
        pass

    # 2) Selenium Enter
    if _press_enter_selenium(driver):
        time.sleep(2)
        if _is_comment_posted(driver, text):
            print("[ACTION comment_post] ✅ Коментар опубліковано (Selenium Enter).")
            return True

    # 3) Кнопка Post/Comment
    if _click_post_button(driver):
        time.sleep(2)
        if _is_comment_posted(driver, text):
            print("[ACTION comment_post] ✅ Коментар опубліковано (кнопка).")
            return True

    print("[ACTION comment_post] ❌ Коментар не знайдено після всіх спроб.")
    return False
