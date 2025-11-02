# src/main.py

from src.core.bot import Bot

if __name__ == "__main__":
    # ID профілю в AdsPower
    USER_ID = "214"

    # Пост для тесту
    POST_URL = "https://www.facebook.com/share/p/1CwNcFNiuD/"

    # Тестовий коментар
    COMMENT_TEXT = (
        "I’m honestly shocked by their relationship dynamics. "
        "It’s wild how everything turned out!"
    )

    bot = Bot(user_id=USER_ID)

    try:
        bot.start()  # запуск профілю AdsPower
        bot.human_behavior()
        bot.comment_post(POST_URL, COMMENT_TEXT)  # тест коментаря
        bot.human_behavior()
    finally:
        bot.stop()  # обов'язково зупиняємо навіть якщо є помилки
