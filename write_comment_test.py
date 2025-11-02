#!/usr/bin/env python3
# write_comment_test.py — стабільний набір коментаря без відправки (через CDP)

import time
import random
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ADSPOWER_API_HOST = "127.0.0.1"
ADSPOWER_API_PORT = 50325
SERIAL_NUMBER = "214"
POST_URL = "https://www.facebook.com/share/p/1CwNcFNiuD/"
COMMENT_TEXT = (
    "I’m honestly shocked by their relationship. "
    "It feels like there’s so much more going on behind the scenes!"
)

API_BASE = f"http://{ADSPOWER_API_HOST}:{ADSPOWER_API_PORT}"


def ads_start_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/start",
                        params={"serial_number": sn}, timeout=30).json()


def ads_stop_profile(sn: str) -> dict:
    return requests.get(f"{API_BASE}/api/v1/browser/stop",
                        params={"serial_number": sn}, timeout=15).json()


def attach_to_debugger(debug_port: str, chromedriver_path: str | None = None):
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    # не чекаємо повного лоаду — все одно працюємо через JS
    try:
        opts.page_load_strategy = "none"
    except Exception:
        pass

    if chromedriver_path:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    driver.implicitly_wait(2)
    return driver


def dom_stable(driver, timeout=10, interval=0.6):
    """Чекаємо поки DOM припинить змінюватись (проти ‘ривків’ React)."""
    last = None
    stable_ticks = 0
    start = time.time()
    while time.time() - start < timeout:
        html = driver.page_source
        if html == last:
            stable_ticks += 1
            if stable_ticks >= 3:  # ~1.8с стабільності
                return True
        else:
            stable_ticks = 0
            last = html
        time.sleep(interval)
    return False


def query_editable(driver):
    """Повертає True, якщо editable знайдено, і фокусується на ньому з курсором в кінець."""
    js = r"""
    const findEditable = () => {
      // спочатку активний, якщо він contenteditable
      const ae = document.activeElement;
      if (ae && ae.getAttribute && ae.getAttribute('contenteditable') === 'true') return ae;
      // інакше шукаємо явний editable
      const cands = document.querySelectorAll("div[contenteditable='true'][role='textbox'], div[contenteditable='true']");
      if (cands && cands.length) return cands[0];
      return null;
    };
    const el = findEditable();
    if (!el) return false;

    // фокус і каретка в кінець
    el.focus();
    try {
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false); // курсор в кінець
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } catch(e) {}

    // невеликий input, щоб React "побачив" фокус
    const ev = new InputEvent('input', {bubbles:true});
    el.dispatchEvent(ev);

    return true;
    """
    try:
        return bool(driver.execute_script(js))
    except Exception:
        return False


def insert_text_cdp(driver, text: str, min_delay=0.06, max_delay=0.16):
    """
    Стабільний ввід через CDP (Chrome DevTools Protocol).
    Працює лише якщо фокус реально у contenteditable.
    """
    for ch in text:
        # періодично перевіряємо/оновлюємо фокус (на випадок ре-рендера)
        if random.random() < 0.2:  # кожні ~5 символів
            if not query_editable(driver):
                # повторити спробу фокусу; якщо не вдалося — ще раз
                if not query_editable(driver):
                    # як зовсім біда — зробимо невелику паузу і ще раз
                    time.sleep(0.3)
                    query_editable(driver)

        try:
            driver.execute_cdp_cmd("Input.insertText", {"text": ch})
        except Exception:
            # якщо CDP відмовив — рефокусимо і повторюємо символ
            query_editable(driver)
            driver.execute_cdp_cmd("Input.insertText", {"text": ch})

        time.sleep(random.uniform(min_delay, max_delay))


def main():
    print("[*] Старт тесту коментаря (CDP)…")
    driver = None
    started = False

    try:
        print("[*] Стартую профіль у AdsPower…")
        resp = ads_start_profile(SERIAL_NUMBER)
        print(resp)
        if resp.get("code") != 0:
            raise RuntimeError(resp)

        data = resp.get("data", {}) or {}
        debug_port = data.get("debug_port")
        chromedriver_path = data.get("webdriver")
        if not debug_port:
            raise RuntimeError("debug_port не знайдено у відповіді AdsPower.")

        print(f"[*] Debug port: {debug_port}")
        driver = attach_to_debugger(debug_port, chromedriver_path)
        started = True

        print("[*] Переходжу на пост через JS…")
        driver.execute_script(f"window.location.href = '{POST_URL}';")
        time.sleep(3)
        dom_stable(driver, timeout=10)

        # знайти editable без скролів і фокуснути
        print("[*] Шукаю і фокусую editable поле коментаря…")
        ok = False
        for _ in range(12):
            if query_editable(driver):
                ok = True
                break
            time.sleep(0.8)

        if not ok:
            print("❌ Не вдалося знайти активне поле для коментаря.")
            return

        # подвійний клік: повторне підтвердження фокусу і ще одна невелика пауза
        time.sleep(2.0)
        query_editable(driver)
        time.sleep(3.0)  # твоя вимога — почекати після встановлення курсора

        print("[*] Друкую текст по-людськи (через CDP)…")
        insert_text_cdp(driver, COMMENT_TEXT, min_delay=0.07, max_delay=0.18)

        print("[*] ✅ Текст надруковано. НЕ відправляю.")
        print("[*] ⏳ Чекаю 10 секунд для перевірки…")
        time.sleep(10)

    except Exception as e:
        print("❌ ПОМИЛКА:", e)
        traceback.print_exc()

    finally:
        if started:
            print("[*] Зупиняю профіль у AdsPower…")
            try:
                ads_stop_profile(SERIAL_NUMBER)
            except Exception:
                pass

        try:
            if driver:
                driver.quit()
        except Exception:
            pass

        print("[*] Кінець.")


if __name__ == "__main__":
    main()
