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

    def _build_start_payload(self, long_user_id: str) -> Dict[str, Any]:
        """Формує JSON для запуску профілю в AdsPower API v2."""

        # ``long_user_id`` – внутрішній ідентифікатор профілю, який повертає AdsPower
        # у полі ``user_id``. Саме його необхідно передавати в API для керування
        # профілем, зокрема під час налаштування стартових параметрів.
        # Решту параметрів тримаємо у конфігурації ``START_PROFILE_PARAMETERS``,
        # щоб централізовано керувати поведінкою браузера під час старту.
        payload: Dict[str, Any] = {"user_id": long_user_id}
        payload.update(START_PROFILE_PARAMETERS)
        return payload

    def _fetch_profile_entry(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Повертає словник із даними профілю для переданого серійного номера."""

        normalized_user_id = str(user_id)
        try:
            # Надсилаємо запит із параметром ``serial_number``, щоб AdsPower одразу
            # повернув інформацію для потрібного профілю й не доводилося фільтрувати
            # список локально. Саме так ми отримуємо ``long_user_id`` (``user_id``),
            # який необхідний для подальших запитів.
            response = self._api_get(
                "/api/v1/user/list", serial_number=normalized_user_id
            )
        except Exception as exc:
            print(
                f"[AdsPower] ❌ Не вдалося отримати перелік профілів для серійного номера {normalized_user_id}: {exc}"
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
            if isinstance(profile, dict) and profile.get("serial_number") == normalized_user_id:
                return profile

        print(
            f"[AdsPower] ⚠️ Профіль із серійним номером {normalized_user_id} не знайдено у відповіді AdsPower."
        )
        return None

    def _fetch_long_user_id(self, user_id: str) -> Optional[str]:
        """Повертає ``long_user_id`` (значення поля ``user_id``) для серійного номера."""

        profile = self._fetch_profile_entry(user_id)
        if profile is None:
            return None

        long_user_id = profile.get("user_id")
        if long_user_id is None:
            normalized_user_id = str(user_id)
            print(
                f"[AdsPower] ⚠️ Для серійного номера {normalized_user_id} не знайдено long_user_id у відповіді."
            )
            return None

        return str(long_user_id)

    def start(self, user_id: str) -> Dict[str, Any]:
        """Стартує профіль AdsPower і повертає службові дані."""

        normalized_user_id = str(user_id)
        long_user_id = self._fetch_long_user_id(normalized_user_id)
        if long_user_id is None:
            raise RuntimeError(
                f"AdsPower не надав long_user_id для серійного номера {normalized_user_id}."
            )

        payload = self._build_start_payload(long_user_id)
        try:
            # AdsPower API v2 очікує POST-запит на endpoint ``/api/v2/browser-profile/start`` із JSON-тілом.
            response = self._api_post("/api/v2/browser-profile/start", payload)
        except Exception as exc:  # pragma: no cover - логування відбувається для відлагодження.
            print(
                f"[AdsPower] ❌ Не вдалося запустити профіль {normalized_user_id}: {exc}"
            )
            traceback.print_exc()
            raise

        if response.get("code") != 0:
            raise RuntimeError(f"AdsPower start failed: {response}")

        # У разі успіху сервіс повертає словник із ключами debug_port, webdriver тощо.
        data = response.get("data") or {}
        if not isinstance(data, dict):
            raise RuntimeError(
                f"AdsPower повернув неочікувану структуру даних для профілю {normalized_user_id}: {response}"
            )
        return data

    def stop(self, user_id: str) -> None:
        """Коректно зупиняє профіль AdsPower."""

        normalized_user_id = str(user_id)
        try:
            self._api_get("/api/v1/browser/stop", serial_number=normalized_user_id)
        except Exception as exc:  # pragma: no cover - мережеві помилки фіксуємо, але не валимо виконання.
            print(
                f"[AdsPower] ⚠️ Не вдалося зупинити профіль {normalized_user_id}: {exc}"
            )
            traceback.print_exc()

    def get_profile_info_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Повертає структуру з інформацією про профіль AdsPower."""

        profile = self._fetch_profile_entry(user_id)
        if profile is None:
            return None

        return profile
