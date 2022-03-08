from brownie import (
    Contract,
    HighriseLand,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)
from eth_account import Account

from . import LAND_BASE_URI_TEMPLATE, LAND_NAME, LAND_SYMBOL
from .common import encode_function_data


def deploy_proxy_admin(account: Account) -> Contract:
    proxy_admin = ProxyAdmin.deploy({"from": account})
    return proxy_admin


def deploy_land(
    account: Account, proxy_admin: Contract, environment: str = "dev"
) -> tuple[Contract, Contract]:
    # Land
    land = HighriseLand.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    # Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker,
    # which may impact the proxy. Manually invoking initializer on implementation contract
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
    )

    # Land proxy deployment
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
    )
    land_proxy = TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land_proxy, land
