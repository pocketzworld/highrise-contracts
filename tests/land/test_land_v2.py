import pytest
from brownie import HighriseLandV2, config, exceptions, network
from brownie.network.contract import ProjectContract

from scripts.common import get_account

LAND_NAME = "Highrise Land"
LAND_SYMBOL = "HRLAND"
BASE_TOKEN_URI = "https://highrise-land.s3.amazonaws.com/metadata/"


@pytest.fixture
def land_contract(admin) -> ProjectContract:
    land = HighriseLandV2.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        BASE_TOKEN_URI,
        {"from": admin},
    )
    return land


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
    assert land_contract.tokenURI(token_id) == f"{BASE_TOKEN_URI}{token_id}"
    assert land_contract.totalSupply() == 1
    assert len(tx.events) == 1
    assert tx.events[0]["to"] == alice
    assert tx.events[0]["tokenId"] == str(token_id)


def test_mint_without_role(land_contract, alice, charlie):
    token_id = 3213145
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.mint(charlie, token_id, {"from": alice})
    assert "revert: AccessControl" in str(excinfo.value)
