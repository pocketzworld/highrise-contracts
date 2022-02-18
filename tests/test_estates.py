import pytest
from brownie.exceptions import VirtualMachineError


def test_estate_minting(land_contract, estate_contract, admin: str, alice: str):
    for i in range(9):
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    tx = estate_contract.mintFromParcels(list(range(9)), {"from": alice})
    tx.wait(1)

    estate_token_id = tx.return_value

    # Alice cannot use her parcel any more.
    with pytest.raises(VirtualMachineError):
        land_contract.safeTransferFrom(alice, admin, 0, {"from": alice}).wait(1)

    # Alice can burn her token.

    estate_contract.burn(estate_token_id)
