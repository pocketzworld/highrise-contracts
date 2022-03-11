from typing import Optional

from brownie import Contract, HighriseLand, TransparentUpgradeableProxy, network
from eth_account import Account

from . import LAND_BASE_URI_TEMPLATE, LAND_NAME, LAND_SYMBOL
from .common import encode_function_data, get_account


def deploy_land_implementation(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    # Land
    land = HighriseLand.deploy(
        {"from": account},
    )
    return land


def initialize(
    land_address: str, environment: str = "dev", account: Optional[Account] = None
):
    if not account:
        account = get_account()
    land = Contract.from_abi("HighriseLand", land_address, HighriseLand.abi)
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
        {"from": account},
    ).wait(1)


def deploy_proxy(
    land_impl_address: str,
    proxy_admin_address: str,
    environment="dev",
    account: Optional[Account] = None,
) -> Contract:
    if not account:
        account = get_account()
    land = Contract.from_abi("HighriseLand", land_impl_address, HighriseLand.abi)
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
    )
    land_proxy = TransparentUpgradeableProxy.deploy(
        land_impl_address,
        proxy_admin_address,
        land_encoded_initializer_function,
        {"from": account, "gas_limit": 2000000},
    )
    return land_proxy


def verify_proxy(proxy_address: str):
    contract = TransparentUpgradeableProxy.at(proxy_address)
    TransparentUpgradeableProxy.publish_source(contract)


def verify_land(land_address: str):
    contract = HighriseLand.at(land_address)
    HighriseLand.publish_source(contract)


def deploy_land(
    proxy_admin: Contract, environment: str = "dev", account: Optional[Account] = None
) -> tuple[Contract, Contract]:
    if not account:
        account = get_account()
    # Land
    land = deploy_land_implementation(account)
    # Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker,
    # which may impact the proxy. Manually invoking initializer on implementation contract
    initialize(land.address, environment, account)
    # Deploy land proxy
    land_proxy = deploy_proxy(land.address, proxy_admin.address, environment, account)
    return land_proxy, land
