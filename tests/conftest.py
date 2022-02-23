import pytest
from brownie import accounts
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from scripts.deploy_with_proxy import deploy_with_proxy


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
def proxy_land_contract(proxy_deployment) -> ProjectContract:
    _, proxy, _ = proxy_deployment
    return proxy
