"""
Спрощений Bot для AdsPower + Selenium.
- Старт/стоп профілю по serial_number (user_id)
- Під’єднання до запущеного браузера AdsPower через debugger port
- Вбудовані методи: like_post, comment_post
- Підтримка екшенів із ``src/core/actions/<action>/<action>.py``
- Метод ``like_post`` приймає бажану реакцію (`"love"`, `"care"`, тощо) і передає її у відповідний action.
"""

from __future__ import annotations

import time
import random
import traceback
from typing import Callable, Iterable, Optional, Tuple

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Bot:
    def __init__(self, user_id: str, api_host: str = "127.0.0.1", api_port: int = 50325):
        self.user_id = str(user_id)
        self.api_host = api_host
        self.api_port = int(api_port)

        self.driver: Optional[webdriver.Chrome] = None
        self._started: bool = False

        self._actions: dict[str, Callable] = {}
        self._load_actions()

    # -------------------- Infrastructure --------------------

    @property
    def _api_base(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    def _api_get(self, path: str, **params) -> dict:
        r = requests.get(f"{self._api_base}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    # -------------------- Lifecycle --------------------

    def start(self) -> None:
        if self._started:
            print(f"[BOT] ⚠️ Профіль {self.user_id} вже запущено.")
            return

        print(f"[BOT] ▶️ Стартую профіль {self.user_id} через AdsPower…")
        try:
            resp = self._api_get("/api/v1/browser/start", serial_number=self.user_id)
            if resp.get("code") != 0:
                raise RuntimeError(f"AdsPower не запустив профіль: {resp}")

            data = resp.get("data", {}) or {}
            debug_port = data.get("debug_port")
            chromedriver_path = data.get("webdriver")

            if not debug_port:
                raise RuntimeError("debug_port не знайдено у відповіді AdsPower.")

            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            try:
                opts.page_load_strategy = "none"
            except Exception:
                pass

            if chromedriver_path:
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=opts)
            else:
                self.driver = webdriver.Chrome(options=opts)

            self.driver.implicitly_wait(3)
            self._started = True
            print("[BOT] ✅ WebDriver підключено до профілю.")

        except Exception as e:
            print(f"[BOT] ❌ Помилка старту: {e}")
            traceback.print_exc()
            self._safe_close_driver()
            self._stop_profile()
            raise

    def stop(self) -> None:
        print(f"[BOT] ⏹️ Завершую сесію профілю {self.user_id}…")
        self._safe_close_driver()
        self._stop_profile()
        self._started = False
        print("[BOT] 🟢 Профіль зупинено.")

    def _stop_profile(self):
        try:
            self._api_get("/api/v1/browser/stop", serial_number=self.user_id)
        except Exception:
            pass

    def _safe_close_driver(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.driver = None

    # -------------------- Load Actions --------------------

    def _load_actions(self) -> None:
        try:
            from src.core.actions.like_post.like_post import like_post
            self._actions["like_post"] = like_post
        except Exception:
            pass

        try:
            from src.core.actions.comment_post.writte_comment import writte_comment

            self._actions["writte_comment"] = writte_comment
        except Exception:
            pass

        try:
            from src.core.actions.comment_post.writte_replay import writte_replay

            self._actions["writte_replay"] = writte_replay
        except Exception:
            pass

        try:
            from src.core.actions.like_comments.like_comments import (
                like_comments as like_comments_action,
            )
            self._actions["like_comments"] = like_comments_action
        except Exception:
            pass

        try:
            from src.core.actions.open_new_tab.open_new_tab import open_new_tab
            self._actions["open_new_tab"] = open_new_tab
        except Exception:
            pass

        try:
            from src.core.actions.close_tab.close_tab import close_tab
            self._actions["close_tab"] = close_tab
        except Exception:
            pass

    # -------------------- ACTION CALLERS --------------------

    def like_post(self, reaction: str = "like") -> Optional[bool]:
        """Встановлює реакцію на пості, делегуючи роботу однойменному action."""

        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        action = self._actions.get("like_post")
        if not action:
            print("[BOT] ⚠️ like_post ще не реалізовано.")
            return None

        print(f"[BOT] 👍 Ставлю реакцію '{reaction}' під постом:")
        try:
            # Передаємо у action тип реакції, яку користувач хоче поставити під постом.
            return bool(action(self.driver, reaction))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в like_post: {e}")
            traceback.print_exc()
            return False

    def writte_comment(self, text: str) -> Optional[bool]:
        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        action = self._actions.get("writte_comment")
        if not action:
            print("[BOT] ⚠️ writte_comment ще не реалізовано.")
            return None

        print(f"[BOT] 💬 Коментую пост:")
        try:
            return bool(action(self.driver, text))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в writte_comment: {e}")
            traceback.print_exc()
            return False

    def comment_post(self, text: str) -> Optional[bool]:
        """Сумісний псевдонім для старої назви методу."""

        print("[BOT] ℹ️ Метод comment_post вважається застарілим, використовую writte_comment().")
        return self.writte_comment(text)

    def writte_replay(
        self,
        comment_snippet: str,
        reply_text: str,
    ) -> Optional[bool]:
        """Виконує action, що залишає відповідь під конкретним коментарем."""

        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        action = self._actions.get("writte_replay")
        if not action:
            print("[BOT] ⚠️ writte_replay ще не реалізовано.")
            return None

        print("[BOT] 💬 Відповідаю на коментар у стрічці.")
        try:
            return bool(action(self.driver, comment_snippet, reply_text))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в writte_replay: {e}")
            traceback.print_exc()
            return False

    def like_comments(
        self,
        comments: Optional[Iterable[str]] = None,
        reaction: str = "like",
    ) -> Optional[bool]:
        """Запускає action, який повинен поставити реакцію на заданому переліку коментарів."""

        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        # Забираємо action із кешу `_actions`, щоб не залежати від прямого імпорту у класі Bot.
        action = self._actions.get("like_comments")
        if not action:
            print("[BOT] ⚠️ like_comments ще не реалізовано.")
            return None

        print("[BOT] ❤️ Ставлю реакції на коментарях.")
        try:
            return bool(action(self.driver, comments, reaction))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в like_comments: {e}")
            traceback.print_exc()
            return False

    def open_new_tab(
        self,
        url: str,
        require_selector: Optional[Tuple[By, str]] = None,
    ) -> Optional[bool]:
        """Виконати action відкриття нової вкладки з очікуванням стабілізації DOM."""

        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        action = self._actions.get("open_new_tab")
        if not action:
            print("[BOT] ⚠️ open_new_tab ще не реалізовано.")
            return None

        print(f"[BOT] 🗂️ Відкриваю нову вкладку для: {url}")
        try:
            return bool(action(self.driver, url, require_selector=require_selector))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в open_new_tab: {e}")
            traceback.print_exc()
            return False

    def close_tab(self, quantity: int = 1) -> Optional[bool]:
        """Виклик екшену закриття поточної або кількох вкладок."""

        if not self._started or not self.driver:
            raise RuntimeError("Спочатку виклич start().")

        action = self._actions.get("close_tab")
        if not action:
            print("[BOT] ⚠️ close_tab ще не реалізовано.")
            return None

        print(f"[BOT] ❎ Закриваю вкладки у кількості: {quantity}.")
        try:
            return bool(action(self.driver, quantity))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в close_tab: {e}")
            traceback.print_exc()
            return False

    # -------------------- Human-like Behavior --------------------

    def human_behavior(self, min_pause: float = 0.8, max_pause: float = 3.0) -> None:
        if not self._started or not self.driver:
            print("[BOT] ℹ️ human_behavior пропущено — сесія не запущена.")
            return

        try:
            actions = [
                lambda: self.driver.execute_script("window.scrollBy(0, arguments[0]);",
                                                   random.randint(120, 480)),
                lambda: self.driver.execute_script("window.scrollBy(0, arguments[0]);",
                                                   -random.randint(80, 300)),
                lambda: self.driver.execute_script(
                    "var e=document.createEvent('MouseEvents');"
                    "e.initMouseEvent('mousemove', true, true, window, 0,0,0,"
                    "arguments[0],arguments[1], false,false,false,false,0,null);"
                    "document.dispatchEvent(e);",
                    random.randint(50, 400), random.randint(50, 400)),
                lambda: time.sleep(random.uniform(min_pause, max_pause)),
            ]

            for _ in range(random.randint(1, 3)):
                random.choice(actions)()
                time.sleep(random.uniform(0.3, 0.7))

            print("[BOT] 🧍 Імітація людської активності виконана.")
        except Exception:
            pass

    def human_behavire_random_short(self) -> None:
        """Виконує короткий сценарій «людської» поведінки з урахуванням даних профілю."""

        # Якщо сесія ще не стартувала, немає сенсу імітувати поведінку.
        if not self._started or not self.driver:
            print("[BOT] ℹ️ human_behavire_random_short пропущено — профіль не активний.")
            return

        try:
            # Отримуємо додаткову інформацію про профіль AdsPower.
            profile_info = self.get_user_info_by_id(self.user_id)
        except Exception as error:
            # Якщо API AdsPower недоступний, працюємо з порожніми даними, але повідомляємо про проблему.
            print(f"[BOT] ⚠️ Не вдалося отримати інформацію профілю: {error}")
            profile_info = {}

        # Визначаємо базову тривалість та кількість дій, щоб поведінка виглядала природніше.
        base_pause = 0.6
        repeat_count = random.randint(1, 2)

        # Якщо в інформації профілю знайдено регіон або часовий пояс, робимо паузи довшими,
        # адже користувачі з реальними геолокаціями часто взаємодіють трохи повільніше.
        region_hint = str(profile_info.get("region") or profile_info.get("timezone") or "").strip()
        if region_hint:
            base_pause += random.uniform(0.2, 0.6)
            repeat_count += 1

        print("[BOT] 🧠 Запускаю коротку імітацію випадкової поведінки користувача.")

        try:
            for _ in range(repeat_count):
                # Легкий прокрут сторінки вгору або вниз.
                scroll_delta = random.randint(-220, 320)
                self.driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_delta)
                time.sleep(base_pause + random.uniform(0.1, 0.5))

                # Імітація випадкового руху миші за допомогою події mousemove.
                mouse_x = random.randint(40, 420)
                mouse_y = random.randint(60, 360)
                self.driver.execute_script(
                    "var e=document.createEvent('MouseEvents');"
                    "e.initMouseEvent('mousemove', true, true, window, 0,0,0,"
                    "arguments[0],arguments[1], false,false,false,false,0,null);"
                    "document.dispatchEvent(e);",
                    mouse_x,
                    mouse_y,
                )
                time.sleep(base_pause)

                # Коротка пауза як реакція на розгляд контенту.
                time.sleep(random.uniform(0.3, 0.9))

            print("[BOT] ✅ human_behavire_random_short завершено успішно.")
        except Exception as action_error:
            # У разі будь-якої помилки не перериваємо роботу всього бота, а лише повідомляємо.
            print(f"[BOT] ❗ Помилка під час human_behavire_random_short: {action_error}")
            traceback.print_exc()

    def get_user_info_by_id(self, user_id: str) -> dict:
        """Повертає інформацію про профіль AdsPower у форматі JSON за заданим serial_number."""

        # Відправляємо запит до AdsPower API. Використовуємо існуючий хелпер `_api_get`,
        # щоб не дублювати налаштування запитів та обробку помилок.
        response = self._api_get("/api/v1/user/info", serial_number=str(user_id))

        # AdsPower повертає код помилки у полі `code`. Якщо він не дорівнює 0 – вважаємо, що запит невдалий.
        if response.get("code") != 0:
            raise RuntimeError(f"AdsPower повернув помилку під час отримання профілю: {response}")

        # Успішна відповідь містить словник у полі `data`. Перевіряємо його наявність.
        data = response.get("data")
        if not isinstance(data, dict):
            raise ValueError("AdsPower повернув неочікувану структуру відповіді.")

        return data
