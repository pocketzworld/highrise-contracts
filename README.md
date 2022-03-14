# Fund Contract

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
- Estate contract is granted `ESTATE_MANAGER_ROLE` on Land contract that provides functionality to bind land to estate when the estate is constructed

- Both Land and Estate contracts are intended to be upgradeable. This is done by using OpenZeppelin `TransparentUpgradeableProxy` to separate the proxy and implementation contracts. This provides us with flexibility to add new logic and storage variables to the contracts in the future.

### Funding contract

- `HighriseLandFund` contract is used for sale purposes. It collects users payments and mints the Land tokens to the users.
- Contract States:
  - `ENABLED` - contract can be funded
  - `DISABLED` - contract can not be funded, owner can enable the contract or withdraw funds
- Entrypoint to the contract from user perspective is `fund` function that accepts payload signed with Highrise wallet key on our backend.
- When the payload signature is confirmed payload is unpacked into `tokenId`, `expiry` and `cost` for minting purposes. After requirements are met Land NFT is minted to the user
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
