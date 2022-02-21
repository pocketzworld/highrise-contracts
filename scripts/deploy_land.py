from brownie import (
    Contract,
    HighriseLandV2,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)

from scripts.common import encode_function_data, get_account


def main():
    account = get_account()
    print(f"Deploying to {network.show_active()}")
    land = HighriseLandV2.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    encoded_initializer_function = encode_function_data(
        land.initialize,
        "Highrise Land",
        "HRLAND",
        "https://highrise-land.s3.amazonaws.com/metadata",
    )
    proxy_admin = ProxyAdmin.deploy({"from": account})
    proxy = TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
    )

    print(f"Proxy deployed to {proxy}")
    proxy_land = Contract.from_abi("HighriseLandV2", proxy.address, HighriseLandV2.abi)
    print(proxy_land.abi)
