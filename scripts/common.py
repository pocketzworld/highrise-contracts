import os

from brownie import accounts, network
from web3 import Web3

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


DEV_PRICE = 0.01  # in ETH
PRODUCTION_PRICE = 0.02  # in ETH


def get_wei_land_price():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return Web3.toWei(DEV_PRICE, "ether")
    else:
        return Web3.toWei(PRODUCTION_PRICE, "ether")


def get_account():
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    else:
        return accounts.load(os.getenv("DEV_ACCOUNT_NAME"))
