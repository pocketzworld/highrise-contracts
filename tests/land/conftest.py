import pytest
from brownie import HighriseEstate, HighriseLand, config, network
from brownie.network.account import LocalAccount
from brownie.network.contract import ProjectContract

from .. import (
    ESTATE_BASE_TOKEN_URI,
    ESTATE_NAME,
    ESTATE_SYMBOL,
    LAND_BASE_TOKEN_URI,
    LAND_NAME,
    LAND_SYMBOL,
)


@pytest.fixture
def land_contract(admin: LocalAccount) -> ProjectContract:
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land.initialize(
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        {"from": admin},
    )
    return land


@pytest.fixture
def estate_contract(land_contract: ProjectContract, admin: LocalAccount):
    estates = HighriseEstate.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    estates.initialize(
        ESTATE_NAME, ESTATE_SYMBOL, ESTATE_BASE_TOKEN_URI, land_contract.address
    )
    land_contract.grantRole(land_contract.ESTATE_MANAGER_ROLE(), estates)
    return estates
