# Fund Contract

## Introduction

* Smart contract to collect funds for highrise land sales

## Functionality

* `HighriseLandFund` contract collects funds for Highrise LAND Sale
* LAND token price is set during deployment
* Storage:
  * Total amount funded per address
* States:
  * `ENABLED` - contract can be funded
  * `DISABLED` - contract can not be funded, owner can enable the contract or withdraw funds
* Funding requirements:
  * Contract is enabled
  * Amount is valid
* `FundLandEvent` is emitted when funding transaction is successful
* Why is event emitted? 
  * There are two types of Solidity event parameters: indexed and not indexed,
  * Events are used for return values from the transaction and as a cheap data storage,
  * Blockchain keeps event parameters in transaction logsEvents can be filtered by name and by contract address
  

## Prerequisites

* Install `ganache` - https://trufflesuite.com/ganache/
* Install `brownie` (`pipx` is also required to install it)
  ```python
  # `pipx` install
  python3 -m pip install --user pipx 
  python3 -m pipx ensurepath
  # install `brownie` with `pipx`
  pipx install eth-brownie
* Setup `.env` file and include the following variables
  * `DEV_ACCOUNT_NAME` - account stored in `brownie` used for deploying to testnets
  * `WEB3_INFURA_PROJECT_ID` - gateway to blockchain development - set up your account here https://infura.io/
  * `ETHERSCAN_TOKEN` - create account on https://etherscan.io/ - used for verifying and publishing smart contracts

## Brownie commands

* `brownie init` - initializes the project and creates project structure
* `brownie compile` - compiles all contracts within `contracts/`
* `brownie run <script>` - runs custom python script 
* `brownie test` - runs tests
* `brownie accounts list` - lists all stored accounts
* `brownie accounts new <account-name>` - import existing account via private key. Stored accounts are in encrypted JSON files known as `keystores` 
* `brownie networks list` - list all available networks to connect
* `brownie networks add` - add new network
