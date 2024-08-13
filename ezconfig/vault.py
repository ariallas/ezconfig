import os
from typing import Any, Self

import cachetools.func
import hvac
import yaml
from loguru import logger

from .exceptions import ConfigurationError


class VaultPath:
    def __init__(self, mount_point: str, path: str, key: str) -> None:
        self.mount_point = mount_point
        self.path = path
        self.key = key

    @classmethod
    def from_str(cls, full_vault_path: str) -> Self:
        mount_point, path, key = _parse_full_vault_path(full_vault_path)
        return cls(mount_point=mount_point, path=path, key=key)

    def __repr__(self) -> str:
        return f"mount_point:{self.mount_point} path={self.path} key={self.key}"


def _parse_full_vault_path(full_vault_path: str) -> tuple[str, str, str]:
    mount_point, path_and_key = full_vault_path.split("/data/")
    path, key = path_and_key.split(",")

    if not (mount_point and path and key):
        msg = (
            f"Cannot parse vault path '{full_vault_path}'."
            "Vault paths must look like: '<mount_point>/data/<path>,<key>"
        )
        raise ConfigurationError(msg)

    return mount_point, path, key


def _read_vault_yaml_secret(full_vault_path: str) -> Any:
    """Прочитать секрет в yaml формате"""
    vp = VaultPath.from_str(full_vault_path)

    try:
        vault_data = _read_vault_secret_vp(vp)
        secret_yaml_content = vault_data[vp.key]
        secret = yaml.safe_load(secret_yaml_content)
    except Exception as e:
        msg = f"Failed to load yaml secret: {vp}\nException: {e!r}"
        raise ConfigurationError(msg) from e

    return secret


def _read_vault_str_secret(full_vault_path: str) -> str:
    """Прочитать секрет с одним значением"""
    vp = VaultPath.from_str(full_vault_path)

    try:
        vault_data = _read_vault_secret_vp(vp)
        secret_content = vault_data[vp.key]
    except Exception as e:
        msg = f"Failed to load str secret: {vp}\nException: {e!r}"
        raise ConfigurationError(msg) from e
    return secret_content


@cachetools.func.ttl_cache(maxsize=128, ttl=60)
def _read_vault_secret_vp(vp: VaultPath) -> dict[str, str]:
    if not os.getenv("EZCONFIG_VAULT_TOKEN"):
        msg = "EZCONFIG_VAULT_TOKEN environmental variable must be set"
        raise ConfigurationError(msg)

    vault_addr = os.environ.get("EZCONFIG_VAULT_ADDR", "https://default.vault.url.ru")
    vault_token = os.environ.get("EZCONFIG_VAULT_TOKEN")

    logger.info(f"Reading vault secret: vault_addr={vault_addr}, {vp}")

    client = hvac.Client(url=vault_addr, token=vault_token)
    full_secret_data = client.secrets.kv.read_secret_version(
        mount_point=vp.mount_point, path=vp.path, raise_on_deleted_version=True
    )

    secret_version = full_secret_data["data"]["metadata"]["version"]
    logger.info(f"Read secret {vp}, version: '{secret_version}'")
    return full_secret_data["data"]["data"]


def read_vault_secret(mount_point: str, path: str) -> dict[str, str]:
    vp = VaultPath(mount_point, path, "")
    return _read_vault_secret_vp(vp)
