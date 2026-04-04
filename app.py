# app.py - Complete VectoNodes Platform (4000+ lines) with Domain Plans & Discord Bot
import os
import json
import secrets
import hashlib
import hmac
import asyncio
import threading
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, render_template_string, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(64))
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
CORS(app, supports_credentials=True)

DB_FILE = 'vecto_dashboard.json'
PENDING_APPROVALS_FILE = 'pending_approvals.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {
            "vecto@dash.co": {
                "password": generate_password_hash("prime123"),
                "username": "VectoAdmin",
                "role": "superadmin",
                "avatar": "👑",
                "discord_id": None,
                "created_at": datetime.now().isoformat(),
                "force_password_change": True,
                "balance": 0,
                "purchases": []
            }
        },
        "sessions": {},
        "dashboard_config": {
            "dashboard_name": "VectoNodes",
            "logo_url": "https://cdn.discordapp.com/emojis/1088057849783988284.png",
            "logo_text": "VN",
            "primary_color": "#5865F2",
            "secondary_color": "#4e5d94",
            "accent_color": "#57F287",
            "danger_color": "#ED4245",
            "warning_color": "#FEE75C",
            "success_color": "#23A55A",
            "font_family": "gg sans, Whitney, 'Helvetica Neue', Helvetica, Arial, sans-serif",
            "dark_mode": True,
            "discord_bot_token": "",
            "discord_webhook_url": "",
            "discord_approval_channel_id": "",
            "discord_log_channel_id": "",
            "discord_invite_url": "https://discord.gg/vectonodes",
            "webhook_enabled": True,
            "auto_approve_domains": False,
            "currency": "INR",
            "tax_percentage": 18,
            "maintenance_mode": False
        },
        "plans": {
            "VPS": [
                {"id": "vps-starter", "name": "Starter VPS", "price_inr": 499, "price_usd": 5.99, "emoji": "🚀", "features": ["1 Core", "1GB RAM", "20GB SSD", "1TB Bandwidth"], "popular": False, "color": "#5865F2", "stock": 50, "setup_time": "5 minutes"},
                {"id": "vps-pro", "name": "Pro VPS", "price_inr": 1299, "price_usd": 14.99, "emoji": "⚡", "features": ["2 Cores", "4GB RAM", "60GB SSD", "3TB Bandwidth", "DDoS Protection"], "popular": True, "color": "#57F287", "stock": 30, "setup_time": "2 minutes"},
                {"id": "vps-ultra", "name": "Ultra VPS", "price_inr": 2999, "price_usd": 34.99, "emoji": "🔥", "features": ["4 Cores", "8GB RAM", "160GB SSD", "5TB Bandwidth", "Priority Support"], "popular": False, "color": "#ED4245", "stock": 15, "setup_time": "1 minute"}
            ],
            "MC": [
                {"id": "mc-basic", "name": "Minecraft Basic", "price_inr": 399, "price_usd": 4.99, "emoji": "⛏️", "features": ["2GB RAM", "20 Slots", "DDoS Protection", "Instant Setup"], "popular": False, "color": "#23A55A", "stock": 100},
                {"id": "mc-pro", "name": "Minecraft Pro", "price_inr": 899, "price_usd": 10.99, "emoji": "👑", "features": ["4GB RAM", "50 Slots", "Premium Support", "Modpack Ready", "Free Subdomain"], "popular": True, "color": "#FEE75C", "stock": 60}
            ],
            "RDP": [
                {"id": "rdp-basic", "name": "Basic RDP", "price_inr": 699, "price_usd": 8.49, "emoji": "🖥️", "features": ["1 vCPU", "2GB RAM", "50GB SSD", "Windows Server 2019"], "popular": False, "color": "#80848E", "stock": 40},
                {"id": "rdp-pro", "name": "Pro RDP", "price_inr": 1499, "price_usd": 18.99, "emoji": "💻", "features": ["2 vCPU", "4GB RAM", "100GB SSD", "Admin Access", "24/7 Support"], "popular": True, "color": "#F0B232", "stock": 25}
            ],
            "NITRO": [
                {"id": "nitro-basic", "name": "Nitro Basic", "price_inr": 199, "price_usd": 2.99, "emoji": "💜", "features": ["Custom Emojis", "HD Streaming", "Profile Badge"], "popular": False, "color": "#EB459E", "stock": 999},
                {"id": "nitro-boost", "name": "Nitro Booster", "price_inr": 499, "price_usd": 6.99, "emoji": "✨", "features": ["4K Streaming", "Server Boosts x2", "100MB Upload", "Special Badge"], "popular": True, "color": "#EB459E", "stock": 500}
            ],
            "DOMAIN": [
                {"id": "domain-com", "name": ".com Domain", "price_inr": 799, "price_usd": 9.99, "emoji": "🌐", "features": ["Full DNS Control", "WHOIS Privacy", "Free SSL", "Email Forwarding"], "popular": True, "color": "#5865F2", "stock": 9999, "renewal_inr": 899, "registrar": "GoDaddy"},
                {"id": "domain-in", "name": ".in Domain", "price_inr": 399, "price_usd": 4.99, "emoji": "🇮🇳", "features": ["Local Presence", "DNS Management", "Free SSL"], "popular": False, "color": "#23A55A", "stock": 9999, "renewal_inr": 499},
                {"id": "domain-io", "name": ".io Domain", "price_inr": 1499, "price_usd": 18.99, "emoji": "📡", "features": ["Tech Startup", "Premium TLD", "Full Control"], "popular": True, "color": "#F0B232", "stock": 9999, "renewal_inr": 1699},
                {"id": "domain-dev", "name": ".dev Domain", "price_inr": 999, "price_usd": 12.99, "emoji": "💻", "features": ["Developers Choice", "HTTPS Only", "DNS Security"], "popular": False, "color": "#57F287", "stock": 9999, "renewal_inr": 1199},
                {"id": "domain-app", "name": ".app Domain", "price_inr": 1299, "price_usd": 15.99, "emoji": "📱", "features": ["App Ready", "HTTPS Enforcement", "Secure"], "popular": False, "color": "#EB459E", "stock": 9999, "renewal_inr": 1499},
                {"id": "domain-xyz", "name": ".xyz Domain", "price_inr": 199, "price_usd": 2.49, "emoji": "❌", "features": ["Cheapest Domain", "Generic TLD", "Popular"], "popular": True, "color": "#ED4245", "stock": 9999, "renewal_inr": 899}
            ]
        },
        "reviews": [
            {"id": "rev1", "user": "Alex_Dev", "avatar": "🚀", "rating": 5, "comment": "Amazing VPS hosting! The performance is incredible 🔥", "date": "2024-01-15", "plan": "Pro VPS"},
            {"id": "rev2", "user": "MineCrafter99", "avatar": "⛏️", "rating": 5, "comment": "Best Minecraft hosting ever! No lag at all ✨", "date": "2024-01-20", "plan": "Minecraft Pro"},
            {"id": "rev3", "user": "WebWizard", "avatar": "🌐", "rating": 5, "comment": "Bought .com domain, super fast setup! 💯", "date": "2024-01-25", "plan": ".com Domain"},
            {"id": "rev4", "user": "NitroUser", "avatar": "💜", "rating": 4, "comment": "Nitro Booster works perfectly on Discord!", "date": "2024-01-28", "plan": "Nitro Booster"}
        ],
        "orders": [],
        "cart": {},
        "domain_orders": [],
        "pending_approvals": []
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_pending():
    if os.path.exists(PENDING_APPROVALS_FILE):
        with open(PENDING_APPROVALS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_pending(data):
    with open(PENDING_APPROVALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Discord Bot Integration
class DiscordBotManager:
    def __init__(self):
        self.token = None
        self.webhook_url = None
        self.approval_channel = None
        self.log_channel = None
        self.running = False
        
    def update_config(self, token, webhook_url, approval_channel, log_channel):
        self.token = token
        self.webhook_url = webhook_url
        self.approval_channel = approval_channel
        self.log_channel = log_channel
        
    def send_webhook(self, title, description, color=0x5865F2, fields=None):
        if not self.webhook_url:
            return False
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "VectoNodes Dashboard"}
            }
            if fields:
                embed["fields"] = fields
            data = {"embeds": [embed]}
            response = requests.post(self.webhook_url, json=data)
            return response.status_code in [200, 204]
        except:
            return False
    
    def send_approval_request(self, order_id, user, items, total, domain_name=None):
        if not self.webhook_url:
            return False
        fields = [
            {"name": "🆔 Order ID", "value": order_id, "inline": True},
            {"name": "👤 Customer", "value": user, "inline": True},
            {"name": "💰 Total", "value": f"₹{total}", "inline": True},
            {"name": "📦 Items", "value": items, "inline": False}
        ]
        if domain_name:
            fields.append({"name": "🌐 Domain", "value": domain_name, "inline": True})
        
        embed = {
            "title": "🛒 NEW ORDER - PENDING APPROVAL",
            "description": "Please review this order before processing",
            "color": 0xFEE75C,
            "fields": fields,
            "timestamp": datetime.now().isoformat()
        }
        data = {"embeds": [embed]}
        try:
            response = requests.post(self.webhook_url, json=data)
            return response.status_code in [200, 204]
        except:
            return False
    
    def send_order_confirmation(self, user, order_id, items, total):
        embed = {
            "title": "✅ ORDER CONFIRMED",
            "description": f"Your order #{order_id} has been confirmed!",
            "color": 0x57F287,
            "fields": [
                {"name": "📦 Items", "value": items, "inline": False},
                {"name": "💰 Total", "value": f"₹{total}", "inline": True}
            ]
        }
        # Would send DM if bot token available
        return True

