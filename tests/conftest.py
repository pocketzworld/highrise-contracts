import pytest
from brownie import Contract, HighriseLand, MockProxyRegistry, accounts, config, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data
from scripts.helpers import Project

from . import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


@pytest.fixture(scope="session")
def oz(pm):
    project = pm("OpenZeppelin/openzeppelin-contracts@4.5.0/")
    return project


@pytest.fixture(scope="session")
def admin() -> LocalAccount:
    a = accounts.add()
    print(f"Admin address is: {a.address}")
    print(f"Admin balance is: {a.balance()}")
    return a


@pytest.fixture(scope="session")
def invalid_admin() -> LocalAccount:
    a = accounts.add()
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


@pytest.fixture(scope="session")
def opensea_proxy_registry(admin: LocalAccount) -> ProjectContract:
    contract = MockProxyRegistry.deploy({"from": admin})
    return contract


@pytest.fixture
def land_contract_impl(admin: LocalAccount) -> ProjectContract:
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land


@pytest.fixture
def land_contract_proxy(
    admin: LocalAccount,
    land_contract_impl: ProjectContract,
    opensea_proxy_registry: ProjectContract,
    oz: Project,
):
    land_encoded_initializer_function = encode_function_data(
        land_contract_impl.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        opensea_proxy_registry.address,
    )
    proxy_admin = oz.ProxyAdmin.deploy({"from": admin})
    land_proxy = oz.TransparentUpgradeableProxy.deploy(
        land_contract_impl.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": admin, "gas_limit": 2000000},
    )
    return land_proxy


@pytest.fixture
def land_contract(land_contract_proxy):
    return Contract.from_abi(
        "HighriseLand", land_contract_proxy.address, HighriseLand.abi
    )
