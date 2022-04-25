from collections import Counter
from struct import pack

import pytest
from brownie.exceptions import VirtualMachineError
from brownie.network.contract import ProjectContract


def coordinates_to_token_id(coords: tuple[int, int]) -> int:
    """X and Y are 2 bytes each."""
    as_bytes = pack(">hh", coords[0], coords[1])
    return int.from_bytes(as_bytes, "big")


def test_minting(
    estate_with_land: tuple[ProjectContract, ProjectContract],
    admin: str,
    alice: str,
    charlie: str,
):
    estate_contract, land_contract = estate_with_land
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

    token_ids = [0, 65536, 131072, 1, 65537, 131073, 2, 65538, 131074]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)

    # Alice has 9 tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Charlie cannot mint the estate.
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(token_ids, {"from": charlie}).wait(1)
    assert "ERC721: transfer caller is not owner nor approved" in str(excinfo.value)

    # Alice cannot mint without approving.
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(token_ids, {"from": alice}).wait(1)
    assert "ERC721: transfer caller is not owner nor approved" in str(excinfo.value)
    # Approve tokens for transfer
    for t_id in token_ids:
        land_contract.approve(estate_contract.address, t_id, {"from": alice}).wait(1)

    (tx := estate_contract.mintFromParcels(token_ids, {"from": alice})).wait(1)

    # Fetch minted estate token from emitted event
    estate_token_id = tx.events[-1]["tokenId"]

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
    estate_with_land: tuple[ProjectContract, ProjectContract],
    admin: str,
    alice: str,
):
    estate_contract, land_contract = estate_with_land
    # Alice has nothing.
    assert land_contract.ownerTokens(alice) == ()

    coords = [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2)]
    token_ids = [coordinates_to_token_id(t) for t in coords]
    for i in token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)
    # Approve tokens for transfer
    for i in token_ids:
        land_contract.approve(estate_contract.address, i, {"from": alice}).wait(1)

    # Alice has 9 tokens.
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)

    # Alice cannot mint the estate only 8 parcels.
    with pytest.raises((VirtualMachineError, AttributeError)):
        estate_contract.mintFromParcels(token_ids[:8], {"from": alice}).wait(1)

    # Columns not same in all rows
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(token_ids, {"from": alice}).wait(1)
    assert (
        "Invalid coordinates: Land parcel rows do not have same column coordinates"
        in str(excinfo.value)
    )

    # Rows not adjacent to eachother
    coords = [(0, -1), (1, -1), (2, -1)]
    new_row_token_ids = [coordinates_to_token_id(t) for t in coords]
    for i in new_row_token_ids:
        land_contract.mint(alice, i, {"from": admin}).wait(1)
        land_contract.approve(estate_contract.address, i, {"from": alice}).wait(1)
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(
            new_row_token_ids + token_ids[:3] + token_ids[6:], {"from": alice}
        ).wait(1)
    assert "Invalid coordinates: Land parcels are not adjacent vertically" in str(
        excinfo.value
    )

    # Columns not adjacent to eachother
    new_token_id = coordinates_to_token_id((0, 1))
    land_contract.mint(alice, new_token_id, {"from": admin}).wait(1)
    land_contract.approve(estate_contract.address, i, {"from": alice}).wait(1)
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(
            token_ids[:3] + [new_token_id] + token_ids[4:],
            {"from": alice},
        ).wait(1)
    assert "Invalid coordinates: Land parcels are not adjacent horizontally" in str(
        excinfo.value
    )

    # Row parcels not in the same vertical position
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(
            [new_token_id] + token_ids[1:],
            {"from": alice},
        ).wait(1)
    assert (
        "Invalid coordinates: Land parcels in row do not have same vertical coordinate"
        in str(excinfo.value)
    )


def test_mint_negative_coords(
    estate_with_land: tuple[ProjectContract, ProjectContract],
    admin: str,
    alice: str,
):
    estate_contract, land_contract = estate_with_land
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
    # Approve for transfer
    for i in token_ids:
        land_contract.approve(estate_contract.address, i, {"from": alice}).wait(1)

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


