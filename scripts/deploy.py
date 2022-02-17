from brownie import HighriseLand, HighriseLandFund, config, network

from .common import get_account, get_wei_land_price


def deploy_highrise_land_fund():
    account = get_account()
    wei_token_price = get_wei_land_price()
    land = HighriseLand.deploy(
        "Land",
        "LND",
        "0x4527be8f31e2ebfbef4fcaddb5a17447b27d2aef",
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    print(f"Land contract deployed to {land.address}")
    land_fund = HighriseLandFund.deploy(
        wei_token_price,
        land.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    print(f"Contract deployed to {land_fund.address}")
    return land, land_fund


def main():
    deploy_highrise_land_fund()
