from brownie import (
    Contract,
    HighriseLand,
    HighriseLandWithdrawal,
    accounts,
    config,
    network,
)

from .common import FORKED_LOCAL_ENVIRONMENTS, LOCAL_BLOCKCHAIN_ENVIRONMENTS

ACCOUNT_NAME = "one"
ADMIN_ACCOUNT = "dev-account"


def deploy_land_withdrawal(land_address: str):
    """Land withdrawal must be deployed after land contract is deployed"""
    account = accounts.load(ACCOUNT_NAME)
    withdrawal_contract = HighriseLandWithdrawal.deploy(
        land_address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )


def grant_roles(withdrawal_contract_address: str, land_address: str):
    account = accounts.load(ADMIN_ACCOUNT)
    # Grant roles
    land_proxy = Contract.from_abi("HighriseLand", land_address, HighriseLand.abi)
    land_proxy.grantRole(
        land_proxy.MINTER_ROLE(),
        withdrawal_contract_address,
        {"from": account},
    ).wait(1)


def disable(withdrawal_contract_address: str):
    account = accounts.load(ACCOUNT_NAME)
    withdrawal_contract = Contract.from_abi(
        "HighriseLandWithdrawal",
        withdrawal_contract_address,
        HighriseLandWithdrawal.abi,
    )
    withdrawal_contract.disable({"from": account}).wait(1)


def enable(withdrawal_contract_address: str):
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        print("Error: Script can only be run on real network")
        return

    withdrawal_contract = Contract.from_abi(
        "HighriseLandWithdrawal",
        withdrawal_contract_address,
        HighriseLandWithdrawal.abi,
    )
    account = accounts.load(ACCOUNT_NAME)
    withdrawal_contract.enable({"from": account}).wait(1)
