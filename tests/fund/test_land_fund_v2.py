import pytest
from brownie import HighriseLandFundV2, config, exceptions, network, HighriseLandV2
from brownie.network.contract import ProjectContract, Contract

from scripts.common import get_account, get_wei_land_price

TEST_RESERVATION_ID = "61ea698cb0bff4c1bd44da98-1-61ea69adb0bff4c1bd44da99"


@pytest.fixture
def initialized_land_fund(proxy_deployment) -> tuple[ProjectContract, ProjectContract]:
    _, proxy, _ = proxy_deployment
    account = get_account()
    wei_token_price = get_wei_land_price()
    land_fund = HighriseLandFundV2.deploy(
        wei_token_price,
        proxy.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land_fund, proxy


@pytest.fixture
def fund_contract_with_mint_role(initialized_land_fund) -> ProjectContract:
    land_fund_contract, proxy = initialized_land_fund
    account = get_account()
    land_proxy = Contract.from_abi("HighriseLandV2", proxy.address, HighriseLandV2.abi)
    minter_role = land_proxy.MINTER_ROLE.call()
    land_proxy.grantRole(minter_role, land_fund_contract.address, {"from": account})
    return land_fund_contract


@pytest.fixture
def enabled_land_funding_contract(fund_contract_with_mint_role):
    account = get_account()
    tx = fund_contract_with_mint_role.enable({"from": account})
    tx.wait(1)
    return fund_contract_with_mint_role


def test_can_fund(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    tx = enabled_land_funding_contract.fund(
        TEST_RESERVATION_ID,
        {"from": account, "value": price},
    )
    tx.wait(1)
    # Check stored fund amount
    assert enabled_land_funding_contract.addressToAmountFunded(account.address) == price
    # Check log events
    assert len(tx.events) == 2
    assert tx.events[0]["to"] == account
    assert tx.events[0]["tokenId"] == "1"
    assert tx.events[1]["sender"] == account
    assert tx.events[1]["fundAmount"] == price
    assert tx.events[1]["reservationId"] == TEST_RESERVATION_ID


def test_modifier_enabled(fund_contract_with_mint_role):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        fund_contract_with_mint_role.fund(
            TEST_RESERVATION_ID,
            {"from": account, "value": price},
        )


def test_modifier_valid_amount(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            TEST_RESERVATION_ID,
            {"from": account, "value": price - 1},
        )


def test_withdraw(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    # Fund the contract
    tx = enabled_land_funding_contract.fund(
        TEST_RESERVATION_ID,
        {"from": account, "value": price},
    )
    tx.wait(1)
    # Disable the contract
    tx = enabled_land_funding_contract.disable({"from": account})
    tx.wait(1)
    balance_before = account.balance()
    funds_total = enabled_land_funding_contract.balance()
    # Withdraw funds
    tx = enabled_land_funding_contract.withdraw({"from": account})
    tx.wait(1)
    assert account.balance() == balance_before + funds_total


def test_modifier_disabled(enabled_land_funding_contract):
    account = get_account()
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.withdraw({"from": account})
