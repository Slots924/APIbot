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

    def _build_start_payload(self, profile_id: str) -> Dict[str, Any]:
        """Формує JSON для запуску профілю в AdsPower API v2."""

        # ``profile_id`` – основний ідентифікатор профілю, який очікує AdsPower API.
        # Решту параметрів тримаємо у конфігурації ``START_PROFILE_PARAMETERS``,
        # щоб централізовано керувати поведінкою браузера під час старту.
        payload: Dict[str, Any] = {"profile_id": profile_id}
        payload.update(START_PROFILE_PARAMETERS)
        return payload

    def _fetch_profile_entry(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Повертає словник із даними профілю для переданого серійного номера."""

        normalized_user_id = str(user_id)
        try:
            # Endpoint ``/api/v1/user/list`` повертає список усіх профілів.
            # Фільтруємо його локально, оскільки AdsPower очікує рядкове порівняння
            # та не завжди приймає параметр ``serial_number`` в запиті.
            response = self._api_get("/api/v1/user/list")
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
            if not isinstance(profile, dict):
                continue
            if profile.get("serial_number") == normalized_user_id:
                return profile

        print(f"[AdsPower] ⚠️ Профіль із серійним номером {normalized_user_id} не знайдено у списку.")
        return None

    def _fetch_profile_id(self, user_id: str) -> Optional[str]:
        """Повертає ``profile_id`` для переданого серійного номера користувача."""

        profile = self._fetch_profile_entry(user_id)
        if profile is None:
            return None

        profile_id = profile.get("user_id")
        if profile_id is None:
            normalized_user_id = str(user_id)
            print(
                f"[AdsPower] ⚠️ Для серійного номера {normalized_user_id} не знайдено profile_id у відповіді."
            )
            return None

        return str(profile_id)

    def start(self, user_id: str) -> Dict[str, Any]:
        """Стартує профіль AdsPower і повертає службові дані."""

        normalized_user_id = str(user_id)
        profile_id = self._fetch_profile_id(normalized_user_id)
        if profile_id is None:
            raise RuntimeError(
                f"AdsPower не надав profile_id для серійного номера {normalized_user_id}."
            )

        payload = self._build_start_payload(profile_id)
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
