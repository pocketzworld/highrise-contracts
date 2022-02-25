import pytest
from brownie.exceptions import VirtualMachineError
from brownie.network.contract import ProjectContract


def test_estate_minting(
    land_contract: ProjectContract,
    estate_contract: ProjectContract,
    admin: str,
    alice: str,
    charlie: str,
):
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

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

    # Alice has 9 tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Charlie cannot mint the estate.
    with pytest.raises(VirtualMachineError):
        tx = estate_contract.mintFromParcels(token_ids, {"from": charlie}).wait(1)

    tx = estate_contract.mintFromParcels(token_ids, {"from": alice})
    tx.wait(1)

    estate_token_id = tx.return_value

    # Alice has no land again.
    assert land_contract.ownerTokens(alice) == ()

    # Alice has an estate now.
    assert estate_contract.balanceOf(alice) == 1

    # Alice cannot use her parcel any more.
    with pytest.raises(VirtualMachineError):
        land_contract.safeTransferFrom(alice, admin, 0, {"from": alice}).wait(1)

    # Charlie cannot burn Alice's token.
    with pytest.raises(VirtualMachineError):
        estate_contract.burn(estate_token_id, {"from": charlie}).wait(1)

    # Alice can burn her token.
    estate_contract.burn(estate_token_id, {"from": alice}).wait(1)

    assert estate_contract.balanceOf(alice) == 0

    # Alice has her tokens again.
    tokens = land_contract.ownerTokens(alice)
    assert set(tokens) == set(token_ids)
