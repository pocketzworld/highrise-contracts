import os

from brownie import network

from scripts.helpers import deploy_estate, deploy_land, deploy_proxy_admin

from .common import get_account

environment = os.environ["ENVIRONMENT_NAME"]


def deploy():
    account = get_account()
    print(f"Deploying for Highrise {environment} environment")
    print(f"Deploying from {account} to {network.show_active()}")
    proxy_admin = deploy_proxy_admin(account)
    land_proxy, _ = deploy_land(account, proxy_admin, environment)
    deploy_estate(account, proxy_admin, land_proxy, environment)


def main():
    deploy()
