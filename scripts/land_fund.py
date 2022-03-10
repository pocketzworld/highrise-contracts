from brownie import Contract, HighriseLand, HighriseLandFund, accounts, config, network

from .common import FORKED_LOCAL_ENVIRONMENTS, LOCAL_BLOCKCHAIN_ENVIRONMENTS


def deploy_land_fund(land_address: str):
    """Land fund must be deployed after `deploy_with_proxy` script is executed"""
    account = accounts.load("one")
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


def disable(fund_address: str):
    account = accounts.load("one")
    land_fund = Contract.from_abi(
        "HighriseLandFund", fund_address, HighriseLandFund.abi
    )
    land_fund.disable({"from": account}).wait(1)


def withdraw(fund_address: str):
    account = accounts.load("one")
    land_fund = Contract.from_abi(
        "HighriseLandFund", fund_address, HighriseLandFund.abi
    )
    land_fund.withdraw({"from": account}).wait(1)


def enable_fund(land_fund_address: str):
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        print("Error: Script can only be run on real network")
        return

    land_fund = Contract.from_abi(
        "HighriseLand", land_fund_address, HighriseLandFund.abi
    )
    account = accounts.load("one")
    land_fund.enable({"from": account}).wait(1)
