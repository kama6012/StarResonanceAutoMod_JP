"""Translate message templates before inserting user data and server values."""

import json
from pathlib import Path

LANGUAGES = ('en', 'ja', 'zh')
_JA = json.loads((Path(__file__).parent / 'locales' / 'ja.json').read_text(encoding='utf-8'))


def normalize_language(lang: str | None = None) -> str:
    value = (lang or 'en').strip().lower()
    return value if value in LANGUAGES else 'en'


def t(lang: str, message: str, *, zh: str | None = None, **values) -> str:
    lang = normalize_language(lang)
    if lang == 'zh' and zh is not None:
        return zh
    template = _JA.get(message, message) if lang == 'ja' else message
    return template.format(**values)
