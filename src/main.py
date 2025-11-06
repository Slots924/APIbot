# src/main.py
"""Точка входу, яка демонструє використання :class:`TaskManager` для керування ботом."""

from src.task_manager import TaskManager

if __name__ == "__main__":
    # ID профілів в AdsPower, для яких ми хочемо повторити однаковий сценарій.
    USER_ID_ARRAY = [215, 216, 217, 218]

    # Посилання на пости, з якими працюватимемо.
    URL_1 = "https://www.facebook.com/photo?fbid=719057444554541&set=a.718138617979757"
    URL_2 = (
        "https://www.facebook.com/permalink.php?story_fbid=pfbid029YpQQP9xz3jKNsD2qJe5FfHTstKy5BRXQsRqHXCo1rMp6B9pq5XHC6bcbpAS9sp6l&id=61554826028950"
    )

    # Набори коментарів, яким потрібно поставити реакції.
    COMMENTS_TO_LIKE_1 = [
        "Hoď sem odkaz na ten web",
        "Tady máš: https://goodlinke.click/21",
        (
            "Díky, ten web je poklad. Všichni tam vědí, proč tam jsou - napíšeš, domluvíte se, "
            "uděláte co je třeba a spokojenej jedeš domů"
        ),
    ]

    COMMENTS_TO_LIKE_2 = [
        "Upřímně, mám trochu zvláštní fetiše v posteli",
        "Tady máš https://goodlinke.click/Cz",
        "Hoď sem odkaz на ten web",
    ]

    # Створюємо менеджер задач, який збере в собі всі дії для повторного виконання.
    task_manager = TaskManager(USER_ID_ARRAY)

    # Формуємо сценарій: відкриття першого поста, проставлення реакцій та закриття вкладки.
    task_manager.open_new_tab(URL_1)
    task_manager.like_comments(COMMENTS_TO_LIKE_1, "love")
    task_manager.close_tab()

    # Повторюємо аналогічні кроки для іншого поста.
    task_manager.open_new_tab(URL_2)
    task_manager.like_comments(COMMENTS_TO_LIKE_2, "love")
    task_manager.close_tab()

    # Запускаємо сценарій для кожного профілю зі списку `USER_ID_ARRAY`.
    task_manager.run()
