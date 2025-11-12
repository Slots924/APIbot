from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
import sys

def facebook_checkout_detect(driver: WebDriver) -> bool:
    """
    Перевіряє URL сторінки на наявність Facebook checkpoint.
    True  -> все ок
    Завершує програму (sys.exit(1)), якщо знайдено checkpoint / верифікацію.
    """
    try:
        current_url = (
            driver.current_url or driver.execute_script("return window.location.href") or ""
        ).lower().strip()
    except WebDriverException as e:
        print(f"[facebook_checkout_detect] ⚠️ Не вдалося отримати URL: {e}. Пропускаю перевірку.")
        return True

    check_parts = (
        "facebook.com/checkpoint",
        "/checkpoint/",
        "/login/checkpoint/",
        "/nt/safetycenter/",
        "/recover/initiate/",
        "/confirm_identity/",
    )

    if any(part in current_url for part in check_parts):
        print(f"[facebook_checkout_detect] ❌ Facebook checkpoint detected (URL: {current_url}) — зупиняю роботу.")
        sys.exit(1)

    print(f"[facebook_checkout_detect] ✅ OK (url: {current_url})")
    return True
