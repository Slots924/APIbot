"""Модуль, що об'єднує дії для імітації людської поведінки курсора та взаємодії з вікном браузера."""

from .micro_mouse_move import micro_mouse_move
from .random_mouse_path import random_mouse_path
from .scroll_up_down_short import scroll_up_down_short
from .scroll_half_page import scroll_half_page
from .move_to_random_element import move_to_random_element
from .hover_pause import hover_pause
from .simulate_typing_pause import simulate_typing_pause
from .window_focus_shift import window_focus_shift
from .human_behavire_random_short import human_behavire_random_short

__all__ = [
    "micro_mouse_move",
    "random_mouse_path",
    "scroll_up_down_short",
    "scroll_half_page",
    "move_to_random_element",
    "hover_pause",
    "simulate_typing_pause",
    "window_focus_shift",
    "human_behavire_random_short",
]
