"""Точка входу, яка демонструє пряме використання класу :class:`Bot`."""

# Імпортуємо клієнт AdsPower, головний клас бота та допоміжну функцію для отримання статі профілю.
from src.core.ads_power import AdsPower
from src.core.bot import Bot
from src.core.api.get_profil_gender_by_id import get_profil_gender_by_id


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

    # Створюємо екземпляри AdsPower та бота. Відтепер усі дії викликаємо з явним ``user_id``.
    ads = AdsPower()
    bot = Bot(ads)

    try:
        # 1. Запускаємо профіль перед виконанням будь-яких дій.
        bot.start(user_id)

        # 2. Отримуємо додаткову інформацію про профіль, наприклад стать.
        sex = get_profil_gender_by_id(ads, user_id)
        print(sex)

        # 3. Тут можна викликати інші методи:
        # bot.open_new_tab(user_id, url)
        # bot.like_post(user_id)
        # bot.writte_comment(user_id, comment)
        # bot.like_comments(user_id, COMMENTS_TO_LIKE)

    except Exception as exc:
        # Фіксуємо можливу помилку, але гарантуємо завершення сесії у блоці finally.
        print(f"[Помилка для user_id {user_id}]: {exc}")

    finally:
        # Завершуємо роботу профілю незалежно від успіху попередніх кроків.
        bot.stop(user_id)
