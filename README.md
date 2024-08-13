# ezconfig

## Описание

Библиотека для упрощения инициализации конфигурации в питоновских сервисах: инициализация из файлов, удобная интеграция с  HashiCorp Vault, разделение на среды.  
Построена на базе [PydanticSettings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

## Использование репозитория

### Инициализация

```bash
poetry install
poetry shell
pre-commit install
```

Cоздать файл `.env` по образцу из `.env.example`
Для работы pre-commit хука должен быть установлен [Node.js](https://nodejs.org/en/download/package-manager).

### Запуск тестов

```bash
poetry shell
pytest
```

### Сборка и деплой

**Обновить версию в pyproject.toml!**

```bash
poetry build
poetry publish ...
```

## Использование библиотеки

Пример файла `config.py` с инициализацией настроек:

```python
from __future__ import annotations

from typing import Annotated

from ezconfig import (
    EzconfigPydanticSettings,
    ReadableFromVault,
    init_settings_multienv,
)
from pydantic import BaseModel, SecretStr


# EzconfigPydanticSettings наследуется от BaseSettings, соответсвенно поддерживает все
# фичи Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
class AppSettings(EzconfigPydanticSettings):
    # Если добавить в свою модель поле environment, при инициализации настроек
    # оно будет заполнено значением текущего окружения (prod/test...)
    environment: str

    # Для указания, что данную переменную можно инициализировать из волта,
    # используется тип Annotated[<тип переменной>, ReadableFromVault]
    secret_str: Annotated[SecretStr, ReadableFromVault]

    # ReadableFromVault можно использовать и для более сложных типов
    secret_dict: Annotated[dict[str, str], ReadableFromVault]

    # ReadableFromVault можно использовать для вложенных моделей
    nested_model: Annotated[NestedModel, ReadableFromVault]

    another_nested_model: AnotherNestedModel


class NestedModel(BaseModel):
    host: str
    port: int


class AnotherNestedModel(BaseModel):
    # ReadableFromVault можно использовать внутри вложенных моделей
    password: Annotated[SecretStr, ReadableFromVault]


# При работе с несколькими окружениями настройки инициализируются через функцию init_settings_multienv
# Необходимы переменные окружения (обычные или в .env):
#  - EZCONFIG_ENVIRONMENT - для указания окружения
#  - EZCONFIG_VAULT_TOKEN - токен для Vault
settings = init_settings_multienv(
    {
        # Указываеться список файлов - они будут объединены через метод update() питоновского словаря, слева направо
        # Поддерживаются yaml и json файлы
        "prod": ["config/shared.yaml", "config/settings_prod.yaml"],
        "test": ["config/shared.yaml", "config/settings_test.yaml"],
    },
    # Далее указывается сам класс настроек, определнный выше
    AppSettings,
)

# Без окружений настройки инициализируются через функцию init_settings
settings = init_settings(["config/shared.yaml", "config/settings_prod.yaml"], AppSettings)
```

Соответствующий `config/settings_prod.yaml`:
```yaml
# Указывается путь к секрету в формате '@<parser> <mount_point>/data/<path>,<key>'
# Доступные парсеры: vault_yaml (парсит yaml в словарь), vault_str (парсит строку)
secret_str: "@vault_str mount-point/data/path,key1"

secret_dict: "@vault_yaml mount-point/data/path,key2"
nested_model: "@vault_yaml mount-point/data/path,key3"

another_nested_model:
	password: "@vault_str mount-point/data/path,key4"
```

Соответствующий `.env`:
```bash
EZCONFIG_VAULT_TOKEN=hvs.CAE...
# или
EZCONFIG_VAULT_TOKEN=${VAULT_TOKEN}  # Использовать значение переменной VAULT_TOKEN

# Определяет, какие файлы будут подгружены через init_settings_multienv
EZCONFIG_ENVIRONMENT=test

# Переменными окружения можно перезаписывать значения конфига
# Доступ к вложенным значениям словарей осуществляется через двойное подчеркивание
NESTED_MODEL__HOST=127.0.0.1
```

Для простых скриптов инициализировать настройки можно и без отдельных файлов:
```python
from typing import Annotated

from ezconfig import EzconfigPydanticSettings, ReadableFromVault, init_settings
from pydantic import SecretStr


class AppSettings(EzconfigPydanticSettings):
    # Типизатор будет ругаться на такое присваивание, это нормально
    secret_str: Annotated[SecretStr, ReadableFromVault] = "@vault_str mount-point/data/path,key1"  # type: ignore

settings = init_settings([], AppSettings)
```
