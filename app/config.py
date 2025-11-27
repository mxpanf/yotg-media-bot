"""
Application configuration loader based on Pydantic Settings.
Reads from YAML file and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

DEFAULT_CONFIG_PATH = Path("config/settings.yaml")


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YOTG_", extra="ignore")

    bot_token: str = Field(..., alias="bot_token")
    locale_default: str = Field("ru", alias="locale_default")
    tmp_dir: Path = Field(Path("/dev/shm/yotg-media-bot"), alias="tmp_dir")

    @classmethod
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    Custom settings source that reads from YAML file.
    """

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls)
        self.path = Path(os.getenv("YOTG_CONFIG_FILE", DEFAULT_CONFIG_PATH))

    def __call__(self) -> dict[str, Any]:
        return self._read()

    def get_field_value(self, field, field_name: str) -> tuple[Any, str, bool]:
        data = self._read()
        value = data.get(field.alias or field_name)
        return value, field.alias or field_name, False

    def prepare_field_value(
        self, field_name: str, field, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            return {}
        return data
