# -*- coding: utf-8 -*-
"""
Simple JSON-based i18n loader.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOCALES_PATH = Path(__file__).parent / "locales"


def load_translations() -> dict[str, dict[str, str]]:
    translations: dict[str, dict[str, str]] = {}
    for path in LOCALES_PATH.glob("*/messages.json"):
        locale = path.parent.name
        with path.open("r", encoding="utf-8") as file:
            translations[locale] = json.load(file)
    return translations


@dataclass
class I18n:
    translations: dict[str, dict[str, str]]
    default_locale: str = "en"

    def gettext(self, key: str, locale: str | None = None, **kwargs: Any) -> str:
        lang = locale or self.default_locale
        value = (
            self.translations.get(lang, {}).get(key)
            or self.translations.get(self.default_locale, {}).get(key)
            or key
        )
        try:
            return value.format(**kwargs)
        except Exception:
            return value
