"""Екшен для акуратного закриття вкладок AdsPower-браузера.

Функція ``close_tab`` дозволяє закрити поточну вкладку або
декілька вкладок підряд. Весь код щедро задокументований українською,
щоб новачкам було легше розібратися в кроках алгоритму.
"""

from __future__ import annotations

import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver


def close_tab(driver: WebDriver, quantity: int = 1) -> bool:
    """Закрити ``quantity`` вкладок, починаючи з поточної.

    Після кожного закриття робимо паузу у 0.5 секунди, щоб AdsPower встиг
    оновити список вкладок і застосувати зміни. Якщо ``quantity`` більше,
    ніж кількість відкритих вкладок, буде закрито всі доступні.
    """

    print(
        f"[ACTION close_tab] 🔻 Отримав запит на закриття {quantity} вкладки/вкладок."
    )

    # Переконуємося, що користувач передав додатне число. Якщо ні — завершуємося.
    if quantity <= 0:
        print(
            "[ACTION close_tab] ⚠️ Кількість має бути більшою за нуль. "
            "Жодну вкладку не закриваю."
        )
        return False

    # Отримуємо поточні хендли, щоб мати уявлення про кількість доступних вкладок.
    try:
        available_handles = list(driver.window_handles)
    except Exception as error:
        print(
            f"[ACTION close_tab] ❌ Не вдалося прочитати список вкладок: {error}."
        )
        return False

    if not available_handles:
        print("[ACTION close_tab] ⚠️ У драйвера немає жодної відкритої вкладки.")
        return False

    # Закриємо не більше, ніж існує, щоб уникнути непотрібних помилок Selenium.
    target_to_close = min(quantity, len(available_handles))
    closed_count = 0

    for step in range(target_to_close):
        # Ще до закриття зчитуємо поточний хендл — це вкладка, яку прибираємо.
        try:
            current_handle: Optional[str] = driver.current_window_handle
        except Exception:
            current_handle = None

        print(
            "[ACTION close_tab] 🪟 Закриваю вкладку номер "
            f"{step + 1} (handle={current_handle})."
        )

        try:
            driver.close()
            closed_count += 1
            print("[ACTION close_tab] ✅ Вкладку закрито успішно.")
        except Exception as error:
            print(f"[ACTION close_tab] ❌ Не вдалося закрити вкладку: {error}.")
            break

        # Невелика пауза, щоб браузер гарантовано опрацював закриття.
        time.sleep(0.5)

        # Якщо після закриття залишилися вкладки — переключаємось на останню.
        try:
            remaining_handles = driver.window_handles
        except Exception:
            remaining_handles = []

        if remaining_handles:
            fallback_handle = remaining_handles[-1]
            try:
                driver.switch_to.window(fallback_handle)
                print(
                    "[ACTION close_tab] 🔁 Перемкнувся на залишену вкладку "
                    f"(handle={fallback_handle})."
                )
            except Exception as switch_error:
                print(
                    "[ACTION close_tab] ⚠️ Не вдалося переключитися на іншу вкладку: "
                    f"{switch_error}."
                )
        else:
            print("[ACTION close_tab] ℹ️ Вкладок більше не лишилося у сесії.")
            break

    if closed_count == target_to_close:
        print("[ACTION close_tab] 🟢 Запит виконано повністю.")
        return True

    print(
        "[ACTION close_tab] ⚠️ Виконано частково: "
        f"закрито {closed_count} з {target_to_close} запитаних вкладок."
    )
    return False


__all__ = ["close_tab"]

