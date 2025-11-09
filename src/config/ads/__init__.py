"""Пакет із конфігураціями для роботи з AdsPower."""

# Імпортуємо публічні константи, щоб ними можна було користуватися через короткий шлях,
# наприклад ``from src.config.ads import START_PROFILE_PARAMETERS``.
from .startup_parameters import START_PROFILE_PARAMETERS

__all__ = ["START_PROFILE_PARAMETERS"]
