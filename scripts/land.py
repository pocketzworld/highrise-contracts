from brownie import Contract, HighriseLand, TransparentUpgradeableProxy, config, network

from . import LAND_BASE_URI_TEMPLATE, LAND_NAME, LAND_SYMBOL
from .common import encode_function_data, get_account


def initialize(land_address: str, environment: str = "dev"):
    account = get_account()
    land = Contract.from_abi("HighriseLand", land_address, HighriseLand.abi)
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
        {"from": account},
    ).wait(1)


def deploy_proxy(land_impl_address: str, proxy_admin_address: str, environment="dev"):
    account = get_account()
    land = Contract.from_abi("HighriseLand", land_impl_address, HighriseLand.abi)
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_URI_TEMPLATE.format(environment=environment),
    )
    TransparentUpgradeableProxy.deploy(
        land_impl_address,
        proxy_admin_address,
        land_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )


def verify_proxy(proxy_address: str):
    contract = TransparentUpgradeableProxy.at(proxy_address)
    TransparentUpgradeableProxy.publish_source(contract)
