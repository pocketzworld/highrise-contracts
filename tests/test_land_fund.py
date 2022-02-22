import pytest
from brownie import HighriseLandFund, config, exceptions, network
from brownie.network.account import LocalAccount
from eth_abi import encode_abi
from eth_hash.auto import keccak

from scripts.common import get_account, get_wei_land_price


@pytest.fixture
def land_funding_contract(land_contract, admin: LocalAccount, alice: str):
    wei_token_price = get_wei_land_price()
    land_fund = HighriseLandFund.deploy(
        wei_token_price,
        land_contract.address,
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land_contract.grantRole(land_contract.MINTER_ROLE(), land_fund)
    return land_fund


@pytest.fixture
def enabled_land_funding_contract(land_funding_contract, admin: str):
    tx = land_funding_contract.enable({"from": admin})
    tx.wait(1)
    return land_funding_contract


def test_can_fund(
    enabled_land_funding_contract, land_contract, admin: LocalAccount, alice: str
):
    price = get_wei_land_price()
    token_id = 15
    expiry = 0
    payload = encode_abi(["uint256", "uint256"], [token_id, expiry])
    print(f"The payload is {payload.hex()}")
    hash = keccak(payload)
    print(f"The hash of the payload is {hash.hex()}")
    signed_message = admin.sign_defunct_message(hash.hex())
    print(f"The signature is {signed_message.signature.hex()}")

    print(enabled_land_funding_contract.test(hash, signed_message.signature))

    # tx = enabled_land_funding_contract.fund(
    #     payload,
    #     signed_message.signature,
    #     {"from": alice, "value": price},
    # )
    # tx.wait(1)
    # # Check stored fund amount
    # assert enabled_land_funding_contract.addressToAmountFunded(alice) == price
    # # Check log events
    # assert tx.events[-1]["sender"] == alice
    # assert tx.events[-1]["fundAmount"] == price

    # assert land_contract.balanceOf(alice) == 1
    # assert land_contract.tokensOfOwner(alice) == (token_id,)


def test_modifier_enabled(land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        land_funding_contract.fund("", {"from": account, "value": price})


def test_modifier_valid_amount(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund("", {"from": account, "value": price - 1})


def test_withdraw(enabled_land_funding_contract):
    account = get_account()
    price = get_wei_land_price()
    # Fund the contract
    tx = enabled_land_funding_contract.fund("", {"from": account, "value": price})
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
