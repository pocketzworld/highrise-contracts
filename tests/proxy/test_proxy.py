from brownie import (
    Contract,
    HighriseLand,
    HighriseLandAlt,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    config,
    network,
)
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from scripts.common import encode_function_data, upgrade
from .. import LAND_NAME, LAND_SYMBOL, LAND_BASE_TOKEN_URI


def test_upgrade(
    admin: LocalAccount, alice: Account, opensea_registry: ProjectContract
):
    proxy_admin = ProxyAdmin.deploy({"from": admin})

    print(f"Deploying to {network.show_active()}")
    # Land
    land = HighriseLand.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    land_encoded_initializer_function = encode_function_data(
        land.initialize,
        LAND_NAME,
        LAND_SYMBOL,
        LAND_BASE_TOKEN_URI,
        opensea_registry.address,
    )
    land_proxy = TransparentUpgradeableProxy.deploy(
        land.address,
        proxy_admin.address,
        land_encoded_initializer_function,
        {"from": admin, "gas_limit": 1000000},
    )

    land_contract = Contract.from_abi(
        "HighriseLand", land_proxy.address, HighriseLand.abi
    )
    token_ids = [
        0,
        16777216,
        33554432,
        256,
        16777472,
        33554688,
        512,
        16777728,
        33554944,
    ]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    alt_land = HighriseLandAlt.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    upgrade_transaction = upgrade(
        admin, land_proxy, alt_land.address, proxy_admin_contract=proxy_admin
    )
    upgrade_transaction.wait(1)
    alt_land_contract = Contract.from_abi(
        "HighriseLandAlt", land_proxy.address, HighriseLandAlt.abi
    )

    # Verify storage is preserved
    assert set(alt_land_contract.ownerTokens(alice)) == set(token_ids)
    assert alt_land_contract.name() == LAND_NAME
    assert alt_land_contract.symbol() == LAND_SYMBOL
    assert alt_land_contract.tokenURI(0) == f"{LAND_BASE_TOKEN_URI}0"
    assert alt_land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE.call(), admin)
    assert alt_land_contract.hasRole(land_contract.MINTER_ROLE.call(), admin)
    assert alt_land_contract.totalSupply() == 9

    # Test new functionality
    alt_land_contract.storeValue(5, {"from": admin}).wait(1)
    assert alt_land_contract.getValue() == 5
