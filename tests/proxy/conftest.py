import pytest
from brownie import HighriseLand, config, network
from brownie.network.account import Account
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data
from scripts.helpers import Project

from .. import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


@pytest.fixture(scope="session")
def proxy_admin(admin: Account, oz: Project) -> ProjectContract:
    proxy_admin = oz.ProxyAdmin.deploy({"from": admin})
    return proxy_admin


@pytest.fixture
def land_proxy(
    admin: Account,
    proxy_admin: ProjectContract,
    opensea_proxy_registry: ProjectContract,
    oz: ProjectContract,
) -> ProjectContract:
    # Land
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    # Land Proxy
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        opensea_proxy_registry.address,
    )
    land_proxy = oz.TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": admin, "gas_limit": 2000000},
    )
    return land_proxy
