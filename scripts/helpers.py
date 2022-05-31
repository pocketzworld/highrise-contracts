from typing import Any, NewType, Optional

from brownie import Contract, MockProxyRegistry, config, network
from eth_account import Account

from .common import get_account, load_openzeppelin




def deploy_proxy_admin(
    account: Optional[Account] = None, oz: Optional[Project] = None
) -> Contract:
    if not account:
        account = get_account()
    if not oz:
        oz = load_openzeppelin()
    proxy_admin = oz.ProxyAdmin.deploy({"from": account})
    return proxy_admin


def opensea_proxy_registry_address(account: Optional[Account] = None) -> str:
    if address := config["networks"][network.show_active()].get("openseaProxyRegistry"):
        print(f"Opensea proxy registry at: {address}")
        return address
    else:
        if not account:
            account = get_account()
        mock_contract = MockProxyRegistry.deploy({"from": account})
        print(f"Opensea proxy registry deployed at: {mock_contract.address}")
        return mock_contract.address
