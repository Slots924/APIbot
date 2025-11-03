from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def like_post(driver, timeout=12) -> bool:
    wait = WebDriverWait(driver, timeout)

    # Локальні словники/хелпери — без глобальних змінних
    like_labels = (
        "Like", "Вподобати", "Нравится", "Me gusta",
        "J’aime", "Gefällt mir", "Mi piace", "Gosto", "Curtidas"
    )

    # 1) Кандидати на контейнер дій (екшени) для поста.
    # Facebook часто міняє структуру, але зберігає aria-label/role у батьківських вузлах.
    container_xpaths = [
        # Найстабільніше в новому дизайні
        "//div[@aria-label='Actions for this post']",
        # Іноді це toolbar із кнопками (Like/Comment/Share)
        "//div[@role='toolbar' and @aria-label and .//div[@role='button']]",
        # Варіант із 'group' (рідше, але трапляється)
        "//div[@role='group' and .//div[@role='button'] and descendant::*[contains(@aria-label,'Share') or contains(@aria-label,'Comment')]]",
        # Біля блоку коментаря "Write a comment..." часто є блок дій вище
        "(.//div[.//div[@role='textbox' and @aria-label and (contains(@aria-label,'comment') or contains(@aria-label,'Коментар') or contains(@aria-label,'коментар'))]])/preceding::div[@role='toolbar'][1]"
    ]

    def find_container():
        for xp in container_xpaths:
            try:
                el = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
                if el:
                    return el
            except Exception:
                continue
        return None

    actions = find_container()

    # 1a) Якщо контейнер не знайдено — зробимо легкий скрол і ще раз пошукаємо
    if actions is None:
        driver.execute_script("window.scrollBy(0, 400);")
        sleep(0.3)
        actions = find_container()

    # 1b) Якщо все одно None — останній шанс: знайти саму кнопку глобально,
    # а потім піднятися до найближчого toolbar/group
    if actions is None:
        like_global = None
        for t in like_labels:
            try:
                like_global = driver.find_element(
                    By.XPATH,
                    f"//div[@role='button' and contains(@aria-label,'{t}') and (not(@aria-pressed) or @aria-pressed='false')]"
                )
                break
            except Exception:
                continue
        if like_global:
            # Підіймаємось до найближчого контейнера дій
            try:
                actions = like_global.find_element(
                    By.XPATH,
                    "ancestor::div[@aria-label='Actions for this post' or @role='toolbar' or @role='group'][1]"
                )
            except Exception:
                actions = None

    if actions is None:
        print("❌ Не вдалося локалізувати контейнер дій для поста.")
        return False

    # 2) Якщо вже лайкнуто — швидко виходимо
    try:
        already = actions.find_elements(
            By.XPATH,
            ".//div[@role='button' and @aria-pressed='true' and "
            + " or ".join([f"contains(@aria-label,'{t}')" for t in like_labels]) + "]"
        )
        if already:
            print("⭐ Вже лайкнуто — пропускаю.")
            return True
    except Exception:
        pass

    # 3) Спробуємо знайти кнопку Like усередині контейнера кількома способами
    btn_candidates = []

    # 3a) За aria-label (різні локалі)
    for t in like_labels:
        try:
            el = actions.find_element(
                By.XPATH,
                f".//div[@role='button' and contains(@aria-label,'{t}') and (not(@aria-pressed) or @aria-pressed='false')]"
            )
            btn_candidates.append(el)
        except Exception:
            continue

    # 3b) Якщо не знайшли — кнопка Like інколи має текстовий span
    if not btn_candidates:
        try:
            el = actions.find_element(
                By.XPATH,
                ".//div[@role='button' and (not(@aria-pressed) or @aria-pressed='false')]"
                "[.//span[normalize-space()='Like' or normalize-space()='Вподобати' or normalize-space()='Нравится']]"
            )
            btn_candidates.append(el)
        except Exception:
            pass

    # 3c) Якщо й це не спрацювало — евристика: серед кнопок тулбара взяти першу toggle-кнопку
    if not btn_candidates:
        try:
            toggles = actions.find_elements(
                By.XPATH,
                ".//div[@role='button' and (not(@aria-pressed) or @aria-pressed='false')]"
            )
            btn_candidates.extend(toggles)
        except Exception:
            pass

    if not btn_candidates:
        print("❌ Не вдалося знайти кнопку Like у контейнері поста.")
        return False

    like_btn = btn_candidates[0]

    # 4) Скролимо у видиму область — FB інколи блокує кліки поза viewport
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", like_btn)
        sleep(0.15)
    except Exception:
        pass

    # 5) Клік + перевірка стану
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, ".")))  # «розморожуємо» очікування
        try:
            like_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", like_btn)
    except Exception:
        driver.execute_script("arguments[0].click();", like_btn)

    # 6) Після кліку DOM може перебудуватись — оновимо посилання на кнопку
    try:
        sleep(0.15)
        like_btn = actions.find_element(
            By.XPATH,
            ".//div[@role='button' and @aria-pressed='true' or .//span[@aria-hidden='true']]"  # трохи ширша перевірка
        )
    except Exception:
        pass

    # 7) Фінальна валідація aria-pressed
    try:
        wait.until(lambda d: like_btn.get_attribute("aria-pressed") == "true")
        print("✅ Лайк поставлено.")
        return True
    except Exception:
        # Якщо aria-pressed відсутній або не оновився — перевіримо за кількістю реакцій у контейнері
        try:
            reactions = actions.find_elements(By.XPATH, ".//span[contains(@aria-label,'reaction') or contains(@aria-label,'реакц')]")
            if reactions:
                print("✅ Лайк імовірно поставлено (виявлено реакції).")
                return True
        except Exception:
            pass
        print("⚠️ Клік зроблено, але не зміг підтвердити зміну стану.")
        return False
