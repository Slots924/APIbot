"""Модуль із менеджером задач, який формує сценарій для класу :class:`Bot`."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from src.core.bot import Bot


class TaskManager:
    """Керує виконанням послідовності дій для кількох користувачів AdsPower."""

    def __init__(self, user_id_array: Iterable[Any]):
        # Зберігаємо ідентифікатори користувачів, для яких потрібно виконати сценарій.
        self.user_id_array = list(user_id_array)
        # Підготовлений список дій: (назва_методу, позиційні_аргументи, іменовані_аргументи).
        self._actions: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def add_action(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Додає опис дії у чергу, з якою потім працюватиме :meth:`run`."""

        # Не обмежуємо назви дій, але фільтрація відбудеться у :meth:`run` через hasattr.
        self._actions.append((method_name, args, kwargs))

    def __getattr__(self, name: str) -> Callable[..., "TaskManager"]:
        """Дає можливість використовувати назви методів бота як зручні обгортки."""

        # Перевіряємо, чи має Bot відповідний метод і чи можна його викликати.
        bot_attr = getattr(Bot, name, None)
        if not callable(bot_attr):
            raise AttributeError(f"У Bot немає методу '{name}'.")

        def _wrapper(*args: Any, **kwargs: Any) -> "TaskManager":
            """Обгортка, що додає дію у список та повертає менеджер для чейнінгу."""

            self.add_action(name, *args, **kwargs)
            return self

        return _wrapper

    def clear(self) -> None:
        """Очищає чергу дій, якщо потрібно зібрати сценарій з нуля."""

        self._actions.clear()

    def run(self) -> None:
        """Створює :class:`Bot` для кожного user_id та послідовно виконує дії."""

        for user_id in self.user_id_array:
            print(f"\n=== Запуск для user_id: {user_id} ===")
            bot = Bot(user_id=user_id)

            try:
                # Запускаємо профіль AdsPower перед виконанням екшенів.
                bot.start()

                for method_name, args, kwargs in self._actions:
                    # Виконуємо лише ті методи, які реально існують у бота.
                    if not hasattr(bot, method_name):
                        print(
                            f"[TaskManager] ⚠️ Метод '{method_name}' відсутній у Bot. Пропускаю дію."
                        )
                        continue

                    method = getattr(bot, method_name)
                    method(*args, **kwargs)

            except Exception as exc:
                # Не зупиняємо роботу для інших користувачів, але повідомляємо про помилку.
                print(f"[Помилка для user_id {user_id}]: {exc}")
            finally:
                # Навіть у випадку помилок гарантуємо коректне завершення сесії.
                bot.stop()
