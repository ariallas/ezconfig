from collections.abc import Callable
from typing import Any

from pydantic import BeforeValidator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .vault import _read_vault_str_secret, _read_vault_yaml_secret


def _validate_from_vault(value: Any) -> Any:
    """Валидатор для Pydantic, реагирующий на строки, начинающиеся с
    директив @...
    """
    if not isinstance(value, str):
        return value

    prefix_mapping: dict[str, Callable[[str], Any]] = {
        "@vault_yaml": _read_vault_yaml_secret,
        "@vault_str": _read_vault_str_secret,
    }

    for prefix, handler in prefix_mapping.items():
        if value.startswith(prefix):
            return handler(value.removeprefix(prefix).strip())

    return value


ReadableFromVault = BeforeValidator(_validate_from_vault)


class EzconfigPydanticSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # Включает возможность перезаписать вложенные ключи словарей
        env_file=".env",
        env_parse_none_str="None",  # Парсить строку "None" как настоящий None
        extra="ignore",  # Со строгим extra любая лишняя переменная в .env приводит к ошибке валидации
    )

    # Оверрайд этого метода нужен, чтобы изменить приоритет определения переменных
    # Мы хотим, чтобы переменные окружения перезаписывали настройки из файла
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/#field-value-priority
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],  # noqa: ARG003
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, dotenv_settings, init_settings, file_secret_settings
