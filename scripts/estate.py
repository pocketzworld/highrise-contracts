from time import sleep
from typing import Optional

from brownie import Contract, HighriseEstate, HighriseLand, TransparentUpgradeableProxy
from eth_account import Account

from . import ESTATE_BASE_URI_TEMPLATE, ESTATE_NAME, ESTATE_SYMBOL
from .common import encode_function_data, get_account


def deploy_estate_implementation(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    estate = HighriseEstate.deploy(
        {"from": account},
    )
    return estate


def deploy_proxy(
    estate_impl_address: str,
    land_address: str,
    proxy_admin_address: str,
    opensea_proxy_registry_address: str,
    environment="dev",
    account: Optional[Account] = None,
) -> Contract:
    if not account:
        account = get_account()
    estate = Contract.from_abi(
        "HighriseEstate", estate_impl_address, HighriseEstate.abi
    )
    print(
        f"Initializing estate with:\n name: {ESTATE_NAME}\n symbol: {ESTATE_SYMBOL}\n uri: {ESTATE_BASE_URI_TEMPLATE.format(environment=environment)}\n land: {land_address}\n opensea: {opensea_proxy_registry_address}"
    )
    estate_encoded_initializer_function = encode_function_data(
        estate.initialize,
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_URI_TEMPLATE.format(environment=environment),
        land_address,
        opensea_proxy_registry_address,
    )
    proxy = TransparentUpgradeableProxy.deploy(
        estate.address,
        proxy_admin_address,
        estate_encoded_initializer_function,
        {"from": account, "gas_limit": 2000000},
    )
    return proxy


def grant_roles(
    land_address: str, estate_address: str, account: Optional[Account] = None
):
    if not account:
        account = get_account()
    land_proxy_with_abi = Contract.from_abi(
        "HighriseLand", land_address, HighriseLand.abi
    )
    land_proxy_with_abi.grantRole(
        land_proxy_with_abi.ESTATE_MANAGER_ROLE(),
        estate_address,
        {"from": account},
    ).wait(1)


def verify_estate(estate_address: str):
    contract = HighriseEstate.at(estate_address)
    HighriseEstate.publish_source(contract)


def verify_estate_proxy(proxy_address: str):
    contract = TransparentUpgradeableProxy.at(proxy_address)
    TransparentUpgradeableProxy.publish_source(contract)


def deploy_estate(
    proxy_admin_address: str,
    land_address: str,
    opensea_proxy_registry_address: str,
    environment: str = "dev",
    account: Optional[Account] = None,
) -> tuple[Contract, Contract]:
    if not account:
        account = get_account()
    estate = deploy_estate_implementation(account)
    # Deploy estate proxy
    estate_proxy = deploy_proxy(
        estate.address,
        land_address,
        proxy_admin_address,
        opensea_proxy_registry_address,
        environment,
        account,
    )
    # Grant roles
    grant_roles(land_address, estate_proxy.address, account)
    return estate_proxy, estate
