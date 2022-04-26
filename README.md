# Highrise Contracts

## Introduction

- This repo contains contracts to support:
  - Highrise land and estates
  - Funding contract to run the sales on our webpage

## Contracts functionality

### Land and Estate

- `HighriseLand` and `HighriseEstate` contracts are ERC721 tokens representing parts of Highrise world that inherit following openzeppelin contracts:

  - ERC721Upgradeable
  - ERC721EnumerableUpgradeable
  - ERC721RoyaltyUpgradeable
  - AccessControlUpgradeable
  - Initializable

- Both of these are supported to work on OpenSea.

  - Owner of the contract for opensea is defined by `OWNER_ROLE` in access control.
  - Gas-less listing is supported by overriding `isApprovedForAll` method

- Estates can be constructed/deconstructed from/to land parcels. Supported shapes are 3x3, 6x6, 9x9 and 12x12
- To create estates from land parcels user must first approve estate contract for transferring. This is achieved by ERC721 `approve` function in `HighriseLand` contract and in custom batch approval function `approveForTransfer` function in `HighriseLandV2`
- Both Land and Estate contracts are intended to be upgradeable. This is done by using OpenZeppelin `TransparentUpgradeableProxy` to separate the proxy and implementation contracts. This provides us with flexibility to add new logic and storage variables to the contracts in the future.

#### Token IDs and Coordinates

- Land coordinates are in range (-250, 250)
- Token ID is generated on Highrise backend with the following logic:

```python
from struct import pack

def coordinates_to_token_id(coords: tuple[int, int]) -> int:
    """X and Y are 2 bytes each."""
    as_bytes = pack(">hh", coords[0], coords[1])
    return int.from_bytes(as_bytes, "big")
```

- See https://docs.python.org/3/library/struct.html for more understanding.
- Estate contract has `token_id>coordinates` conversion function implemented. In that way estate contract can validate that parcels passed for estate creation have valid shape.
- Two tests are implemented to validate `token_id<>coordinates` conversion works:
  - `test_coordinates_parsing` - generates token id from coordinates in python and calls estate contract parse function. Compares that function returned coordinates match the ones initially used for `token_id` generation
  - `test_full_map_to_estates` - All land parcels in the map are merged into 3x3 estates
  - these tests are skipped when running `brownie test` due to long execution time

### Funding contract

- `HighriseLandFund` contract is a temporary contract used for sale purposes. It collects users payments and mints the Land tokens to the users.
- Contract States:
  - `ENABLED` - contract accepts payments and mints Land
  - `DISABLED` - contract does not accept payments, owner can enable the contract or withdraw funds
- Entrypoint to the contract from the user perspective is the `fund` function, which accepts a payload signed with a wallet key on our backend.
- When the payload signature is confirmed the payload is unpacked into `tokenId`, `expiry` and `cost` for minting purposes. After requirements are met Land NFT is minted to the user
- `FundLandEvent` is emitted when funding transaction is successful. Pending potential removal - not required anymore since we can track ERC721 `Transfer` events directly.
- Contract is granted `MINTER_ROLE` for `HighriseLand`

## Prerequisites

- Install `ganache` - https://trufflesuite.com/ganache/
- Install `brownie` (`pipx` is also required to install it)
  ```python
  # `pipx` install
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  # install `brownie` with `pipx`
  pipx install eth-brownie
  ```
- Setup `.env` file and include the following variables
  - `DEV_ACCOUNT_NAME` - account stored in `brownie` used for deploying to testnets
  - `WEB3_INFURA_PROJECT_ID` - gateway to blockchain development - set up your account here https://infura.io/
  - `ETHERSCAN_TOKEN` - create account on https://etherscan.io/ - used for verifying and publishing smart contracts
  - `ENVIRONMENT_NAME` - Highrise environment that contracts will be used on

## Brownie commands

- `brownie init` - initializes the project and creates project structure
- `brownie compile` - compiles all contracts within `contracts/`
- `brownie run <script>` - runs custom python script
- `brownie test` - runs tests
- `brownie accounts list` - lists all stored accounts
- `brownie accounts new <account-name>` - import existing account via private key. Stored accounts are in encrypted JSON files known as `keystores`
- `brownie networks list` - list all available networks to connect
- `brownie networks add` - add new network

## Ethereum Theory

- Why to emit events
  - There are two types of Solidity event parameters: indexed and not indexed,
  - Events are used for return values from the transaction and as a cheap data storage,
  - Blockchain keeps event parameters in transaction logsEvents can be filtered by name and by contract address
