# Hyperliquid Withdrawal Script

⚠️ **Security warning**

- Run this script only on your own computer, never on a server or third-party service.
- The private key is never written into any file that could be committed. This script only
  reads the key from an environment variable or a hidden (masked) prompt.
- This is a personal-use / educational project.

## Usage

1. Install the library:
```
pip install hyperliquid-python-sdk
```

2. Set the key and destination address in your terminal (for that session only):

**Linux/macOS:**
```
export HL_PRIVATE_KEY="0xYOUR_PRIVATE_KEY"
export HL_WITHDRAW_ADDRESS="0xYOUR_ARBITRUM_ADDRESS"
python3 hyperliquid_withdraw.py
```

**Windows (PowerShell):**
```
$env:HL_PRIVATE_KEY="0xYOUR_PRIVATE_KEY"
$env:HL_WITHDRAW_ADDRESS="0xYOUR_ARBITRUM_ADDRESS"
python3 hyperliquid_withdraw.py
```

If the variables aren't set, the script prompts for them at runtime (the key input is hidden).

## What this script does

1. Displays your Perp and Spot account balances.
2. With your confirmation, transfers the Perp balance to Spot.
3. With your confirmation, withdraws the specified amount to the destination address (on Arbitrum).

## Disclaimer

Provided as-is, with no warranty. Test with a small amount before using with large sums.
