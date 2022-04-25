import pytest
from brownie import Contract, HighriseLand, HighriseLandV2, config, exceptions, network
from brownie.network.account import Account, LocalAccount
from brownie.network.contract import ProjectContract

from scripts.common import upgrade

from .. import LAND_BASE_TOKEN_URI, LAND_NAME, LAND_SYMBOL


def test_init_success(admin: Account, land_proxy: ProjectContract):
    land_contract = Contract.from_abi(
        "HighriseLand", land_proxy.address, HighriseLand.abi
    )

    assert land_contract.name() == LAND_NAME
    assert land_contract.symbol() == LAND_SYMBOL
    assert land_contract.hasRole(land_contract.DEFAULT_ADMIN_ROLE.call(), admin)
    assert land_contract.hasRole(land_contract.MINTER_ROLE.call(), admin)


def test_init_proxy_only_once(admin: Account, land_proxy: ProjectContract):
    land_contract = Contract.from_abi(
        "HighriseLand", land_proxy.address, HighriseLand.abi
    )
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.initialize("Name", "Symbol", "", admin.address, {"from": admin})
    assert "revert: Initializable: contract is already initialized" in str(
        excinfo.value
    )


def test_init_implementation_only_once(
    alice: Account, land_proxy: ProjectContract, proxy_admin: Account
):
    implementation_address = proxy_admin.getProxyImplementation(land_proxy)
    land_contract = Contract.from_abi(
        "HighriseLand", implementation_address, HighriseLand.abi
    )
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        land_contract.initialize("Name", "Symbol", "", alice.address, {"from": alice})
    assert "revert: Initializable: contract is already initialized" in str(
        excinfo.value
    )


def test_upgrade(
    admin: LocalAccount,
    alice: LocalAccount,
    charlie: LocalAccount,
    land_proxy: ProjectContract,
    proxy_admin: ProjectContract,
):
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

    land_v2 = HighriseLandV2.deploy(
        {"from": admin},
        publish_source=config["networks"][network.show_active()].get("verify"),
    )
    upgrade_transaction = upgrade(
        admin, land_proxy, land_v2.address, proxy_admin_contract=proxy_admin
    )
    upgrade_transaction.wait(1)
    land_contract_v2 = Contract.from_abi(
        "HighriseLandV2", land_proxy.address, HighriseLandV2.abi
    )

    # Verify implementation address changed
    implementation_address = proxy_admin.getProxyImplementation(land_proxy)
    assert implementation_address == land_v2.address

    # Verify storage is preserved
    assert set(land_contract_v2.ownerTokens(alice)) == set(token_ids)
    assert land_contract_v2.name() == LAND_NAME
    assert land_contract_v2.symbol() == LAND_SYMBOL
    assert land_contract_v2.tokenURI(0) == f"{LAND_BASE_TOKEN_URI}0"
    assert land_contract_v2.hasRole(land_contract.DEFAULT_ADMIN_ROLE.call(), admin)
    assert land_contract_v2.hasRole(land_contract.MINTER_ROLE.call(), admin)
    assert land_contract_v2.totalSupply() == 9

    # Test new functionality
    land_contract_v2.approveForTransfer(charlie, token_ids, {"from": alice}).wait(1)
    for t_id in token_ids:
        land_contract_v2.safeTransferFrom(alice, charlie, t_id, {"from": charlie}).wait(
            1
        )
    assert set(land_contract_v2.ownerTokens(charlie)) == set(token_ids)
