"""Ввід тексту коментаря з імітацією людського друку."""

import random
import time

from selenium.webdriver.remote.webdriver import WebDriver


def comment_human_behavire_writting(driver: WebDriver, text: str) -> None:
    """Друкує текст по символах, роблячи випадкові затримки між натисканнями."""

    for ch in text:
        try:
            driver.execute_cdp_cmd("Input.insertText", {"text": ch})
        except Exception:
            try:
                driver.switch_to.active_element.send_keys(ch)
            except Exception:
                pass
        # Невелика пауза між символами допомагає імітувати природне введення.
        time.sleep(random.uniform(0.07, 0.21))
