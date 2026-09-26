"""
Hyperliquid Withdrawal Script (using the official SDK)
========================================================

Important security notes (please read):

1. Run this script only on your own computer, never on a server or third-party service.
2. The private key is never written into this file. This version only reads it from
   an environment variable or a hidden (masked) prompt, specifically so it can never
   be accidentally committed to version control.
3. Set the key in your terminal, only for that one session, like this:

   Linux/macOS:
       export HL_PRIVATE_KEY="0xYOUR_PRIVATE_KEY"
       export HL_WITHDRAW_ADDRESS="0xYOUR_DESTINATION_ADDRESS"
       python3 hyperliquid_withdraw.py

   Windows (PowerShell):
       $env:HL_PRIVATE_KEY="0xYOUR_PRIVATE_KEY"
       $env:HL_WITHDRAW_ADDRESS="0xYOUR_DESTINATION_ADDRESS"
       python3 hyperliquid_withdraw.py

   These variables are cleared automatically once you close the terminal.
4. Before running, check the official docs since SDK method names may have changed:
   https://github.com/hyperliquid-dex/hyperliquid-python-sdk
   https://hyperliquid.gitbook.io/hyperliquid-docs/

Install requirements:
    pip install hyperliquid-python-sdk
"""

import getpass
import os
import sys

try:
    from eth_account import Account
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
except ImportError:
    print("Please install the required library first:")
    print("    pip install hyperliquid-python-sdk")
    sys.exit(1)


def get_private_key():
    """Read the key only from an environment variable, or prompt for it (masked, like a password)."""
    key = os.getenv("HL_PRIVATE_KEY")
    if key:
        return key
    print("Environment variable HL_PRIVATE_KEY is not set.")
    key = getpass.getpass("Enter your private key (input hidden): ").strip()
    if not key:
        print("Error: no private key was entered.")
        sys.exit(1)
    return key


def get_withdraw_address():
    address = os.getenv("HL_WITHDRAW_ADDRESS")
    if address:
        return address
    address = input("Enter the destination address (Arbitrum): ").strip()
    if not address:
        print("Error: no destination address was entered.")
        sys.exit(1)
    return address


def main():
    private_key = get_private_key()
    withdraw_address = get_withdraw_address()

    try:
        wallet = Account.from_key(private_key)
    except Exception as e:
        print(f"Error: invalid private key: {e}")
        sys.exit(1)

    address = wallet.address
    print(f"Your wallet address: {address}")

    base_url = constants.MAINNET_API_URL
    info = Info(base_url, skip_ws=True)
    exchange = Exchange(wallet, base_url)

    print("\n--- Checking balances ---")
    try:
        user_state = info.user_state(address)
        spot_state = info.spot_user_state(address)
        print("Perp state:", user_state.get("marginSummary", {}))
        print("Spot state:", spot_state.get("balances", []))
    except Exception as e:
        print(f"Error fetching account state: {e}")
        sys.exit(1)

    perp_usdc = float(user_state.get("marginSummary", {}).get("accountValue", 0))
    print(f"\nApproximate Perp balance: {perp_usdc} USDC")

    if perp_usdc <= 0:
        print("No transferable balance found in Perp.")
        return

    amount_to_move = round(perp_usdc - 1, 2)  # keep a small margin for fees/fluctuations
    if amount_to_move > 0:
        confirm = input(
            f"\nTransfer {amount_to_move} USDC from Perp to Spot? (yes/no): "
        )
        if confirm.strip().lower() == "yes":
            try:
                # exact method name may differ between SDK versions — check the docs
                result = exchange.usd_class_transfer(amount_to_move, to_perp=False)
                print("Perp -> Spot transfer result:", result)
            except Exception as e:
                print(f"Transfer error: {e}")
                sys.exit(1)

    confirm2 = input(
        f"\nWithdraw the balance to address {withdraw_address}? (yes/no): "
    )
    if confirm2.strip().lower() == "yes":
        raw_amount = input("Enter the USDC amount to withdraw: ")
        try:
            withdraw_amount = float(raw_amount)
        except ValueError:
            print("Error: the amount entered is not a valid number.")
            sys.exit(1)
        try:
            result = exchange.withdraw_from_bridge(withdraw_amount, withdraw_address)
            print("Withdrawal result:", result)
        except Exception as e:
            print(f"Withdrawal error: {e}")
            sys.exit(1)

    print("\nDone. Please check the destination address on the Arbitrum explorer (arbiscan.io).")


if __name__ == "__main__":
    main()
