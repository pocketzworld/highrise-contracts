from time import time

import pytest
from brownie import HighriseLandFund, config, exceptions, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract
from eth_abi import encode_abi
from eth_account._utils.signing import sign_message_hash
from eth_hash.auto import keccak
from eth_keys import keys

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


def generate_fund_request(token_id: int, expiry: int, key: str) -> tuple[bytes, bytes]:
    payload = encode_abi(["uint256", "uint256"], [token_id, expiry])
    hash = keccak(payload)
    _, _, _, signature = sign_message_hash(
        keys.PrivateKey(bytes.fromhex(key[2:])), hash
    )
    return payload, signature


def test_can_fund(
    enabled_land_funding_contract: ProjectContract,
    land_contract,
    admin: LocalAccount,
    alice: str,
):
    price = get_wei_land_price()
    token_id = 15
    expiry = int(time() + 10)
    payload, sig = generate_fund_request(token_id, expiry, admin.private_key)

    tx = enabled_land_funding_contract.fund(
        payload,
        sig,
        {"from": alice, "value": price},
    )
    tx.wait(1)
    # Check stored fund amount
    assert enabled_land_funding_contract.addressToAmountFunded(alice) == price
    # Check log events
    assert tx.events[-1]["sender"] == alice
    assert tx.events[-1]["fundAmount"] == price

    assert land_contract.balanceOf(alice) == 1
    assert land_contract.tokensOfOwner(alice) == (token_id,)


def test_modifier_enabled(
    land_funding_contract: ProjectContract, admin: LocalAccount, alice: str
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(1, int(time() + 10), admin.private_key)

    # Alice may not fund while the contract is disabled.
    with pytest.raises(exceptions.VirtualMachineError):
        land_funding_contract.fund(payload, sig, {"from": alice, "value": price})


def test_modifier_valid_amount(
    enabled_land_funding_contract: ProjectContract, alice: str, admin: LocalAccount
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(1, int(time() + 10), admin.private_key)
    # Alice may not underpay.
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            payload, sig, {"from": alice, "value": price - 1}
        )


def test_reservation_expired(
    enabled_land_funding_contract: ProjectContract, alice: str, admin: LocalAccount
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(1, int(time() - 1), admin.private_key)
    # Alice may not use an expired reservation.
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            payload, sig, {"from": alice, "value": price - 1}
        )


def test_withdraw(
    enabled_land_funding_contract: ProjectContract, alice: Account, admin: LocalAccount
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(10, int(time() + 10), admin.private_key)
    # Fund the contract
    enabled_land_funding_contract.fund(
        payload, sig, {"from": alice, "value": price}
    ).wait(1)
    # Disable the contract
    enabled_land_funding_contract.disable({"from": admin}).wait(1)

    balance_before = admin.balance()
    funds_total = enabled_land_funding_contract.balance()

    # Withdraw funds
    enabled_land_funding_contract.withdraw({"from": admin}).wait(1)
    assert admin.balance() == balance_before + funds_total


def test_modifier_disabled(enabled_land_funding_contract):
    account = get_account()
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.withdraw({"from": account})
