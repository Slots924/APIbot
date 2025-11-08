# src/main.py
"""Точка входу, яка демонструє пряме використання класу :class:`Bot`."""

# Імпортуємо головний клас бота, який інкапсулює усю взаємодію з AdsPower.
from src.core.bot import Bot


if __name__ == "__main__":
    # Посилання на пост Facebook, з яким будемо взаємодіяти.
    url = "https://www.facebook.com/photo/?fbid=1391853225638244&set=pcb.1391853252304908"

    # Коментар, який потрібно залишити під публікацією.
    comment = "This looks insanely good — bartender level perfection"

    COMMENTS_TO_LIKE = [

        "My warmest congratulations to you! You truly deserve all the happiness and success"
    ]

    # Ідентифікатор профілю в AdsPower, що відповідає потрібному браузеру.
    user_id = 214

    # Створюємо екземпляр бота. Усі подальші дії проводитимемо через нього.
    bot = Bot(user_id=user_id)

    try:
      
        sex = bot.get_profile_sex_by_id(user_id)
        print(sex)

      

    except Exception as exc:
        # Фіксуємо можливу помилку, але гарантуємо завершення сесії у блоці finally.
        print(f"[Помилка для user_id {user_id}]: {exc}")

    finally:
        # 5. Завершуємо роботу профілю, навіть якщо сталася помилка.
        bot.stop()
