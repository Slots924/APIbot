"""Точка входу, яка демонструє пряме використання класу :class:`Bot`."""

# Імпортуємо клієнт AdsPower, головний клас бота та допоміжну функцію для отримання статі профілю.
from src.core.ads_power import AdsPower
from src.core.bot import Bot
from src.core.api.get_profil_gender_by_serial_number import get_profil_gender_by_id


if __name__ == "__main__":
    # Посилання на пост Facebook, з яким будемо взаємодіяти.
    url = "https://www.facebook.com/photo/?fbid=1391853225638244&set=pcb.1391853252304908"

    # Коментар, який потрібно залишити під публікацією.
    comment = "Also bitte, wie charmant kann ein Mann eigentlich ausschauen? 😏 Mit so einem Lächeln verdrehst du ja halb Wien den Kopf. Würd’ dich sofort auf einen Melange einladen! ☕💛"

    COMMENTS_TO_LIKE = [
        "Also bitte, wie charmant kann ein Mann eigentlich ausschauen? 😏 Mit so einem Lächeln verdrehst du ja halb Wien den Kopf. Würd’ dich sofort auf einen Melange einladen! ☕💛"
    ]

    # Серійний номер профілю в AdsPower, що відповідає потрібному браузеру.
    serial_number = 137

    # Створюємо екземпляри AdsPower та бота. Відтепер усі дії викликаємо з явним ``serial_number``.
    ads = AdsPower()
    bot = Bot(ads)

    try:
        # 1. Запускаємо профіль перед виконанням будь-яких дій.
        bot.start(serial_number)

        bot.open_new_tab(serial_number, url)
        bot.like_post(serial_number)
        bot.writte_comment(serial_number, comment)
        bot.like_comments(serial_number, COMMENTS_TO_LIKE, 'love')
        bot.close_tab(serial_number)
        # 3. Тут можна викликати інші методи:
        # bot.open_new_tab(serial_number, url)
        # bot.like_post(serial_number)
        # bot.writte_comment(serial_number, comment)
        # bot.like_comments(serial_number, COMMENTS_TO_LIKE)

    except Exception as exc:
        # Фіксуємо можливу помилку, але гарантуємо завершення сесії у блоці finally.
        print(f"[Помилка для serial_number {serial_number}]: {exc}")

    finally:
        # Завершуємо роботу профілю незалежно від успіху попередніх кроків.
        bot.stop(serial_number)
