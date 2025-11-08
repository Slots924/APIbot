"""Випадковий вибір короткої дії, що імітує людську поведінку."""

from __future__ import annotations

import random

from selenium.webdriver.remote.webdriver import WebDriver

from .hover_pause import hover_pause
from .micro_mouse_move import micro_mouse_move
from .move_to_random_element import move_to_random_element
from .random_mouse_path import random_mouse_path
from .scroll_half_page import scroll_half_page
from .scroll_up_down_short import scroll_up_down_short
from .simulate_typing_pause import simulate_typing_pause
from .window_focus_shift import window_focus_shift


def human_behavire_random_short(driver: WebDriver) -> None:
    """Випадково запускає одну з коротких поведінкових дій."""
    # Обираємо випадковий сценарій. Набір функцій жорстко зашитий, щоб уникнути складних залежностей.
    choice = random.randint(1, 8)

    if choice == 1:
        micro_mouse_move(driver)
    elif choice == 2:
        random_mouse_path(driver)
    elif choice == 3:
        scroll_up_down_short(driver)
    elif choice == 4:
        scroll_half_page(driver)
    elif choice == 5:
        move_to_random_element(driver)
    elif choice == 6:
        hover_pause(driver)
    elif choice == 7:
        simulate_typing_pause(driver)
    else:
        window_focus_shift(driver)
