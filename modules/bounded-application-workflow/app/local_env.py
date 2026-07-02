from pathlib import Path

_MODULE_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _MODULE_ROOT / ".env"
_values: dict[str, str] | None = None


def local_env() -> dict[str, str]:
    """Read module-local .env (cached). Missing file => empty dict."""
    global _values
    if _values is not None:
        return _values

    values: dict[str, str] = {}
    if _ENV_PATH.is_file():
        for line in _ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value

    _values = values
    return _values


def get_local_env(key: str, default: str | None = None) -> str | None:
    return local_env().get(key, default)
