"""Допоміжний клас для взаємодії з локальним AdsPower API."""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

import requests

from src.config.AdsPower.AdsPower import ADSPOWER_HOST, ADSPOWER_PORT


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

    def start(self, user_id: str) -> Dict[str, Any]:
        """Стартує профіль AdsPower і повертає службові дані."""

        normalized_user_id = str(user_id)
        try:
            response = self._api_get("/api/v1/browser/start", serial_number=normalized_user_id)
        except Exception as exc:  # pragma: no cover - логування відбувається для відлагодження.
            print(
                f"[AdsPower] ❌ Не вдалося запустити профіль {normalized_user_id}: {exc}"
            )
            traceback.print_exc()
            raise

        if response.get("code") != 0:
            raise RuntimeError(
                f"AdsPower повернув помилку під час старту профілю {normalized_user_id}: {response}"
            )

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

        normalized_user_id = str(user_id)
        try:
            response = self._api_get("/api/v1/user/list", serial_number=normalized_user_id)
        except Exception as exc:
            print(
                f"[AdsPower] ❌ Не вдалося отримати інформацію про профіль {normalized_user_id}: {exc}"
            )
            traceback.print_exc()
            return None

        if response.get("code") != 0:
            print(
                f"[AdsPower] ❌ Сервіс повернув помилку для профілю {normalized_user_id}: {response}"
            )
            return None

        data: Any = response.get("data")
        if isinstance(data, dict):
            profiles = data.get("list")
            if isinstance(profiles, list) and profiles:
                return profiles[0]
            if isinstance(profiles, list):
                print(f"[AdsPower] ⚠️ Профіль {normalized_user_id} не знайдено у відповіді.")
                return None
            return data

        print(
            f"[AdsPower] ❌ Неочікуваний формат відповіді AdsPower для профілю {normalized_user_id}: {response}"
        )
        return None
