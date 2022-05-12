import pytest
from brownie import HighriseLandWithdrawal, exceptions
from brownie.network.account import LocalAccount
from brownie.network.contract import ProjectContract
from eth_abi import encode_abi
from eth_account import Account
from eth_account._utils.signing import sign_message_hash
from eth_keys import keys
from eth_utils import keccak


def generate_withdrawal_request(
    token_id: int, wallet: str, key: str
) -> tuple[bytes, bytes]:
    payload = encode_abi(["uint256", "address"], [token_id, wallet])
    hash = keccak(payload)
    _, _, _, signature = sign_message_hash(
        keys.PrivateKey(bytes.fromhex(key[2:])), hash
    )
    return payload, signature


@pytest.fixture
def withdrawal_contract(admin: LocalAccount, land_contract) -> ProjectContract:
    withdrawal_contract = HighriseLandWithdrawal.deploy(
        land_contract.address, {"from": admin}
    )
    return withdrawal_contract


@pytest.fixture
def withdrawal_minter_contract(
    admin: LocalAccount,
    withdrawal_contract: ProjectContract,
    land_contract: ProjectContract,
) -> ProjectContract:
    land_contract.grantRole(
        land_contract.MINTER_ROLE(), withdrawal_contract, {"from": admin}
    )
    return withdrawal_contract


@pytest.fixture
def enabled_withdrawal_contract(
    admin: LocalAccount, withdrawal_minter_contract: ProjectContract
) -> ProjectContract:
    withdrawal_minter_contract.enable({"from": admin}).wait(1)
    return withdrawal_minter_contract


def test_withdraw(
    admin: LocalAccount,
    enabled_withdrawal_contract: ProjectContract,
    alice: Account,
    charlie: Account,
    invalid_admin: LocalAccount,
):
    # Test success
    token_id = 15
    payload, sig = generate_withdrawal_request(
        token_id, alice.address, admin.private_key
    )
    (tx := enabled_withdrawal_contract.withdraw(payload, sig, {"from": alice})).wait(1)
    assert len(tx.events) == 2
    assert tx.events[-1]["sender"] == alice
    assert tx.events[-1]["tokenId"] == token_id

    # Test failure on invalid sender
    token_id = 16
    payload, sig = generate_withdrawal_request(
        token_id, alice.address, admin.private_key
    )
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        enabled_withdrawal_contract.withdraw(payload, sig, {"from": charlie}).wait(1)
    assert "Sender not approved to buy token" in str(excinfo.value)

    # Test failure on invalid signature
    token_id = 17
    payload, sig = generate_withdrawal_request(
        token_id, charlie.address, invalid_admin.private_key
    )
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        enabled_withdrawal_contract.withdraw(payload, sig, {"from": charlie}).wait(1)
    assert "Payload verification failed" in str(excinfo.value)


def test_modifier_enabled(
    admin: LocalAccount, alice: Account, withdrawal_minter_contract: ProjectContract
):
    token_id = 15
    payload, sig = generate_withdrawal_request(
        token_id, alice.address, admin.private_key
    )
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        withdrawal_minter_contract.withdraw(payload, sig, {"from": alice}).wait(1)
    assert "Contract not enabled" in str(excinfo.value)


def test_modifier_only_owner(
    admin: LocalAccount, alice: Account, withdrawal_minter_contract: ProjectContract
):
    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        withdrawal_minter_contract.enable({"from": alice}).wait(1)
    assert "Sender is not the owner" in str(excinfo.value)

    withdrawal_minter_contract.enable({"from": admin}).wait(1)

    with pytest.raises(exceptions.VirtualMachineError) as excinfo:
        withdrawal_minter_contract.disable({"from": alice}).wait(1)
    assert "Sender is not the owner" in str(excinfo.value)

    withdrawal_minter_contract.disable({"from": admin}).wait(1)
