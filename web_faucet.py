#!/usr/bin/env python3
"""
Web Bitcoin Signet Faucet
A simple web interface for the Signet faucet to onboard newbies.
"""

import os
import random
from flask import Flask, request, render_template_string, session, redirect, url_for
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

app = Flask(__name__)
app.secret_key = 'signet-faucet-key-x9f2z'

# RPC connection
RPC_USER = 'devuser'
RPC_PASSWORD = 'devpass123'
RPC_HOST = '::1'
RPC_PORT = 38332
RPC_WALLET = 'test-wallet'

# Faucet settings
AMOUNT = 0.001

def get_rpc_connection():
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@[{RPC_HOST}]:{RPC_PORT}/wallet/{RPC_WALLET}")

def validate_address(rpc, address):
    try:
        info = rpc.validateaddress(address)
        return info['isvalid'] and not info.get('isscript', False)
    except:
        return False

def generate_captcha():
    code = str(random.randint(1000, 9999))
    session['captcha'] = code
    return code

def verify_captcha(user_input):
    return user_input.strip() == session.get('captcha', '')

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
        .captcha-box {
            display: inline-block;
            background: #f0f0f0;
            border: 2px dashed #f7931a;
            border-radius: 8px;
            padding: 12px 30px;
            font-size: 2.6rem;
            font-weight: bold;
            letter-spacing: 16px;
            color: #222;
            margin: 10px 0 6px;
            user-select: none;
            font-family: 'Courier New', monospace;
        }
        .captcha-label {
            font-size: 0.9rem;
            color: #777;
            margin-bottom: 4px;
        }
        .ui-guide {
            margin: 16px 0 8px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .ui-step {
            display: flex;
            gap: 16px;
            align-items: flex-start;
        }
        .ui-step-label {
            background: #f7931a;
            color: white;
            font-weight: bold;
            font-size: 0.8rem;
            border-radius: 50%;
            min-width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 4px;
        }
        .ui-step-content {
            flex: 1;
        }
        .ui-step-content p {
            margin: 0 0 8px;
            font-size: 0.93rem;
        }
        .ui-mockup {
            background: #f0f0f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 18px rgba(0,0,0,0.2);
            font-family: 'Segoe UI', sans-serif;
            font-size: 0.85rem;
            color: #222;
            max-width: 540px;
            border: 1px solid #bbb;
        }
        .ui-titlebar {
            background: #e0e0e0;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #bbb;
        }
        .ui-titlebar-text {
            flex: 1;
            font-size: 0.78rem;
            color: #555;
        }
        .ui-win-btn {
            width: 16px; height: 16px;
            border-radius: 3px;
            background: #c0c0c0;
            border: 1px solid #999;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.65rem;
            color: #555;
            margin-left: 3px;
        }
        .ui-menubar {
            background: #f5f5f5;
            padding: 3px 10px;
            display: flex;
            gap: 2px;
            border-bottom: 1px solid #ccc;
        }
        .ui-menu-item {
            padding: 3px 10px;
            border-radius: 3px;
            cursor: default;
            color: #333;
            font-size: 0.82rem;
        }
        .ui-menu-item.active {
            background: #d0d8e8;
            color: #000;
        }
        .ui-sparrow-layout {
            display: flex;
            min-height: 200px;
        }
        .ui-sidebar {
            background: #2196c4;
            width: 80px;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 10px;
            gap: 0;
        }
        .ui-sidebar-item {
            width: 100%;
            padding: 12px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            color: rgba(255,255,255,0.7);
            font-size: 0.72rem;
            cursor: default;
        }
        .ui-sidebar-item.active {
            background: #1a6f9a;
            color: white;
        }
        .ui-sidebar-icon { font-size: 1.2rem; }
        .ui-content {
            flex: 1;
            background: white;
            padding: 16px 18px;
        }
        .ui-content h4 {
            margin: 0 0 10px;
            font-size: 0.95rem;
            color: #222;
        }
        .ui-type-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
        }
        .ui-type-label {
            font-size: 0.82rem;
            color: #444;
            min-width: 40px;
        }
        .ui-server-types {
            display: flex;
            gap: 4px;
        }
        .ui-server-btn {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            border: 1px solid #bbb;
            background: #f0f0f0;
            color: #555;
            cursor: default;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .ui-server-btn.active {
            background: #e8e8e8;
            border-color: #888;
            color: #222;
            font-weight: bold;
        }
        .ui-dot { width:9px; height:9px; border-radius:50%; display:inline-block; }
        .ui-dot-y { background:#e6a817; }
        .ui-dot-g { background:#4caf50; }
        .ui-dot-b { background:#2196c4; }
        .ui-field {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 9px;
        }
        .ui-field label {
            font-size: 0.78rem;
            color: #555;
            min-width: 70px;
            text-align: right;
        }
        .ui-input {
            background: white;
            border: 1px solid #bbb;
            border-radius: 3px;
            padding: 4px 8px;
            color: #222;
            font-size: 0.78rem;
            width: 140px;
            display: inline-block;
        }
        .ui-input.highlight {
            border-color: #2196c4;
            box-shadow: 0 0 0 2px rgba(33,150,196,0.2);
        }
        .ui-input.short { width: 55px; }
        .ui-dropdown-field {
            background: white;
            border: 1px solid #bbb;
            border-radius: 3px;
            padding: 4px 8px;
            color: #222;
            font-size: 0.78rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            min-width: 180px;
        }
        .ui-dropdown-field span { flex:1; }
        .ui-btn-test {
            margin-top: 10px;
            background: #f0f0f0;
            color: #333;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 5px 14px;
            font-size: 0.78rem;
            cursor: default;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .ui-connected {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            font-size: 0.78rem;
            color: #2e7d32;
            font-weight: bold;
        }
        .ui-dropdown-list {
            background: white;
            border: 1px solid #bbb;
            border-radius: 3px;
            min-width: 200px;
            display: inline-block;
            margin-top: -4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        }
        .ui-dropdown-list div {
            padding: 5px 12px;
            font-size: 0.78rem;
            color: #333;
        }
        .ui-dropdown-list div.selected {
            background: #d0e8f5;
            color: #111;
        }
        .ui-arrow { font-size: 1.1rem; }
        .faq-item {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 8px;
            overflow: hidden;
        }
        .faq-question {
            width: 100%;
            background: #f8f8f8;
            border: none;
            padding: 12px 16px;
            text-align: left;
            font-size: 0.92rem;
            font-weight: bold;
            color: #333;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
            box-shadow: none;
            transform: none;
            border-radius: 0;
        }
        .faq-question:hover {
            background: #f0f0f0;
            transform: none;
            box-shadow: none;
        }
        .faq-answer {
            display: none;
            padding: 12px 16px;
            font-size: 0.88rem;
            color: #555;
            line-height: 1.6;
            border-top: 1px solid #e0e0e0;
            background: white;
        }
        .intro-box {
            background: #fff8e1;
            border-left: 5px solid #f7931a;
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 16px;
            color: #555;
            line-height: 1.7;
        }
        .courses-section {
            margin-bottom: 24px;
        }
        .courses-section h3 {
            color: #d35400;
            margin: 0 0 12px;
            font-size: 1.05rem;
        }
        .course-cards {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .course-card {
            background: white;
            border: 2px solid rgba(247, 147, 26, 0.3);
            border-radius: 12px;
            padding: 16px;
            text-decoration: none;
            color: #333;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .course-card:hover {
            transform: translateY(-3px);
            border-color: #f7931a;
            box-shadow: 0 6px 18px rgba(247,147,26,0.15);
            text-decoration: none;
            color: #333;
        }
        .course-card .course-num {
            font-size: 0.75rem;
            font-weight: bold;
            color: #f7931a;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .course-card .course-title {
            font-size: 0.95rem;
            font-weight: bold;
            color: #333;
            line-height: 1.4;
        }
        .course-card .course-desc {
            font-size: 0.82rem;
            color: #777;
            line-height: 1.5;
        }
        @media (max-width: 600px) {
            .course-cards {
                grid-template-columns: 1fr;
            }
        }
        @media (max-width: 768px) {
            .main-menu {
                grid-template-columns: 1fr;
            }
        }
        .success-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.55);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            cursor: pointer;
            overflow: hidden;
        }
        .success-popup {
            background: white;
            border-radius: 24px;
            border: 3px solid #f7931a;
            padding: 40px 50px;
            text-align: center;
            position: relative;
            min-width: 300px;
            max-width: 420px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            animation: popup-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1001;
        }
        @keyframes popup-in {
            from { transform: scale(0.4); opacity: 0; }
            to   { transform: scale(1);   opacity: 1; }
        }
        .popup-emoji {
            font-size: 4rem;
            display: block;
            animation: bounce 0.6s ease infinite alternate;
        }
        @keyframes bounce {
            from { transform: translateY(0); }
            to   { transform: translateY(-10px); }
        }
        .popup-title {
            font-size: 1.7rem;
            font-weight: bold;
            color: #f7931a;
            margin: 14px 0 8px;
        }
        .popup-sub {
            color: #555;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .popup-close {
            margin-top: 18px;
            font-size: 0.82rem;
            color: #bbb;
        }
        .firework {
            position: fixed;
            pointer-events: none;
            z-index: 1002;
        }
        .spark {
            position: fixed;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 1002;
        }
        .os-tab-btn {
            background: #f0f0f0;
            color: #555;
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 12px 22px;
            font-size: 0.95rem;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s, border-color 0.2s, color 0.2s;
            box-shadow: none;
            transform: none;
            min-width: 120px;
            min-height: 44px;
        }
        @media (max-width: 420px) {
            .os-tab-btn { flex: 1; min-width: 0; padding: 12px 8px; font-size: 0.88rem; }
        }
        .os-tab-btn:hover {
            background: #fff3e0;
            border-color: #f7931a;
            color: #f7931a;
            transform: none;
            box-shadow: none;
        }
        .os-tab-btn.active {
            background: #f7931a;
            color: white;
            border-color: #f7931a;
        }
        .addr-preview {
            font-size: 0.83rem;
            margin: -8px 0 10px;
            padding: 7px 12px;
            border-radius: 6px;
            display: none;
        }
        .addr-preview.ok  { background: #f0fff4; color: #2e7d32; border-left: 3px solid #4caf50; }
        .addr-preview.bad { background: #fff3cd; color: #856404; border-left: 3px solid #f7931a; }
        .os-warning {
            background: #fff3cd;
            border-left: 4px solid #f7931a;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 10px 0;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Signet Faucet Hub</h1>
        <div class="intro-box">
            <strong>What is this?</strong> This is a Signet faucet — a tool that sends you free test Bitcoin so you can practise using it safely. Signet is a practice version of Bitcoin that works exactly the same way, but the coins have no real value. You can send, receive, and experiment freely without risking any money.
        </div>
        <div class="courses-section">
            <h3>&#127891; New to Bitcoin? We recommend starting with these free courses:</h3>
            <div class="course-cards">
                <a class="course-card" href="https://planb.academy/en/courses/the-bitcoin-journey-2b7dc507-81e3-4b70-88e6-41ed44239966" target="_blank">
                    <span class="course-num">Course 1</span>
                    <span class="course-title">The Bitcoin Journey</span>
                    <span style="font-size:0.75rem; color:#bbb;">↗ opens in new tab</span>
                    <span class="course-desc">Understand what Bitcoin is, how it works, and why it matters — from scratch.</span>
                </a>
                <a class="course-card" href="https://planb.academy/en/courses/getting-your-first-bitcoins-f3e3843d-1a1d-450c-96d6-d7232158b81f" target="_blank">
                    <span class="course-num">Course 2</span>
                    <span class="course-title">Getting Your First Bitcoins</span>
                    <span style="font-size:0.75rem; color:#bbb;">↗ opens in new tab</span>
                    <span class="course-desc">Learn how to safely acquire and store Bitcoin for the first time.</span>
                </a>
                <a class="course-card" href="https://planb.academy/en/courses/setting-up-your-first-bitcoin-node-3cd9cb94-82e8-417a-9c5a-02afc2589426" target="_blank">
                    <span class="course-num">Course 3</span>
                    <span class="course-title">Setting Up Your First Bitcoin Node</span>
                    <span style="font-size:0.75rem; color:#bbb;">↗ opens in new tab</span>
                    <span class="course-desc">Run your own Bitcoin node — exactly what powers this faucet.</span>
                </a>
            </div>
        </div>
        <p>Ready to get started? Choose a network below.</p>

        <div class="main-menu" id="homeMenu">
            <button class="menu-card" onclick="showSection('bitcoinSection')">
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

        <div class="section-wrapper hidden" id="bitcoinSection">
            <button class="back-button" onclick="showSection('homeMenu')">← Back</button>
            <h2>Bitcoin Signet Faucet</h2>
            <p>Do you already have a Signet wallet set up?</p>
            <div class="main-menu">
                <button class="menu-card" onclick="showSection('faucetSection')">
                    <h2>I have a wallet</h2>
                    <div class="menu-icon">👛</div>
                    <p>I already have a Signet wallet and just need test coins.</p>
                </button>
                <button class="menu-card" onclick="showSection('newUserSection')">
                    <h2>I'm new here</h2>
                    <div class="menu-icon">🚀</div>
                    <p>I need to set up a wallet and get started on Signet.</p>
                </button>
            </div>
        </div>

        <div class="section-wrapper hidden" id="lightningSection">
            <button class="back-button" onclick="showSection('homeMenu')">← Back</button>
            <h2>Lightning Signet Faucet</h2>
            <div class="menu-icon">⚡</div>
            <p>This feature is coming soon. Stay tuned for Lightning on Signet.</p>
        </div>

        <div class="section-wrapper hidden" id="faucetSection">
            <button class="back-button" onclick="showSection('bitcoinSection')">← Back</button>
            <p>Enter your Signet address below to receive 0.001 test BTC.</p>
            <form method="post" autocomplete="off">
                <label for="address">Signet Address:</label>
                <input type="text" id="address" name="address" placeholder="tb1..." required autocomplete="off" oninput="previewAddress(this.value)">
                <div id="addrPreview" class="addr-preview"></div>
                <p style="font-size:0.85rem; color:#777; margin:-4px 0 12px;">Find this in the <strong>Receive</strong> tab of your wallet. It starts with <code>tb1</code>, for example: <code>tb1q3x7k2m...</code> &nbsp;<a href="#" onclick="showSection('newUserSection'); return false;" style="font-size:0.82rem;">Don't have a wallet yet?</a></p>
                <p class="captcha-label">Type the code below to confirm you're human:</p>
                <div class="captcha-box">{{ captcha_code }}</div>
                <input type="text" id="captcha" name="captcha" placeholder="Enter the 4-digit code" maxlength="4" required autocomplete="off">
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
            <div style="background:#f0fff4; border-left:4px solid #4caf50; border-radius:8px; padding:14px 18px; margin:16px 0;">
                <strong>&#127381; What can you do with your test coins?</strong>
                <ul style="margin:8px 0 0; padding-left:20px; background:none; border:none; color:#555;">
                    <li>Send them to a friend's Signet address to practise a real Bitcoin transaction</li>
                    <li>Try sending a small amount back to a different address in your own wallet</li>
                    <li>Paste the Transaction ID into the Signet Explorer to watch it confirm in real time</li>
                    <li>These coins have no real value — experiment freely and make mistakes safely</li>
                </ul>
            </div>
        </div>
        <div class="section-wrapper hidden" id="newUserSection">
            <button class="back-button" onclick="showSection('bitcoinSection')">← Back</button>
            <h2>Choose your setup path</h2>
            <p>Both options get you a working Signet wallet. Pick the one that suits you best.</p>
            <div class="main-menu">
                <button class="menu-card" onclick="showSection('sparrowSection')">
                    <h2>Easy — Sparrow Wallet</h2>
                    <div class="menu-icon">🪟</div>
                    <p>A beginner-friendly desktop wallet with a visual interface. No command line needed.</p>
                    <p class="subtext">Recommended for most people</p>
                </button>
                <button class="menu-card" onclick="showSection('guideSection')">
                    <h2>Advanced — Bitcoin Core</h2>
                    <div class="menu-icon">⌨️</div>
                    <p>Run the full Bitcoin node directly. Uses the command line. More control, more to learn.</p>
                    <p class="subtext">For those who want to go deeper</p>
                </button>
            </div>
        </div>

        <div class="section-wrapper hidden" id="sparrowSection">
            <button class="back-button" onclick="showSection('newUserSection')">← Back</button>
            <h2>Easy Setup — Sparrow Wallet</h2>

            <p>Sparrow is a free desktop Bitcoin wallet with a clear visual interface — no command line needed. We will walk you through two things: installing Sparrow, and then switching it to practice mode (Signet) so you can use this faucet safely.</p>

            <div style="background:#fff8e1; border-left:4px solid #f7931a; border-radius:8px; padding:14px 18px; margin:16px 0;">
                <strong>Before you start — what do you need?</strong>
                <ul style="margin:8px 0 0; padding-left:20px; background:none; border:none;">
                    <li>A computer running Windows, macOS, or Linux</li>
                    <li>An internet connection</li>
                    <li>About 15 minutes</li>
                </ul>
            </div>

            <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:14px 18px; margin:16px 0;">
                <strong>What is a node?</strong>
                <p style="margin:8px 0 0;">A Bitcoin node is like a connection to the Bitcoin network — it checks transactions and keeps everything in sync. Sparrow needs to connect to one to work. Don't worry, you don't need to run your own for now. We will connect Sparrow to a trusted node from a list, which is fine for practice.</p>
            </div>

            <div style="margin:24px 0 10px;">
                <p style="margin-bottom:10px; font-weight:bold;">&#128187; Select your operating system — the guide will update automatically:</p>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <button class="os-tab-btn" data-os="windows" onclick="selectOS('windows')">🪟 Windows</button>
                    <button class="os-tab-btn" data-os="macos" onclick="selectOS('macos')">🍎 macOS</button>
                    <button class="os-tab-btn" data-os="linux" onclick="selectOS('linux')">🐧 Linux</button>
                </div>
            </div>

            <p style="margin-top:20px;"><strong>Step 1 — Download and install Sparrow Wallet</strong></p>
            <p>Go to <a href="https://sparrowwallet.com/download/" target="_blank">sparrowwallet.com/download</a> and download the version for your system. Here is what to look for and how to install it:</p>

            <div data-os="windows" style="margin-top:10px;">
                <ul>
                    <li>Download the <code>.exe</code> installer</li>
                    <li>Run it and click through the installer — you can leave all default options as they are</li>
                    <li>Once installed, open <strong>Sparrow Wallet</strong> from the Start menu</li>
                </ul>
                <div class="os-warning">&#128272; <strong>Windows Defender warning:</strong> Windows may flag the installer as unknown software. This is normal for open-source apps. You can verify the download is genuine using the checksum listed on the Sparrow download page. Click <em>More info → Run anyway</em> to proceed.</div>
            </div>
            <div data-os="macos" style="margin-top:10px;">
                <ul>
                    <li>Download the <code>.dmg</code> file</li>
                    <li>Open the .dmg, then drag the Sparrow app into your Applications folder</li>
                    <li>First time you open it, macOS may say "unidentified developer" — right-click the app icon and choose <strong>Open</strong> to bypass this once</li>
                </ul>
            </div>
            <div data-os="linux" style="margin-top:10px;">
                <ul>
                    <li>Download the <code>.deb</code> package (for Debian/Ubuntu) or the <code>.tar.gz</code> archive for other distributions</li>
                    <li>For the .deb package, install it with:</li>
                </ul>
                <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0; position:relative;">
                    <pre id="sparrow-deb" style="margin:0; font-size:0.85rem;">sudo dpkg -i sparrow-*.deb</pre>
                    <button onclick="copyToClipboard('sparrow-deb')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
                <p style="color:#777; font-size:0.88rem;">After installing, launch Sparrow from your applications menu or by running <code>sparrow</code> in a terminal.</p>
            </div>

            <p style="margin-top:16px;">For a full walkthrough with screenshots, the Plan B Academy tutorial covers the installation in detail. <strong>Stop when you reach "Server Configuration" or "Connect to a node" — then come back here and continue from Step 2.</strong></p>
            <div style="margin:12px 0 4px;">
                <a href="https://planb.academy/en/tutorials/wallet/desktop/sparrow-c674e2ac-d46f-4c82-92a7-7d1b0e262f5d" target="_blank"
                   style="display:inline-flex; align-items:center; gap:10px; background: linear-gradient(135deg, #f7931a, #ff9800); color:white; padding:14px 24px; border-radius:10px; font-weight:bold; font-size:1rem; text-decoration:none;">
                    &#127891; Open the Sparrow Wallet Tutorial on Plan B Academy
                </a>
            </div>

            <p style="margin-top:24px;"><strong>Step 2 — Switch Sparrow to Signet (practice mode)</strong></p>
            <p>By default Sparrow is set up for real Bitcoin. We need to switch it to Signet — the practice network — so everything you do here stays safe and costs nothing.</p>
            <p>In Sparrow, click <strong>Tools</strong> in the top menu, then hover over <strong>Restart in</strong>, and click <strong>Signet</strong>. <em>Don't worry — this is normal. Sparrow is just restarting in Signet mode, nothing is lost.</em></p>
            <div class="ui-guide">
                <div class="ui-step">
                    <div class="ui-step-label">A</div>
                    <div class="ui-step-content">
                        <p>Click <strong>Tools</strong> in the top menu, hover over <strong>Restart in</strong>, then click <strong>Signet</strong>.</p>
                        <img src="/static/sparrow-restart-signet.png" alt="Sparrow Tools menu showing Restart in Signet" style="max-width:480px; border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,0.18); border:1px solid #ccc;">
                    </div>
                </div>
            </div>
            <div style="background:#f0fff4; border-left:4px solid #4caf50; border-radius:8px; padding:12px 16px; margin:10px 0;">
                <strong>✓ How to confirm it worked:</strong> After Sparrow restarts, look at the title bar at the very top of the window. It should now say <strong>Sparrow [Signet]</strong> instead of just <strong>Sparrow</strong>. If you see that, you are in practice mode and ready to continue.
            </div>

            <p style="margin-top:24px;"><strong>Step 3 — Connect Sparrow to a Bitcoin node</strong></p>
            <p>Now we need to point Sparrow at a node so it can see the Signet network.</p>
            <div class="ui-guide">
                <div class="ui-step">
                    <div class="ui-step-label">A</div>
                    <div class="ui-step-content">
                        <p>Click <strong>File</strong> in the top menu bar, then click <strong>Settings...</strong> near the bottom of the list.</p>
                        <img src="/static/sparrow-file-menu.png" alt="Sparrow File menu showing Settings option" style="max-width:300px; border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,0.18); border:1px solid #ccc;">
                    </div>
                </div>
                <div class="ui-step">
                    <div class="ui-step-label">B</div>
                    <div class="ui-step-content">
                        <p>A settings window opens. Click <strong>Server</strong> in the left sidebar. Then under <strong>Type</strong>, click <strong>Bitcoin Core</strong>.</p>
                        <p style="color:#777; font-size:0.9rem;">You will see three options: Public Server, Bitcoin Core, and Private Electrum. <strong>Bitcoin Core is the best available option for this task.</strong></p>
                        <img src="/static/sparrow-server-settings.png" alt="Sparrow Server settings with Bitcoin Core selected" style="max-width:480px; border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,0.18); border:1px solid #ccc;">
                    </div>
                </div>
                <div class="ui-step">
                    <div class="ui-step-label">C</div>
                    <div class="ui-step-content">
                        <p>In the <strong>URL</strong> field, click the small arrow (▾) to open the dropdown and pick a Signet node from the list.</p>
                        <p style="color:#777; font-size:0.9rem;">If the list is empty or no Signet nodes appear, enter the details below manually. Set Authentication to <strong>User / Pass</strong> and fill in the fields as shown:</p>
                        <div style="background:#f8f9fa; border:1px solid #ddd; border-radius:8px; padding:14px 18px; margin:10px 0; font-size:0.88rem;">
                            <div style="display:grid; grid-template-columns:120px 1fr; gap:6px 12px; align-items:center;">
                                <span style="color:#777;">URL</span><code>86.104.228.47</code>
                                <span style="color:#777;">Port</span><code>38332</code>
                                <span style="color:#777;">Authentication</span><span>User / Pass</span>
                                <span style="color:#777;">Username</span><code>devuser</code>
                                <span style="color:#777;">Password</span><code>devpass123</code>
                            </div>
                        </div>
                        <p style="color:#777; font-size:0.9rem;">If you have your own Bitcoin node running, you can enter its details here instead.</p>
                    </div>
                </div>
                <div class="ui-step">
                    <div class="ui-step-label">D</div>
                    <div class="ui-step-content">
                        <p>Click the <strong>Test Connection</strong> button. If everything is correct you will see a green success message. If not, try selecting a different node from the dropdown and test again.</p>
                    </div>
                </div>
            </div>

            <p style="margin-top:24px;"><strong>Step 4 — Create your wallet</strong></p>
            <p>Go back to the Plan B Academy tutorial and continue from the <strong>"Creating a New Wallet"</strong> section. Since Sparrow is now in Signet mode, any wallet you create will be a practice wallet — perfect for testing.</p>

            <p style="margin-top:20px;"><strong>Step 5 — Get your receive address</strong></p>
            <p>In Sparrow, click the <strong>Receive</strong> tab — it is in the left sidebar of your open wallet. You will see a long string of letters and numbers — this is your Signet address. It will start with <code>tb1</code>, for example: <code>tb1q3x7k2m...</code>.</p>
            <p>You need to copy this address so you can paste it into the faucet. Here is how to do it:</p>

            <div data-os="windows" style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px; margin:10px 0;">
                <strong>🪟 Copying and pasting on Windows</strong>
                <ol style="margin:8px 0 0; padding-left:20px; background:none; border:none;">
                    <li>In Sparrow, click on the address to select it, or right-click it and choose <strong>Copy</strong></li>
                    <li>Alternatively, click the address once, then press <code>Ctrl + A</code> to select all, then <code>Ctrl + C</code> to copy</li>
                    <li>Go to the faucet page, click inside the address box, and press <code>Ctrl + V</code> to paste</li>
                </ol>
                <p style="margin:8px 0 0; font-size:0.88rem; color:#777;">Sparrow also has a small copy icon next to the address — clicking it copies it automatically.</p>
            </div>
            <div data-os="macos" style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px; margin:10px 0;">
                <strong>🍎 Copying and pasting on macOS</strong>
                <ol style="margin:8px 0 0; padding-left:20px; background:none; border:none;">
                    <li>In Sparrow, click on the address to select it, or right-click it and choose <strong>Copy</strong></li>
                    <li>Alternatively, click the address once, then press <code>Cmd + A</code> to select all, then <code>Cmd + C</code> to copy</li>
                    <li>Go to the faucet page, click inside the address box, and press <code>Cmd + V</code> to paste</li>
                </ol>
                <p style="margin:8px 0 0; font-size:0.88rem; color:#777;">Sparrow also has a small copy icon next to the address — clicking it copies it automatically.</p>
            </div>
            <div data-os="linux" style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px; margin:10px 0;">
                <strong>🐧 Copying and pasting on Linux</strong>
                <ol style="margin:8px 0 0; padding-left:20px; background:none; border:none;">
                    <li>In Sparrow, click on the address to select it, or right-click it and choose <strong>Copy</strong></li>
                    <li>Alternatively, click the address once, then press <code>Ctrl + A</code> to select all, then <code>Ctrl + C</code> to copy</li>
                    <li>Go to the faucet page, click inside the address box, and press <code>Ctrl + V</code> to paste</li>
                </ol>
                <p style="margin:8px 0 0; font-size:0.88rem; color:#777;">On Linux you can also highlight text with your mouse and middle-click anywhere in the address box to paste it directly.</p>
            </div>

            <p style="margin-top:20px;"><strong>Step 6 — Get your test coins</strong></p>
            <p><a href="#" onclick="showSection('faucetSection'); return false;">Go to the faucet →</a>, paste your address into the box, complete the code check, and click <strong>Get Coins</strong>.</p>

            <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:14px 18px; margin:16px 0;">
                <strong>What happens next?</strong>
                <p style="margin:8px 0 0;">Your coins won't appear instantly. The network needs to confirm your transaction first, which happens when the next block is mined — this usually takes a few minutes. You can track your transaction using the Transaction ID shown after you submit, and the Signet Explorer link on the faucet page.</p>
            </div>

            <div style="margin-top:20px;">
                <strong>&#128736; Troubleshooting — click a problem to see the fix</strong>
                <div style="margin-top:10px;">
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Test Connection failed <span>＋</span>
                        </button>
                        <div class="faq-answer">Make sure you selected or entered a Signet node, not a mainnet one. If entering manually, double-check the URL, port, and credentials. Also confirm Sparrow is running in Signet mode — the title bar should say <strong>Sparrow [Signet]</strong>.</div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Invalid address error on the faucet <span>＋</span>
                        </button>
                        <div class="faq-answer">Make sure you copied the full address from the Receive tab and that it starts with <code>tb1</code>. Do not use a mainnet Bitcoin address here — those start with <code>bc1</code> and will be rejected.</div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Coins not showing up in Sparrow <span>＋</span>
                        </button>
                        <div class="faq-answer">Wait a few minutes — coins only appear after the next block is mined on the network. If nothing arrives after 10 minutes, copy the Transaction ID shown on the faucet page and paste it into the Signet Explorer to check its status.</div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Sparrow shows "Disconnected" at the bottom <span>＋</span>
                        </button>
                        <div class="faq-answer">Your node connection dropped. Go to <strong>File → Settings → Server</strong>, click <strong>Test Connection</strong> again. If it still fails, try selecting a different node from the dropdown.</div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 28px; background: #fff3cd; border-left: 5px solid #f7931a; border-radius: 10px; padding: 16px 20px;">
                <strong>⚠️ Important — if you ever use Sparrow with real Bitcoin:</strong>
                <p style="margin: 10px 0 0;">For Signet practice, connecting to a third-party node is completely fine — the coins have no value. But if you switch to real Bitcoin, that node can see your wallet addresses and transaction history. For real funds, you should run your own Bitcoin node (Core, Knots, or another implementation) and ideally your own Electrum server alongside it. This keeps your finances private and means you are not trusting anyone else's infrastructure. The Plan B Academy has courses to help you get there when you are ready.</p>
            </div>
        </div>

        <div class="section-wrapper hidden" id="guideSection">
            <button class="back-button" onclick="showSection('newUserSection')">← Back</button>
            <h2>Advanced Setup — Run Your Own Bitcoin Node</h2>
            <p>Running your own Bitcoin node means your computer independently verifies every transaction and block on the network — you don't have to trust anyone else. It's the most private and self-sovereign way to use Bitcoin. This guide walks you through setting one up on Signet (the practice network) so you can learn safely.</p>

            <div style="background:#fff8e1; border-left:4px solid #f7931a; border-radius:8px; padding:14px 18px; margin:16px 0;">
                <strong>Before you start — what do you need?</strong>
                <ul style="margin:8px 0 0; padding-left:20px; background:none; border:none;">
                    <li>A computer running Windows, macOS, or Linux</li>
                    <li>About 30–60 minutes and a stable internet connection</li>
                    <li>Comfort using a terminal (command line) — we'll guide you through every step</li>
                </ul>
            </div>

            <div style="margin:24px 0 10px;">
                <p style="margin-bottom:10px; font-weight:bold;">&#128187; Select your operating system — the guide will update automatically:</p>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <button class="os-tab-btn" data-os="windows" onclick="selectOS('windows')">🪟 Windows</button>
                    <button class="os-tab-btn" data-os="macos" onclick="selectOS('macos')">🍎 macOS</button>
                    <button class="os-tab-btn" data-os="linux" onclick="selectOS('linux')">🐧 Linux</button>
                </div>
            </div>

            <p style="margin-top:20px;"><strong>Step 1 — Choose a Bitcoin node to install</strong></p>
            <p>There are several Bitcoin node implementations to choose from. They all follow the same rules and work on the same network — they just differ in features and philosophy. Pick one:</p>

            <div style="display:flex; flex-direction:column; gap:10px; margin:14px 0;">
                <div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px;">
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <strong>Bitcoin Core</strong>
                        <a href="https://bitcoincore.org/en/download/" target="_blank" style="font-size:0.82rem; background:#f7931a; color:white; padding:3px 10px; border-radius:12px; text-decoration:none;">Download</a>
                        <button class="hint-btn" style="color:#f7931a; border-color:#f7931a;" onclick="toggleInfo('info-core')">i</button>
                    </div>
                    <div id="info-core" class="hint-box">The original Bitcoin software, maintained since 2009. It is the most widely used implementation and the reference for the Bitcoin protocol. A solid default choice — well-tested and supported by a large developer community.</div>
                </div>
                <div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px;">
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <strong>Bitcoin Knots</strong>
                        <a href="https://bitcoinknots.org/" target="_blank" style="font-size:0.82rem; background:#f7931a; color:white; padding:3px 10px; border-radius:12px; text-decoration:none;">Download</a>
                        <button class="hint-btn" style="color:#f7931a; border-color:#f7931a;" onclick="toggleInfo('info-knots')">i</button>
                    </div>
                    <div id="info-knots" class="hint-box">A fork of Bitcoin Core with additional features and stricter defaults — for example it gives you more control over which transactions your node accepts and relays. Popular with users who want a bit more configurability. Compatible with everything Bitcoin Core supports.</div>
                </div>
                <div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px;">
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <strong>btcd</strong>
                        <a href="https://github.com/btcsuite/btcd" target="_blank" style="font-size:0.82rem; background:#f7931a; color:white; padding:3px 10px; border-radius:12px; text-decoration:none;">GitHub</a>
                        <button class="hint-btn" style="color:#f7931a; border-color:#f7931a;" onclick="toggleInfo('info-btcd')">i</button>
                    </div>
                    <div id="info-btcd" class="hint-box">A full Bitcoin node written in the Go programming language, maintained by the btcsuite team. Popular in developer environments and cloud deployments. A good choice if you are coming from a Go or DevOps background.</div>
                </div>
                <div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:10px; padding:14px 18px;">
                    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                        <strong>Libbitcoin</strong>
                        <a href="https://libbitcoin.info/" target="_blank" style="font-size:0.82rem; background:#f7931a; color:white; padding:3px 10px; border-radius:12px; text-decoration:none;">Website</a>
                        <button class="hint-btn" style="color:#f7931a; border-color:#f7931a;" onclick="toggleInfo('info-libbitcoin')">i</button>
                    </div>
                    <div id="info-libbitcoin" class="hint-box">An independent C++ implementation of Bitcoin, built as a toolkit for developers. Less common for everyday node running but valuable as a fully independent codebase — having multiple independent implementations strengthens the network's resilience.</div>
                </div>
            </div>
            <p style="color:#777; font-size:0.88rem; margin-top:4px;">Not sure which to pick? <strong>Bitcoin Core</strong> or <strong>Bitcoin Knots</strong> are the most beginner-friendly starting points. The steps below use commands that work for both.</p>

            <p style="margin-top:28px;"><strong>Step 2 — Download and install</strong></p>
            <p>Go to the download page for the node you chose and follow the steps for your system:</p>

            <div data-os="windows" style="margin-top:8px;">
                <ul>
                    <li>Download the <code>.exe</code> installer file</li>
                    <li>Run it and follow the on-screen steps — you can leave all default settings as they are</li>
                    <li>Bitcoin Core and Knots also install a visual app (Bitcoin-Qt) — you can open it to watch sync progress if you prefer</li>
                </ul>
                <div class="os-warning">&#128272; <strong>Windows Defender warning:</strong> Windows may flag the installer. This is a standard warning for software not signed by a large company. Bitcoin Core and Knots are open-source — you can verify the download is genuine using the checksums listed on the download page.</div>
            </div>
            <div data-os="macos" style="margin-top:8px;">
                <ul>
                    <li>Download the <code>.dmg</code> file</li>
                    <li>Open the .dmg, then drag the Bitcoin app into your Applications folder</li>
                    <li>First time you open it, macOS may say "unidentified developer" — right-click the app icon and choose <strong>Open</strong> to bypass this once</li>
                    <li>Bitcoin Core and Knots include a visual interface — you can open it from Applications to watch sync progress</li>
                </ul>
            </div>
            <div data-os="linux" style="margin-top:8px;">
                <ul>
                    <li>Download the <code>.tar.gz</code> archive for your CPU (usually <code>x86_64-linux-gnu</code>)</li>
                    <li>Extract it and copy the programs to <code>/usr/local/bin/</code> so you can run them from any terminal:</li>
                </ul>
                <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin:8px 0; position:relative;">
                    <pre id="linux-install" style="margin:0; font-size:0.85rem; white-space:pre-wrap;">tar -xzf bitcoin-*.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin bitcoin-*/bin/*</pre>
                    <button onclick="copyToClipboard('linux-install')" style="position:absolute; top:8px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
                <p style="color:#777; font-size:0.88rem;">Bitcoin Core and Knots also ship with <code>bitcoin-qt</code> (a visual interface) installed by the same command above.</p>
            </div>

            <p style="margin-top:28px;"><strong>Step 3 — Find (or create) your Bitcoin data folder</strong></p>
            <p>Your node stores its configuration and data in a specific folder. You need to put the settings file there in the next step.</p>

            <div data-os="windows" style="margin-top:8px;">
                <ol>
                    <li>Press <code>Win+R</code> to open the Run box</li>
                    <li>Type <code>%APPDATA%\Bitcoin</code> and press Enter</li>
                    <li>If a folder opens, you are in the right place. If Windows says "cannot find path", you need to create it manually: open File Explorer, navigate to <code>C:\\Users\\YourName\\AppData\\Roaming\\</code> and create a new folder named <code>Bitcoin</code></li>
                </ol>
            </div>
            <div data-os="macos" style="margin-top:8px;">
                <ol>
                    <li>Open Finder</li>
                    <li>Press <code>Cmd+Shift+G</code> to open the Go to Folder box</li>
                    <li>Type <code>~/Library/Application Support/Bitcoin</code> and press Enter</li>
                    <li>If the folder does not exist yet, navigate to <code>~/Library/Application Support/</code> and create a new folder named <code>Bitcoin</code></li>
                </ol>
            </div>
            <div data-os="linux" style="margin-top:8px;">
                <ol>
                    <li>Open your home folder in the file manager</li>
                    <li>Press <code>Ctrl+H</code> to show hidden folders (names starting with a dot)</li>
                    <li>Look for a folder named <code>.bitcoin</code></li>
                    <li>If it does not exist, create it — or run this command in a terminal:</li>
                </ol>
                <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0; position:relative;">
                    <pre id="linux-mkdir" style="margin:0; font-size:0.85rem;">mkdir -p ~/.bitcoin</pre>
                    <button onclick="copyToClipboard('linux-mkdir')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
            </div>

            <p style="margin-top:28px;"><strong>Step 4 — Create a bitcoin.conf file</strong></p>
            <p>Inside that folder, create a file named exactly <code>bitcoin.conf</code>. Open it in a plain text editor, paste the settings below, and save.</p>

            <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:12px 16px; margin:12px 0;">
                <strong>What are rpcuser and rpcpassword?</strong>
                <p style="margin:8px 0 0; font-size:0.9rem;">These are local-only credentials — they are not connected to any online account or service. Your node uses them to make sure only programs on your own computer can talk to it. You can set them to anything you like, for example <code>rpcuser=alice</code> and <code>rpcpassword=mypassword123</code>. Just make a note of what you choose, as you may need them later.</p>
            </div>

            <p><strong>Replace <code>youruser</code> and <code>yourpass</code> with your own values before saving.</strong></p>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin:10px 0; position:relative;">
                <pre id="bitcoin-conf" style="margin:0; white-space:pre-wrap;">signet=1
server=1
txindex=1
rpcuser=youruser
rpcpassword=yourpass
signetchallenge=512103da0ee65a81d9d035a9bfff4810c5065d647153f3396b1fde56158cdf04bbace451ae
dnsseed=0
addnode=86.104.228.47:38333</pre>
                <button onclick="copyToClipboard('bitcoin-conf')" style="position:absolute; top:10px; right:10px; background:#f7931a; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Copy</button>
            </div>

            <div data-os="windows">
                <div class="os-warning">&#9888; <strong>Windows tip — beware of the hidden .txt extension:</strong> Windows hides file extensions by default, so Notepad often secretly saves <code>bitcoin.conf</code> as <code>bitcoin.conf.txt</code> — and the node will not find it. To prevent this: in Notepad use <em>File → Save As</em>, change "Save as type" to <strong>All Files (*.*)</strong>, and type the filename as <code>bitcoin.conf</code>. To check afterwards, enable extensions in File Explorer via <em>View → Show → File name extensions</em>.</div>
            </div>
            <div data-os="macos">
                <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:12px 16px; margin:10px 0; font-size:0.9rem;">
                    &#128187; <strong>macOS tip:</strong> Use TextEdit but switch to plain text mode first: <em>Format → Make Plain Text</em>. Rich text (.rtf) will not work. Alternatively, use a code editor like VS Code or BBEdit which handle plain text by default.
                </div>
            </div>
            <div data-os="linux">
                <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:12px 16px; margin:10px 0; font-size:0.9rem;">
                    &#128039; <strong>Linux tip:</strong> You can create and edit the file directly in the terminal with nano:
                    <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                        <pre id="linux-conf-edit" style="margin:0; font-size:0.85rem;">nano ~/.bitcoin/bitcoin.conf</pre>
                        <button onclick="copyToClipboard('linux-conf-edit')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                    </div>
                    Paste the config above, then press <code>Ctrl+O</code> to save and <code>Ctrl+X</code> to exit.
                </div>
            </div>

            <p style="margin-top:28px;"><strong>Step 5 — Open a terminal</strong></p>

            <div data-os="windows" style="margin-top:8px;">
                <p>Press <code>Win+R</code>, type <code>cmd</code>, press Enter. A black window with a blinking cursor will appear — this is the Command Prompt.</p>
                <p style="color:#777; font-size:0.88rem;">You will need to navigate to the folder where Bitcoin was installed. By default this is <code>C:\Program Files\Bitcoin\daemon\</code>. In the Command Prompt, type:</p>
                <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0; position:relative;">
                    <pre id="win-cd" style="margin:0; font-size:0.85rem;">cd "C:\Program Files\Bitcoin\daemon"</pre>
                    <button onclick="copyToClipboard('win-cd')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
            </div>
            <div data-os="macos" style="margin-top:8px;">
                <p>Press <code>Cmd+Space</code>, type <code>Terminal</code>, press Enter. A window with a command prompt will appear.</p>
            </div>
            <div data-os="linux" style="margin-top:8px;">
                <p>Search for <strong>Terminal</strong> in your apps, or press <code>Ctrl+Alt+T</code>. Most Linux desktops have a terminal shortcut built in.</p>
            </div>

            <p style="margin-top:28px;"><strong>Step 6 — Start your node</strong></p>

            <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:12px 16px; margin:10px 0;">
                <strong>Prefer a visual interface?</strong> Bitcoin Core and Knots come with a graphical app — you can use it instead of (or alongside) the terminal.
                <span data-os="windows"> On Windows, find <strong>Bitcoin Core</strong> or <strong>Bitcoin Knots</strong> in the Start menu and open it.</span>
                <span data-os="macos"> On macOS, open <strong>Bitcoin Core</strong> or <strong>Bitcoin Knots</strong> from your Applications folder.</span>
                <span data-os="linux"> On Linux, run <code>bitcoin-qt -signet</code> in a terminal to open the graphical interface.</span>
                A progress bar will show how much of the network has synced. You can still use the terminal commands in the steps below while the GUI is running.
            </div>

            <p>To start your node in the background without a window, run the command below and press Enter:</p>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin:10px 0; position:relative;">
                <pre id="start-cmd" style="margin:0;">bitcoind -signet -daemon</pre>
                <button onclick="copyToClipboard('start-cmd')" style="position:absolute; top:10px; right:10px; background:#f7931a; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Copy</button>
            </div>

            <div style="background:#f0fff4; border-left:4px solid #4caf50; border-radius:8px; padding:12px 16px; margin:10px 0;">
                <strong>What syncing looks like:</strong> When your node starts for the first time it downloads the Signet blockchain — a record of all past practice transactions. You will see a block count climbing (for example <code>"blocks": 234</code> increasing over time) — that is completely normal. Signet is much smaller than real Bitcoin so this usually finishes in a few minutes. Leave your node running while it catches up before moving to the next step.
            </div>

            <div style="background:#f0f7ff; border-left:4px solid #2196c4; border-radius:8px; padding:12px 16px; margin:10px 0;">
                <strong>How to confirm it is running:</strong> Run the command below. If you see a response including <code>"chain": "signet"</code>, your node is up and syncing.
                <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                    <pre id="check-cmd" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet getblockchaininfo</pre>
                    <button onclick="copyToClipboard('check-cmd')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
            </div>

            <div style="background:#fff8e1; border-left:4px solid #f7931a; border-radius:8px; padding:12px 16px; margin:10px 0; font-size:0.9rem;">
                <strong>How to stop the node:</strong> Do not just close the terminal — the node keeps running in the background. To shut it down cleanly, run:
                <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                    <pre id="stop-cmd" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet stop</pre>
                    <button onclick="copyToClipboard('stop-cmd')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                </div>
            </div>

            <p style="margin-top:28px;"><strong>Step 7 — Create a wallet</strong></p>
            <p>A wallet stores your addresses and keeps track of your test coins — think of it like opening a bank account. Run the command below and press Enter.</p>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin:10px 0; position:relative;">
                <pre id="wallet-cmd" style="margin:0;">bitcoin-cli -signet createwallet mywallet</pre>
                <button onclick="copyToClipboard('wallet-cmd')" style="position:absolute; top:10px; right:10px; background:#f7931a; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Copy</button>
            </div>

            <p style="margin-top:28px;"><strong>Step 8 — Get a receive address</strong></p>
            <p>An address is like your account number — you give it to the faucet so it can send coins to you. Run the command below and copy the address that appears. It will start with <code>tb1</code>.</p>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin:10px 0; position:relative;">
                <pre id="addr-cmd" style="margin:0;">bitcoin-cli -signet -rpcwallet=mywallet getnewaddress</pre>
                <button onclick="copyToClipboard('addr-cmd')" style="position:absolute; top:10px; right:10px; background:#f7931a; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">Copy</button>
            </div>

            <p style="margin-top:28px;"><strong>Step 9 — Get your test coins</strong></p>
            <p><a href="#" onclick="showSection('faucetSection'); return false;">Go to the faucet →</a>, paste your address into the box, complete the code check, and click <strong>Get Coins</strong>. Your coins will appear in your wallet once the next block is mined — usually within a few minutes.</p>

            <div style="margin-top:28px;">
                <strong>&#128736; Troubleshooting — click a problem to see the fix</strong>
                <div style="margin-top:10px;">
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            "Could not connect to the server" when running bitcoin-cli <span>＋</span>
                        </button>
                        <div class="faq-answer">Your node is not running yet, or it's still starting up. Wait 30 seconds and try the command below again. If it still fails, double-check that <code>bitcoind -signet -daemon</code> ran without any error message.
                            <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                                <pre id="faq-check1" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet getblockchaininfo</pre>
                                <button onclick="copyToClipboard('faq-check1')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                            </div>
                        </div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            "bitcoind: command not found" <span>＋</span>
                        </button>
                        <div class="faq-answer">Bitcoin's programs are not in your system path. On Windows, navigate to the folder where you installed Bitcoin and run the command from there. On Mac or Linux, you may need to move the downloaded files to <code>/usr/local/bin/</code> or run them using their full path, e.g. <code>~/bitcoin/bin/bitcoind</code>.</div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Node is stuck at the same block count <span>＋</span>
                        </button>
                        <div class="faq-answer">It may still be connecting to peers. Give it 2–3 minutes. If it stays stuck, confirm your <code>bitcoin.conf</code> has the <code>addnode=86.104.228.47:38333</code> line — this is the peer that connects you to this Signet network. Also make sure you saved the file without a .txt extension.</div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            "Wallet not found" when creating a wallet <span>＋</span>
                        </button>
                        <div class="faq-answer">Make sure your node is fully started before running <code>createwallet</code>. Confirm it's ready by running the command below — if you see a response with <code>"chain": "signet"</code>, the node is up and wallet creation should work.
                            <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                                <pre id="faq-check2" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet getblockchaininfo</pre>
                                <button onclick="copyToClipboard('faq-check2')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                            </div>
                        </div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Invalid address error on the faucet <span>＋</span>
                        </button>
                        <div class="faq-answer">Make sure the address you copied starts with <code>tb1</code> — that is the format for Signet. A regular Bitcoin address starting with <code>bc1</code> will be rejected here. Run the command below again and copy the full output.
                            <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                                <pre id="faq-newaddr" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet -rpcwallet=mywallet getnewaddress</pre>
                                <button onclick="copyToClipboard('faq-newaddr')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                            </div>
                        </div>
                    </div>
                    <div class="faq-item">
                        <button class="faq-question" onclick="toggleFaq(this)">
                            Coins not appearing in my wallet <span>＋</span>
                        </button>
                        <div class="faq-answer">Coins only appear after the next block is confirmed on the network — this usually takes a few minutes. Run the command below to check your balance. If nothing shows after 10 minutes, copy the Transaction ID from the faucet page and check it on the Signet Explorer.
                            <div style="background:#f8f9fa; padding:8px 10px; border-radius:5px; margin:8px 0 0; position:relative;">
                                <pre id="faq-balance" style="margin:0; font-size:0.85rem;">bitcoin-cli -signet -rpcwallet=mywallet getbalance</pre>
                                <button onclick="copyToClipboard('faq-balance')" style="position:absolute; top:6px; right:8px; background:#f7931a; color:white; border:none; padding:4px 8px; border-radius:3px; cursor:pointer; font-size:0.8rem;">Copy</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-top: 28px; background: #fff3cd; border-left: 5px solid #f7931a; border-radius: 10px; padding: 16px 20px;">
                <strong>&#9888;&#65039; A note on privacy for real Bitcoin:</strong>
                <p style="margin: 10px 0 0;">On Signet everything is safe to experiment with. But when you move to real Bitcoin, running your own node means you verify transactions yourself without trusting anyone else — that is the real value. For the best privacy, pair your node with your own Electrum server (like Fulcrum or Electrs) so your wallet software doesn't leak your addresses to a third party. The Plan B Academy has courses to help you go further when you're ready.</p>
            </div>
        </div>
        <div style="text-align:center; margin-top:30px; padding-top:20px; border-top:1px solid #f0e0c8;">
            <p style="color:#aaa; font-size:0.85rem; margin-bottom:10px;">Need help or have a question?</p>
            <button style="background:transparent; border:2px solid #f7931a; color:#f7931a; border-radius:10px; padding:10px 24px; font-size:0.95rem; cursor:pointer; font-weight:bold;">
                &#9993; Contact Support
            </button>
            <div style="margin-top:18px; display:flex; flex-direction:column; align-items:center; gap:10px;">
                <a href="https://www.youtube.com/playlist?list=PLxdf8G0kzsUVxZHq3IY7ur_sM8w9TnqeN" target="_blank"
                   style="display:inline-flex; align-items:center; gap:8px; color:#f7931a; font-size:0.92rem; font-weight:bold; text-decoration:none;">
                    &#127909; Bitcoin video tutorials — YouTube playlist ↗
                </a>
                <a href="https://planb.academy/en/learn-anytime" target="_blank"
                   style="display:inline-flex; align-items:center; gap:8px; color:#f7931a; font-size:0.92rem; font-weight:bold; text-decoration:none;">
                    &#127891; Learn Bitcoin anytime — Plan B Academy ↗
                </a>
            </div>
        </div>
    </div>
    {% if success %}
    <div class="success-overlay" id="successOverlay" onclick="closePopup()">
        <div class="success-popup" id="successPopup">
            <span class="popup-emoji">🎉</span>
            <div class="popup-title">You got your Signet BTC!</div>
            <div class="popup-sub">0.001 signet BTC is on its way to your wallet.</div>
            <div class="popup-close">Click anywhere to close</div>
        </div>
    </div>
    {% endif %}

    <script>
        function closePopup() {
            const overlay = document.getElementById('successOverlay');
            if (overlay) overlay.style.display = 'none';
        }
        function launchFireworks() {
            const colors = ['#f7931a','#ff5722','#e91e63','#9c27b0','#2196f3','#4caf50','#ffeb3b','#ff9800'];
            function burst(x, y) {
                for (let i = 0; i < 14; i++) {
                    const spark = document.createElement('div');
                    spark.className = 'spark';
                    spark.style.background = colors[Math.floor(Math.random() * colors.length)];
                    spark.style.left = x + 'px';
                    spark.style.top = y + 'px';
                    document.body.appendChild(spark);
                    const angle = (i / 14) * 2 * Math.PI;
                    const dist = 60 + Math.random() * 100;
                    const tx = Math.cos(angle) * dist;
                    const ty = Math.sin(angle) * dist;
                    spark.animate([
                        { transform: 'translate(0,0) scale(1)', opacity: 1 },
                        { transform: `translate(${tx}px,${ty}px) scale(0)`, opacity: 0 }
                    ], { duration: 700 + Math.random() * 400, easing: 'ease-out', fill: 'forwards' })
                    .onfinish = () => spark.remove();
                }
            }
            let count = 0;
            const interval = setInterval(() => {
                if (count++ >= 8) { clearInterval(interval); return; }
                burst(
                    Math.random() * window.innerWidth,
                    Math.random() * window.innerHeight * 0.7
                );
            }, 350);
        }
        window.addEventListener('load', function() {
            try {
                selectOS(localStorage.getItem('preferred-os') || detectOS());
            } catch(e) { selectOS('windows'); }
            if (document.getElementById('successOverlay')) {
                const addrField = document.getElementById('address');
                if (addrField) { addrField.value = ''; previewAddress(''); }
                launchFireworks();
                setTimeout(closePopup, 5000);
                showSection('faucetSection');
            } else if (document.getElementById('hintBox') || document.querySelector('.message')) {
                showSection('faucetSection');
            }
        });
        function previewAddress(val) {
            const el = document.getElementById('addrPreview');
            if (!el) return;
            const v = val.trim();
            if (!v) { el.style.display = 'none'; return; }
            el.style.display = 'block';
            if (v.startsWith('tb1') && v.length >= 26) {
                el.className = 'addr-preview ok';
                el.textContent = '✓ Looks good: ' + v.slice(0, 12) + '...' + v.slice(-6);
            } else if (v.startsWith('bc1')) {
                el.className = 'addr-preview bad';
                el.textContent = '⚠ This looks like a real Bitcoin address (bc1...) — please use your Signet address (tb1...) instead.';
            } else {
                el.className = 'addr-preview bad';
                el.textContent = '⚠ A Signet address should start with tb1 and be about 42 characters long.';
            }
        }
        function detectOS() {
            const ua = navigator.userAgent || '';
            if (/Win/i.test(ua)) return 'windows';
            if (/Mac/i.test(ua)) return 'macos';
            return 'linux';
        }
        function selectOS(os) {
            document.querySelectorAll('.os-tab-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.os === os);
            });
            document.querySelectorAll('[data-os]').forEach(el => {
                const isSpan = el.tagName === 'SPAN';
                el.style.display = el.dataset.os === os ? (isSpan ? 'inline' : '') : 'none';
            });
            try { localStorage.setItem('preferred-os', os); } catch(e) {}
        }
        function toggleInfo(id) {
            const box = document.getElementById(id);
            if (box) box.style.display = box.style.display === 'block' ? 'none' : 'block';
        }
        function toggleFaq(btn) {
            const answer = btn.nextElementSibling;
            const icon = btn.querySelector('span');
            const isOpen = answer.style.display === 'block';
            answer.style.display = isOpen ? 'none' : 'block';
            icon.textContent = isOpen ? '＋' : '－';
        }
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
            ['homeMenu','bitcoinSection','lightningSection','faucetSection','newUserSection','sparrowSection','guideSection'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
        }
        function showSection(id) {
            hideAllSections();
            const el = document.getElementById(id);
            el.classList.remove('hidden');
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def faucet():
    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        captcha_input = request.form.get('captcha', '')
        if not address:
            session['result'] = {'message': "Please enter an address.", 'hint': "A Signet address is a string of letters and numbers that identifies your test wallet. It usually starts with 'tb1'. Follow the Setup Guide to create one.", 'success': False}
        elif not verify_captcha(captcha_input):
            session['result'] = {'message': "Incorrect code. Please try again.", 'hint': "Look at the 4-digit code displayed above the input box and type it in exactly.", 'success': False}
        else:
            rpc = get_rpc_connection()
            if not validate_address(rpc, address):
                session['result'] = {'message': "Invalid Signet address.", 'hint': "A valid Signet address starts with 'tb1' and is about 42 characters long. Make sure you copied it correctly from your wallet. Do not use a mainnet Bitcoin address here.", 'success': False}
            else:
                try:
                    balance = rpc.getbalance()
                    if balance < AMOUNT:
                        session['result'] = {'message': f"Insufficient funds. Balance: {balance} signet BTC", 'hint': "The faucet wallet has run low on test coins. Please check back later — it will be topped up soon.", 'success': False}
                    else:
                        txid = send_coins(rpc, address)
                        if txid and not txid.startswith('error'):
                            session['result'] = {'message': f"Sent {AMOUNT} signet BTC to {address}. Transaction ID: {txid}", 'hint': "A Transaction ID is a unique code for your transaction. You can paste it into the Signet Explorer to track it. Your coins will appear once the next block is mined.", 'success': True}
                        else:
                            session['result'] = {'message': f"Transaction failed: {txid}", 'hint': "Something went wrong while sending the coins. This can happen if the node is busy or restarting. Please try again in a few minutes.", 'success': False}
                except Exception as e:
                    session['result'] = {'message': f"Error: {str(e)}", 'hint': "An unexpected error occurred. Please try again. If the problem persists, the node may be offline or restarting.", 'success': False}
        return redirect(url_for('faucet'))

    result = session.pop('result', None)
    message = result['message'] if result else None
    hint = result['hint'] if result else None
    success = result['success'] if result else False
    captcha_code = generate_captcha()
    return render_template_string(HTML_TEMPLATE, message=message, hint=hint, success=success, captcha_code=captcha_code)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)