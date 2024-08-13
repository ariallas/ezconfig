from typing import Annotated

from pydantic import BaseModel

from ezconfig.settings_pydantic import EzconfigPydanticSettings, ReadableFromVault


class TstNested(BaseModel):
    name: str
    surname: str


class TstVaultNested(BaseModel):
    login: str
    password: str
    hostname: str


class TstSettings(EzconfigPydanticSettings):
    environment: str
    string: str
    integer: int
    none: None

    nested: TstNested

    vault_string: Annotated[str, ReadableFromVault]
    vault_nested: Annotated[TstVaultNested, ReadableFromVault]


nested_filled = {
    "name": "Harry",
    "surname": "Potter",
}
vault_string_filled = "aaabbbccc"
nested_vault_filled = {
    "login": "admin",
    "password": "pa55wOrd",
    "hostname": "yandex.ru",
}
settings_filled = {
    "environment": "UNDEFINED",
    "string": "abc",
    "integer": 123,
    "none": None,
    "nested": nested_filled,
    "vault_string": vault_string_filled,
    "vault_nested": nested_vault_filled,
}
settings_filled_test = settings_filled.copy()
settings_filled_test["environment"] = "test"
