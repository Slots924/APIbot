"""Модуль для генерації випадкового плавного шляху курсора."""

from __future__ import annotations

import random
import time
from typing import List, Tuple

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def _generate_control_points(width: int, height: int) -> List[Tuple[int, int]]:
    """Формує набір контрольних точок для імітації кривої траєкторії."""
    # Вибираємо випадкову кількість проміжних точок, щоб кожна траєкторія була унікальною.
    steps = random.randint(3, 5)
    points: List[Tuple[int, int]] = []
    for _ in range(steps):
        point = (random.randint(0, width), random.randint(0, height))
        points.append(point)
    return points


def random_mouse_path(driver: WebDriver) -> None:
    """Рухається по плавній траєкторії між випадковими точками екрана."""
    # Отримуємо доступні розміри області перегляду, щоб не виходити за межі вікна.
    viewport_width, viewport_height = driver.execute_script("return [window.innerWidth, window.innerHeight];")

    # Генеруємо випадкові контрольні точки у межах вікна браузера.
    control_points = _generate_control_points(viewport_width, viewport_height)

    # Для кожної точки виконуємо м'який рух курсора та коротку паузу для природності.
    body_element = driver.find_element(By.TAG_NAME, "body")
    actions = ActionChains(driver)
    for x, y in control_points:
        actions.move_to_element_with_offset(body_element, x, y)
        actions.pause(random.uniform(0.05, 0.2))
    actions.perform()

    # Після проходження шляху додаємо невелику паузу, ніби користувач зупинився розглянути контент.
    time.sleep(random.uniform(0.2, 0.5))
