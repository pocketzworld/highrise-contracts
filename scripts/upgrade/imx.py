from optparse import Option
from time import sleep
from brownie import Contract
from typing import Optional
from scripts.common import get_account, upgrade

from brownie import (
    Contract,
    ProxyAdmin,
    HighriseLandImx,
    TransparentUpgradeableProxy,
    config,
    network,
)
from eth_account import Account


def deploy_land_imx(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    imx_land = HighriseLandImx.deploy({"from": account})
    return imx_land


def verify_land_imx(imx_land_address: str):
    contract = HighriseLandImx.at(imx_land_address)
    HighriseLandImx.publish_source(contract)


def upgrade_implementation(
    proxy_admin_address: str,
    land_proxy_address: str,
    imx_land_address: str,
    account: Optional[Account] = None,
):
    imx_core_address = config["networks"][network.show_active()].get("imxCore")
    if not imx_core_address:
        print(
            f"IMX not supported on network: {config['networks'][network.show_active()]}"
        )
        imx_core_address = "0xdEbC221d934D26F9CB96D2F7FfA0Abd12A997948"  # Mock address for other networks
    print(f"Using IMX address: {imx_core_address}")
    if not account:
        account = get_account()
    # Fetch proxy admin and land_proxy
    proxy_admin = Contract.from_abi("ProxyAdmin", proxy_admin_address, ProxyAdmin.abi)
    land_proxy = Contract.from_abi(
        "TransparentUpgradeableProxy",
        land_proxy_address,
        TransparentUpgradeableProxy.abi,
    )
    imx_land = Contract.from_abi(
        "HighriseLandImx", imx_land_address, HighriseLandImx.abi
    )
    # Do the upgrade
    upgrade_transaction = upgrade(
        account,
        land_proxy,
        imx_land.address,
        proxy_admin,
        imx_land.initIMX,  # This is not real initializer but we still need to init imx address
        imx_core_address,
    )
    upgrade_transaction.wait(1)


def upgrade_imx(proxy_admin_address: str, land_proxy_address: str):
    imx_core_address = config["networks"][network.show_active()].get("imxCore")
    if not imx_core_address:
        print(
            f"IMX not supported on network: {config['networks'][network.show_active()]}"
        )
        imx_core_address = "0xdEbC221d934D26F9CB96D2F7FfA0Abd12A997948"  # Mock address for other networks
    print(f"Using IMX address: {imx_core_address}")
    account = get_account()
    # Deploy land imx contract, contract is initialized with constructor
    imx_land = deploy_land_imx(account)
    # When deploying to real network there seems to be a lag with infura connection before contract is available
    sleep(2)
    # Upgrade implementation
    upgrade_implementation(
        proxy_admin_address, land_proxy_address, imx_land.address, account
    )

    # Publish and verify implementation contract
    if config["networks"][network.show_active()].get("verify"):
        verify_land_imx(imx_land.address)
