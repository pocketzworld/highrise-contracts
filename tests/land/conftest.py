import pytest
from brownie import Contract, HighriseEstate, config, network
from brownie.network.account import LocalAccount
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data
from scripts.helpers import Project

from .. import ESTATE_BASE_TOKEN_URI, ESTATE_NAME, ESTATE_SYMBOL


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
