"""Надсилання відповіді на коментар."""

from selenium.webdriver.remote.webdriver import WebDriver

from .send_comment import send_comment


def send_reply(driver: WebDriver, expected_text: str | None = None) -> bool:
    """Використовує ту саму логіку, що і звичайний коментар, але з іншим логом."""

    return send_comment(driver, expected_text=expected_text, label="відповідь")
