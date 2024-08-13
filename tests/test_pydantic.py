import copy

import pytest

from ezconfig.exceptions import ConfigurationError
from ezconfig.settings_base import init_settings, init_settings_multienv
from tests import utils
from tests.utils import TstSettings


def test_yaml() -> None:
    settings = init_settings(
        ["tests/configs/testconfig.yaml", "tests/configs/testconfig.json"],
        TstSettings,
    )
    assert settings.model_dump() == utils.settings_filled


@pytest.fixture()
def _override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_STRING", "new_string")
    monkeypatch.setenv("NESTED__NAME", "Bruce")


@pytest.mark.usefixtures("_override_env")
def test_env_overrides() -> None:
    settings = init_settings(
        ["tests/configs/testconfig.yaml", "tests/configs/testconfig.json"],
        TstSettings,
    )

    modified_settings_filled = copy.deepcopy(utils.settings_filled)
    modified_settings_filled["vault_string"] = "new_string"
    modified_settings_filled["nested"]["name"] = "Bruce"

    assert settings.model_dump() == modified_settings_filled


def test_multienv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZCONFIG_ENVIRONMENT", "test")

    settings = init_settings_multienv(
        {
            "test": ["tests/configs/testconfig.yaml", "tests/configs/testconfig.json"],
            "prod": ["lol"],
        },
        TstSettings,
    )
    assert settings.model_dump() == utils.settings_filled_test


def test_multienv_not_set() -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        init_settings_multienv({"test": [], "prod": []}, TstSettings)
    assert "must be set" in str(exc_info.value)
