import pytest
from brownie import HighriseLand, accounts, config, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from . import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


@pytest.fixture(scope="session")
def admin() -> LocalAccount:
    a = accounts.add()
    print(f"Admin address is: {a.address}")
    print(a.balance())
    return a


@pytest.fixture
def alice() -> Account:
    print(f"Alice address is: {accounts[1]}")
    return accounts[1]


@pytest.fixture
def bob() -> Account:
    return accounts[2]


@pytest.fixture
def charlie() -> Account:
    return accounts[3]


@pytest.fixture
def land_contract(admin: LocalAccount) -> ProjectContract:
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        {"from": admin},
    )
    return land


@pytest.fixture
def proxy_land_contract(proxy_deployment) -> ProjectContract:
    _, proxy, _ = proxy_deployment
    return proxy
