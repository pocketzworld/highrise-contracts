import pytest
from brownie import HighriseEstates, HighriseLand, accounts, config, network
from brownie.network.account import LocalAccount
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


@pytest.fixture(scope="session")
def admin() -> LocalAccount:
    a = accounts.add()
    print(f"Admin address is: {a.address}")
    return a


@pytest.fixture
def alice() -> str:
    print(f"Alice address is: {accounts[1]}")
    return accounts[1]


@pytest.fixture
def bob() -> str:
    return accounts[2]


@pytest.fixture
def charlie() -> str:
    return accounts[3]
