# src/main.py
from time import sleep

from src.core.bot import Bot

if __name__ == "__main__":
    # ID профілю в AdsPower
    USER_ID = "214"

    # Пост для тесту
    POST_URL = "https://www.facebook.com/photo/?fbid=820363857527889&set=a.100412672856348"

    # Тестовий коментар
    COMMENT_TEXT = (
        "I’m honestly shocked by their relationship dynamics. "
        "It’s wild how everything turned out!"
    )
    URL_1 = "https://www.facebook.com/photo?fbid=719057444554541&set=a.718138617979757"
    URL_2 = "https://www.facebook.com/permalink.php?story_fbid=pfbid029YpQQP9xz3jKNsD2qJe5FfHTstKy5BRXQsRqHXCo1rMp6B9pq5XHC6bcbpAS9sp6l&id=61554826028950"
    

    
    COMMENTS_TO_LIKE_1 = [
        "Hoď sem odkaz na ten web",
        "Tady máš: https://goodlinke.click/21",
        "Díky, ten web je poklad. Všichni tam vědí, proč tam jsou - napíšeš, domluvíte se, uděláte co je třeba a spokojenej jedeš domů"

    ]

    COMMENTS_TO_LIKE_2 = [
        "Upřímně, mám trochu zvláštní fetiše v posteli",
        "Tady máš https://goodlinke.click/Cz",
        "Hoď sem odkaz na ten web"

    ]



    bot = Bot(user_id=USER_ID)

    try:
        bot.start()  # запуск профілю AdsPower
        bot.open_new_tab(URL_1)

        # bot.like_post("love")
        bot.like_comments(COMMENTS_TO_LIKE_1, "love")
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
