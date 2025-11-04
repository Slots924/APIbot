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

    user_id_array = [215,216,217,218]


def run_for_users(user_id_array, url_1, comments_1, url_2, comments_2):
    for user_id in user_id_array:
        print(f"\n=== Запуск для user_id: {user_id} ===")

        bot = Bot(user_id=user_id)

        try:
            bot.start()  # запуск профілю AdsPower

            bot.open_new_tab(url_1)
            bot.like_comments(comments_1, "love")
            bot.close_tab()

            bot.open_new_tab(url_2)
            bot.like_comments(comments_2, "love")
            bot.close_tab()

        except Exception as e:
            print(f"[Помилка для user_id {user_id}]: {e}")

        finally:
            bot.stop()  # обов'язково зупиняємо навіть якщо є помилка


run_for_users(user_id_array, URL_1, COMMENTS_TO_LIKE_1, URL_2, COMMENTS_TO_LIKE_2)












    # 

    # bot = Bot(user_id=user_id)

    # try:
    #     bot.start()  # запуск профілю AdsPower

    #     bot.open_new_tab(URL_1)
    #     bot.like_comments(COMMENTS_TO_LIKE_1, "love")
    #     bot.close_tab()


    #     bot.open_new_tab(URL_2)
    #     bot.like_comments(COMMENTS_TO_LIKE_2, "love")
    #     bot.close_tab()
        
    # finally:
    #     bot.stop()  # обов'язково зупиняємо навіть якщо є помилки
