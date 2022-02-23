from brownie import (
    HighriseEstateV3,
    HighriseLandV3,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)
from brownie.network.account import Account
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data, get_account


def deploy_with_proxy(
    account: Account,
) -> tuple[ProjectContract, ProjectContract, ProjectContract]:
    proxy_admin = ProxyAdmin.deploy({"from": account})

    print(f"Deploying to {network.show_active()}")
    # Land
    land = HighriseLandV3.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        "Highrise Land",
        "HRLAND",
        "https://highrise-land.s3.amazonaws.com/metadata",
    )
    land_proxy = TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
    )

    # Estate
    estate = HighriseEstateV3.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    estate_encoded_initializer_function = encode_function_data(
        estate.initialize,
        "Highrise Estate",
        "HRESTATE",
        "https://highrise-estate.s3.amazonaws.com/metadata",
        land_proxy.address,
    )
    estate_proxy = TransparentUpgradeableProxy.deploy(
        estate.address,
        proxy_admin.address,
        estate_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
    )

    return proxy_admin, land_proxy, land, estate_proxy, estate


def main():
    account = get_account()
    deploy_with_proxy(account)
