import pytest
from brownie import exceptions, accounts

from scripts.common import get_account, get_wei_land_price
from scripts.deploy import deploy_highrise_land_fund


def deploy_and_enable(account):
    land_fund = deploy_highrise_land_fund()
    tx = land_fund.enable({"from": account})
    tx.wait(1)
    tx = land_fund.addUser(account.address, {"from": account})
    tx.wait(1)
    return land_fund


def test_can_fund():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    tx = land_fund.fund([1, 2, 3, 4], {"from": account, "value": price * 4})
    tx.wait(1)
    assert land_fund.addressToAmountFunded(account.address) == price * 4
    assert land_fund.getWalletTokens(account.address) == [1, 2, 3, 4]


def test_modifier_enabled():
    account = get_account()
    land_fund = deploy_highrise_land_fund()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1, 2, 3], {"from": account, "value": price * 3})


def test_modifier_valid_tokens_length():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        # No parameters
        land_fund.fund([], {"from": account, "value": price})
    with pytest.raises(exceptions.VirtualMachineError):
        # More then max parameters
        land_fund.fund([1, 2, 3, 4, 5], {"from": account, "value": price * 5})


def test_modifier_valid_tokens_unique():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1, 1], {"from": account, "value": price * 2})


def test_modifier_limit_not_reached():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    tx = land_fund.fund([1, 2, 3, 4], {"from": account, "value": price * 4})
    tx.wait(1)
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([5], {"from": account, "value": price})


def test_modifier_valid_amount():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1], {"from": account, "value": price - 1})
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1, 2], {"from": account, "value": 2 * price - 1})
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1, 2, 3], {"from": account, "value": 2 * price - 1})
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1, 2, 3, 4], {"from": account, "value": 2 * price - 1})


def test_withdraw():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    # Fund the contract
    tx = land_fund.fund([1, 2, 3, 4], {"from": account, "value": price * 4})
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


def test_whitelist():
    account = get_account()
    land_fund = deploy_and_enable(account)
    assert land_fund.verifyUser(account.address)


def test_modifier_only_whitelisted():
    account = get_account()
    land_fund = deploy_and_enable(account)
    price = get_wei_land_price()
    not_whitelisted_account = accounts[1]
    with pytest.raises(exceptions.VirtualMachineError):
        land_fund.fund([1], {"from": not_whitelisted_account, "value": price})
