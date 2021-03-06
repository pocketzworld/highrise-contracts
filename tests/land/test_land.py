from random import randint

import pytest
from brownie import exceptions
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from brownie.network import accounts

from .. import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


def test_initialization(land_contract: ProjectContract, admin: LocalAccount):
    assert land_contract.name() == LAND_NAME
    assert land_contract.symbol() == LAND_SYMBOL
    assert land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE.call(), admin)
    assert land_contract.hasRole(land_contract.MINTER_ROLE.call(), admin)
    royalty_info = land_contract.royaltyInfo(1, 100)
    assert royalty_info[0] == admin  # Royalty is owned to the owner
    assert royalty_info[1] == 5  # Percentage is set to 5


def test_mint(land_contract: ProjectContract, admin: LocalAccount, alice: LocalAccount):
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


def test_mint_without_role(
    land_contract: ProjectContract, alice: LocalAccount, charlie: LocalAccount
):
    token_id = 3213145
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.mint(charlie, token_id, {"from": alice})
    assert "revert: AccessControl" in str(excinfo.value)


def test_transfer_after_approval(
    land_contract: ProjectContract,
    admin: LocalAccount,
    alice: LocalAccount,
    bob: LocalAccount,
    charlie: LocalAccount,
):
    token_id = 323323
    # 1. Mint the token
    land_contract.mint(alice, token_id, {"from": admin}).wait(1)
    # 2. Approve Charlie for transfering token
    land_contract.approve(charlie, token_id, {"from": alice}).wait(1)
    # 3. Alice can transfer the token after approval
    land_contract.safeTransferFrom(alice, bob, token_id, {"from": alice}).wait(1)
    # 4. Charlie is no longer approved after transfer
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.safeTransferFrom(bob, charlie, token_id, {"from": charlie}).wait(
            1
        )
    assert "revert: ERC721: transfer caller is not owner nor approved" in str(
        excinfo.value
    )
    # 5. Bob approves charlie again
    land_contract.approve(charlie, token_id, {"from": bob}).wait(1)
    # 6. Charlie trnasfers the token
    land_contract.safeTransferFrom(bob, charlie, token_id, {"from": charlie}).wait(1)
    assert land_contract.ownerOf(token_id) == charlie


def test_change_uri(
    land_contract: ProjectContract, admin: LocalAccount, alice: LocalAccount
):
    # First mint token so that we can fetch tokenURI
    token_id = 4324239
    land_contract.mint(alice, token_id, {"from": admin}).wait(1)
    assert land_contract.tokenURI(token_id) == f"{LAND_BASE_TOKEN_URI}{token_id}"

    # Validate uri changed
    NEW_URI = "changed/"
    land_contract.setBaseTokenURI(NEW_URI, {"from": admin}).wait(1)
    assert land_contract.tokenURI(token_id) == f"{NEW_URI}{token_id}"

    # Validate uri can be changed only by admin
    FAIL_URI = "failed/"
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.setBaseTokenURI(FAIL_URI, {"from": alice}).wait(1)
    assert "revert: AccessControl" in str(excinfo.value)


def test_opensea_proxy(
    land_contract: ProjectContract,
    opensea_proxy_registry: ProjectContract,
    admin: LocalAccount,
    alice: LocalAccount,
    charlie: LocalAccount,
):
    # Set opensea proxy account for alice
    alice_opensea_proxy = accounts.add()
    opensea_proxy_registry.setProxy(
        alice.address, alice_opensea_proxy.address, {"from": admin}
    )
    # Mint to alice
    token_id = 4324239
    land_contract.mint(alice, token_id, {"from": admin}).wait(1)
    # Transfer triggered
    land_contract.safeTransferFrom(
        alice, charlie, token_id, {"from": alice_opensea_proxy}
    ).wait(1)
    assert land_contract.ownerTokens(alice) == []
    assert land_contract.ownerTokens(charlie) == [token_id]


def test_ownership(
    land_contract: ProjectContract, admin: LocalAccount, alice: LocalAccount
):
    assert land_contract.owner() == admin
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.grantRole(land_contract.OWNER_ROLE(), alice, {"from": admin})
    assert "revert: There can be only one owner" in str(excinfo.value)

    land_contract.revokeRole(land_contract.OWNER_ROLE(), admin, {"from": admin})
    land_contract.grantRole(land_contract.OWNER_ROLE(), alice, {"from": admin})
    assert land_contract.owner() == alice


def test_royalty_change(
    land_contract: ProjectContract, admin: LocalAccount, alice: LocalAccount
):
    land_contract.setDefaultRoyalty(alice, 300, {"from": admin}).wait(1)
    royalty_info = land_contract.royaltyInfo(1, 100)
    assert royalty_info[0] == alice  # Royalty is owned to the owner
    assert royalty_info[1] == 3  # Percentage is set to 5
