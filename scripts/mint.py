from brownie import HighriseLandFund, network
from eth_abi import encode_abi
from eth_account._utils.signing import sign_message_hash
from eth_hash.auto import keccak
from eth_keys import keys

from .common import (
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)

# TOKEN_ID = 2013288447
TOKEN_ID = 1912611839


def generate_fund_request(
    token_id: int, expiry: int, cost: int, key: str
) -> tuple[bytes, bytes]:
    payload = encode_abi(["uint256", "uint256", "uint256"], [token_id, expiry, cost])
    hash = keccak(payload)
    _, _, _, signature = sign_message_hash(
        keys.PrivateKey(bytes.fromhex(key[2:])), hash
    )
    return payload, signature


def mint():
    if (
        network.show_active()
        in LOCAL_BLOCKCHAIN_ENVIRONMENTS + FORKED_LOCAL_ENVIRONMENTS
    ):
        print("Error: Script can only be run on real network")
        return
    land_fund = HighriseLandFund[-1]
    account = get_account()
    payload, sig = generate_fund_request(
        TOKEN_ID, 10000000000000000, 2000000000000000, account.private_key
    )
    land_fund.fund(payload, sig, {"from": account, "value": 2000000000000000}).wait(1)


def main():
    mint()
