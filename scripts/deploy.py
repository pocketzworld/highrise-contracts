import os

from brownie import network

from .common import get_account
from .helpers import deploy_estate, deploy_land, deploy_proxy_admin, opensea_registry

environment = os.environ["ENVIRONMENT_NAME"]


def deploy():
    account = get_account()
    print(f"Deploying for Highrise {environment} environment")
    print(f"Deploying from {account} to {network.show_active()}")
    proxy_admin = deploy_proxy_admin(account)
    opensea_proxy_registry = opensea_registry(account)
    land_proxy, _ = deploy_land(
        account, proxy_admin, opensea_proxy_registry, environment
    )
    deploy_estate(account, proxy_admin, land_proxy, environment)


def main():
    deploy()
