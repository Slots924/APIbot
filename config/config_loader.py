import os
import yaml
from typing import Any, Mapping, MutableMapping, Iterable


class ConfigError(Exception):
    """Raised when required config is missing or malformed."""
    pass


class DotDict(dict):
    """
    Deep dot-access + dict access.
    - obj.key  and  obj['key']
    - recursively wraps dicts in DotDict and lists/tuples inside as well
    """
    __getattr__ = dict.get  # fallback to dict.get for attribute access

    def __init__(self, *args, **kwargs):
        super().__init__()
        data = dict(*args, **kwargs)
        for k, v in data.items():
            super().__setitem__(k, self._wrap(v))

    def __setattr__(self, key: str, value: Any) -> None:
        # keep attribute-style sets in sync with dict
        super().__setitem__(key, self._wrap(value))

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, self._wrap(value))

    @classmethod
    def _wrap(cls, value: Any) -> Any:
        if isinstance(value, Mapping):
            return DotDict(value)
        if isinstance(value, (list, tuple)):
            return type(value)(cls._wrap(v) for v in value)
        return value


def _load_yaml_file(path: str) -> dict:
    if not os.path.exists(path):
        raise ConfigError(f"Required config file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"Config must be a YAML mapping (dict): {path}")
        return data
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML parse error in {path}: {e}") from e


def _deep_merge(base: MutableMapping[str, Any], extra: Mapping[str, Any]) -> MutableMapping[str, Any]:
    """
    Non-destructive deep merge: base <- extra.
    For mapping keys found in both, merge recursively; lists/values are overwritten by 'extra'.
    """
    for k, v in extra.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, Mapping):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(
    settings_path: str = os.path.join("config", "settings.yaml"),
    secrets_path: str = os.path.join("config", "secrets.yaml"),
) -> DotDict:
    """
    Load configuration:
      - REQUIRED: config/settings.yaml (must exist & be valid)
      - OPTIONAL: config/secrets.yaml (merged if present)
    Returns DotDict with deep dot-access (O3).
    """
    settings = _load_yaml_file(settings_path)

    # secrets are optional — if present, merge over settings
    secrets = {}
    if os.path.exists(secrets_path):
        secrets = _load_yaml_file(secrets_path)

    merged = _deep_merge(settings.copy(), secrets)
    return DotDict(merged)