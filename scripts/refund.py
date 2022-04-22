import csv

from .common import get_refund_account


def refund():
    account = get_refund_account()
    with open("refund.csv", newline="\n") as refund_file:
        reader = csv.reader(refund_file, delimiter=",")
        for row in reader:
            wallet, wei_amount = row[0], int(row[1])
            print(f"Returning funds to {wallet}: {wei_amount}")
            if account.balance() < wei_amount:
                print("Insufficient funds. Stopping execution")
                return
            account.transfer(wallet, wei_amount)


def main():
    refund()
