# src/main.py
from time import sleep

from src.core.bot import Bot

if __name__ == "__main__":
    # ID профілю в AdsPower
    USER_ID = "214"

    # Пост для тесту
    POST_URL = "https://www.facebook.com/photo/?fbid=817298384343945&set=a.137234542350336"

    # Тестовий коментар
    COMMENT_TEXT = (
        "I’m honestly shocked by their relationship dynamics. "
        "It’s wild how everything turned out!"
    )
    URL1 = "https://www.facebook.com/photo/?fbid=1669832114466241&set=pcb.1669832301132889"
    URL2 = "https://www.facebook.com/photo/?fbid=1443679874429048&set=pcb.1443680051095697"
    URL3 =  "https://www.facebook.com/photo/?fbid=815878634634705&set=a.115800767975832"

    COMMENT = "Мальовниче місце, просто зачаровує своєю красою! І я б із задоволенням побував там, щоб відчути цю атмосферу наживо."

    bot = Bot(user_id=USER_ID)

    try:
        bot.start()  # запуск профілю AdsPower
        bot.open_new_tab(URL1)
        # bot.comment_post(COMMENT)
        # sleep(5)

        bot.like_post()
        sleep(5)



        # bot.open_new_tab(URL2)
        # sleep(5)
        # bot.close_tab()
        #
        # bot.open_new_tab(URL3)
        # sleep(5)

        bot.close_tab()
    finally:
        bot.stop()  # обов'язково зупиняємо навіть якщо є помилки
