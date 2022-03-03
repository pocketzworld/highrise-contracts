from brownie import (
    Contract,
    HighriseEstate,
    HighriseLand,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)
from eth_account import Account

from . import (
    ESTATE_BASE_URI_TEMPLATE,
    ESTATE_NAME,
    ESTATE_SYMBOL,
    LAND_BASE_URI_TEMPLATE,
    LAND_NAME,
    LAND_SYMBOL,
)
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


def deploy_estate(
    account: Account,
    proxy_admin: Contract,
    land_proxy: Contract,
    environment: str = "dev",
) -> tuple[Contract, Contract]:
    # Estate
    estate = HighriseEstate.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    estate_encoded_initializer_function = encode_function_data(
        estate.initialize,
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_URI_TEMPLATE.format(environment=environment),
        land_proxy.address,
    )
    estate_proxy = TransparentUpgradeableProxy.deploy(
        estate.address,
        proxy_admin.address,
        estate_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )

    # Grant estate minting role
    land_proxy_with_abi = Contract.from_abi(
        "HighriseLand", land_proxy.address, HighriseLand.abi
    )
    land_proxy_with_abi.grantRole(
        land_proxy_with_abi.ESTATE_MANAGER_ROLE(),
        estate_proxy.address,
        {"from": account},
    ).wait(1)
    estate_proxy, estate
