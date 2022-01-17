from brownie import HighriseLandFund, config, network

from .common import get_account, get_wei_land_price


def deploy_highrise_land_fund():
    account = get_account()
    wei_token_price = get_wei_land_price()
    land_fund = HighriseLandFund.deploy(
        wei_token_price,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    print(f"Contract deployed to {land_fund.address}")
    return land_fund


def main():
    deploy_highrise_land_fund()
