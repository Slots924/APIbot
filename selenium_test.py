# selenium_keep_open.py
# Запуск Chrome через Selenium, інжект stealth-скрипта і відкриття сторінки.
# Зверху задається USER_ID як глобальна змінна (НЕ використовує input()).

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os

# ----------------- Налаштування (тут правимо) -----------------
USER_ID = "149"  # <-- Вкажи потрібний user id тут (рядок)
CHROMEDRIVER_PATH = None  # наприклад: r"C:\path\to\chromedriver.exe" або None щоб використовувати PATH
START_URL = "https://google.com"
KEEP_OPEN = True  # якщо True — браузер лишається відкритим після завершення скрипта
# ---------------------------------------------------------------


def make_stealth_script():
    # JS, який виконається до завантаження кожної сторінки (addScriptToEvaluateOnNewDocument)
    return r"""
// Приховуємо navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined
});

// Підмінюємо мови
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en']
});

// Простий mock plugins
Object.defineProperty(navigator, 'plugins', {
  get: () => [1,2,3,4,5]
});

// Перехоплення permissions.query для notification
try {
  const origQuery = window.navigator.permissions && window.navigator.permissions.query;
  if (origQuery) {
    window.navigator.permissions.query = (params) => {
      if (params && params.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission });
      }
      return origQuery(params);
    };
  }
} catch (e) {}

// Невелика підміна userAgent (видаляємо "Headless" якщо є)
try {
  const ua = navigator.userAgent;
  Object.defineProperty(navigator, 'userAgent', { get: () => ua.replace('Headless', '') });
} catch (e) {}
"""


def create_driver(chromedriver_path: str | None = None) -> webdriver.Chrome:
    opts = Options()

    # detach зберігає вікно відкритим після завершення процесу (працює у звичних локальних запусках)
    opts.add_experimental_option("detach", True)

    # Базові опції (мінімізуємо зайві флаги)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # За бажання можна підмінити UA:
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    # Інжектимо stealth JS на кожен новий документ (через CDP)
    stealth_js = make_stealth_script()
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
    except Exception as e:
        # Якщо CDP недоступний — просто продовжуємо
        print("[warn] CDP injection failed:", e)

    driver.implicitly_wait(3)
    return driver


def main():
    print(f"[*] Виконується для USER_ID = {USER_ID}")
    driver = None
    try:
        driver = create_driver(CHROMEDRIVER_PATH)
        print("[*] Відкриваю:", START_URL)
        driver.get(START_URL)

        # Даємо сторінці трохи часу
        time.sleep(10)

        print("[*] Основні дії виконано.")
        if not KEEP_OPEN:
            driver.quit()
            print("[*] Браузер закрито.")
        else:
            print("[*] Браузер залишився відкритим (KEEP_OPEN=True). Закрий його вручну при потребі.")

    except Exception as e:
        print("[error] Сталася помилка:", e)
        try:
            if driver:
                driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
