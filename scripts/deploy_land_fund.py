from brownie import (
    Contract,
    HighriseLand,
    HighriseLandFund,
    TransparentUpgradeableProxy,
    config,
    network,
)
from eth_account import Account

from .common import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)
from .helpers import deploy_land, deploy_proxy_admin


def get_land_proxy(account: Account) -> Contract:
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):

        # Since it is local network we need to deploy the land contract first
        proxy_admin = deploy_proxy_admin(account)
        proxy, _ = deploy_land(account, proxy_admin)
    else:
        proxy = TransparentUpgradeableProxy[-2]

    land_proxy = Contract.from_abi("HighriseLand", proxy.address, HighriseLand.abi)
    return land_proxy


def deploy_land_fund(land_address: str):
    """Land fund must be deployed after `deploy_with_proxy` script is executed"""
    account = get_account()
    land_fund = HighriseLandFund.deploy(
        land_address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    # Grant roles
    land_proxy = Contract.from_abi("HighriseLand", land_address, HighriseLand.abi)
    land_proxy.grantRole(
        land_proxy.MINTER_ROLE(),
        land_fund.address,
        {"from": account},
    ).wait(1)


def main():
    deploy_land_fund()
