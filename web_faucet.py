#!/usr/bin/env python3
"""
Web Bitcoin Signet Faucet
A simple web interface for the Signet faucet to onboard newbies.
"""

import os
import time
import json
from flask import Flask, request, render_template_string
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

app = Flask(__name__)

# RPC connection
RPC_USER = 'devuser'
RPC_PASSWORD = 'devpass123'
RPC_HOST = '127.0.0.1'
RPC_PORT = 38332
RPC_WALLET = 'test-wallet'

# Faucet settings
AMOUNT = 0.001
RATE_LIMIT_FILE = 'faucet_requests.json'
RATE_LIMIT_HOURS = 12

def get_rpc_connection():
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{RPC_WALLET}")

def validate_address(rpc, address):
    try:
        info = rpc.validateaddress(address)
        return info['isvalid'] and not info.get('isscript', False)
    except:
        return False

def check_rate_limit(ip):
    if not os.path.exists(RATE_LIMIT_FILE):
        return True
    try:
        with open(RATE_LIMIT_FILE, 'r') as f:
            requests = json.load(f)
    except:
        return True
    now = time.time()
    if ip in requests:
        last = requests[ip]
        if now - last < RATE_LIMIT_HOURS * 3600:
            return False
    return True

def update_rate_limit(ip):
    requests = {}
    if os.path.exists(RATE_LIMIT_FILE):
        try:
            with open(RATE_LIMIT_FILE, 'r') as f:
                requests = json.load(f)
        except:
            pass
    requests[ip] = time.time()
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump(requests, f)

