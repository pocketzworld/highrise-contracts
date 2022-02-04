from brownie import HighriseLandFund, network

from .common import get_account


def enable_fund():
    if network.show_active() != "ropsten":
        print(f"Cannot enable fund on {network.show_active()}")
        return
    account = get_account()
    land_fund = HighriseLandFund[-1]
    land_fund.enable({"from": account})


def main():
    enable_fund()
