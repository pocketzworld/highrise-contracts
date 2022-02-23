import pytest
from brownie import HighriseEstates, HighriseLand, accounts, config, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from scripts.deploy_with_proxy import deploy_with_proxy
from scripts.deploy_with_proxy_v3 import deploy_with_proxy as deploy_with_proxy_v3


@pytest.fixture
def land_contract(admin: LocalAccount) -> ProjectContract:
    land = HighriseLand.deploy(
        "Land",
        "LND",
        "0x4527be8f31e2ebfbef4fcaddb5a17447b27d2aef",
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land


@pytest.fixture
def estate_contract(land_contract: ProjectContract, admin: LocalAccount):
    estates = HighriseEstates.deploy(
        "Highrise Estates",
        "HES",
        land_contract.address,
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land_contract.grantRole(land_contract.ESTATE_MANAGER_ROLE(), estates)
    return estates


@pytest.fixture(scope="session")
def admin() -> LocalAccount:
    return get_account()


@pytest.fixture
def alice() -> Account:
    print(f"Alice address is: {accounts[1]}")
    return accounts[1]


@pytest.fixture
def bob() -> str:
    return accounts[2]


@pytest.fixture
def charlie() -> str:
    return accounts[3]


@pytest.fixture
def proxy_deployment() -> tuple[ProjectContract, ProjectContract, ProjectContract]:
    proxy_admin, proxy, land = deploy_with_proxy()
    return proxy_admin, proxy, land


@pytest.fixture
def proxy_land_contract(proxy_deployment) -> ProjectContract:
    _, proxy, _ = proxy_deployment
    return proxy


@pytest.fixture
def proxy_deployment_v3() -> tuple[ProjectContract, ProjectContract, ProjectContract]:
    proxy_admin, land_proxy, land, estate_proxy, estate = deploy_with_proxy_v3()
    return proxy_admin, land_proxy, land, estate_proxy, estate