def send_coins(rpc, address):
    try:
        txid = rpc.sendtoaddress(address, AMOUNT)
        return txid
    except JSONRPCException as e:
        return str(e)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bitcoin Signet Faucet</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 25%, #ffe082 50%, #ffca28 75%, #ffb300 100%);
            background-attachment: fixed;
            background-size: cover;
            color: #333;
            min-height: 100vh;
            position: relative;
        }
        .container { 
            background: rgba(255, 255, 255, 0.95);
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: 2px solid #f7931a;
            margin: 20px auto;
        }
        h1 { 
            color: #f7931a; 
            text-align: center; 
            margin-bottom: 20px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        p { 
            line-height: 1.6; 
            color: #555;
        }
        ul { 
            background: #fff3cd; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 5px solid #f7931a;
        }
        input[type="text"] { 
            width: 100%; 
            padding: 12px; 
            margin: 15px 0; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus { 
            border-color: #f7931a; 
            outline: none;
        }
        button { 
            background: linear-gradient(135deg, #f7931a 0%, #ff9800 100%);
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(247, 147, 26, 0.3);
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(247, 147, 26, 0.4);
        }
        .message { 
            margin: 15px 0; 
            padding: 15px; 
            border-radius: 8px; 
            font-weight: bold;
        }
        .success { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724; 
            border: 1px solid #c3e6cb;
        }
        .error { 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24; 
            border: 1px solid #f5c6cb;
        }
        a { 
            color: #f7931a; 
            text-decoration: none;
        }
        a:hover { 
            text-decoration: underline;
        }
        .main-menu {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        .menu-card {
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 180px;
            padding: 28px;
            border-radius: 22px;
            border: 2px solid rgba(247, 147, 26, 0.23);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 18px 35px rgba(0, 0, 0, 0.08);
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            text-align: left;
        }
        .menu-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 24px 45px rgba(0, 0, 0, 0.12);
            border-color: rgba(247, 147, 26, 0.45);
        }
        .menu-card h2 {
            margin: 0 0 12px;
            font-size: 1.6rem;
            color: #d35400;
        }
        .menu-icon {
            font-size: 4.5rem;
            line-height: 1;
            margin: 18px 0;
            color: #f7931a;
            text-align: center;
        }
        .menu-card p {
            margin: 0;
            color: #555;
            line-height: 1.7;
        }
        .menu-card .subtext {
            margin-top: 12px;
            font-size: 0.98rem;
            color: #777;
        }
        .hidden {
            display: none;
        }
        .section-wrapper {
            background: rgba(255, 255, 255, 0.98);
            padding: 25px;
            border-radius: 20px;
            border: 1px solid rgba(247, 147, 26, 0.18);
            margin-top: 20px;
        }
        .back-button {
            background: transparent;
            color: #f7931a;
            border: 2px solid #f7931a;
            border-radius: 12px;
            padding: 10px 18px;
            font-size: 0.95rem;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .back-button:hover {
            background: #f7931a;
            color: white;
        }
        .hint-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid currentColor;
            background: transparent;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            margin-left: 10px;
            padding: 0;
            vertical-align: middle;
            line-height: 1;
            box-shadow: none;
            transform: none;
        }
        .hint-btn:hover {
            transform: none;
            box-shadow: none;
            opacity: 0.75;
        }
        .hint-box {
            display: none;
            margin-top: 10px;
            padding: 12px 15px;
            background: #fff9f0;
            border-left: 4px solid #f7931a;
            border-radius: 6px;
            font-size: 0.92rem;
            font-weight: normal;
            color: #555;
            line-height: 1.6;
        }
        .intro-box {
            background: #fff8e1;
            border-left: 5px solid #f7931a;
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 22px;
            color: #555;
            line-height: 1.7;
        }
        @media (max-width: 768px) {
            .main-menu {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Signet Faucet Hub</h1>
        <div class="intro-box">
            <strong>New to Bitcoin?</strong> Signet is a safe practice network that works exactly like real Bitcoin — but the coins have no value. It's the perfect place to learn how wallets, transactions, and the Lightning Network work without risking any real money. This faucet gives you free Signet coins so you can start experimenting right away.
        </div>
        <p>Choose a network below to continue.</p>

        <div class="main-menu" id="homeMenu">
            <button class="menu-card" onclick="showSection('faucetSection')">
                <h2>Bitcoin Signet Faucet</h2>
                <div class="menu-icon">₿</div>
                <p>Request free test coins to your Signet wallet address.</p>
            </button>
            <button class="menu-card" onclick="showSection('lightningSection')">
                <h2>Lightning Signet Faucet</h2>
                <div class="menu-icon">⚡</div>
                <p class="subtext">Coming soon</p>
            </button>
        </div>

        <div class="section-wrapper hidden" id="lightningSection">
            <button class="back-button" onclick="showSection('homeMenu')">← Back to networks</button>
            <h2>Lightning Signet Faucet</h2>
            <div class="menu-icon">⚡</div>
            <p>This feature is coming soon. Stay tuned for Lightning on Signet.</p>
        </div>

        <div class="section-wrapper hidden" id="faucetSection">
            <button class="back-button" onclick="showSection('homeMenu')">← Back to networks</button>
            <p>Enter your Signet address below to receive 0.001 test BTC. One request per device every 12 hours.</p>
            <p style="font-size:0.95rem;">First time here? <a href="#" onclick="showSection('guideSection'); return false;">Read the setup guide →</a></p>
            <form method="post">
                <label for="address">Signet Address:</label>
                <input type="text" id="address" name="address" placeholder="tb1..." required>
                <button type="submit">Get Coins</button>
            </form>
            {% if message %}
            <div class="message {{ 'success' if success else 'error' }}">
                {{ message }}
                {% if hint %}
                <button class="hint-btn" onclick="toggleHint()">?</button>
                {% endif %}
            </div>
            {% if hint %}
            <div class="hint-box" id="hintBox">{{ hint }}</div>
            {% endif %}
            {% endif %}
            <p>Explore transactions on <a href="https://explorer.bc-2.jp/" target="_blank">Signet Explorer</a> or <a href="https://mempool.space/signet/" target="_blank">Mempool Space</a></p>
        </div>
        <div class="section-wrapper hidden" id="guideSection">
            <button class="back-button" onclick="showSection('faucetSection')">← Back to faucet</button>
            <p>Signet is a safe Bitcoin test network. Follow these steps to set it up — no experience needed.</p>
            <p><strong>Step-by-step setup guide:</strong></p>
            <ol>
                <li><strong>Download Bitcoin Core:</strong> Go to <a href="https://bitcoin.org/en/download" target="_blank">bitcoin.org</a>, download the version for your operating system (Windows, Mac, or Linux), and install it like any other program. Bitcoin Core is the official Bitcoin software — it's free and open source.</li>
                <li><strong>Find your Bitcoin data folder:</strong> This is where Bitcoin stores its files.
                    <ul style="margin-top:8px;">
                        <li><strong>Windows:</strong> Press Win+R, type <code>%APPDATA%\Bitcoin</code> and press Enter.</li>
                        <li><strong>Mac:</strong> Open Finder, press Cmd+Shift+G, type <code>~/Library/Application Support/Bitcoin</code>.</li>
                        <li><strong>Linux:</strong> Open your file manager, go to your home folder, press Ctrl+H to show hidden files, then open the <code>.bitcoin</code> folder.</li>
                    </ul>
                </li>
                <li><strong>Create a bitcoin.conf file:</strong> Inside that folder, create a new text file named exactly <code>bitcoin.conf</code> (no .txt extension). Open it with any text editor, paste the settings below, and save.
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; position: relative;">
                        <pre id="bitcoin-conf" style="margin: 0; white-space: pre-wrap;">signet=1
server=1
txindex=1
rpcuser=youruser
rpcpassword=yourpass
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
signetchallenge=512103da0ee65a81d9d035a9bfff4810c5065d647153f3396b1fde56158cdf04bbace451ae
dnsseed=0
addnode=86.104.228.47:38333</pre>
                        <button onclick="copyToClipboard('bitcoin-conf')" style="position: absolute; top: 10px; right: 10px; background: #f7931a; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Copy</button>
                    </div>
                </li>
                <li><strong>Open a terminal:</strong> A terminal lets you type commands directly to your computer.
                    <ul style="margin-top:8px;">
                        <li><strong>Windows:</strong> Press Win+R, type <code>cmd</code>, press Enter.</li>
                        <li><strong>Mac:</strong> Press Cmd+Space, type <code>Terminal</code>, press Enter.</li>
                        <li><strong>Linux:</strong> Search for "Terminal" in your apps, or press Ctrl+Alt+T.</li>
                    </ul>
                </li>
                <li><strong>Start Bitcoin Core on Signet:</strong> In the terminal, type the command below and press Enter. Bitcoin Core will start syncing in the background — this takes a few minutes the first time.
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; position: relative;">
                        <pre id="start-cmd" style="margin: 0;">bitcoind -signet -daemon</pre>
                        <button onclick="copyToClipboard('start-cmd')" style="position: absolute; top: 10px; right: 10px; background: #f7931a; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Copy</button>
                    </div>
                </li>
                <li><strong>Create a wallet:</strong> Think of this like opening a bank account — it stores your test coins. Type the command below and press Enter.
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; position: relative;">
                        <pre id="wallet-cmd" style="margin: 0;">bitcoin-cli -signet createwallet mywallet</pre>
                        <button onclick="copyToClipboard('wallet-cmd')" style="position: absolute; top: 10px; right: 10px; background: #f7931a; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Copy</button>
                    </div>
                </li>
                <li><strong>Get a receive address:</strong> An address is like your account number — share it so others can send you coins. Type the command below and copy the address that appears.
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; position: relative;">
                        <pre id="addr-cmd" style="margin: 0;">bitcoin-cli -signet -rpcwallet=mywallet getnewaddress</pre>
                        <button onclick="copyToClipboard('addr-cmd')" style="position: absolute; top: 10px; right: 10px; background: #f7931a; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Copy</button>
                    </div>
                </li>
                <li><strong>Get your test coins:</strong> <a href="#" onclick="showSection('faucetSection'); return false;">Go to the faucet →</a>, paste your address, and click "Get Coins" to receive 0.001 signet BTC.</li>
            </ol>
        </div>
    </div>
    <script>
        function toggleHint() {
            const box = document.getElementById('hintBox');
            if (box) box.style.display = box.style.display === 'block' ? 'none' : 'block';
        }
        function copyToClipboard(id) {
            const text = document.getElementById(id).textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        }
        function hideAllSections() {
            ['homeMenu','lightningSection','faucetSection','guideSection'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
        }
        function showSection(id) {
            hideAllSections();
            document.getElementById(id).classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def faucet():
    message = None
    hint = None
    success = False
    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        ip = request.remote_addr
        if not address:
            message = "Please enter an address."
            hint = "A Signet address is a string of letters and numbers that identifies your test wallet. It usually starts with 'tb1'. Follow the Setup Guide to create one."
        else:
            rpc = get_rpc_connection()
            if not validate_address(rpc, address):
                message = "Invalid Signet address."
                hint = "A valid Signet address starts with 'tb1' and is about 42 characters long. Make sure you copied it correctly from your wallet. Do not use a mainnet Bitcoin address here."
            elif not check_rate_limit(ip):
                message = f"Rate limit: One request per {RATE_LIMIT_HOURS} hours per IP."
                hint = f"To keep the faucet fair for everyone, each device can only request coins once every {RATE_LIMIT_HOURS} hours. Please try again later."
            else:
                try:
                    balance = rpc.getbalance()
                    if balance < AMOUNT:
                        message = f"Insufficient funds. Balance: {balance} signet BTC"
                        hint = "The faucet wallet has run low on test coins. Please check back later — it will be topped up soon."
                    else:
                        txid = send_coins(rpc, address)
                        if txid and not txid.startswith('error'):
                            update_rate_limit(ip)
                            message = f"Sent {AMOUNT} signet BTC to {address}. Transaction ID: {txid}"
                            hint = "A Transaction ID (TXID) is a unique code for your transaction. You can paste it into the Signet Explorer to track it. Your coins will appear in your wallet once the next block is mined."
                            success = True
                        else:
                            message = f"Transaction failed: {txid}"
                            hint = "Something went wrong while sending the coins. This can happen if the node is busy or restarting. Please try again in a few minutes."
                except Exception as e:
                    message = f"Error: {str(e)}"
                    hint = "An unexpected error occurred. Please try again. If the problem persists, the node may be offline or restarting."
    return render_template_string(HTML_TEMPLATE, message=message, hint=hint, success=success)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)