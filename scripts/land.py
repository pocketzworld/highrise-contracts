from time import sleep
from typing import Optional

from brownie import Contract, HighriseLand
from eth_account import Account

from . import LAND_BASE_URI_TEMPLATE, LAND_NAME, LAND_SYMBOL
from .common import encode_function_data, get_account
from .helpers import Project, load_openzeppelin


def deploy_land_implementation(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    # Land
    land = HighriseLand.deploy(
        {"from": account},
    )
    return land


def deploy_proxy(
    land_impl_address: str,
    proxy_admin_address: str,
    opensea_proxy_registry_address: str,
    environment="dev",
    account: Optional[Account] = None,
    oz: Optional[Project] = None,
) -> Contract:
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
    land = Contract.from_abi("HighriseLand", land_impl_address, HighriseLand.abi)
    print(
        f"Initializing land with:\n name: {LAND_NAME}\n symbol: {LAND_SYMBOL}\n uri: {LAND_BASE_URI_TEMPLATE.format(environment=environment)}\n opensea_registry: {opensea_proxy_registry_address}"
    )
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
        opensea_proxy_registry_address,
    )
    land_proxy = oz.TransparentUpgradeableProxy.deploy(
        land_impl_address,
        proxy_admin_address,
        land_encoded_initializer_function,
        {"from": account, "gas_limit": 2000000},
    )
    return land_proxy


def verify_proxy(proxy_address: str, oz: Optional[Project]):
    if not oz:
        oz = load_openzeppelin()
    contract = oz.TransparentUpgradeableProxy.at(proxy_address)
    oz.TransparentUpgradeableProxy.publish_source(contract)


def verify_land(land_address: str):
    contract = HighriseLand.at(land_address)
    HighriseLand.publish_source(contract)


def deploy_land(
    proxy_admin_address: str,
    opensea_proxy_registry_address: str,
    environment: str = "dev",
    account: Optional[Account] = None,
    oz: Optional[Project] = None,
) -> tuple[Contract, Contract]:
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
    # Land
    land = deploy_land_implementation(account)
    sleep(2)
    # Deploy land proxy
    land_proxy = deploy_proxy(
        land.address,
        proxy_admin_address,
        opensea_proxy_registry_address,
        environment,
        account,
        oz,
    )
    return land_proxy, land
