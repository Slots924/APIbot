"""Функція для отримання статі профілю AdsPower за його ідентифікатором."""

from __future__ import annotations

import json
from typing import Optional

from src.core.ads_power import AdsPower


def get_profil_gender_by_id(ads: AdsPower, user_id: str) -> Optional[str]:
    """Повертає стать профілю (``Male`` або ``Female``) через клієнт :class:`AdsPower`."""

    # Нормалізуємо ідентифікатор, щоб уникнути помилок при роботі з числами.
    normalized_user_id = str(user_id)

    # Запитуємо детальну інформацію про профіль безпосередньо через AdsPower.
    profile_info = ads.get_profile_info_by_id(normalized_user_id)
    if not profile_info:
        print(
            f"[API] ❌ Не вдалося отримати профіль {normalized_user_id} для визначення статі."
        )
        return None

    # Поле ``name`` містить рядок зі службовими даними у форматі ``метадані :: {"sex": "Male"}``.
    name_field = profile_info.get("name")
    if not isinstance(name_field, str) or "::" not in name_field:
        print(
            f"[API] ❌ Поле name профілю {normalized_user_id} не містить очікуваного роздільника '::'."
        )
        return None

    # Розділяємо рядок і забираємо JSON-частину з правої половини.
    _, json_part = name_field.split("::", 1)
    json_part = json_part.strip()

    try:
        # Перетворюємо JSON-рядок на Python-словник, щоб дістати потрібний ключ.
        name_payload = json.loads(json_part)
    except json.JSONDecodeError as exc:
        print(
            f"[API] ❌ Не вдалося розібрати JSON зі статтю профілю {normalized_user_id}: {exc}"
        )
        return None

    # Повертаємо стать лише якщо значення відповідає очікуваному переліку.
    sex = name_payload.get("sex")
    if sex in ("Male", "Female"):
        return sex

    print(
        f"[API] ❌ JSON-інформація профілю {normalized_user_id} не містить коректного поля 'sex': {name_payload}"
    )
    return None
