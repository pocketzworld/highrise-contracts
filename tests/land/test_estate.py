import pytest
from brownie.exceptions import VirtualMachineError
from brownie.network.contract import ProjectContract


def test_minting(
    land_contract: ProjectContract,
    estate_contract: ProjectContract,
    admin: str,
    alice: str,
    charlie: str,
):
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

    token_ids = [0, 65536, 131072, 1, 65537, 131073, 2, 65538, 131074]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    # Alice has 9 tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Charlie cannot mint the estate.
    with pytest.raises((VirtualMachineError, AttributeError)):
        estate_contract.mintFromParcels(token_ids, {"from": charlie}).wait(1)

    (tx := estate_contract.mintFromParcels(token_ids, {"from": alice})).wait(1)

    estate_token_id = tx.return_value

    # Alice has no land again.
    assert land_contract.ownerTokens(alice) == ()

    # Alice has an estate now.
    assert estate_contract.balanceOf(alice) == 1

    # Alice cannot use her parcel any more.
    with pytest.raises((VirtualMachineError, AttributeError)):
        land_contract.safeTransferFrom(alice, admin, 0, {"from": alice}).wait(1)

    # Charlie cannot burn Alice's token.
    with pytest.raises((VirtualMachineError, AttributeError)):
        estate_contract.burn(estate_token_id, {"from": charlie}).wait(1)

    # Alice can burn her token.
    estate_contract.burn(estate_token_id, {"from": alice}).wait(1)

    assert estate_contract.balanceOf(alice) == 0

    # Alice has her tokens again.
    tokens = land_contract.ownerTokens(alice)
    assert set(tokens) == set(token_ids)


def test_wrong_shape(
    land_contract: ProjectContract,
    estate_contract: ProjectContract,
    admin: str,
    alice: str,
    charlie: str,
):
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

    token_ids = [0, 65536, 131072, 1, 65537, 131073, 2, 65538, 131074]

    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    # Alice has 9 tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Alice cannot mint the estate only 8 parcels.
    with pytest.raises((VirtualMachineError, AttributeError)):
        estate_contract.mintFromParcels(token_ids[:8], {"from": alice}).wait(1)


def test_minting_negative_coords(
    land_contract: ProjectContract,
    estate_contract: ProjectContract,
    admin: str,
    alice: str,
):
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

    # a 12x12 estate, from -6 to 5 for both X and Y
    token_ids = [
        4294639610,
        4294705146,
        4294770682,
        4294836218,
        4294901754,
        4294967290,
        65530,
        131066,
        196602,
        262138,
        327674,
        393210,
        4294639611,
        4294705147,
        4294770683,
        4294836219,
        4294901755,
        4294967291,
        65531,
        131067,
        196603,
        262139,
        327675,
        393211,
        4294639612,
        4294705148,
        4294770684,
        4294836220,
        4294901756,
        4294967292,
        65532,
        131068,
        196604,
        262140,
        327676,
        393212,
        4294639613,
        4294705149,
        4294770685,
        4294836221,
        4294901757,
        4294967293,
        65533,
        131069,
        196605,
        262141,
        327677,
        393213,
        4294639614,
        4294705150,
        4294770686,
        4294836222,
        4294901758,
        4294967294,
        65534,
        131070,
        196606,
        262142,
        327678,
        393214,
        4294639615,
        4294705151,
        4294770687,
        4294836223,
        4294901759,
        4294967295,
        65535,
        131071,
        196607,
        262143,
        327679,
        393215,
        4294574080,
        4294639616,
        4294705152,
        4294770688,
        4294836224,
        4294901760,
        0,
        65536,
        131072,
        196608,
        262144,
        327680,
        4294574081,
        4294639617,
        4294705153,
        4294770689,
        4294836225,
        4294901761,
        1,
        65537,
        131073,
        196609,
        262145,
        327681,
        4294574082,
        4294639618,
        4294705154,
        4294770690,
        4294836226,
        4294901762,
        2,
        65538,
        131074,
        196610,
        262146,
        327682,
        4294574083,
        4294639619,
        4294705155,
        4294770691,
        4294836227,
        4294901763,
        3,
        65539,
        131075,
        196611,
        262147,
        327683,
        4294574084,
        4294639620,
        4294705156,
        4294770692,
        4294836228,
        4294901764,
        4,
        65540,
        131076,
        196612,
        262148,
        327684,
        4294574085,
        4294639621,
        4294705157,
        4294770693,
        4294836229,
        4294901765,
        5,
        65541,
        131077,
        196613,
        262149,
        327685,
    ]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    # Alice has all the tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Alice mints the estate.
    estate_contract.mintFromParcels(token_ids, {"from": alice}).wait(1)

    estate_token_id = estate_contract.tokenOfOwnerByIndex(alice, 0)

    # Alice has no land again.
    assert land_contract.ownerTokens(alice) == ()

    # Alice has an estate now.
    assert estate_contract.balanceOf(alice) == 1

    # Alice cannot use her parcel any more.
    with pytest.raises((VirtualMachineError, AttributeError)):
        land_contract.safeTransferFrom(
            alice, admin, token_ids[0], {"from": alice}
        ).wait(1)

    # Alice can burn her token.
    estate_contract.burn(estate_token_id, {"from": alice}).wait(1)

    assert estate_contract.balanceOf(alice) == 0

    # Alice has her tokens again.
    tokens = land_contract.ownerTokens(alice)
    assert set(tokens) == set(token_ids)
