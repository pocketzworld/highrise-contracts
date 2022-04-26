from typing import Optional

from brownie import Contract, HighriseLandV2
from eth_account import Account

from .common import get_account, upgrade
from .helpers import Project, load_openzeppelin


def deploy_land_v2_implementation(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    land = HighriseLandV2.deploy(
        {"from": account},
    )
    return land


def verify_land_v2(land_v2_address: str):
    contract = HighriseLandV2.at(land_v2_address)
    HighriseLandV2.publish_source(contract)


def upgrade_proxy(
    land_v2_impl_address: str,
    land_proxy_address: str,
    proxy_admin_address: str,
    account: Optional[Account] = None,
    oz: Optional[Project] = None,
):
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
    proxy = oz.TransparentUpgradeableProxy.at(land_proxy_address)
    proxy_admin = oz.ProxyAdmin.at(proxy_admin_address)
    upgrade_transaction = upgrade(
        account, proxy, land_v2_impl_address, proxy_admin_contract=proxy_admin
    )
    upgrade_transaction.wait(1)
