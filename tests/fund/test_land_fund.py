from time import time

import pytest
from brownie import HighriseLandFund, HighriseLand, config, exceptions, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import Contract, ProjectContract
from eth_abi import encode_abi
from eth_account._utils.signing import sign_message_hash
from eth_hash.auto import keccak
from eth_keys import keys

from scripts.common import get_wei_land_price

TEST_RESERVATION_ID = "61ea698cb0bff4c1bd44da98-1-61ea69adb0bff4c1bd44da99"


def generate_fund_request(token_id: int, expiry: int, key: str) -> tuple[bytes, bytes]:
    payload = encode_abi(["uint256", "uint256"], [token_id, expiry])
    hash = keccak(payload)
    _, _, _, signature = sign_message_hash(
        keys.PrivateKey(bytes.fromhex(key[2:])), hash
    )
    return payload, signature


@pytest.fixture
def initialized_land_fund(
    admin: LocalAccount,
    proxy_deployment: tuple[
        ProjectContract,
        ProjectContract,
        ProjectContract,
        ProjectContract,
        ProjectContract,
    ],
) -> tuple[ProjectContract, ProjectContract]:
    _, proxy, _, _, _ = proxy_deployment
    wei_token_price = get_wei_land_price()
    land_fund = HighriseLandFund.deploy(
        wei_token_price,
        proxy.address,
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land_fund, proxy


@pytest.fixture
def fund_contract_with_mint_role(admin, initialized_land_fund) -> ProjectContract:
    land_fund_contract, proxy = initialized_land_fund
    land_proxy = Contract.from_abi("HighriseLand", proxy.address, HighriseLand.abi)
    minter_role = land_proxy.MINTER_ROLE.call()
    land_proxy.grantRole(minter_role, land_fund_contract.address, {"from": admin})
    return land_fund_contract


@pytest.fixture
def enabled_land_funding_contract(admin, fund_contract_with_mint_role):
    tx = fund_contract_with_mint_role.enable({"from": admin})
    tx.wait(1)
    return fund_contract_with_mint_role


def test_can_fund(
    admin: LocalAccount, enabled_land_funding_contract: ProjectContract, alice: Account
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
    assert len(tx.events) == 2
    assert tx.events[-1]["sender"] == alice
    assert tx.events[-1]["fundAmount"] == price


def test_modifier_enabled(
    admin: LocalAccount, alice: Account, fund_contract_with_mint_role: ProjectContract
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(1, int(time() + 10), admin.private_key)
    # No-one can fund while the contract is disabled.
    with pytest.raises(exceptions.VirtualMachineError):
        fund_contract_with_mint_role.fund(
            payload,
            sig,
            {"from": alice, "value": price},
        )


def test_modifier_valid_amount(
    admin: LocalAccount, enabled_land_funding_contract: ProjectContract, alice: Account
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(1, 0, admin.private_key)
    # No-one can underpay
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            payload,
            sig,
            {"from": alice, "value": price - 1},
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
    admin: LocalAccount, enabled_land_funding_contract: ProjectContract, alice: Account
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(10, int(time() + 10), admin.private_key)
    # Fund the contract
    enabled_land_funding_contract.fund(
        payload,
        sig,
        {"from": alice, "value": price},
    ).wait(1)
    # Disable the contract
    enabled_land_funding_contract.disable({"from": admin}).wait(1)
    balance_before = admin.balance()
    funds_total = enabled_land_funding_contract.balance()
    # Withdraw funds
    enabled_land_funding_contract.withdraw({"from": admin}).wait(1)
    assert admin.balance() == balance_before + funds_total


def test_modifier_disabled(admin, enabled_land_funding_contract):
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.withdraw({"from": admin})
