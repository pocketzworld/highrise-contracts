import pytest
from brownie import HighriseEstates, HighriseLand, accounts, config, network
from brownie.network.contract import ProjectContract

from scripts.common import get_account


@pytest.fixture
def land_contract():
    account = get_account()
    land = HighriseLand.deploy(
        "Land",
        "LND",
        "0x4527be8f31e2ebfbef4fcaddb5a17447b27d2aef",
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land


@pytest.fixture
def estate_contract(land_contract: ProjectContract):
    account = get_account()
    estates = HighriseEstates.deploy(
        "Highrise Estates",
        "HES",
        land_contract.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land_contract.grantRole(land_contract.ESTATE_MANAGER_ROLE(), estates)
    return estates


@pytest.fixture
def admin() -> str:
    return accounts[0]


@pytest.fixture
def alice() -> str:
    return accounts[1]


@pytest.fixture
def bob() -> str:
    return accounts[2]


@pytest.fixture
def charlie() -> str:
    return accounts[3]
