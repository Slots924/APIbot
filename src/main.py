"""Точка входу, яка демонструє пряме використання класу :class:`Bot`."""

# Імпортуємо клієнт AdsPower, головний клас бота та сценарій публікації коментарів.
from src.core.ads_power import AdsPower
from src.core.bot import Bot
from src.flow import writte_all_coments_to_post


if __name__ == "__main__":
    

    # Пул серійних номерів профілів, які можна використати для написання коментарів.
    serial_number_pool = [225, 231]

    # Шлях до JSON-файла з коментарями та необхідною статтю для кожного запису.
    comments_path = r"C:\\Users\\Darkness\\Documents\\Projects\\APIbot\\src\\data\\comments\\W1S.json"

    # Створюємо клієнта AdsPower та обгортку Bot, через яку виконуватимемо дії.
    ads = AdsPower()
    bot = Bot(ads)
    BOT = bot

    URL_1 = 'https://www.facebook.com/share/p/1BNzquzqhN/'
    URL_2 = 'https://www.facebook.com/share/p/1BTHDys7Qe/'

    COMENTS_TO_LIKE_1 = ['Kdyby se mě někdo zeptal, kde potkat všechny moje kámošky, co jsou připravený skočit do postele s prvním týpkem',
                        'Ty vole, to je neskutečně dobrej web!',
                        'Zvědavost mi nedala, tak jsem',
                        'Tyjo, měla jsem tam jednou příběh'

    ]

    COMENTS_TO_LIKE_2 = ['Rzuć tu linka do tego',
                        'Jakieś 40 minut po rejestracji',
                        'o jest po prostu najlepszy web, na '

    ]


    id_array_1 = [148,149,151,153]
    id_array_2 = []


    def run_for_users(user_id_array, url_1, comments_1, url_2, comments_2):
        for user_id in user_id_array:
            print(f"\n=== Запуск для user_id: {user_id} ===")

            bot = BOT
            try:
                bot.start(user_id)  # запуск профілю AdsPower

                bot.open_new_tab(user_id, url_1)
                bot.like_comments(user_id, comments_1, "love")
                bot.close_tab(user_id)

                bot.open_new_tab(user_id, url_2)
                bot.like_comments(user_id, comments_2, "love")
                bot.close_tab(user_id)

            except Exception as e:
                print(f"[Помилка для user_id {user_id}]: {e}")

            finally:
                bot.stop(user_id)  # обов'язково зупиняємо навіть якщо є помилка


    run_for_users(id_array_1, URL_1, COMENTS_TO_LIKE_1, URL_2, COMENTS_TO_LIKE_2)







    # try:
    #     # Весь сценарій з обробки коментарів винесено у функцію ``writte_all_coments_to_post``.
    #     writte_all_coments_to_post(
    #         bot,
    #         url,
    #         serial_number_pool,
    #         comments_path,
    #         like_post_reaction=reaction_before_comment,
    #     )
    # except Exception as exc:
    #     # Якщо сценарій згенерував помилку, логування допоможе швидко знайти причину.
    #     print(f"[MAIN] ❌ Сталася помилка під час виконання сценарію: {exc}")
    # finally:
    #     # Якщо якісь профілі все ще запущені (наприклад, через аварійне завершення), акуратно їх зупинимо.
    #     for active_serial in list(bot._drivers.keys()):  # type: ignore[attr-defined]
    #         try:
    #             bot.stop(active_serial)
    #         except Exception:
    #             # У разі додаткових помилок при зупинці просто продовжуємо, бо сесія і так завершується.
    #             pass
