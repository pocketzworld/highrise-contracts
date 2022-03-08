from brownie import Contract, HighriseEstate, HighriseLand, TransparentUpgradeableProxy

from . import ESTATE_BASE_URI_TEMPLATE, ESTATE_NAME, ESTATE_SYMBOL
from .common import encode_function_data, get_account


def deploy_estate(
    land_address: str,
    environment: str = "dev",
) -> tuple[Contract, Contract]:
    account = get_account()
    estate = HighriseEstate.deploy(
        {"from": account},
    )
    # Do not leave an implementation contract uninitialized. An uninitialized implementation contract can be taken over by an attacker,
    # which may impact the proxy. Manually invoking initializer on implementation contract
    estate.initialize(
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_URI_TEMPLATE.format(environment=environment),
        land_address,
        {"from": account, "gas_limit": 1000000},
    )


def initialize_state(estate_address: str, land_address: str, environment="dev"):
    account = get_account()
    estate = Contract.from_abi("HighriseEstate", estate_address, HighriseEstate.abi)
    estate.initialize(
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_URI_TEMPLATE.format(environment=environment),
        land_address,
        {"from": account, "gas_limit": 1000000},
    ).wait(1)


def deploy_proxy(
    estate_impl_address: str,
    land_address: str,
    proxy_admin_address: str,
    environment="dev",
):
    account = get_account()
    estate = Contract.from_abi(
        "HighriseEstate", estate_impl_address, HighriseEstate.abi
    )
    estate_encoded_initializer_function = encode_function_data(
        estate.initialize,
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_URI_TEMPLATE.format(environment=environment),
        land_address,
    )
    TransparentUpgradeableProxy.deploy(
        estate.address,
        proxy_admin_address,
        estate_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
    )


def grant_roles(land_address: str, estate_address: str):
    account = get_account()
    land_proxy_with_abi = Contract.from_abi(
        "HighriseLand", land_address, HighriseLand.abi
    )
    land_proxy_with_abi.grantRole(
        land_proxy_with_abi.ESTATE_MANAGER_ROLE(),
        estate_address,
        {"from": account},
    ).wait(1)
