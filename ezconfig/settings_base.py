import json
import os
from pathlib import Path
from typing import Any, TypeVar

import yaml
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel

from .exceptions import ConfigurationError

_BaseModelSubclass = TypeVar("_BaseModelSubclass", bound=BaseModel)

EZCONFIG_ENVIRONMENT_VAR = "EZCONFIG_ENVIRONMENT"


def init_settings_multienv(
    settings_files_per_env: dict[str, list[str]],
    settings_model: type[_BaseModelSubclass],
) -> _BaseModelSubclass:
    logger.info("Determining what environment to load")
    load_dotenv()

    possible_envs = list(settings_files_per_env.keys())

    environment = os.getenv(EZCONFIG_ENVIRONMENT_VAR)
    if not environment:
        msg = f"Environmental variable {EZCONFIG_ENVIRONMENT_VAR}={possible_envs} must be set"
        raise ConfigurationError(msg)
    if environment not in possible_envs:
        msg = f"Environmental variable {EZCONFIG_ENVIRONMENT_VAR} has invalid value: '{environment}'. Has to be one of: {possible_envs}"
        raise ConfigurationError(msg)

    setting_files = settings_files_per_env[environment]
    return init_settings(setting_files, settings_model)


def init_settings(
    settings_files: list[str], settings_model: type[_BaseModelSubclass]
) -> _BaseModelSubclass:
    logger.info("Initializing settings instance")
    load_dotenv()

    settings_dict: dict[str, Any] = {
        "environment": os.getenv(EZCONFIG_ENVIRONMENT_VAR, "UNDEFINED")
    }
    for filename in settings_files:
        file_dict = _read_file(filename)
        settings_dict.update(file_dict)
    logger.debug(f"Settings dict before validation:\n{settings_dict}")

    settings = settings_model(**settings_dict)
    logger.info(f"Validated settings:\n{settings.model_dump_json(indent=2)}")
    return settings


def _read_file(filename: str) -> dict[str, Any]:
    path = Path(filename)
    if not path.exists():
        msg = f"File {filename} not found"
        raise ConfigurationError(msg)

    logger.info(f"Reading from file {filename}")

    file_str = path.read_text()
    parsed_file = None
    try:
        if filename.endswith(".yaml"):
            parsed_file = yaml.safe_load(file_str)
        if filename.endswith(".json"):
            parsed_file = json.loads(file_str)
    except Exception as e:
        msg = f"Failed to parse file {filename}: {e}"
        raise ConfigurationError(msg) from e

    if parsed_file is None:
        msg = f"Format for file {filename} not supported"
        raise ConfigurationError(msg)

    if not isinstance(parsed_file, dict):
        msg = f"File {filename} is not a dict - only dicts are supported"
        raise ConfigurationError(msg)

    return parsed_file
