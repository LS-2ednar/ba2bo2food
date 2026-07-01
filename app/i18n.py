import json
from pathlib import Path

SUPPORTED_LOCALES = ("en", "de")
DEFAULT_LOCALE = "en"

_I18N_DIR = Path(__file__).parent / "i18n"
_translations: dict[str, dict[str, str]] = {}


def _load(locale: str) -> dict[str, str]:
    if locale not in _translations:
        path = _I18N_DIR / f"{locale}.json"
        _translations[locale] = json.loads(path.read_text(encoding="utf-8"))
    return _translations[locale]


def translate(locale: str, key: str) -> str:
    locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    value = _load(locale).get(key)
    if value is None and locale != DEFAULT_LOCALE:
        value = _load(DEFAULT_LOCALE).get(key)
    return value if value is not None else key


def resolve_locale(accept_language: str | None) -> str:
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code in SUPPORTED_LOCALES:
            return code
    return DEFAULT_LOCALE
