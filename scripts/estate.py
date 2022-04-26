from time import sleep
from typing import Optional

from brownie import Contract, HighriseEstate, HighriseLand
from eth_account import Account

from . import ESTATE_BASE_URI_TEMPLATE, ESTATE_NAME, ESTATE_SYMBOL
from .common import encode_function_data, get_account
from .helpers import Project, load_openzeppelin


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
    oz: Optional[Project] = None,
) -> Contract:
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
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
    proxy = oz.TransparentUpgradeableProxy.deploy(
        estate.address,
        proxy_admin_address,
        estate_encoded_initializer_function,
        {"from": account, "gas_limit": 2000000},
    )
    return proxy


def verify_estate(estate_address: str):
    contract = HighriseEstate.at(estate_address)
    HighriseEstate.publish_source(contract)


def verify_estate_proxy(proxy_address: str, oz: Optional[Project] = None):
    if not oz:
        oz = load_openzeppelin()
    contract = oz.TransparentUpgradeableProxy.at(proxy_address)
    oz.TransparentUpgradeableProxy.publish_source(contract)


def deploy_estate(
    proxy_admin_address: str,
    land_address: str,
    opensea_proxy_registry_address: str,
    environment: str = "dev",
    account: Optional[Account] = None,
    oz: Optional[Project] = None,
) -> tuple[Contract, Contract]:
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
    estate = deploy_estate_implementation(account)
    sleep(2)
    # Deploy estate proxy
    estate_proxy = deploy_proxy(
        estate.address,
        land_address,
        proxy_admin_address,
        opensea_proxy_registry_address,
        environment,
        account,
        oz,
    )
    return estate_proxy, estate
