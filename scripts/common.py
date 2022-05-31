import os
from typing import Any, NewType, Optional

import eth_utils
from brownie import accounts, config, network, project
from brownie.network.contract import Contract, ContractTx
from eth_account import Account
from web3 import Web3

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


DEV_PRICE = 0.01  # in ETH
PRODUCTION_PRICE = 0.02  # in ETH
Project = NewType("Project", Any)


def get_wei_land_price() -> int:
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return Web3.toWei(DEV_PRICE, "ether")
    else:
        return Web3.toWei(PRODUCTION_PRICE, "ether")


def load_openzeppelin() -> Project:
    oz = project.load(config["dependencies"][0])
    return oz


def get_account() -> Account:
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    else:
        return accounts.load(os.getenv("DEV_ACCOUNT_NAME"))


def encode_function_data(initializer: Optional[ContractTx] = None, *args) -> bytes:
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer - The initializer function we want to call
        args - Arguments to pass to the initalizer function
    Returns:
        Encoded bytes
    """
    if not args or not initializer:
        return eth_utils.to_bytes(hexstr="0x")
    return initializer.encode_input(*args)


def upgrade(
    account: Account,
    proxy: Contract,
    new_implementation_address: str,
    proxy_admin_contract: Optional[Contract] = None,
    initializer=None,
    *args
):
    transaction = None
    if proxy_admin_contract:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy_admin_contract.upgradeAndCall(
                proxy.address,
                new_implementation_address,
                encoded_function_call,
                {"from": account, "gas_limit": 2000000},
            )
        else:
            transaction = proxy_admin_contract.upgrade(
                proxy.address,
                new_implementation_address,
                {"from": account, "gas_limit": 2000000},
            )
    else:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy.upgradeToAndCall(
                new_implementation_address,
                encoded_function_call,
                {"from": account, "gas_limit": 2000000},
            )
        else:
            transaction = proxy.upgradeTo(
                new_implementation_address, {"from": account, "gas_limit": 2000000}
            )
    return transaction
