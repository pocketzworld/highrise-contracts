import pytest
from brownie import (
    Contract,
    HighriseEstate,
    HighriseLand,
    HighriseLandV2,
    config,
    network,
)
from brownie.network.account import LocalAccount
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data, upgrade
from scripts.helpers import Project

from .. import (
    ESTATE_BASE_TOKEN_URI,
    ESTATE_NAME,
    ESTATE_SYMBOL,
    LAND_BASE_TOKEN_URI,
    LAND_NAME,
    LAND_SYMBOL,
)


@pytest.fixture
def estate_contract_impl(admin: LocalAccount) -> ProjectContract:
    estates = HighriseEstate.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    return estates


@pytest.fixture
def estate_contract_proxy(
    admin: LocalAccount,
    estate_contract_impl: ProjectContract,
    land_contract: ProjectContract,
    opensea_proxy_registry: ProjectContract,
    oz: Project,
) -> tuple[ProjectContract, ProjectContract]:
    estate_encoded_initializer_function = encode_function_data(
        estate_contract_impl.initialize,
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_TOKEN_URI,
        land_contract.address,
        opensea_proxy_registry.address,
    )
    proxy_admin = oz.ProxyAdmin.deploy({"from": admin})
    proxy = oz.TransparentUpgradeableProxy.deploy(
        estate_contract_impl.address,
        proxy_admin.address,
        estate_encoded_initializer_function,
        {"from": admin, "gas_limit": 2000000},
    )
    return proxy, land_contract


@pytest.fixture
def estate_with_land(
    estate_contract_proxy: ProjectContract,
):
    estate_proxy, land = estate_contract_proxy
    return (
        Contract.from_abi("HighriseEstate", estate_proxy.address, HighriseEstate.abi),
        land,
    )


@pytest.fixture
def estate_with_land_upgrade(
    admin: LocalAccount,
    alice: LocalAccount,
    estate_contract_impl: ProjectContract,
    land_contract_impl: ProjectContract,
    opensea_proxy_registry: ProjectContract,
    oz: Project,
):
    # Deploy proxy admin
    proxy_admin = oz.ProxyAdmin.deploy({"from": admin})
    # Set land proxy
    land_encoded_initializer_function = encode_function_data(
        land_contract_impl.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        opensea_proxy_registry.address,
    )
    land_proxy = oz.TransparentUpgradeableProxy.deploy(
        land_contract_impl.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": admin, "gas_limit": 2000000},
    )
    # Set estate proxy
    estate_encoded_initializer_function = encode_function_data(
        estate_contract_impl.initialize,
        ESTATE_NAME,
        ESTATE_SYMBOL,
        ESTATE_BASE_TOKEN_URI,
        land_proxy.address,
        opensea_proxy_registry.address,
    )
    estate_proxy = oz.TransparentUpgradeableProxy.deploy(
        estate_contract_impl.address,
        proxy_admin.address,
        estate_encoded_initializer_function,
        {"from": admin, "gas_limit": 2000000},
    )

    land_contract = Contract.from_abi(
        "HighriseLand", land_proxy.address, HighriseLand.abi
    )
    # Mint tokens
    assert land_contract.ownerTokens(alice) == ()
    token_ids = [0, 65536, 131072, 1, 65537, 131073, 2, 65538, 131074]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Upgrade land
    land_v2 = HighriseLandV2.deploy(
        {"from": admin},
    )
    upgrade(admin, land_proxy, land_v2.address, proxy_admin_contract=proxy_admin).wait(
        1
    )

    return (
        Contract.from_abi("HighriseEstate", estate_proxy.address, HighriseEstate.abi),
        Contract.from_abi("HighriseLandV2", land_proxy.address, HighriseLandV2.abi),
        token_ids,
    )
