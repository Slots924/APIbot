"""Головна дія для встановлення реакції на пості."""

from selenium.webdriver.remote.webdriver import WebDriver

from .reaction_executor import apply_reaction
from .reaction_verifier import verify_reaction_result
from .request_preparer import prepare_requested_reaction
from .skip_logic import should_skip_action
from .state_evaluator import evaluate_current_state


def like_post(driver: WebDriver, reaction: str = "like") -> bool:
    """Оркеструє послідовність кроків встановлення реакції під постом."""

    print("[ACTION like_post] 🚀 Починаю перевірку реакцій під постом.")

    normalized_reaction = prepare_requested_reaction(reaction)
    like_state, reaction_state = evaluate_current_state(driver)

    if should_skip_action(like_state, reaction_state):
        return True

    if not apply_reaction(driver, normalized_reaction):
        return False

    return verify_reaction_result(driver, normalized_reaction)
