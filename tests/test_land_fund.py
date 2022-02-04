import pytest
from brownie import exceptions, accounts

from scripts.common import get_account, get_wei_land_price
from scripts.deploy import deploy_highrise_land_fund


TEST_RESERVATION_ID = "61ea698cb0bff4c1bd44da98-1-61ea69adb0bff4c1bd44da99"


def deploy_and_enable(account):
    land_fund = deploy_highrise_land_fund()
    tx = land_fund.enable({"from": account})
    tx.wait(1)
    return land_fund


def test_can_fund():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    tx = land_fund.fund(TEST_RESERVATION_ID, {"from": account, "value": price})
    tx.wait(1)
    # Check stored fund amount
    assert land_fund.addressToAmountFunded(account.address) == price
    # Check log events
    assert len(tx.events) == 1
    assert tx.events[0]["sender"] == account
    assert tx.events[0]["fundAmount"] == price
    assert tx.events[0]["reservationId"] == TEST_RESERVATION_ID


def test_modifier_enabled():
    account = get_account()
    land_fund = deploy_highrise_land_fund()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund(TEST_RESERVATION_ID, {"from": account, "value": price})


def test_modifier_valid_amount():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund(
            TEST_RESERVATION_ID, {"from": account, "value": price - 1}
        )


def test_withdraw():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    # Fund the contract
    tx = land_fund.fund(TEST_RESERVATION_ID, {"from": account, "value": price})
    tx.wait(1)
    # Disable the contract
    tx = land_fund.disable({"from": account})
    tx.wait(1)
    balance_before = account.balance()
    funds_total = land_fund.balance()
    # Withdraw funds
    tx = land_fund.withdraw({"from": account})
    tx.wait(1)
    assert account.balance() == balance_before + funds_total


def test_modifier_disabled():
    account = get_account()
    land_fund = deploy_and_enable(account)
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.withdraw({"from": account})
