import os

from brownie import config, network

from .common import get_account
from .estate import deploy_estate, verify_estate, verify_estate_proxy
from .helpers import (
    deploy_proxy_admin,
    load_openzeppelin,
    opensea_proxy_registry_address,
)
from .land import deploy_land, verify_land, verify_proxy

environment = os.environ["ENVIRONMENT_NAME"]


def deploy():
    account = get_account()
    oz = load_openzeppelin()
    print(f"Deploying for Highrise {environment} environment")
    print(f"Deploying from {account} to {network.show_active()}")
    proxy_admin = deploy_proxy_admin(account, oz)
    opensea_address = opensea_proxy_registry_address(account)
    land_proxy, land = deploy_land(
        proxy_admin, opensea_address, environment, account, oz
    )
    estate_proxy, estate = deploy_estate(
        proxy_admin, land_proxy.address, opensea_address, environment, account, oz
    )

    if config["networks"][network.show_active()].get("verify"):
        verify_land(land.address)
        verify_proxy(land_proxy.address, oz)
        verify_estate(estate.address)
        verify_estate_proxy(estate_proxy.address, oz)


def main():
    deploy()
