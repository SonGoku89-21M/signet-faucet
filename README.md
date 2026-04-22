# Bitcoin Signet Faucet

A beginner-friendly web faucet for the Bitcoin Signet test network. Lets users request free test coins and includes a step-by-step setup guide for Bitcoin Core.

## What is Signet?

Signet is a safe Bitcoin test network — it works exactly like real Bitcoin but the coins have no value. It's ideal for learning and development without risking real money.

## Requirements

- Python 3.8+
- Bitcoin Core running on Signet
- The following Python packages:

```bash
pip install flask python-bitcoinrpc
```

## Configuration

Open `web_faucet.py` and update the RPC settings to match your `bitcoin.conf`:

```python
RPC_USER = 'your_rpc_username'
RPC_PASSWORD = 'your_rpc_password'
RPC_HOST = '127.0.0.1'
RPC_PORT = 38332
RPC_WALLET = 'your_wallet_name'
```

## Running

```bash
python3 web_faucet.py
```

The faucet runs on `http://localhost:5000` by default.

## Features

- Request 0.001 signet BTC per IP every 12 hours
- Step-by-step Bitcoin Core setup guide for beginners (Windows, Mac, Linux)
- Beginner-friendly error messages with explanations
- Signet Explorer links to track transactions

## Bitcoin Core Signet config (bitcoin.conf)

```ini
[signet]
server=1
txindex=1
rpcuser=youruser
rpcpassword=yourpass
signetchallenge=512103da0ee65a81d9d035a9bfff4810c5065d647153f3396b1fde56158cdf04bbace451ae
dnsseed=0
addnode=86.104.228.47:38333
fallbackfee=0.0002
```
