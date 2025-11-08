"""Перевірка попереджень Facebook про підозрілу активність або прохання верифікації."""

from __future__ import annotations

import sys
from typing import Iterable

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver


# Ключові фрази, які свідчать про підозрілі перевірки Facebook.
# Зібрано найтиповіші повідомлення англійською та українською мовами.
SUSPICIOUS_KEYWORDS: tuple[str, ...] = (
    "unusual activity",
    "suspicious activity",
    "suspicious login",
    "secure your account",
    "confirm your identity",
    "we suspended your account",
    "upload a selfie",
    "upload a photo",
    "selfie",
    "confirm that this is your account",
    "security check",
    "we noticed unusual",
    "підозріла активність",
    "перевірте свою особу",
    "підтвердьте свою особу",
    "захистіть свій акаунт",
    "завантажте фото",
    "завантажте селфі",
)


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    """Перевіряє, чи містить текст хоча б одну з вказаних підрядків."""

    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def facebook_checkout_detect(driver: WebDriver) -> bool:
    """Перевірити сторінку на ознаки блокувань Facebook та завершити програму при їх виявленні.

    Повертає ``True``, якщо підозрілих перевірок не знайдено.
    У випадку виявлення проблем логуються повідомлення та виконується ``sys.exit(1)``.
    """

    try:
        page_source = driver.page_source
    except WebDriverException as error:
        # Якщо не вдалось отримати розмітку — виводимо попередження та вважаємо, що все гаразд.
        print(
            "[ACTION facebook_checkout_detect] ⚠️ Не вдалося прочитати HTML сторінки: "
            f"{error}. Пропускаю перевірку."
        )
        return True

    if not page_source:
        print(
            "[ACTION facebook_checkout_detect] ⚠️ Отримано порожнє тіло сторінки. "
            "Не можу визначити стан перевірок, припускаю що все гаразд."
        )
        return True

    if _contains_any(page_source, SUSPICIOUS_KEYWORDS):
        print(
            "[ACTION facebook_checkout_detect] ❌ Facebook показує перевірку безпеки або "
            "просить додаткову верифікацію. Завершую роботу бота, щоб не погіршити ситуацію."
        )
        sys.exit(1)

    print("[ACTION facebook_checkout_detect] ✅ Ознак блокувань або перевірок не виявлено.")
    return True


__all__ = ["facebook_checkout_detect"]