def test_estate_after_land_upgrade(
    estate_with_land_upgrade: tuple[ProjectContract, ProjectContract, list[int]],
    alice: str,
    charlie: str,
):
    estate_contract, land_contract, token_ids = estate_with_land_upgrade
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)
    # Approve estate contract for transfer
    land_contract.approveForTransfer(
        estate_contract.address, token_ids, {"from": alice}
    ).wait(1)
    # Mint estate
    (tx := estate_contract.mintFromParcels(token_ids, {"from": alice})).wait(1)
    estate_token_id = tx.events[-1]["tokenId"]
    assert land_contract.ownerTokens(alice) == ()
    assert estate_contract.balanceOf(alice) == 1
    assert set(estate_contract.ownerTokens(alice)) == set([estate_token_id])
    # Burn estate
    estate_contract.burn(estate_token_id, {"from": alice}).wait(1)
    assert estate_contract.balanceOf(alice) == 0
    assert set(land_contract.ownerTokens(alice)) == set(token_ids)
    # Approve again for transfer
    land_contract.approveForTransfer(
        estate_contract.address, token_ids, {"from": alice}
    ).wait(1)
    # Transfer one of the tokens to charlie
    land_contract.safeTransferFrom(alice, charlie, token_ids[0], {"from": alice}).wait(
        1
    )
    assert set(land_contract.ownerTokens(charlie)) == set([token_ids[0]])
    # Alice can no longer mint estate
    with pytest.raises((VirtualMachineError, AttributeError)) as excinfo:
        estate_contract.mintFromParcels(token_ids, {"from": alice}).wait(1)
    assert "ERC721: transfer caller is not owner nor approved" in str(excinfo.value)


def test_coordinates_parsing(estate_contract_impl: ProjectContract):
    # Uncomment this line to run the test
    pytest.skip("Long execution time")
    MIN_COORD = -250
    MAX_COORD = 250
    for x in range(MIN_COORD, MAX_COORD + 1):
        for y in range(MIN_COORD, MAX_COORD + 1):
            token_id = coordinates_to_token_id((x, y))
            x_sol, y_sol = estate_contract_impl.parseToCoordinates(token_id)
            assert x == x_sol
            assert y == y_sol


def test_full_map_to_estates(
    estate_with_land: tuple[ProjectContract, ProjectContract], admin: str, alice: str
):
    # Uncomment this line to run the test
    pytest.skip("Long execution time")
    estate_contract, land_contract = estate_with_land
    MIN_COORD = -250
    MAX_COORD = 250
    ESTATE_SIZE = 3
    coords_processed = Counter()
    estates_created = 0
    # Generate estates
    for y in range(MIN_COORD, MAX_COORD + 1, ESTATE_SIZE):
        for x in range(MIN_COORD, MAX_COORD + 1, ESTATE_SIZE):
            token_ids = []
            for j in range(ESTATE_SIZE):
                for i in range(ESTATE_SIZE):
                    coords_processed[(x + i, y + j)] += 1
                    token_id = coordinates_to_token_id((x + i, y + j))
                    land_contract.mint(alice, token_id, {"from": admin}).wait(1)
                    land_contract.approve(
                        estate_contract.address, token_id, {"from": alice}
                    ).wait(1)
                    token_ids.append(token_id)
            print(
                f"ESTATE FROM ({x},{y}) TO ({x + ESTATE_SIZE - 1},{y + ESTATE_SIZE - 1})"
            )
            estate_contract.mintFromParcels(token_ids, {"from": alice}).wait(1)
            estates_created += 1
    # Validate each parcel used only once
    for y in range(MIN_COORD, MAX_COORD + 1):
        for x in range(MIN_COORD, MAX_COORD + 1):
            assert coords_processed[(x, y)] == 1
    # Validate total number of estates created
    assert len(coords_processed) == 251001
    assert estates_created == 27889