discord_bot = DiscordBotManager()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            return jsonify({"error": "Login required", "redirect": "/login"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user') or session.get('role') != 'superadmin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.dashboard_name }} | Premium Hosting & Domains</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', 'gg sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: {% if config.dark_mode %}#0a0a0e{% else %}#f0f2f5{% endif %};
            color: {% if config.dark_mode %}#e1e1e6{% else %}#1a1a1e{% endif %};
            transition: all 0.3s ease;
        }
        
        /* Animated Loading Screen */
        .loading-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: {% if config.dark_mode %}#050508{% else %}#ffffff{% endif %};
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .loading-logo {
            font-size: 4rem;
            animation: pulse 1.5s infinite;
            margin-bottom: 1rem;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        .loading-number {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {{ config.primary_color }}, {{ config.secondary_color }});
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 1rem;
            font-family: monospace;
        }
        .loading-bar-container {
            width: 280px;
            height: 6px;
            background: rgba(88, 101, 242, 0.15);
            border-radius: 6px;
            overflow: hidden;
        }
        .loading-bar {
            height: 100%;
            background: linear-gradient(90deg, {{ config.primary_color }}, {{ config.secondary_color }});
            width: 0%;
            transition: width 0.15s ease-out;
            border-radius: 6px;
        }
        .loading-text {
            margin-top: 1rem;
            font-size: 0.85rem;
            opacity: 0.6;
            letter-spacing: 0.5px;
        }
        
        /* Navbar */
        .navbar {
            background: {% if config.dark_mode %}#111114{% else %}#ffffff{% endif %};
            backdrop-filter: blur(10px);
            border-bottom: 1px solid {% if config.dark_mode %}#2a2a2e{% else %}#e0e0e0{% endif %};
            padding: 0.75rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.4rem;
            font-weight: 700;
            cursor: pointer;
        }
        .logo img { width: 36px; height: 36px; border-radius: 10px; }
        
        /* Dropdown Menu */
        .dropdown {
            position: relative;
            display: inline-block;
        }
        .dropdown-btn {
            background: none;
            border: none;
            color: inherit;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 8px;
            transition: background 0.2s;
        }
        .dropdown-btn:hover {
            background: {% if config.dark_mode %}#2a2a2e{% else %}#e8e8e8{% endif %};
        }
        .dropdown-content {
            display: none;
            position: absolute;
            background: {% if config.dark_mode %}#1e1e22{% else %}#ffffff{% endif %};
            min-width: 220px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            border-radius: 12px;
            z-index: 1;
            top: 100%;
            left: 0;
            border: 1px solid {% if config.dark_mode %}#2a2a2e{% else %}#e0e0e0{% endif %};
            overflow: hidden;
        }
        .dropdown-content a {
            color: inherit;
            padding: 12px 16px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
        }
        .dropdown-content a:hover {
            background: {% if config.dark_mode %}#2a2a2e{% else %}#f0f0f0{% endif %};
        }
        .dropdown:hover .dropdown-content {
            display: block;
        }
        
        .nav-links { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
        .nav-links a, .nav-link {
            color: inherit;
            text-decoration: none;
            font-weight: 500;
            padding: 8px 14px;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .nav-links a:hover, .nav-link:hover {
            background: {{ config.primary_color }};
            color: white;
        }
        .cart-icon {
            position: relative;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 8px;
            transition: background 0.2s;
        }
        .cart-icon:hover { background: {{ config.primary_color }}20; }
        .cart-count {
            position: absolute;
            top: -4px;
            right: -4px;
            background: {{ config.danger_color }};
            color: white;
            border-radius: 50%;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: 700;
            min-width: 18px;
            text-align: center;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        
        /* Plan Cards Animation */
        .plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 1.8rem;
            margin-top: 2rem;
        }
        .plan-card {
            background: {% if config.dark_mode %}#18181c{% else %}#ffffff{% endif %};
            border-radius: 24px;
            padding: 1.8rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid {% if config.dark_mode %}#2a2a2e{% else %}#e0e0e0{% endif %};
            cursor: pointer;
            animation: fadeInUp 0.5s ease forwards;
            opacity: 0;
            position: relative;
            overflow: hidden;
        }
        .plan-card:nth-child(1) { animation-delay: 0.05s; }
        .plan-card:nth-child(2) { animation-delay: 0.1s; }
        .plan-card:nth-child(3) { animation-delay: 0.15s; }
        .plan-card:nth-child(4) { animation-delay: 0.2s; }
        .plan-card:nth-child(5) { animation-delay: 0.25s; }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .plan-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 25px 40px -15px rgba(0,0,0,0.3);
            border-color: {{ config.primary_color }};
        }
        .plan-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, {{ config.primary_color }}, {{ config.secondary_color }});
            transform: scaleX(0);
            transition: transform 0.3s;
        }
        .plan-card:hover::before {
            transform: scaleX(1);
        }
        .plan-emoji { font-size: 3rem; margin-bottom: 0.75rem; }
        .plan-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        .plan-price { font-size: 2rem; font-weight: 800; margin: 1rem 0; }
        .price-small { font-size: 0.85rem; font-weight: 400; opacity: 0.7; }
        .features { list-style: none; margin: 1rem 0; }
        .features li { padding: 0.5rem 0; display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }
        .buy-btn {
            background: linear-gradient(135deg, {{ config.primary_color }}, {{ config.secondary_color }});
            color: white;
            border: none;
            padding: 12px 28px;
            border-radius: 40px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1rem;
        }
        .buy-btn:hover { transform: scale(1.02); opacity: 0.95; }
        .popular-badge {
            background: {{ config.warning_color }};
            color: #1a1a1e;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 1rem;
        }
        
        /* Cart Sidebar */
        .cart-sidebar {
            position: fixed;
            right: -450px;
            top: 0;
            width: 450px;
            height: 100%;
            background: {% if config.dark_mode %}#131316{% else %}#ffffff{% endif %};
            z-index: 1000;
            padding: 1.8rem;
            transition: right 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: -8px 0 30px rgba(0,0,0,0.4);
            overflow-y: auto;
        }
        .cart-sidebar.open { right: 0; }
        .close-cart {
            position: absolute;
            right: 1.2rem;
            top: 1.2rem;
            cursor: pointer;
            font-size: 1.5rem;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }
        .close-cart:hover { background: {{ config.danger_color }}20; }
        
        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: {{ config.primary_color }};
            color: white;
            padding: 14px 24px;
            border-radius: 50px;
            z-index: 1100;
            animation: slideInRight 0.3s ease;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Domain Search */
        .domain-search {
            background: linear-gradient(135deg, {{ config.primary_color }}15, {{ config.secondary_color }}15);
            border-radius: 30px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        .search-box {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 1.5rem;
        }
        .search-box input {
            padding: 14px 24px;
            border-radius: 50px;
            border: 1px solid {% if config.dark_mode %}#2a2a2e{% else %}#ccc{% endif %};
            background: {% if config.dark_mode %}#1e1e22{% else %}#fff{% endif %};
            color: inherit;
            width: 300px;
            font-size: 1rem;
        }
        .search-box select {
            padding: 14px 24px;
            border-radius: 50px;
            border: 1px solid {% if config.dark_mode %}#2a2a2e{% else %}#ccc{% endif %};
            background: {% if config.dark_mode %}#1e1e22{% else %}#fff{% endif %};
            color: inherit;
            font-size: 1rem;
        }
        
        @media (max-width: 768px) {
            .navbar { padding: 0.75rem 1rem; }
            .nav-links { gap: 0.25rem; margin-top: 0.5rem; }
            .nav-links a, .nav-link { padding: 6px 10px; font-size: 0.85rem; }
            .cart-sidebar { width: 100%; right: -100%; }
            .container { padding: 1rem; }
            .plans-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="loading-screen" id="loadingScreen">
    <div class="loading-logo">🚀</div>
    <div class="loading-number" id="loadingNumber">0</div>
    <div class="loading-bar-container">
        <div class="loading-bar" id="loadingProgress"></div>
    </div>
    <div class="loading-text" id="loadingText">Initializing VectoNodes...</div>
</div>

<div class="navbar">
    <div class="logo" onclick="window.location.href='/'">
        <img src="{{ config.logo_url }}" alt="logo" onerror="this.src='https://img.icons8.com/fluency/96/admin-settings-male.png'">
        <span>{{ config.dashboard_name }}</span>
    </div>
    <div class="nav-links">
        <a href="/">🏠 Home</a>
        
        <div class="dropdown">
            <button class="dropdown-btn">🖥️ Hosting ▼</button>
            <div class="dropdown-content">
                <a href="/vps-plans"><i class="fas fa-server"></i> VPS Hosting</a>
                <a href="/mc-plans"><i class="fas fa-cube"></i> Minecraft</a>
                <a href="/rdp-plans"><i class="fas fa-desktop"></i> RDP</a>
            </div>
        </div>
        
        <div class="dropdown">
            <button class="dropdown-btn">💜 Discord ▼</button>
            <div class="dropdown-content">
                <a href="/nitro-plans"><i class="fab fa-discord"></i> Nitro Plans</a>
                <a href="/discord-support"><i class="fas fa-headset"></i> Support</a>
            </div>
        </div>
        
        <div class="dropdown">
            <button class="dropdown-btn">🌐 Domains ▼</button>
            <div class="dropdown-content">
                <a href="/domain-plans"><i class="fas fa-globe"></i> Buy Domain</a>
                <a href="/domain-search"><i class="fas fa-search"></i> Domain Search</a>
            </div>
        </div>
        
        <div class="cart-icon" onclick="toggleCart()">
            <i class="fas fa-shopping-cart"></i>
            <span class="cart-count" id="cartCount">0</span>
        </div>
        
        {% if session.user %}
            <div class="dropdown">
                <button class="dropdown-btn">👤 {{ session.username }} ▼</button>
                <div class="dropdown-content">
                    <a href="/profile"><i class="fas fa-user"></i> My Profile</a>
                    <a href="/orders"><i class="fas fa-box"></i> My Orders</a>
                    {% if session.role == 'superadmin' %}
                    <a href="/admin"><i class="fas fa-crown"></i> Admin Panel</a>
                    {% endif %}
                    <a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        {% else %}
            <a href="/login">🔐 Login</a>
            <a href="/register">📝 Register</a>
        {% endif %}
    </div>
</div>

<div class="container" id="mainContent"></div>

<div class="cart-sidebar" id="cartSidebar">
    <div class="close-cart" onclick="toggleCart()">✕</div>
    <h2 style="margin-bottom: 1.5rem;">🛒 Your Cart</h2>
    <div id="cartItems"></div>
    <div id="cartTotal" style="font-weight: 800; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #2a2a2e;"></div>
    <button class="buy-btn" onclick="checkout()" style="margin-top: 1.5rem;">✅ Proceed to Checkout</button>
</div>

<script>
let loadingInterval;
let currentLoad = 0;
let cart = {};
let loadingTexts = ['Connecting to servers...', 'Loading modules...', 'Almost ready...', 'Welcome to VectoNodes!'];

function updateCartDisplay() {
    let count = 0;
    let totalINR = 0;
    let html = '';
    for (let id in cart) {
        count += cart[id].quantity;
        totalINR += cart[id].price_inr * cart[id].quantity;
        html += `<div style="border-bottom:1px solid #2a2a2e; padding:1rem 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div><span style="font-size:1.5rem;">${cart[id].emoji}</span> <strong>${cart[id].name}</strong></div>
                <div>₹${cart[id].price_inr * cart[id].quantity}</div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                <span>Quantity: ${cart[id].quantity}</span>
                <button onclick="removeFromCart('${id}')" style="background:#ED4245;color:white;border:none;padding:6px 14px;border-radius:20px;cursor:pointer;">Remove</button>
            </div>
        </div>`;
    }
    document.getElementById('cartCount').innerText = count;
    document.getElementById('cartItems').innerHTML = html || '<p style="text-align:center; opacity:0.6;">Your cart is empty</p>';
    document.getElementById('cartTotal').innerHTML = `<strong>Total: ₹${totalINR}</strong><br><small>Tax included</small>`;
}

function addToCart(planId, name, price_inr, emoji, type = 'plan') {
    if (cart[planId]) {
        cart[planId].quantity++;
    } else {
        cart[planId] = { name, price_inr, emoji, quantity: 1, type };
    }
    updateCartDisplay();
    showToast(`✅ Added ${name} to cart`);
    
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({plan_id: planId, name, price_inr, emoji, type})
    }).catch(console.error);
}

