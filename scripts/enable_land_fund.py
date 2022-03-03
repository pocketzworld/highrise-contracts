from cgitb import enable
from brownie import network, HighriseLandFund

from .common import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)


def enable_fund():
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        print("Error: Script can only be run on real network")
        return

    land_fund = HighriseLandFund[-1]
    account = get_account()
    land_fund.enable({"from": account}).wait(1)


def main():
    enable_fund()
