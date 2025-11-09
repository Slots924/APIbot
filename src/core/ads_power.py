"""Допоміжний клас для взаємодії з локальним AdsPower API."""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

import requests

from src.config.AdsPower.AdsPower import ADSPOWER_HOST, ADSPOWER_PORT
from src.config.ads import START_PROFILE_PARAMETERS


class AdsPower:
    """Інкапсулює мережеві виклики до AdsPower."""

    def __init__(self, host: str = ADSPOWER_HOST, port: int = ADSPOWER_PORT) -> None:
        # Зберігаємо параметри підключення, щоб не дублювати їх у кожному запиті.
        self.host = host
        self.port = port

    @property
    def _api_base(self) -> str:
        # Будуємо базову URL-адресу, через яку викликаємо локальне API AdsPower.
        return f"http://{self.host}:{self.port}"

    def _api_get(self, path: str, **params: Any) -> Dict[str, Any]:
        """Виконує GET-запит до AdsPower і повертає JSON-відповідь."""

        response = requests.get(f"{self._api_base}{path}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _api_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Надсилає POST-запит до AdsPower та повертає JSON-відповідь."""

        # Формуємо повну адресу endpoint-у та надсилаємо JSON у форматі, який очікує AdsPower API.
        response = requests.post(f"{self._api_base}{path}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def _build_start_payload(self, serial_number: str) -> Dict[str, Any]:
        """Формує JSON для запуску профілю в AdsPower API v2."""

        # ``serial_number`` – зовнішній ідентифікатор профілю, який бачимо в
        # інтерфейсі AdsPower. Відтепер саме його очікує endpoint старту, тому
        # одразу формуємо словник з ключем ``profile_no`` і доповнюємо його
        # параметрами з конфігурації ``START_PROFILE_PARAMETERS``.
        payload: Dict[str, Any] = {"profile_no": serial_number}
        payload.update(START_PROFILE_PARAMETERS)
        return payload

    def _fetch_profile_entry(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """Повертає словник із даними профілю для переданого серійного номера."""

        normalized_serial_number = str(serial_number)
        try:
            # Надсилаємо запит із параметром ``serial_number``, щоб AdsPower одразу
            # повернув інформацію для потрібного профілю й не доводилося фільтрувати
            # список локально. Саме так ми отримуємо внутрішній ``user_id`` профілю,
            # який необхідний для подальших запитів.
            response = self._api_get(
                "/api/v1/user/list", serial_number=normalized_serial_number
            )
        except Exception as exc:
            print(
                f"[AdsPower] ❌ Не вдалося отримати перелік профілів для серійного номера {normalized_serial_number}: {exc}"
            )
            traceback.print_exc()
            return None

        data: Any = response.get("data")
        if not isinstance(data, dict):
            print(
                f"[AdsPower] ❌ Відповідь AdsPower містить неочікуваний формат даних: {response}"
            )
            return None

        profiles = data.get("list")
        if not isinstance(profiles, list):
            print(
                f"[AdsPower] ❌ Неочікувана структура списку профілів у відповіді: {response}"
            )
            return None

        for profile in profiles:
            # API повертає список, але в успішному сценарії він містить лише один
            # елемент з деталями профілю, який ми й віддаємо далі.
            if isinstance(profile, dict) and profile.get("serial_number") == normalized_serial_number:
                return profile

        print(
            f"[AdsPower] ⚠️ Профіль із серійним номером {normalized_serial_number} не знайдено у відповіді AdsPower."
        )
        return None

    def _fetch_ads_user_id(self, serial_number: str) -> Optional[str]:
        """Повертає ``user_id`` AdsPower для серійного номера профілю."""

        profile = self._fetch_profile_entry(serial_number)
        if profile is None:
            return None

        ads_user_id = profile.get("user_id")
        if ads_user_id is None:
            normalized_serial_number = str(serial_number)
            print(
                f"[AdsPower] ⚠️ Для серійного номера {normalized_serial_number} не знайдено user_id у відповіді."
            )
            return None

        return str(ads_user_id)

    def start(self, serial_number: str) -> Dict[str, Any]:
        """Стартує профіль AdsPower за серійним номером і повертає службові дані."""

        normalized_serial_number = str(serial_number)
        # Формуємо тіло запиту так, щоб AdsPower отримав серійний номер профілю
        # в полі ``profile_no`` і налаштування запуску з конфігурації. Додаткові
        # мережеві виклики більше не потрібні: старт виконується безпосередньо
        # за серійним номером, який ми отримали від користувача.
        payload = self._build_start_payload(normalized_serial_number)
        try:
            # AdsPower API v2 очікує POST-запит на endpoint ``/api/v2/browser-profile/start`` із JSON-тілом.
            response = self._api_post("/api/v2/browser-profile/start", payload)
        except Exception as exc:  # pragma: no cover - логування відбувається для відлагодження.
            print(
                f"[AdsPower] ❌ Не вдалося запустити профіль {normalized_serial_number}: {exc}"
            )
            traceback.print_exc()
            raise

        if response.get("code") != 0:
            raise RuntimeError(f"AdsPower start failed: {response}")

        # У разі успіху сервіс повертає словник із ключами debug_port, webdriver тощо.
        data = response.get("data") or {}
        if not isinstance(data, dict):
            raise RuntimeError(
                f"AdsPower повернув неочікувану структуру даних для профілю {normalized_serial_number}: {response}"
            )
        return data

    def stop(self, serial_number: str) -> None:
        """Коректно зупиняє профіль AdsPower за серійним номером."""

        normalized_serial_number = str(serial_number)
        try:
            self._api_get("/api/v1/browser/stop", serial_number=normalized_serial_number)
        except Exception as exc:  # pragma: no cover - мережеві помилки фіксуємо, але не валимо виконання.
            print(
                f"[AdsPower] ⚠️ Не вдалося зупинити профіль {normalized_serial_number}: {exc}"
            )
            traceback.print_exc()

    def get_profile_info_by_serial_number(
        self, serial_number: str
    ) -> Optional[Dict[str, Any]]:
        """Повертає структуру з інформацією про профіль AdsPower за серійним номером."""

        profile = self._fetch_profile_entry(serial_number)
        if profile is None:
            return None

        return profile

    def get_profile_info_by_id(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """Залишено для сумісності: делегує виклик до :meth:`get_profile_info_by_serial_number`."""

        return self.get_profile_info_by_serial_number(serial_number)
