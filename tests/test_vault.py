import pytest
from dotenv import load_dotenv

from ezconfig import vault
from tests import utils


@pytest.fixture(autouse=True)
def _load_dotenv() -> None:
    load_dotenv()


def test_yaml_secret() -> None:
    path = "services/data/000_ezconfig,secret.yaml"
    secret = vault._read_vault_yaml_secret(path)
    assert secret == utils.nested_vault_filled


def test_str_secret() -> None:
    path = "services/data/000_ezconfig,secret.str"
    secret = vault._read_vault_str_secret(path)
    assert secret == utils.vault_string_filled


def test_read_vault_secret() -> None:
    vault_data = vault.read_vault_secret("services", "000_ezconfig")
    assert vault_data["secret.str"] == utils.vault_string_filled
