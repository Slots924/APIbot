"""Спрощений Bot для керування кількома профілями AdsPower одночасно."""

from __future__ import annotations

import json
import time
import random
import traceback
from typing import Dict, Iterable, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from src.core.actions.like_post.like_post import like_post
from src.core.actions.comment_post.writte_comment import writte_comment
from src.core.actions.comment_post.writte_replay import writte_replay
from src.core.actions.like_comments.like_comments import like_comments
from src.core.actions.open_new_tab.open_new_tab import open_new_tab
from src.core.actions.close_tab.close_tab import close_tab
from src.core.ads_power import AdsPower


class Bot:
    """Організує життєвий цикл Selenium-драйверів для профілів AdsPower."""

    def __init__(self, ads: AdsPower):
        """Приймає попередньо налаштований клієнт :class:`AdsPower`."""

        # ``AdsPower`` відповідає за всі HTTP-запити до локального API.
        self.ads = ads
        # У цьому словнику зберігаємо Selenium-драйвер для кожного активного user_id.
        self._drivers: Dict[str, webdriver.Chrome] = {}

    # -------------------- Допоміжні методи --------------------

    def get_profile_info_by_id(self, user_id: str) -> Optional[dict]:
        """Делегує виклик до ``AdsPower`` для отримання інформації про профіль."""

        return self.ads.get_profile_info_by_id(user_id)

    def get_profile_sex_by_id(self, user_id: str) -> Optional[str]:
        """Повертає стать профілю (``Male`` або ``Female``) на основі даних AdsPower."""

        normalized_user_id = str(user_id)
        profile_info = self.get_profile_info_by_id(normalized_user_id)
        if not profile_info:
            print(
                f"[BOT] ❌ Не вдалося отримати профіль {normalized_user_id} для визначення статі."
            )
            return None

        name_field = profile_info.get("name")
        if not isinstance(name_field, str) or "::" not in name_field:
            print(
                f"[BOT] ❌ Поле name профілю {normalized_user_id} не містить очікуваного роздільника '::'."
            )
            return None

        # Рядок має формат «непотрібні дані :: {"sex": "Male"}». Забираємо JSON-частину та парсимо її.
        _, json_part = name_field.split("::", 1)
        json_part = json_part.strip()

        try:
            name_payload = json.loads(json_part)
        except json.JSONDecodeError as exc:
            print(
                f"[BOT] ❌ Не вдалося розібрати JSON зі статтю профілю {normalized_user_id}: {exc}"
            )
            return None

        sex = name_payload.get("sex")
        if sex in ("Male", "Female"):
            return sex

        print(
            f"[BOT] ❌ JSON-інформація профілю {normalized_user_id} не містить коректного поля 'sex': {name_payload}"
        )
        return None

    def _ensure_driver(self, user_id: str) -> webdriver.Chrome:
        """Переконується, що для профілю вже запущено Selenium-драйвер."""

        normalized_user_id = str(user_id)
        driver = self._drivers.get(normalized_user_id)
        if not driver:
            raise RuntimeError("Спочатку виклич start(user_id).")
        return driver

    # -------------------- Життєвий цикл профілю --------------------

    def start(self, user_id: str) -> None:
        """Запускає профіль AdsPower і створює прив'язаний до нього Selenium-драйвер."""

        normalized_user_id = str(user_id)
        if normalized_user_id in self._drivers:
            print(f"[BOT] ⚠️ Профіль {normalized_user_id} вже запущено.")
            return

        print(f"[BOT] ▶️ Стартую профіль {normalized_user_id} через AdsPower…")
        try:
            # Отримуємо службову інформацію від AdsPower: порт для дебагу та шлях до chromedriver.
            data = self.ads.start(normalized_user_id)
            debug_port = data.get("debug_port")
            chromedriver_path = data.get("webdriver")

            if not debug_port:
                raise RuntimeError("debug_port не знайдено у відповіді AdsPower.")

            # Налаштовуємо ChromeOptions для підключення до вже запущеного профілю.
            opts = Options()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            try:
                opts.page_load_strategy = "none"
            except Exception:
                # На старих версіях Selenium ця опція може бути недоступна — пропускаємо помилку.
                pass

            # Якщо AdsPower повернув власний chromedriver — використовуємо його.
            if chromedriver_path:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=opts)
            else:
                driver = webdriver.Chrome(options=opts)

            # Невелика неявна затримка допомагає стабілізувати роботу екшенів.
            driver.implicitly_wait(3)
            self._drivers[normalized_user_id] = driver
            print("[BOT] ✅ WebDriver підключено до профілю.")

        except Exception as exc:
            # Якщо щось пішло не так — повідомляємо про це та намагаємося зупинити профіль у AdsPower.
            print(f"[BOT] ❌ Помилка старту: {exc}")
            traceback.print_exc()
            self.ads.stop(normalized_user_id)
            raise

    def stop(self, user_id: str) -> None:
        """Закриває Selenium-драйвер і надсилає запит на зупинку профілю в AdsPower."""

        normalized_user_id = str(user_id)
        print(f"[BOT] ⏹️ Завершую сесію профілю {normalized_user_id}…")

        driver = self._drivers.pop(normalized_user_id, None)
        self._safe_close_driver(driver)
        self.ads.stop(normalized_user_id)

        print("[BOT] 🟢 Профіль зупинено.")

    @staticmethod
    def _safe_close_driver(driver: Optional[webdriver.Chrome]) -> None:
        """Акуратно закриває Selenium-драйвер, ігноруючи дрібні помилки."""

        try:
            if driver:
                driver.quit()
        except Exception:
            pass

    # -------------------- Взаємодія з екшенами --------------------

    def like_post(self, user_id: str, reaction: str = "like") -> Optional[bool]:
        """Ставить реакцію на пост, використовуючи відповідний action."""

        driver = self._ensure_driver(user_id)

        print(f"[BOT] 👍 Ставлю реакцію '{reaction}' під постом:")
        try:
            return bool(like_post(driver, reaction))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в like_post: {e}")
            traceback.print_exc()
            return False

    def writte_comment(self, user_id: str, text: str) -> Optional[bool]:
        """Залишає коментар під дописом через action ``writte_comment``."""

        driver = self._ensure_driver(user_id)

        print("[BOT] 💬 Коментую пост:")
        try:
            return bool(writte_comment(driver, text))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в writte_comment: {e}")
            traceback.print_exc()
            return False

    def comment_post(self, user_id: str, text: str) -> Optional[bool]:
        """Залишено для сумісності зі старим інтерфейсом бота."""

        print("[BOT] ℹ️ Метод comment_post вважається застарілим, використовую writte_comment().")
        return self.writte_comment(user_id, text)

    def writte_replay(
        self,
        user_id: str,
        comment_snippet: str,
        reply_text: str,
    ) -> Optional[bool]:
        """Відповідає на конкретний коментар під постом."""

        driver = self._ensure_driver(user_id)

        print("[BOT] 💬 Відповідаю на коментар у стрічці.")
        try:
            return bool(writte_replay(driver, comment_snippet, reply_text))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в writte_replay: {e}")
            traceback.print_exc()
            return False

    def like_comments(
        self,
        user_id: str,
        comments: Optional[Iterable[str]] = None,
        reaction: str = "like",
    ) -> Optional[bool]:
        """Ставить реакцію на коментарях, переданих списком ``comments``."""

        driver = self._ensure_driver(user_id)

        print("[BOT] ❤️ Ставлю реакції на коментарях.")
        try:
            return bool(like_comments(driver, comments, reaction))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в like_comments: {e}")
            traceback.print_exc()
            return False

    def open_new_tab(
        self,
        user_id: str,
        url: str,
        require_selector: Optional[Tuple[By, str]] = None,
    ) -> Optional[bool]:
        """Відкриває нову вкладку та, за потреби, очікує на появу селектора ``require_selector``."""

        driver = self._ensure_driver(user_id)

        print(f"[BOT] 🗂️ Відкриваю нову вкладку для: {url}")
        try:
            return bool(open_new_tab(driver, url, require_selector=require_selector))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в open_new_tab: {e}")
            traceback.print_exc()
            return False

    def close_tab(self, user_id: str, quantity: int = 1) -> Optional[bool]:
        """Закриває одну або декілька вкладок у межах активного профілю."""

        driver = self._ensure_driver(user_id)

        print(f"[BOT] ❎ Закриваю вкладки у кількості: {quantity}.")
        try:
            return bool(close_tab(driver, quantity))
        except Exception as e:
            print(f"[BOT] ❗ Помилка в close_tab: {e}")
            traceback.print_exc()
            return False

    # -------------------- Імітація людської поведінки --------------------

    def human_behavior(
        self,
        user_id: str,
        min_pause: float = 0.8,
        max_pause: float = 3.0,
    ) -> None:
        """Виконує випадкові дії у вкладці, щоб бот виглядав природніше."""

        driver = self._ensure_driver(user_id)

        try:
            actions = [
                lambda: driver.execute_script(
                    "window.scrollBy(0, arguments[0]);",
                    random.randint(120, 480),
                ),
                lambda: driver.execute_script(
                    "window.scrollBy(0, arguments[0]);",
                    -random.randint(80, 300),
                ),
                lambda: driver.execute_script(
                    "var e=document.createEvent('MouseEvents');"
                    "e.initMouseEvent('mousemove', true, true, window, 0,0,0,"
                    "arguments[0],arguments[1], false,false,false,false,0,null);"
                    "document.dispatchEvent(e);",
                    random.randint(50, 400),
                    random.randint(50, 400),
                ),
                lambda: time.sleep(random.uniform(min_pause, max_pause)),
            ]

            for _ in range(random.randint(1, 3)):
                random.choice(actions)()
                time.sleep(random.uniform(0.3, 0.7))

            print("[BOT] 🧍 Імітація людської активності виконана.")
        except Exception:
            # Якщо якась дія зламалась — замовчуємо, щоб не зривати основні сценарії.
            pass
