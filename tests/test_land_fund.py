import pytest
from brownie import HighriseLandFund, config, exceptions, network

from scripts.common import get_account, get_wei_land_price

TEST_RESERVATION_ID = "61ea698cb0bff4c1bd44da98-1-61ea69adb0bff4c1bd44da99"


@pytest.fixture
def land_funding_contract(land_contract):
    account = get_account()
    wei_token_price = get_wei_land_price()
    land_fund = HighriseLandFund.deploy(
        wei_token_price,
        land_contract.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land_fund


@pytest.fixture
def enabled_land_funding_contract(land_funding_contract):
    account = get_account()
    tx = land_funding_contract.enable({"from": account})
    tx.wait(1)
    return land_funding_contract


def test_can_fund(enabled_land_funding_contract, land_contract):
    account = get_account()
    price = get_wei_land_price()
    tx = enabled_land_funding_contract.fund(
        TEST_RESERVATION_ID, {"from": account, "value": price}
    )
    tx.wait(1)
    # Check stored fund amount
    assert enabled_land_funding_contract.addressToAmountFunded(account.address) == price
    # Check log events
    assert len(tx.events) == 3
    assert tx.events[1]["to"] == account
    assert tx.events[1]["id"] == "1"
    assert tx.events[2]["sender"] == account
    assert tx.events[2]["fundAmount"] == price
    assert tx.events[2]["reservationId"] == TEST_RESERVATION_ID

    assert land_contract.balanceOf(account) == 1
    assert land_contract.tokensOfOwner(account) == (1,)


def test_modifier_enabled(land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_funding_contract.fund(
            TEST_RESERVATION_ID, {"from": account, "value": price}
        )


def test_modifier_valid_amount(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            TEST_RESERVATION_ID, {"from": account, "value": price - 1}
        )


def test_withdraw(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    # Fund the contract
    tx = enabled_land_funding_contract.fund(
        TEST_RESERVATION_ID, {"from": account, "value": price}
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
