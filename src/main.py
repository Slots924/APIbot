"""Точка входу, яка демонструє пряме використання класу :class:`Bot`."""

# Імпортуємо клієнт AdsPower, головний клас бота та сценарій публікації коментарів.
from src.core.ads_power import AdsPower
from src.core.bot import Bot
from src.flow import writte_all_coments_to_post


if __name__ == "__main__":
    # Посилання на пост Facebook, з яким будемо працювати.
    url = "https://www.facebook.com/photo/?fbid=1391853225638244&set=pcb.1391853252304908"

    # Пул серійних номерів профілів, які можна використати для написання коментарів.
    serial_number_pool = [214, 215, 216, 217, 218, 219]

    # Шлях до JSON-файла з коментарями та необхідною статтю для кожного запису.
    comments_path = r"C:\\Users\\Darkness\\Documents\\Projects\\APIbot\\src\\data\\comments\\W1S.json"

    # Створюємо клієнта AdsPower та обгортку Bot, через яку виконуватимемо дії.
    ads = AdsPower()
    bot = Bot(ads)

    try:
        # Весь сценарій з обробки коментарів винесено у функцію ``writte_all_coments_to_post``.
        writte_all_coments_to_post(bot, url, serial_number_pool, comments_path)
    except Exception as exc:
        # Якщо сценарій згенерував помилку, логування допоможе швидко знайти причину.
        print(f"[MAIN] ❌ Сталася помилка під час виконання сценарію: {exc}")
    finally:
        # Якщо якісь профілі все ще запущені (наприклад, через аварійне завершення), акуратно їх зупинимо.
        for active_serial in list(bot._drivers.keys()):  # type: ignore[attr-defined]
            try:
                bot.stop(active_serial)
            except Exception:
                # У разі додаткових помилок при зупинці просто продовжуємо, бо сесія і так завершується.
                pass
