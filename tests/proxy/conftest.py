import pytest
from brownie import (
    HighriseLand,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)
from brownie.network.account import Account
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data

from .. import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


@pytest.fixture(scope="session")
def proxy_admin(admin: Account) -> ProjectContract:
    proxy_admin = ProxyAdmin.deploy({"from": admin})
    return proxy_admin


@pytest.fixture
def land_proxy(admin: Account, proxy_admin: ProjectContract) -> ProjectContract:
    # Land
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    # Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker,
    # which may impact the proxy. Manually invoking initializer on implementation contract
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
    )
    # Land Proxy
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
    )
    land_proxy = TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": admin, "gas_limit": 1000000},
    )
    return land_proxy