from typing import Optional

from brownie import Contract, ProxyAdmin
from eth_account import Account

from .common import get_account


def deploy_proxy_admin(account: Optional[Account] = None) -> Contract:
    if not account:
        account = get_account()
    proxy_admin = ProxyAdmin.deploy({"from": account})
    return proxy_admin
