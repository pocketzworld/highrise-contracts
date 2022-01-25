# Fund Contract

## Introduction

* Smart contract to collect funds for highrise land sales

## Functionality

* `HighriseLandFund` contract collects funds for Highrise LAND Sale
* LAND token price is set during deployment
* Storage:
  * Total amount funded per address
  * Whitelisted addresses
  * Land tokens payed for per address
* States:
  * `ENABLED` - contract can be funded
  * `DISABLED` - contract can not be funded, owner can enable the contract or withdraw funds
* Whitelist:
  * Contract owner can add users to whitelist
* Funding requirements:
  * Contract is enabled
  * User is whitelisted
  * Amount is valid

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