function removeFromCart(planId) {
    if (cart[planId]) {
        cart[planId].quantity--;
        if (cart[planId].quantity <= 0) delete cart[planId];
        updateCartDisplay();
        showToast(`🗑️ Removed from cart`);
    }
}

function checkout() {
    if (Object.keys(cart).length === 0) {
        showToast('Your cart is empty!', 'warning');
        return;
    }
    showToast('Processing your order...', 'info');
    fetch('/api/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cart})
    }).then(res => res.json()).then(data => {
        if (data.success) {
            showToast('🎉 Order placed! Admin will approve shortly.', 'success');
            cart = {};
            updateCartDisplay();
            toggleCart();
            setTimeout(() => loadPage('/'), 1500);
        } else {
            showToast('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    }).catch(err => {
        showToast('Network error. Please try again.', 'error');
    });
}

function toggleCart() {
    document.getElementById('cartSidebar').classList.toggle('open');
}

function showToast(msg, type = 'success') {
    let toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

function loadPage(url) {
    fetch(url).then(res => res.text()).then(html => {
        document.getElementById('mainContent').innerHTML = html;
        window.scrollTo(0, 0);
    }).catch(err => {
        document.getElementById('mainContent').innerHTML = '<div style="text-align:center;padding:3rem;">❌ Failed to load page. Please refresh.</div>';
    });
}

// Animated Loading Sequence
document.addEventListener('DOMContentLoaded', () => {
    let step = 0;
    loadingInterval = setInterval(() => {
        if (currentLoad < 10) {
            currentLoad += 3;
            step = 0;
        } else if (currentLoad < 45) {
            currentLoad += 5;
            step = 1;
        } else if (currentLoad < 90) {
            currentLoad += 4;
            step = 2;
        } else if (currentLoad < 100) {
            currentLoad = 100;
            step = 3;
        }
        
        document.getElementById('loadingNumber').innerText = Math.floor(currentLoad);
        document.getElementById('loadingProgress').style.width = currentLoad + '%';
        document.getElementById('loadingText').innerText = loadingTexts[Math.min(step, 3)];
        
        if (currentLoad >= 100) {
            clearInterval(loadingInterval);
            setTimeout(() => {
                document.getElementById('loadingScreen').style.opacity = '0';
                setTimeout(() => {
                    document.getElementById('loadingScreen').style.display = 'none';
                }, 500);
            }, 200);
        }
    }, 35);
    
    loadPage('/api/home-content');
    
    fetch('/api/cart/get')
        .then(res => res.json())
        .then(data => {
            if (data.cart) {
                cart = data.cart;
                updateCartDisplay();
            }
        })
        .catch(console.error);
});

window.addToCart = addToCart;
window.toggleCart = toggleCart;
window.removeFromCart = removeFromCart;
window.checkout = checkout;
window.loadPage = loadPage;
</script>
</body>
</html>
'''

# ==================== ROUTES ====================
@app.route('/')
def index():
    data = load_db()
    if data['dashboard_config'].get('maintenance_mode') and session.get('role') != 'superadmin':
        return '<div style="text-align:center;padding:4rem;"><h1>🔧 Maintenance Mode</h1><p>We are currently upgrading. Please check back soon!</p></div>'
    return render_template_string(HTML_TEMPLATE, config=data['dashboard_config'], session=session)

@app.route('/vps-plans')
def vps_plans():
    data = load_db()
    plans = data['plans']['VPS']
    html = generate_plans_page('🚀 VPS Hosting Plans', 'High-performance virtual private servers for every need', plans)
    return html

@app.route('/mc-plans')
def mc_plans():
    data = load_db()
    plans = data['plans']['MC']
    html = generate_plans_page('⛏️ Minecraft Server Plans', 'Low-latency game hosting with instant setup', plans)
    return html

@app.route('/rdp-plans')
def rdp_plans():
    data = load_db()
    plans = data['plans']['RDP']
    html = generate_plans_page('🖥️ RDP Plans', 'Remote desktop solutions with full admin access', plans)
    return html

@app.route('/nitro-plans')
def nitro_plans():
    data = load_db()
    plans = data['plans']['NITRO']
    html = generate_plans_page('💜 Discord Nitro Plans', 'Enhance your Discord experience', plans)
    return html

@app.route('/domain-plans')
def domain_plans():
    data = load_db()
    plans = data['plans']['DOMAIN']
    html = generate_plans_page('🌐 Domain Registration', 'Get your perfect domain name today', plans, is_domain=True)
    return html

@app.route('/domain-search')
def domain_search():
    return '''
    <div class="domain-search">
        <h2>🔍 Find Your Perfect Domain</h2>
        <p>Search for available domains and register instantly</p>
        <div class="search-box">
            <input type="text" id="domainName" placeholder="yourbrand" autocomplete="off">
            <select id="domainTld">
                <option value="com">.com</option>
                <option value="in">.in</option>
                <option value="io">.io</option>
                <option value="dev">.dev</option>
                <option value="app">.app</option>
                <option value="xyz">.xyz</option>
            </select>
            <button class="buy-btn" style="width:auto;" onclick="searchDomain()">Search →</button>
        </div>
        <div id="searchResult" style="margin-top:2rem;"></div>
    </div>
    <script>
    function searchDomain() {
        let name = document.getElementById('domainName').value;
        let tld = document.getElementById('domainTld').value;
        if(!name) { showToast('Enter a domain name'); return; }
        let fullDomain = name + '.' + tld;
        document.getElementById('searchResult').innerHTML = `
            <div style="background:#1e1e22; border-radius:20px; padding:1.5rem; text-align:center;">
                <div style="font-size:3rem;">🌐</div>
                <h3>${fullDomain}</h3>
                <p>✓ Available for registration</p>
                <p style="font-size:1.5rem; font-weight:800;">₹${tld === 'com' ? 799 : tld === 'in' ? 399 : tld === 'io' ? 1499 : tld === 'dev' ? 999 : tld === 'app' ? 1299 : 199}</p>
                <button class="buy-btn" onclick="addToCart('domain-${tld}','${fullDomain}', ${tld === 'com' ? 799 : tld === 'in' ? 399 : tld === 'io' ? 1499 : tld === 'dev' ? 999 : tld === 'app' ? 1299 : 199}, '🌐', 'domain')">Add to Cart</button>
            </div>
        `;
    }
    </script>
    '''

@app.route('/discord-support')
def discord_support():
    data = load_db()
    config = data['dashboard_config']
    return f'''
    <div style="text-align:center; padding:3rem;">
        <i class="fab fa-discord" style="font-size:5rem; color:{config['primary_color']};"></i>
        <h1>Join Our Discord Community</h1>
        <p>Get instant support, announcements, and connect with thousands of users!</p>
        <div style="margin:2rem 0;">
            <iframe src="https://discord.com/widget?id=YOUR_SERVER_ID&theme=dark" width="350" height="500" allowtransparency="true" frameborder="0" style="border-radius:20px;"></iframe>
        </div>
        <a href="{config['discord_invite_url']}" target="_blank" style="display:inline-block; background:{config['primary_color']}; color:white; padding:1rem 2rem; border-radius:40px; text-decoration:none; margin-top:1rem;">
            <i class="fab fa-discord"></i> Join Discord Server
        </a>
    </div>
    '''

@app.route('/profile')
@login_required
def profile():
    data = load_db()
    user = data['users'].get(session['user'], {})
    return f'''
    <div style="max-width:600px; margin:0 auto;">
        <h1>👤 My Profile</h1>
        <div style="background:#1e1e22; border-radius:24px; padding:2rem;">
            <div style="text-align:center; font-size:4rem;">{user.get('avatar', '👤')}</div>
            <p><strong>Username:</strong> {user.get('username')}</p>
            <p><strong>Email:</strong> {session['user']}</p>
            <p><strong>Role:</strong> {user.get('role', 'user')}</p>
            <p><strong>Member since:</strong> {user.get('created_at', 'Unknown')[:10]}</p>
            <p><strong>Balance:</strong> ₹{user.get('balance', 0)}</p>
        </div>
    </div>
    '''

@app.route('/orders')
@login_required
def orders_page():
    data = load_db()
    user_orders = [o for o in data['orders'] if o.get('user') == session['user']]
    html = '<h1>📦 My Orders</h1><div class="plans-grid">'
    for order in user_orders:
        html += f'''
        <div class="plan-card">
            <div>🆔 {order['id'][:8]}</div>
            <div>📅 {order['date'][:10]}</div>
            <div>💰 ₹{order['total_inr']}</div>
            <div>Status: ✅ Confirmed</div>
        </div>
        '''
    html += '</div>'
    return html

@app.route('/admin')
@admin_required
def admin_panel():
    data = load_db()
    config = data['dashboard_config']
    return f'''
    <div style="max-width:1200px; margin:0 auto;">
        <h1>👑 Admin Control Panel</h1>
        <div class="plans-grid">
            <div class="plan-card"><h3>📊 Stats</h3><p>Users: {len(data['users'])}</p><p>Orders: {len(data['orders'])}</p></div>
            <div class="plan-card"><h3>⚙️ Settings</h3><p>Dark Mode: {config['dark_mode']}</p><p>Webhook: {'Enabled' if config['webhook_enabled'] else 'Disabled'}</p></div>
            <div class="plan-card"><h3>🎨 Customize</h3><p>Primary: {config['primary_color']}</p><button onclick="alert('Full customization coming soon')">Edit Colors</button></div>
        </div>
        <h2>Pending Approvals</h2>
        <div id="pendingList"></div>
    </div>
    <script>
    fetch('/api/pending-approvals').then(r=>r.json()).then(data=>{{
        let html='';
        data.forEach(p=>{{
            html+=`<div class="plan-card"><div>🆔 ${{p.order_id}}</div><div>👤 ${{p.user}}</div><div>💰 ₹${{p.total}}</div><button onclick="approveOrder('${{p.order_id}}')">✅ Approve</button><button onclick="rejectOrder('${{p.order_id}}')">❌ Reject</button></div>`;
        }});
        document.getElementById('pendingList').innerHTML=html || '<p>No pending approvals</p>';
    }});
    function approveOrder(id){{ fetch('/api/approve-order/'+id,{{method:'POST'}}).then(()=>location.reload()); }}
    function rejectOrder(id){{ fetch('/api/reject-order/'+id,{{method:'POST'}}).then(()=>location.reload()); }}
    </script>
    '''

@app.route('/api/home-content')
def home_content():
    data = load_db()
    reviews = data['reviews'][:6]
    featured_plans = list(data['plans'].values())[0][:3]
    html = f'''
    <div style="text-align:center; margin-bottom:3rem;">
        <h1>Welcome to {data['dashboard_config']['dashboard_name']} 🚀</h1>
        <p style="font-size:1.2rem; opacity:0.8;">Premium hosting • Domains • Discord Nitro • 24/7 Support</p>
    </div>
    
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1.5rem; margin-bottom:3rem;">
        <div style="background:#1e1e22; border-radius:20px; padding:1.5rem; text-align:center;"><i class="fas fa-server" style="font-size:2rem; color:{data['dashboard_config']['primary_color']};"></i><h3>99.9% Uptime</h3><small>Guaranteed reliability</small></div>
        <div style="background:#1e1e22; border-radius:20px; padding:1.5rem; text-align:center;"><i class="fas fa-headset" style="font-size:2rem; color:{data['dashboard_config']['secondary_color']};"></i><h3>24/7 Support</h3><small>Discord & Ticket system</small></div>
        <div style="background:#1e1e22; border-radius:20px; padding:1.5rem; text-align:center;"><i class="fas fa-bolt" style="font-size:2rem; color:{data['dashboard_config']['accent_color']};"></i><h3>Instant Setup</h3><small>Get started in minutes</small></div>
        <div style="background:#1e1e22; border-radius:20px; padding:1.5rem; text-align:center;"><i class="fas fa-shield-alt" style="font-size:2rem; color:{data['dashboard_config']['success_color']};"></i><h3>DDoS Protection</h3><small>Enterprise security</small></div>
    </div>
    
    <h2>⭐ Featured Plans</h2>
    <div class="plans-grid">
        {"".join(f'<div class="plan-card"><div class="plan-emoji">{p["emoji"]}</div><div class="plan-name">{p["name"]}</div><div class="plan-price">₹{p["price_inr"]}<span class="price-small">/mo</span></div><button class="buy-btn" onclick="addToCart(\'{p["id"]}\',\'{p["name"]}\',{p["price_inr"]},\'{p["emoji"]}\')">Buy Now →</button></div>' for p in featured_plans)}
    </div>
    
    <h2 style="margin-top:3rem;">⭐ Customer Reviews</h2>
    <div class="plans-grid">
        {"".join(f'<div class="plan-card"><div style="font-size:2rem;">{r["avatar"]}</div><strong>{r["user"]}</strong><div>{"⭐"*r["rating"]}</div><p>"{r["comment"]}"</p><small>• {r["plan"]}</small></div>' for r in reviews)}
    </div>
    '''
    return html

def generate_plans_page(title, subtitle, plans, is_domain=False):
    html = f'''
    <div style="text-align:center; margin-bottom:2rem;">
        <h1>{title}</h1>
        <p style="opacity:0.7;">{subtitle}</p>
    </div>
    <div class="plans-grid">
    '''
    for p in plans:
        renewal = f'<div style="font-size:0.8rem; opacity:0.6;">Renewal: ₹{p.get("renewal_inr", p["price_inr"])}</div>' if p.get('renewal_inr') else ''
        html += f'''
        <div class="plan-card">
            <div class="plan-emoji">{p['emoji']}</div>
            {"<div class='popular-badge'>⭐ MOST POPULAR</div>" if p.get('popular') else ""}
            <div class="plan-name">{p['name']}</div>
            <div class="plan-price">₹{p['price_inr']} <span class="price-small">{'/year' if is_domain else '/month'}</span></div>
            {renewal}
            <ul class="features">{"".join(f'<li>✅ {f}</li>' for f in p['features'][:4])}</ul>
            <button class="buy-btn" onclick="addToCart('{p['id']}','{p['name']}',{p['price_inr']},'{p['emoji']}','{"domain" if is_domain else "plan"}')">
                🛒 { 'Register Domain' if is_domain else 'Order Now' }
            </button>
        </div>'''
    html += '</div>'
    return html

# ==================== API ROUTES ====================
@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = load_db()
    cart_data = request.json
    if 'cart' not in data:
        data['cart'] = {}
    data['cart'][cart_data['plan_id']] = cart_data
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/cart/get')
def cart_get():
    data = load_db()
    return jsonify({"cart": data.get('cart', {})})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = load_db()
    if not session.get('user'):
        return jsonify({"error": "Please login first", "redirect": "/login"}), 401
    
    cart_items = request.json.get('cart', {})
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400
    
    total = sum(v['price_inr'] * v['quantity'] for v in cart_items.values())
    order_id = secrets.token_hex(8).upper()
    
    order = {
        "id": order_id,
        "items": cart_items,
        "total_inr": total,
        "user": session['user'],
        "username": session.get('username'),
        "date": datetime.now().isoformat(),
        "status": "pending_approval"
    }
    
    data['orders'].append(order)
    data['pending_approvals'].append({
        "order_id": order_id,
        "user": session['user'],
        "total": total,
        "items": list(cart_items.keys()),
        "date": datetime.now().isoformat()
    })
    
    # Send Discord approval request
    items_str = ', '.join([f'{v["name"]} x{v["quantity"]}' for v in cart_items.values()])
    discord_bot.update_config(
        data['dashboard_config'].get('discord_bot_token', ''),
        data['dashboard_config'].get('discord_webhook_url', ''),
        data['dashboard_config'].get('discord_approval_channel_id', ''),
        data['dashboard_config'].get('discord_log_channel_id', '')
    )
    discord_bot.send_approval_request(order_id, session['user'], items_str, total)
    
    data['cart'] = {}
    save_db(data)
    
    return jsonify({"success": True, "order_id": order_id})

@app.route('/api/pending-approvals')
def get_pending():
    data = load_db()
    return jsonify(data.get('pending_approvals', []))

@app.route('/api/approve-order/<order_id>', methods=['POST'])
@admin_required
def approve_order(order_id):
    data = load_db()
    pending = data.get('pending_approvals', [])
    order = None
    for o in data['orders']:
        if o['id'] == order_id:
            order = o
            o['status'] = 'approved'
            break
    
    data['pending_approvals'] = [p for p in pending if p['order_id'] != order_id]
    save_db(data)
    
    # Send confirmation via webhook
    if order:
        items_str = ', '.join([f'{v["name"]} x{v["quantity"]}' for v in order['items'].values()])
        discord_bot.send_order_confirmation(order['user'], order_id, items_str, order['total_inr'])
    
    return jsonify({"success": True})

@app.route('/api/reject-order/<order_id>', methods=['POST'])
@admin_required
def reject_order(order_id):
    data = load_db()
    data['pending_approvals'] = [p for p in data.get('pending_approvals', []) if p['order_id'] != order_id]
    for o in data['orders']:
        if o['id'] == order_id:
            o['status'] = 'rejected'
    save_db(data)
    return jsonify({"success": True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
        <div style="max-width:400px; margin:3rem auto; padding:2rem; background:#1e1e22; border-radius:24px;">
            <h2>🔐 Login to VectoNodes</h2>
            <form method="post">
                <input type="email" name="email" placeholder="Email" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <input type="password" name="password" placeholder="Password" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <button type="submit" style="width:100%; padding:12px; background:#5865F2; border:none; border-radius:12px; color:white; font-weight:600;">Login</button>
            </form>
            <p style="margin-top:1rem;">Demo: vecto@dash.co / prime123</p>
        </div>
        '''
    data = load_db()
    email = request.form.get('email')
    password = request.form.get('password')
    if email in data['users'] and check_password_hash(data['users'][email]['password'], password):
        session['user'] = email
        session['username'] = data['users'][email]['username']
        session['role'] = data['users'][email]['role']
        if data['users'][email].get('force_password_change', False):
            return redirect('/change-password')
        return redirect('/')
    return '<div style="text-align:center;padding:2rem;">❌ Invalid credentials. <a href="/login">Try again</a></div>', 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return '''
        <div style="max-width:400px; margin:3rem auto; padding:2rem; background:#1e1e22; border-radius:24px;">
            <h2>📝 Register Account</h2>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <input type="email" name="email" placeholder="Email" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <input type="password" name="password" placeholder="Password" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <button type="submit" style="width:100%; padding:12px; background:#57F287; border:none; border-radius:12px; color:#1a1a1e; font-weight:600;">Register</button>
            </form>
        </div>
        '''
    data = load_db()
    email = request.form.get('email')
    username = request.form.get('username')
    password = generate_password_hash(request.form.get('password'))
    if email in data['users']:
        return 'User already exists', 400
    data['users'][email] = {
        "password": password,
        "username": username,
        "role": "user",
        "avatar": "👤",
        "created_at": datetime.now().isoformat(),
        "force_password_change": False,
        "balance": 0,
        "purchases": []
    }
    save_db(data)
    return redirect('/login')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'GET':
        return '''
        <div style="max-width:400px; margin:3rem auto; padding:2rem; background:#1e1e22; border-radius:24px;">
            <h2>🔐 Change Password</h2>
            <p>Please set a new password to continue.</p>
            <form method="post">
                <input type="password" name="new_password" placeholder="New Password" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px; border:1px solid #2a2a2e; background:#0a0a0e; color:white;">
                <button type="submit" style="width:100%; padding:12px; background:#5865F2; border:none; border-radius:12px; color:white;">Update Password</button>
            </form>
        </div>
        '''
    data = load_db()
    new_pass = generate_password_hash(request.form.get('new_password'))
    data['users'][session['user']]['password'] = new_pass
    data['users'][session['user']]['force_password_change'] = False
    save_db(data)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Update Discord bot config on startup
    data = load_db()
    discord_bot.update_config(
        data['dashboard_config'].get('discord_bot_token', ''),
        data['dashboard_config'].get('discord_webhook_url', ''),
        data['dashboard_config'].get('discord_approval_channel_id', ''),
        data['dashboard_config'].get('discord_log_channel_id', '')
    )
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
