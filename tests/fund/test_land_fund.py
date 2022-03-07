from time import time

import pytest
from brownie import (
    HighriseLand,
    HighriseLandFund,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    exceptions,
    network,
)
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import Contract, ProjectContract
from eth_abi import encode_abi
from eth_account._utils.signing import sign_message_hash
from eth_hash.auto import keccak
from eth_keys import keys

from scripts.common import encode_function_data, get_wei_land_price


def generate_fund_request(
    token_id: int, expiry: int, cost: int, key: str
) -> tuple[bytes, bytes]:
    payload = encode_abi(["uint256", "uint256", "uint256"], [token_id, expiry, cost])
    hash = keccak(payload)
    _, _, _, signature = sign_message_hash(
        keys.PrivateKey(bytes.fromhex(key[2:])), hash
    )
    return payload, signature


@pytest.fixture
def initialized_land_fund(
    admin: LocalAccount, land_contract
) -> tuple[ProjectContract, ProjectContract]:
    land_fund = HighriseLandFund.deploy(
        land_contract.address,
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return land_fund


@pytest.fixture
def fund_contract_with_mint_role(admin, initialized_land_fund, land_contract) -> ProjectContract:
    land_contract.grantRole(
        land_contract.MINTER_ROLE(), initialized_land_fund.address, {"from": admin}
    )
    return initialized_land_fund


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
    payload, sig = generate_fund_request(token_id, expiry, price, admin.private_key)
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
    payload, sig = generate_fund_request(1, int(time() + 10), price, admin.private_key)
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
    payload, sig = generate_fund_request(1, 0, price, admin.private_key)
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
    payload, sig = generate_fund_request(1, int(time() - 1), price, admin.private_key)
    # Alice may not use an expired reservation.
    with pytest.raises(exceptions.VirtualMachineError):
        enabled_land_funding_contract.fund(
            payload, sig, {"from": alice, "value": price - 1}
        )


def test_withdraw(
    admin: LocalAccount, enabled_land_funding_contract: ProjectContract, alice: Account
):
    price = get_wei_land_price()
    payload, sig = generate_fund_request(10, int(time() + 10), price, admin.private_key)
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
