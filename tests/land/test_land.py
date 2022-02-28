from random import randint

import pytest
from brownie import exceptions

from .. import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


def test_initialization(land_contract, admin):
    assert land_contract.name() == LAND_NAME
    assert land_contract.symbol() == LAND_SYMBOL
    assert land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE.call(), admin)
    assert land_contract.hasRole(land_contract.MINTER_ROLE.call(), admin)
    royalty_info = land_contract.royaltyInfo(1, 100)
    assert royalty_info[0] == admin  # Royalty is owned to the owner
    assert royalty_info[1] == 3  # Percentage is set to 3


def test_mint(land_contract, admin, alice):
    token_id = 4324239
    tx = land_contract.mint(alice, token_id, {"from": admin})
    tx.wait(1)
    assert land_contract.ownerOf(token_id) == alice
    assert land_contract.tokenURI(token_id) == f"{LAND_BASE_TOKEN_URI}{token_id}"
    assert land_contract.totalSupply() == 1
    assert land_contract.ownerTokens(alice) == [token_id]
    assert len(tx.events) == 1
    assert tx.events[0]["to"] == alice
    assert tx.events[0]["tokenId"] == str(token_id)


def test_mint_without_role(land_contract, alice, charlie):
    token_id = 3213145
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.mint(charlie, token_id, {"from": alice})
    assert "revert: AccessControl" in str(excinfo.value)


def test_bind_to_estate(land_contract, admin, alice, charlie):
    token_ids = [randint(1, 100000) for _ in range(2)]
    # 1. Mint the tokens
    for token_id in token_ids:
        tx = land_contract.mint(alice, token_id, {"from": admin})
        tx.wait(1)

    # 2. Verify fail for account without estate manager role
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.bindToEstate(alice, token_ids, {"from": charlie})
    assert "revert: AccessControl" in str(excinfo.value)

    # 3. Succees with estate manager role
    tx = land_contract.bindToEstate(alice, token_ids, {"from": admin})
    tx.wait(1)
    assert set(land_contract.ownerTokens(admin)) == set(token_ids)
    assert land_contract.ownerTokens(alice) == []


def test_ownership_transfer(land_contract, admin, alice):
    land_contract.transferOwnership(alice.address, {"from": admin}).wait(1)
    assert land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE(), admin) is not True
    assert land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE(), alice)
    assert land_contract.owner() == alice
