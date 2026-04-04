# app.py - Complete VeCho Hub Dashboard with Offers, Discord Bot, Stock Management, Admin Panel
# Version 3.0 - Full Feature Rich Dashboard
# Total Lines: 5000+

import os
import json
import secrets
import hashlib
import requests
import threading
import time
import re
import asyncio
import uuid
import hmac
import base64
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, url_for, render_template_string, make_response, flash, send_file, abort
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Try to import discord for bot functionality
try:
    import discord
    from discord.ext import commands, tasks
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("Discord.py not installed. Install with: pip install discord.py")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(64))
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
CORS(app, supports_credentials=True)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '1359842739835170886')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', 'YOUR_CLIENT_SECRET_HERE')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', 'http://localhost:5000/auth/discord/callback')
DISCORD_API_BASE = 'https://discord.com/api/v10'

DB_FILE = 'vecho_hub.json'
STOCK_FILES_DIR = 'stock_files'
os.makedirs(STOCK_FILES_DIR, exist_ok=True)

# Global bot instance
bot_instance = None
bot_thread = None
bot_running = False

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {
            "admin@vechohub.com": {
                "password": generate_password_hash("admin123"),
                "username": "SuperAdmin",
                "role": "superadmin",
                "avatar": "👑",
                "discord_id": None,
                "discord_username": None,
                "discord_avatar": None,
                "created_at": datetime.now().isoformat(),
                "force_password_change": False,
                "balance": 0,
                "purchases": [],
                "api_key": secrets.token_hex(32),
                "two_factor_enabled": False,
                "two_factor_secret": None
            }
        },
        "discord_users": {},
        "sessions": {},
        "announcements": [
            {
                "id": "ann1",
                "title": "🎉 Welcome to VeCho Hub!",
                "content": "Your premium destination for VPS, RDP, Minecraft servers, and Discord Nitro!",
                "type": "success",
                "emoji": "🚀",
                "active": True,
                "created_at": datetime.now().isoformat(),
                "expires_at": None,
                "priority": 1
            },
            {
                "id": "ann2",
                "title": "⚡ New VPS Plans Available",
                "content": "Check out our new VPS Professional and Enterprise plans with up to 32GB RAM!",
                "type": "info",
                "emoji": "💻",
                "active": True,
                "created_at": datetime.now().isoformat(),
                "expires_at": None,
                "priority": 2
            }
        ],
        "bot_config": {
            "bot_token": "",
            "bot_enabled": False,
            "bot_status": "online",
            "bot_activity_type": "playing",
            "bot_activity_name": "VeCho Hub | !help",
            "bot_prefix": "!",
            "dm_on_purchase": True,
            "discord_invite_url": "https://discord.gg/vechohub",
            "discord_server_id": "",
            "discord_widget_enabled": True,
            "dm_message_template": "🎉 Thank you for your purchase!\n\n📦 Plan: {plan_name}\n💰 Amount: ${price}\n🆔 Order ID: {order_id}\n\nYour order will be delivered within 5 minutes. Use the stock below:\n\n{stock_codes}\n\nNeed help? Join our Discord: {discord_invite}",
            "welcome_channel_id": "",
            "welcome_message": "Welcome {user} to {server}!",
            "log_channel_id": "",
            "auto_role_id": "",
            "ticket_category_id": "",
            "suggestion_channel_id": "",
            "announcement_channel_id": ""
        },
        "dashboard_config": {
            "website_name": "VeCho Hub",
            "logo_url": "https://img.icons8.com/fluency/96/admin-settings-male.png",
            "favicon_url": "https://img.icons8.com/color/48/admin-settings-male.png",
            "theme": "dark",
            "maintenance_mode": False,
            "maintenance_message": "We are currently upgrading our systems. Please check back soon!",
            "maintenance_end_time": None,
            "maintenance_countdown": False,
            "backgrounds": {
                "dashboard_main": "#0A0A0A",
                "sidebar": "#111111",
                "vps_section": "#0F0F0F",
                "rdp_section": "#0F0F0F",
                "mc_section": "#0F0F0F",
                "games_section": "#0F0F0F",
                "nitro_section": "#0F0F0F",
                "trial_section": "#0F0F0F",
                "header": "#1A1A1A",
                "footer": "#0A0A0A",
                "cards": "#1E1E22"
            },
            "colors": {
                "primary": "#4F46E5",
                "secondary": "#10B981",
                "accent": "#F59E0B",
                "danger": "#EF4444",
                "warning": "#F59E0B",
                "info": "#3B82F6",
                "success": "#10B981"
            },
            "stats": {
                "total_customers": 12847,
                "active_services": 24391,
                "uptime_percentage": 99.9,
                "rating": 4.9,
                "review_count": 8432,
                "never_down_since": "January 2024",
                "response_time_ms": 48,
                "servers_worldwide": 14,
                "ddos_capacity": "2TB/s",
                "total_orders": 52341,
                "total_revenue": 847231
            },
            "uptime_monitors": [],
            "activity_feed": [
                {"user": "Alex_Dev", "action": "purchased VPS", "plan": "VPS Standard", "time": "2 minutes ago", "amount": 20},
                {"user": "MineCrafter", "action": "deployed Minecraft server", "plan": "MC Pro", "time": "15 minutes ago", "amount": 12},
                {"user": "DiscordLover", "action": "bought Nitro", "plan": "Nitro Full Yearly", "time": "1 hour ago", "amount": 100},
                {"user": "GameMaster", "action": "rented game server", "plan": "Rust Server", "time": "3 hours ago", "amount": 15}
            ],
            "seo": {
                "meta_title": "VeCho Hub - Premium Hosting & Discord Services",
                "meta_description": "Get the best VPS, RDP, Minecraft servers, and Discord Nitro at unbeatable prices. 24/7 support, 99.9% uptime guarantee.",
                "meta_keywords": "vps, rdp, minecraft hosting, discord nitro, game servers",
                "og_image": "https://img.icons8.com/fluency/96/admin-settings-male.png"
            },
            "social_links": {
                "discord": "https://discord.gg/vechohub",
                "twitter": "https://twitter.com/vechohub",
                "github": "https://github.com/vechohub",
                "telegram": "https://t.me/vechohub"
            },
            "payment_methods": {
                "stripe": True,
                "paypal": True,
                "crypto": True,
                "credit_card": True
            },
            "featured_plans": ["vps-standard", "mc-pro", "nitro-full-yearly"],
            "testimonials": [
                {"user": "JohnDoe", "rating": 5, "comment": "Amazing service! Best VPS provider I've used.", "date": "2024-01-15"},
                {"user": "JaneSmith", "rating": 5, "comment": "Support is incredibly fast and helpful.", "date": "2024-01-20"},
                {"user": "TechGuru", "rating": 4.9, "comment": "Reliable servers, great pricing.", "date": "2024-01-25"}
            ]
        },
        "plans": {
            "VPS": [
                {"id": "vps-mini", "name": "VPS Mini", "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "price": 5, "popular": False, "emoji": "🖥️", "features": ["1 IPv4", "DDoS Protection", "24/7 Support"]},
                {"id": "vps-basic", "name": "VPS Basic", "cpu": "2 Core", "ram": "2GB", "storage": "50GB SSD", "bandwidth": "2TB", "price": 10, "popular": False, "emoji": "💻", "features": ["1 IPv4", "DDoS Protection", "24/7 Support", "Backup"]},
                {"id": "vps-standard", "name": "VPS Standard", "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "price": 20, "popular": True, "emoji": "⚡", "features": ["2 IPv4", "DDoS Protection", "24/7 Support", "Backup", "Snapshot"]},
                {"id": "vps-advanced", "name": "VPS Advanced", "cpu": "8 Core", "ram": "8GB", "storage": "200GB SSD", "bandwidth": "8TB", "price": 40, "popular": False, "emoji": "🚀", "features": ["2 IPv4", "DDoS Protection", "24/7 Support", "Backup", "Snapshot", "Load Balancer"]},
                {"id": "vps-professional", "name": "VPS Professional", "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "price": 80, "popular": False, "emoji": "🔥", "features": ["3 IPv4", "DDoS Protection", "24/7 Support", "Backup", "Snapshot", "Load Balancer", "Dedicated IP"]},
                {"id": "vps-enterprise", "name": "VPS Enterprise", "cpu": "16 Core", "ram": "32GB", "storage": "1TB SSD", "bandwidth": "Unlimited", "price": 160, "popular": False, "emoji": "👑", "features": ["5 IPv4", "DDoS Protection", "24/7 Priority Support", "Backup", "Snapshot", "Load Balancer", "Dedicated IP", "Custom Configuration"]}
            ],
            "RDP": [
                {"id": "rdp-lite", "name": "RDP Lite", "ram": "2GB", "cpu": "1 Core", "storage": "40GB SSD", "features": "Windows Server 2019", "price": 10, "emoji": "🖥️", "extras": ["Admin Access", "1 User"]},
                {"id": "rdp-pro", "name": "RDP Pro", "ram": "4GB", "cpu": "2 Core", "storage": "80GB SSD", "features": "Windows Server 2019", "price": 20, "emoji": "💻", "popular": True, "extras": ["Admin Access", "2 Users", "RemoteApp"]},
                {"id": "rdp-business", "name": "RDP Business", "ram": "8GB", "cpu": "4 Core", "storage": "160GB SSD", "features": "Windows Server 2019", "price": 35, "emoji": "🏢", "extras": ["Admin Access", "5 Users", "RemoteApp", "Print Redirection"]},
                {"id": "rdp-enterprise", "name": "RDP Enterprise", "ram": "16GB", "cpu": "6 Core", "storage": "320GB SSD", "features": "Windows Server 2019", "price": 60, "emoji": "🏛️", "extras": ["Admin Access", "10 Users", "RemoteApp", "Print Redirection", "Audio Redirection"]}
            ],
            "MC": [
                {"id": "mc-starter", "name": "MC Starter", "ram": "1GB", "slots": 10, "price": 3, "emoji": "🌱", "features": ["Paper/Purpur", "MySQL", "DDoS Protection"]},
                {"id": "mc-basic", "name": "MC Basic", "ram": "2GB", "slots": 25, "price": 6, "emoji": "⛏️", "features": ["Paper/Purpur", "MySQL", "DDoS Protection", "Mod Support"]},
                {"id": "mc-pro", "name": "MC Pro", "ram": "4GB", "slots": 50, "price": 12, "emoji": "⚔️", "popular": True, "features": ["Paper/Purpur", "MySQL", "DDoS Protection", "Mod Support", "Auto Backup"]},
                {"id": "mc-advanced", "name": "MC Advanced", "ram": "8GB", "slots": 100, "price": 24, "emoji": "🏰", "features": ["Paper/Purpur", "MySQL", "DDoS Protection", "Mod Support", "Auto Backup", "Dedicated IP"]},
                {"id": "mc-extreme", "name": "MC Extreme", "ram": "16GB", "slots": 200, "price": 48, "emoji": "💎", "features": ["Paper/Purpur", "MySQL", "DDoS Protection", "Mod Support", "Auto Backup", "Dedicated IP", "Priority Support"]},
                {"id": "mc-ultimate", "name": "MC Ultimate", "ram": "32GB", "slots": 500, "price": 96, "emoji": "👑", "features": ["Paper/Purpur", "MySQL", "DDoS Protection", "Mod Support", "Auto Backup", "Dedicated IP", "Priority Support", "Custom JAR"]}
            ],
            "GAMES": [
                {"id": "game-rust", "name": "Rust Server", "ram": "4GB", "slots": 50, "price": 15, "emoji": "🦀", "features": ["Full Control", "Mod Support", "DDoS Protection"]},
                {"id": "game-ark", "name": "Ark Server", "ram": "8GB", "slots": 70, "price": 25, "emoji": "🦖", "features": ["Full Control", "Mod Support", "DDoS Protection", "Cross-Play"]},
                {"id": "game-cs2", "name": "CS2 Server", "ram": "2GB", "slots": 20, "price": 8, "emoji": "🎯", "features": ["Full Control", "Plugin Support", "DDoS Protection", "Tournament Ready"]},
                {"id": "game-valheim", "name": "Valheim Server", "ram": "4GB", "slots": 10, "price": 12, "emoji": "🌲", "features": ["Full Control", "Mod Support", "DDoS Protection", "Cross-Play"]},
                {"id": "game-palworld", "name": "Palworld Server", "ram": "8GB", "slots": 32, "price": 20, "emoji": "🐾", "popular": True, "features": ["Full Control", "Mod Support", "DDoS Protection", "Auto Backup"]},
                {"id": "game-minecraft-bedrock", "name": "MC Bedrock", "ram": "2GB", "slots": 20, "price": 10, "emoji": "📱", "features": ["Cross-Play", "Addon Support", "DDoS Protection"]}
            ],
            "NITRO": [
                {"id": "nitro-basic-monthly", "name": "Nitro Basic Monthly", "price": 3, "features": "Custom emojis, 720p streaming, 50MB upload", "emoji": "💜", "savings": 0},
                {"id": "nitro-basic-yearly", "name": "Nitro Basic Yearly", "price": 30, "features": "Save $6, Custom emojis, 720p streaming, 50MB upload", "emoji": "💜✨", "popular": True, "savings": 6},
                {"id": "nitro-full-monthly", "name": "Nitro Full Monthly", "price": 10, "features": "4K streaming, 500MB upload, 2 boosts, HD streaming", "emoji": "💎", "savings": 0},
                {"id": "nitro-full-yearly", "name": "Nitro Full Yearly", "price": 100, "features": "Save $20, 4K streaming, 500MB upload, 2 boosts, HD streaming", "emoji": "👑", "popular": True, "savings": 20},
                {"id": "boost-1", "name": "1 Server Boost", "price": 4, "emoji": "⚡", "features": "Increase server level by 1"},
                {"id": "boost-2", "name": "2 Server Boosts", "price": 8, "emoji": "⚡⚡", "features": "Increase server level by 2", "savings": 0},
                {"id": "boost-5", "name": "5 Server Boosts", "price": 18, "emoji": "⚡⚡⚡", "features": "Increase server level by 5", "savings": 2},
                {"id": "boost-10", "name": "10 Server Boosts", "price": 35, "emoji": "🔥", "popular": True, "features": "Increase server level by 10", "savings": 5},
                {"id": "boost-20", "name": "20 Server Boosts", "price": 65, "emoji": "💎", "features": "Increase server level by 20", "savings": 15}
            ],
            "TRIAL": [
                {"id": "trial-3month", "name": "3 Month Nitro Trial", "duration": "3 months", "price": 15, "stock": 50, "emoji": "🎁", "original_price": 30},
                {"id": "trial-1month", "name": "1 Month Nitro Trial", "duration": "1 month", "price": 8, "stock": 100, "emoji": "🎟️", "popular": True, "original_price": 10},
                {"id": "trial-2week", "name": "2 Week Nitro Trial", "duration": "2 weeks", "price": 5, "stock": 200, "emoji": "✨", "original_price": 7},
                {"id": "trial-edu", "name": "Educational Nitro", "duration": "6 months", "price": 25, "stock": 30, "emoji": "🎓", "original_price": 50}
            ]
        },
        "offers": [
            {
                "id": "offer1",
                "title": "🎉 FLASH SALE!",
                "description": "Get 30% OFF on all VPS plans",
                "discount_type": "percentage",
                "discount_value": 30,
                "applicable_plans": "vps",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "is_active": True,
                "banner_color": "#4F46E5",
                "emoji": "🔥",
                "code": "FLASH30",
                "usage_limit": 100,
                "used_count": 0,
                "min_purchase": 10,
                "max_discount": 100
            },
            {
                "id": "offer2",
                "title": "🎁 NITRO SPECIAL",
                "description": "Buy any Nitro plan and get 20% OFF",
                "discount_type": "percentage",
                "discount_value": 20,
                "applicable_plans": "nitro",
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "is_active": True,
                "banner_color": "#5865F2",
                "emoji": "💜",
                "code": "NITRO20",
                "usage_limit": 200,
                "used_count": 0,
                "min_purchase": 0,
                "max_discount": 50
            }
        ],
        "stock_files": {},
        "orders": [],
        "pending_approvals": [],
        "tickets": [],
        "coupons": [],
        "affiliates": [],
        "api_logs": [],
        "webhooks": [],
        "backup_config": {
            "auto_backup": True,
            "backup_interval": 24,
            "backup_retention": 7,
            "last_backup": None
        }
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_stock_for_plan(plan_id, quantity=1):
    data = load_db()
    stock_files = data.get('stock_files', {})
    if plan_id not in stock_files:
        return None
    filename = stock_files[plan_id]
    filepath = os.path.join(STOCK_FILES_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        codes = [line.strip() for line in f if line.strip()]
    if len(codes) < quantity:
        return None
    used_codes = codes[:quantity]
    remaining_codes = codes[quantity:]
    with open(filepath, 'w') as f:
        f.write('\n'.join(remaining_codes))
    return used_codes

def get_active_offers(plan_type=None):
    data = load_db()
    now = datetime.now().isoformat()
    active_offers = []
    for offer in data.get('offers', []):
        if offer.get('is_active') and offer.get('start_date') <= now <= offer.get('end_date'):
            if plan_type is None or offer.get('applicable_plans') == 'all' or offer.get('applicable_plans') == plan_type:
                active_offers.append(offer)
    return active_offers

def calculate_discounted_price(original_price, plan_type, coupon_code=None):
    data = load_db()
    final_price = original_price
    
    # Apply active offers
    offers = get_active_offers(plan_type)
    for offer in offers:
        if offer['discount_type'] == 'percentage':
            final_price = final_price * (1 - offer['discount_value'] / 100)
        elif offer['discount_type'] == 'fixed':
            final_price = max(0, final_price - offer['discount_value'])
    
    # Apply coupon if provided
    if coupon_code:
        for coupon in data.get('coupons', []):
            if coupon.get('code', '').upper() == coupon_code.upper() and coupon.get('is_active'):
                if coupon['discount_type'] == 'percentage':
                    final_price = final_price * (1 - coupon['discount_value'] / 100)
                elif coupon['discount_type'] == 'fixed':
                    final_price = max(0, final_price - coupon['discount_value'])
    
    return round(final_price, 2)

def send_discord_dm(user_discord_id, message):
    data = load_db()
    bot_token = data['bot_config'].get('bot_token', '')
    if not bot_token:
        return False
    headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
    try:
        dm_response = requests.post(f'{DISCORD_API_BASE}/users/@me/channels', headers=headers, json={'recipient_id': user_discord_id}, timeout=10)
        if dm_response.status_code != 200:
            return False
        channel_id = dm_response.json().get('id')
        msg_response = requests.post(f'{DISCORD_API_BASE}/channels/{channel_id}/messages', headers=headers, json={'content': message}, timeout=10)
        return msg_response.status_code == 200
    except:
        return False

def send_discord_webhook(message, embed=None):
    data = load_db()
    webhook_url = data['bot_config'].get('webhook_url', '')
    if not webhook_url:
        return False
    payload = {'content': message}
    if embed:
        payload['embeds'] = [embed]
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 204
    except:
        return False

def generate_invoice(order_id, user_email, plan_name, price):
    invoice = {
        "invoice_id": f"INV-{order_id}",
        "date": datetime.now().isoformat(),
        "customer": user_email,
        "items": [{"description": plan_name, "quantity": 1, "unit_price": price, "total": price}],
        "subtotal": price,
        "tax": round(price * 0.1, 2),
        "total": round(price * 1.1, 2),
        "status": "pending"
    }
    return invoice

def log_api_request(endpoint, method, user, status, response_time):
    data = load_db()
    log = {
        "id": secrets.token_hex(8),
        "endpoint": endpoint,
        "method": method,
        "user": user,
        "status": status,
        "response_time_ms": response_time,
        "timestamp": datetime.now().isoformat()
    }
    data.setdefault('api_logs', []).append(log)
    data['api_logs'] = data['api_logs'][-1000:]  # Keep last 1000 logs
    save_db(data)

def create_backup():
    data = load_db()
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f'vecho_hub_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)
    data['backup_config']['last_backup'] = datetime.now().isoformat()
    save_db(data)
    return backup_file

def restore_backup(backup_file):
    with open(backup_file, 'r') as f:
        data = json.load(f)
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return True

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

# Discord Bot Class
if DISCORD_AVAILABLE:
    class VeChoBot(commands.Bot):
        def __init__(self):
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.guilds = True
            super().__init__(command_prefix='!', intents=intents, help_command=None)
            self.db_file = DB_FILE
        
        async def setup_hook(self):
            await self.add_cog(AdminCommands(self))
            await self.add_cog(ModerationCommands(self))
            await self.add_cog(EconomyCommands(self))
            await self.add_cog(TicketCommands(self))
            await self.add_cog(UtilityCommands(self))
        
        async def on_ready(self):
            print(f'✅ Bot is ready! Logged in as {self.user}')
            data = load_db()
            status = data['bot_config'].get('bot_status', 'online')
            activity_type = data['bot_config'].get('bot_activity_type', 'playing')
            activity_name = data['bot_config'].get('bot_activity_name', 'VeCho Hub | !help')
            
            activity_map = {
                'playing': discord.Game(name=activity_name),
                'streaming': discord.Streaming(name=activity_name, url='https://twitch.tv/vechohub'),
                'listening': discord.Activity(type=discord.ActivityType.listening, name=activity_name),
                'watching': discord.Activity(type=discord.ActivityType.watching, name=activity_name)
            }
            await self.change_presence(status=discord.Status[status], activity=activity_map.get(activity_type, discord.Game(name=activity_name)))
        
        async def on_member_join(self, member):
            data = load_db()
            welcome_channel_id = data['bot_config'].get('welcome_channel_id')
            if welcome_channel_id:
                channel = self.get_channel(int(welcome_channel_id))
                if channel:
                    welcome_msg = data['bot_config'].get('welcome_message', 'Welcome {user} to {server}!')
                    await channel.send(welcome_msg.format(user=member.mention, server=member.guild.name))
            
            auto_role_id = data['bot_config'].get('auto_role_id')
            if auto_role_id:
                role = member.guild.get_role(int(auto_role_id))
                if role:
                    await member.add_roles(role)
        
        async def on_member_remove(self, member):
            data = load_db()
            log_channel_id = data['bot_config'].get('log_channel_id')
            if log_channel_id:
                channel = self.get_channel(int(log_channel_id))
                if channel:
                    await channel.send(f'👋 {member.name} left the server.')
        
        async def on_message(self, message):
            if message.author.bot:
                return
            
            # Auto-reply system
            data = load_db()
            for trigger, response in data.get('auto_replies', {}).items():
                if trigger.lower() in message.content.lower():
                    await message.channel.send(response)
                    break
            
            await self.process_commands(message)

    class AdminCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='help')
        async def help_command(self, ctx):
            embed = discord.Embed(title="🤖 VeCho Hub Bot Commands", description="Here are all available commands:", color=0x4F46E5)
            embed.add_field(name="📊 Admin Commands", value="`!stats` - View bot stats\n`!announce` - Make announcement\n`!setstatus` - Change bot status", inline=False)
            embed.add_field(name="🛡️ Moderation", value="`!kick` - Kick member\n`!ban` - Ban member\n`!mute` - Mute member\n`!clear` - Clear messages", inline=False)
            embed.add_field(name="💰 Economy", value="`!balance` - Check balance\n`!shop` - View shop\n`!buy` - Purchase item", inline=False)
            embed.add_field(name="🎫 Tickets", value="`!ticket` - Create ticket\n`!close` - Close ticket", inline=False)
            embed.add_field(name="🔧 Utility", value="`!ping` - Check latency\n`!serverinfo` - Server info\n`!userinfo` - User info", inline=False)
            await ctx.send(embed=embed)
        
        @commands.command(name='stats')
        @commands.has_permissions(administrator=True)
        async def bot_stats(self, ctx):
            data = load_db()
            embed = discord.Embed(title="📊 Bot Statistics", color=0x10B981)
            embed.add_field(name="Total Users", value=len(data['users']), inline=True)
            embed.add_field(name="Total Orders", value=len(data['orders']), inline=True)
            embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
            embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            await ctx.send(embed=embed)
        
        @commands.command(name='announce')
        @commands.has_permissions(administrator=True)
        async def announce(self, ctx, channel_id: int = None, *, message: str):
            channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
            if channel:
                embed = discord.Embed(title="📢 Announcement", description=message, color=0x4F46E5)
                embed.set_footer(text=f"Announced by {ctx.author.name}")
                await channel.send(embed=embed)
                await ctx.send(f"✅ Announcement sent to {channel.mention}")
            else:
                await ctx.send("❌ Channel not found!")
        
        @commands.command(name='setstatus')
        @commands.has_permissions(administrator=True)
        async def set_status(self, ctx, status_type: str, *, status_text: str):
            data = load_db()
            data['bot_config']['bot_activity_type'] = status_type
            data['bot_config']['bot_activity_name'] = status_text
            save_db(data)
            
            activity_map = {
                'playing': discord.Game(name=status_text),
                'streaming': discord.Streaming(name=status_text, url='https://twitch.tv/vechohub'),
                'listening': discord.Activity(type=discord.ActivityType.listening, name=status_text),
                'watching': discord.Activity(type=discord.ActivityType.watching, name=status_text)
            }
            await self.bot.change_presence(activity=activity_map.get(status_type, discord.Game(name=status_text)))
            await ctx.send(f"✅ Bot status changed to {status_type} `{status_text}`")

    class ModerationCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='kick')
        @commands.has_permissions(kick_members=True)
        async def kick(self, ctx, member: discord.Member, *, reason=None):
            await member.kick(reason=reason)
            embed = discord.Embed(title="✅ Member Kicked", description=f"{member.mention} has been kicked.\nReason: {reason}", color=0xF59E0B)
            await ctx.send(embed=embed)
        
        @commands.command(name='ban')
        @commands.has_permissions(ban_members=True)
        async def ban(self, ctx, member: discord.Member, *, reason=None):
            await member.ban(reason=reason)
            embed = discord.Embed(title="✅ Member Banned", description=f"{member.mention} has been banned.\nReason: {reason}", color=0xEF4444)
            await ctx.send(embed=embed)
        
        @commands.command(name='clear')
        @commands.has_permissions(manage_messages=True)
        async def clear(self, ctx, amount: int):
            if amount > 100:
                amount = 100
            await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"✅ Cleared {amount} messages!")
            await msg.delete(delay=3)
        
        @commands.command(name='mute')
        @commands.has_permissions(manage_roles=True)
        async def mute(self, ctx, member: discord.Member, *, reason=None):
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not mute_role:
                mute_role = await ctx.guild.create_role(name="Muted")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False)
            await member.add_roles(mute_role)
            embed = discord.Embed(title="🔇 Member Muted", description=f"{member.mention} has been muted.\nReason: {reason}", color=0xF59E0B)
            await ctx.send(embed=embed)

    class EconomyCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='balance', aliases=['bal'])
        async def balance(self, ctx):
            data = load_db()
            user_email = None
            for email, info in data['users'].items():
                if info.get('discord_id') == str(ctx.author.id):
                    user_email = email
                    break
            if user_email:
                balance = data['users'][user_email].get('balance', 0)
                embed = discord.Embed(title="💰 Balance", description=f"Your balance: **${balance}**", color=0x10B981)
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ You don't have an account linked! Please register on the website.")
        
        @commands.command(name='shop')
        async def shop(self, ctx):
            data = load_db()
            embed = discord.Embed(title="🛒 VeCho Hub Shop", description="Check out our plans!", color=0x4F46E5)
            for category, plans in data['plans'].items():
                if plans:
                    plan_list = "\n".join([f"• {p['emoji']} **{p['name']}** - ${p['price']}" for p in plans[:3]])
                    embed.add_field(name=category, value=plan_list, inline=True)
            embed.set_footer(text="Visit our website to purchase!")
            await ctx.send(embed=embed)

    class TicketCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='ticket')
        async def create_ticket(self, ctx, *, reason="Support needed"):
            data = load_db()
            category_id = data['bot_config'].get('ticket_category_id')
            if category_id:
                category = ctx.guild.get_channel(int(category_id))
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", category=category, overwrites=overwrites)
                embed = discord.Embed(title="🎫 Support Ticket", description=f"Thank you for creating a ticket!\nReason: {reason}\n\nSupport team will assist you shortly.", color=0x4F46E5)
                await channel.send(ctx.author.mention, embed=embed)
                await ctx.send(f"✅ Ticket created! {channel.mention}")
        
        @commands.command(name='close')
        async def close_ticket(self, ctx):
            if "ticket-" in ctx.channel.name:
                await ctx.send("Closing ticket in 5 seconds...")
                await asyncio.sleep(5)
                await ctx.channel.delete()

    class UtilityCommands(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command(name='ping')
        async def ping(self, ctx):
            latency = round(self.bot.latency * 1000)
            embed = discord.Embed(title="🏓 Pong!", description=f"Latency: **{latency}ms**", color=0x10B981)
            await ctx.send(embed=embed)
        
        @commands.command(name='serverinfo')
        async def server_info(self, ctx):
            guild = ctx.guild
            embed = discord.Embed(title=guild.name, description=guild.description, color=0x4F46E5)
            embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
            embed.add_field(name="Members", value=guild.member_count, inline=True)
            embed.add_field(name="Channels", value=len(guild.channels), inline=True)
            embed.add_field(name="Roles", value=len(guild.roles), inline=True)
            embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            await ctx.send(embed=embed)
        
        @commands.command(name='userinfo')
        async def user_info(self, ctx, member: discord.Member = None):
            member = member or ctx.author
            embed = discord.Embed(title=member.name, color=0x4F46E5)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            await ctx.send(embed=embed)

def start_discord_bot():
    global bot_instance, bot_running
    if not DISCORD_AVAILABLE:
        print("Discord.py not available")
        return
    
    data = load_db()
    bot_token = data['bot_config'].get('bot_token', '')
    bot_enabled = data['bot_config'].get('bot_enabled', False)
    
    if not bot_token or not bot_enabled:
        print("Bot not configured or disabled")
        return
    
    if bot_running:
        print("Bot already running")
        return
    
    try:
        bot_instance = VeChoBot()
        
        def run_bot():
            global bot_running
            try:
                bot_instance.run(bot_token)
            except Exception as e:
                print(f"Bot error: {e}")
                bot_running = False
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        bot_running = True
        print("Discord bot started successfully!")
    except Exception as e:
        print(f"Failed to start bot: {e}")

def stop_discord_bot():
    global bot_instance, bot_running
    if bot_instance:
        try:
            asyncio.run_coroutine_threadsafe(bot_instance.close(), bot_instance.loop)
        except:
            pass
    bot_running = False
    print("Discord bot stopped")

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>{{ config.website_name }} | Premium Hosting & Services</title>
    <meta name="description" content="{{ config.seo.meta_description }}">
    <meta name="keywords" content="{{ config.seo.meta_keywords }}">
    <meta property="og:title" content="{{ config.seo.meta_title }}">
    <meta property="og:description" content="{{ config.seo.meta_description }}">
    <meta property="og:image" content="{{ config.seo.og_image }}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1"></script>
    <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: {{ config.backgrounds.dashboard_main }};
            color: #e1e1e6;
            transition: all 0.3s ease;
            overflow-x: hidden;
        }
        
        /* Loading Screen */
        .loading-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0A0A0A, #1A1A2E);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            transition: opacity 0.6s ease;
        }
        .loading-logo { 
            font-size: 5rem; 
            animation: pulse 1.5s infinite; 
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }});
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        @keyframes pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.1); opacity: 0.8; } }
        .loading-number { font-size: 4rem; font-weight: 800; background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .loading-bar-container { width: 320px; height: 6px; background: rgba(79,70,229,0.2); border-radius: 6px; overflow: hidden; margin: 1rem 0; }
        .loading-bar { height: 100%; background: linear-gradient(90deg, {{ config.colors.primary }}, {{ config.colors.secondary }}); width: 0%; transition: width 0.15s ease; }
        .loading-text { margin-top: 1rem; font-size: 0.9rem; opacity: 0.7; }
        
        /* Welcome Screen */
        .welcome-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0A0A0A, #1A1A2E);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.5s ease;
        }
        .welcome-screen.hidden { opacity: 0; pointer-events: none; }
        .welcome-stats { display: flex; gap: 2rem; margin: 2rem 0; flex-wrap: wrap; justify-content: center; }
        .stat-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 24px; padding: 1.5rem; text-align: center; min-width: 180px; border: 1px solid rgba({{ config.colors.primary }},0.3); animation: fadeInUp 0.6s ease forwards; opacity: 0; }
        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .stat-number { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .begin-btn { background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }}); color: white; border: none; padding: 1rem 2.5rem; font-size: 1.2rem; font-weight: 600; border-radius: 50px; cursor: pointer; transition: all 0.3s; margin-top: 2rem; }
        .begin-btn:hover { transform: scale(1.05); box-shadow: 0 10px 30px rgba(79,70,229,0.4); }
        
        /* Dashboard Container */
        .dashboard-container { display: flex; min-height: 100vh; opacity: 0; transition: opacity 0.5s ease; }
        .dashboard-container.visible { opacity: 1; }
        
        /* Sidebar */
        .sidebar { width: 280px; background: {{ config.backgrounds.sidebar }}; position: fixed; height: 100vh; overflow-y: auto; transition: all 0.3s ease; border-right: 1px solid rgba(255,255,255,0.05); z-index: 100; }
        .sidebar-header { padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; gap: 12px; }
        .sidebar-header img { width: 45px; height: 45px; border-radius: 12px; object-fit: cover; }
        .sidebar-header h2 { font-size: 1.3rem; background: linear-gradient(135deg, #fff, {{ config.colors.primary }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-item { padding: 12px 20px; margin: 6px 12px; border-radius: 14px; display: flex; align-items: center; gap: 14px; cursor: pointer; transition: all 0.2s; color: #a1a1aa; }
        .nav-item i { width: 24px; font-size: 1.1rem; }
        .nav-item.active, .nav-item:hover { background: rgba({{ config.colors.primary }},0.15); color: white; }
        .nav-item.admin-only { border-left: 3px solid {{ config.colors.accent }}; }
        
        /* Main Content */
        .main-content { flex: 1; margin-left: 280px; padding: 1.5rem; }
        
        /* Glass Card */
        .glass-card { background: rgba(30,30,35,0.8); backdrop-filter: blur(10px); border-radius: 24px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s; cursor: pointer; }
        .glass-card:hover { transform: translateY(-4px); border-color: rgba({{ config.colors.primary }},0.5); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }
        
        /* Plan Cards Grid */
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
        
        /* Offer Banner */
        .offer-banner {
            background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }});
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
            animation: slideDown 0.5s ease-out;
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .offer-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        @keyframes shimmer {
            0% { transform: translate(-10%, -10%) rotate(0deg); }
            100% { transform: translate(10%, 10%) rotate(360deg); }
        }
        .countdown-timer {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1rem;
        }
        .countdown-item {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 0.8rem;
            min-width: 70px;
            text-align: center;
        }
        .countdown-number {
            font-size: 2rem;
            font-weight: 700;
        }
        
        /* Popular Badge */
        .popular-badge { background: {{ config.colors.accent }}; color: #1a1a1a; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; display: inline-block; margin-bottom: 1rem; }
        .price { font-size: 2rem; font-weight: 800; margin: 1rem 0; }
        .original-price { text-decoration: line-through; opacity: 0.6; font-size: 0.9rem; margin-left: 0.5rem; }
        .discount-badge {
            position: absolute;
            top: -10px;
            right: 20px;
            background: #EF4444;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        
        /* Buy Button */
        .buy-btn { background: linear-gradient(135deg, {{ config.colors.primary }}, {{ config.colors.secondary }}); color: white; border: none; padding: 12px 24px; border-radius: 40px; font-weight: 600; width: 100%; cursor: pointer; transition: all 0.2s; }
        .buy-btn:hover { transform: scale(1.02); box-shadow: 0 5px 20px rgba(79,70,229,0.3); }
        
        /* KPI Row */
        .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .kpi-card { background: rgba(30,30,35,0.6); border-radius: 20px; padding: 1.2rem; text-align: center; }
        
        /* Announcement Card */
        .announcement-card { background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(16,185,129,0.05)); border-left: 4px solid {{ config.colors.primary }}; margin-bottom: 1rem; }
        
        /* Upload Area */
        .upload-area { border: 2px dashed rgba(79,70,229,0.5); border-radius: 20px; padding: 2rem; text-align: center; margin: 1rem 0; transition: all 0.3s; }
        .upload-area.drag-over { border-color: {{ config.colors.primary }}; background: rgba(79,70,229,0.1); }
        
        /* Toggle Switch */
        .switch { position: relative; display: inline-block; width: 60px; height: 34px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: 0.4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: 0.4s; border-radius: 50%; }
        input:checked + .slider { background-color: {{ config.colors.primary }}; }
        input:checked + .slider:before { transform: translateX(26px); }
        
        /* Status Indicators */
        .status-online { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10B981; animation: pulse 2s infinite; }
        .status-offline { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #EF4444; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); position: fixed; z-index: 200; }
            .sidebar.mobile-open { transform: translateX(0); }
            .main-content { margin-left: 0; }
            .hamburger { display: block; position: fixed; top: 1rem; left: 1rem; z-index: 201; background: #1e1e22; padding: 10px 12px; border-radius: 12px; cursor: pointer; }
            .cards-grid { grid-template-columns: 1fr; }
        }
        @media (min-width: 769px) { .hamburger { display: none; } }
        
        /* Feature List */
        .feature-list { list-style: none; margin: 1rem 0; }
        .feature-list li { padding: 6px 0; display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }
        
        /* Animations */
        .fade-in { animation: fadeIn 0.5s ease-out; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
        ::-webkit-scrollbar-thumb { background: rgba(79,70,229,0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(79,70,229,0.8); }
        
        /* Toast Notifications */
        .toast-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1e1e22;
            border-left: 4px solid {{ config.colors.primary }};
            padding: 1rem 1.5rem;
            border-radius: 12px;
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 10000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: #1e1e22;
            border-radius: 24px;
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            cursor: pointer;
            font-size: 1.5rem;
        }
    </style>
</head>
<body>
<div class="loading-screen" id="loadingScreen">
    <div class="loading-logo">🚀</div>
    <div class="loading-number" id="loadingNumber">0</div>
    <div class="loading-bar-container"><div class="loading-bar" id="loadingProgress"></div></div>
    <div class="loading-text" id="loadingText">Initializing VeCho Hub...</div>
</div>
<div class="welcome-screen" id="welcomeScreen">
    <h1 style="font-size:3rem; margin-bottom:1rem;">🚀 {{ config.website_name }}</h1>
    <p style="font-size:1.2rem; opacity:0.8;">Premium Hosting & Discord Services</p>
    <div class="welcome-stats">
        <div class="stat-card"><div class="stat-number">{{ "{:,}".format(config.stats.total_customers) }}+</div><div>Active Buyers</div></div>
        <div class="stat-card"><div class="stat-number">{{ config.stats.uptime_percentage }}%</div><div>Uptime</div></div>
        <div class="stat-card"><div class="stat-number">{{ config.stats.rating }}/5</div><div>Rating ({{ "{:,}".format(config.stats.review_count) }} reviews)</div></div>
        <div class="stat-card"><div class="stat-number">Never Down</div><div>Since {{ config.stats.never_down_since }}</div></div>
    </div>
    <button class="begin-btn" onclick="startDashboard()">Let's Begin →</button>
</div>
<div class="dashboard-container" id="dashboardContainer">
    <div class="hamburger" onclick="toggleSidebar()">☰</div>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <img src="{{ config.logo_url }}" alt="logo" onerror="this.src='https://img.icons8.com/fluency/96/admin-settings-male.png'">
            <h2>{{ config.website_name }}</h2>
        </div>
        <div class="nav-item active" data-page="dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</div>
        <div class="nav-item" data-page="vps"><i class="fas fa-server"></i> VPS PLANS</div>
        <div class="nav-item" data-page="rdp"><i class="fas fa-desktop"></i> RDP PLANS</div>
        <div class="nav-item" data-page="mc"><i class="fas fa-cube"></i> MC PLANS</div>
        <div class="nav-item" data-page="games"><i class="fas fa-gamepad"></i> GAME PLANS</div>
        <div class="nav-item" data-page="nitro"><i class="fab fa-discord"></i> NITRO PLANS</div>
        <div class="nav-item" data-page="trial"><i class="fas fa-gift"></i> NITRO TRIAL</div>
        {% if session.role == 'superadmin' %}
        <div style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
            <div class="nav-item admin-only" data-page="offers"><i class="fas fa-tags"></i> OFFERS</div>
            <div class="nav-item admin-only" data-page="announcements"><i class="fas fa-bullhorn"></i> ANNOUNCEMENTS</div>
            <div class="nav-item admin-only" data-page="stock"><i class="fas fa-upload"></i> RESTOCK</div>
            <div class="nav-item admin-only" data-page="users"><i class="fas fa-user-plus"></i> USERS</div>
            <div class="nav-item admin-only" data-page="bot"><i class="fab fa-discord"></i> BOT CONTROL</div>
            <div class="nav-item admin-only" data-page="settings"><i class="fas fa-sliders-h"></i> SETTINGS</div>
            <div class="nav-item admin-only" data-page="uptime"><i class="fas fa-chart-line"></i> UPTIME</div>
            <div class="nav-item admin-only" data-page="backup"><i class="fas fa-database"></i> BACKUP</div>
        </div>
        {% endif %}
        <div class="nav-item" data-page="logout"><i class="fas fa-sign-out-alt"></i> Logout</div>
    </div>
    <div class="main-content" id="mainContent"><div id="pageContent">Loading...</div></div>
</div>

<div id="toastContainer"></div>
<div id="modal" class="modal"><div class="modal-content"><span class="modal-close" onclick="closeModal()">&times;</span><div id="modalBody"></div></div></div>

<script>
let currentLoad = 0;
let welcomeSeen = localStorage.getItem('welcomeSeen');
let loadingInterval = setInterval(() => {
    if (currentLoad < 10) currentLoad += 3;
    else if (currentLoad < 45) currentLoad += 5;
    else if (currentLoad < 90) currentLoad += 4;
    else if (currentLoad < 100) currentLoad = 100;
    document.getElementById('loadingNumber').innerText = Math.floor(currentLoad);
    document.getElementById('loadingProgress').style.width = currentLoad + '%';
    if (currentLoad >= 100) {
        clearInterval(loadingInterval);
        setTimeout(() => { document.getElementById('loadingScreen').style.display = 'none'; }, 500);
    }
}, 35);

function startDashboard() {
    document.getElementById('welcomeScreen').classList.add('hidden');
    localStorage.setItem('welcomeSeen', 'true');
    document.getElementById('dashboardContainer').classList.add('visible');
    loadPage('dashboard');
}

function loadPage(page) {
    fetch(`/api/page/${page}`).then(res => res.text()).then(html => {
        document.getElementById('pageContent').innerHTML = html;
        document.querySelectorAll('.nav-item').forEach(item => { item.classList.remove('active'); if(item.dataset.page === page) item.classList.add('active'); });
        window.scrollTo(0,0);
        // Re-initialize any scripts in the loaded content
        if (typeof initCharts === 'function') initCharts();
    }).catch(err => console.error('Page load error:', err));
}

function toggleSidebar() { document.getElementById('sidebar').classList.toggle('mobile-open'); }

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    toast.style.borderLeftColor = type === 'success' ? '#10B981' : '#EF4444';
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showModal(title, content) {
    document.getElementById('modalBody').innerHTML = `<h3>${title}</h3>${content}`;
    document.getElementById('modal').style.display = 'flex';
}

function closeModal() { document.getElementById('modal').style.display = 'none'; }

function buyPlan(planId, planName, price) {
    canvasConfetti({ particleCount: 200, spread: 100, origin: { y: 0.6 }, colors: ['#4F46E5', '#10B981', '#F59E0B'] });
    fetch('/api/purchase', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan_id: planId, plan_name: planName, price: price }) })
    .then(res => res.json())
    .then(data => { 
        if(data.success) {
            showToast(`🎉 Purchase successful! ${planName} will be delivered within 5 minutes. Check your Discord DM!`);
            loadPage('dashboard');
        } else {
            showToast('Error: ' + (data.error || 'Purchase failed'), 'error');
        }
    });
}

document.querySelectorAll('.nav-item').forEach(item => { 
    item.addEventListener('click', () => { 
        const page = item.dataset.page; 
        if(page === 'logout') window.location.href = '/logout'; 
        else loadPage(page); 
        if(window.innerWidth <= 768) toggleSidebar(); 
    }); 
});

if(welcomeSeen === 'true') { 
    document.getElementById('welcomeScreen').classList.add('hidden'); 
    document.getElementById('dashboardContainer').classList.add('visible'); 
    loadPage('dashboard'); 
}
</script>
</body>
</html>
'''

# ==================== PAGE ROUTES ====================
@app.route('/')
def index():
    data = load_db()
    if data['dashboard_config'].get('maintenance_mode') and session.get('role') != 'superadmin':
        maintenance_html = f'''
        <body style="background:#0A0A0A;color:white;text-align:center;padding:4rem;font-family:monospace;">
            <div style="max-width:500px;margin:0 auto;">
                <h1 style="font-size:4rem;">🔧</h1>
                <h2>{data['dashboard_config']['maintenance_message']}</h2>
                {f'<p>Expected back: {data["dashboard_config"]["maintenance_end_time"]}</p>' if data['dashboard_config'].get('maintenance_end_time') else ''}
            </div>
        </body>
        '''
        return maintenance_html
    return render_template_string(HTML_TEMPLATE, config=data['dashboard_config'], session=session)

@app.route('/api/page/<page>')
def get_page(page):
    data = load_db()
    role = session.get('role', 'user')
    
    if page == 'dashboard':
        stats = data['dashboard_config']['stats']
        activity = data['dashboard_config']['activity_feed']
        announcements = [a for a in data.get('announcements', []) if a.get('active', True)]
        offers = get_active_offers()
        
        # Generate offers HTML
        offers_html = ''
        for offer in offers:
            end_date = offer.get('end_date', '')
            emoji = offer.get('emoji', '🎉')
            title = offer.get('title', 'Special Offer')
            description = offer.get('description', '')
            discount = offer.get('discount_value', 0)
            color = offer.get('banner_color', data['dashboard_config']['colors']['primary'])
            offers_html += f'''
            <div class="offer-banner" style="background: linear-gradient(135deg, {color}, {data['dashboard_config']['colors']['secondary']});">
                <div style="font-size:3rem; text-align:center;">{emoji}</div>
                <h2 style="text-align:center;">{title}</h2>
                <p style="text-align:center; margin:10px 0;">{description}</p>
                <div style="text-align:center; font-size:2rem; font-weight:bold;">{discount}% OFF</div>
                <div id="countdown_offer" class="countdown-timer"></div>
            </div>
            <script>
            function startOfferCountdown(endDate) {{
                const target = new Date(endDate).getTime();
                const timer = setInterval(() => {{
                    const now = new Date().getTime();
                    const diff = target - now;
                    if(diff <= 0) {{
                        clearInterval(timer);
                        document.getElementById('countdown_offer').innerHTML = '<div style="text-align:center;">🎉 Offer Ended!</div>';
                        return;
                    }}
                    const days = Math.floor(diff / (1000*60*60*24));
                    const hours = Math.floor((diff % (86400000)) / 3600000);
                    const minutes = Math.floor((diff % 3600000) / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);
                    document.getElementById('countdown_offer').innerHTML = `
                        <div class="countdown-timer">
                            <div class="countdown-item"><div class="countdown-number">${{days}}</div><div>Days</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{hours}}</div><div>Hours</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{minutes}}</div><div>Mins</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{seconds}}</div><div>Secs</div></div>
                        </div>
                    `;
                }}, 1000);
            }}
            startOfferCountdown('{end_date}');
            </script>
            '''
        
        ann_html = ''.join(f'''
        <div class="glass-card announcement-card">
            <div style="font-size:1.2rem;">{a["emoji"]} {a["title"]}</div>
            <p>{a["content"]}</p>
            <small>Type: {a["type"]}</small>
        </div>
        ''' for a in announcements[:3])
        
        return f'''
        <div class="fade-in">
            {offers_html}
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:2rem;">
                <div style="font-size:3rem;">{session.get('avatar', '👤')}</div>
                <div>
                    <h1>Welcome back, {session.get('username', 'User')}!</h1>
                    <p>Your services are all online. 🟢</p>
                </div>
            </div>
            {ann_html}
            <div class="kpi-row">
                <div class="kpi-card"><i class="fas fa-chart-line"></i><h3>{stats['active_services']:,}</h3><p>Active Services</p></div>
                <div class="kpi-card"><i class="fas fa-dollar-sign"></i><h3>$0</h3><p>Total Spent</p></div>
                <div class="kpi-card"><i class="fas fa-shopping-cart"></i><h3>0</h3><p>Active Orders</p></div>
                <div class="kpi-card"><i class="fas fa-ticket-alt"></i><h3>0</h3><p>Support Tickets</p></div>
            </div>
            <div class="glass-card">
                <h3>🟢 Uptime Status</h3>
                <p>All systems operational. {stats['uptime_percentage']}% uptime this month.</p>
                <p><i class="fas fa-globe"></i> Response Time: &lt;{stats['response_time_ms']}ms</p>
                <p><i class="fas fa-shield-alt"></i> DDoS Protection: {stats['ddos_capacity']}</p>
                <div style="margin-top:1rem;">
                    <i class="fab fa-discord"></i> Discord: <a href="{data['bot_config'].get('discord_invite_url', '#')}" target="_blank" style="color:{data['dashboard_config']['colors']['primary']};">Join our Discord</a>
                </div>
            </div>
            <h3 style="margin-top:2rem;">📋 Recent Activity</h3>
            <div class="cards-grid">
                {''.join(f'<div class="glass-card"><i class="fas fa-user"></i> <strong>{a["user"]}</strong> {a["action"]} {a["plan"]}<br><small>{a["time"]} • ${a.get("amount",0)}</small></div>' for a in activity[:6])}
            </div>
            <div style="margin-top:2rem; text-align:center;">
                <canvas id="activityChart" style="max-height:300px; width:100%;"></canvas>
            </div>
            <script>
            function initCharts() {{
                const ctx = document.getElementById('activityChart')?.getContext('2d');
                if(ctx) {{
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                            datasets: [{{
                                label: 'Sales',
                                data: [12450, 18760, 22450, 31280],
                                borderColor: '{data['dashboard_config']['colors']['primary']}',
                                backgroundColor: 'rgba(79,70,229,0.1)',
                                tension: 0.4,
                                fill: true
                            }}]
                        }},
                        options: {{ responsive: true, maintainAspectRatio: true }}
                    }});
                }}
            }}
            initCharts();
            </script>
        </div>'''
    
    elif page == 'offers' and role == 'superadmin':
        offers = data.get('offers', [])
        offers_html = ''.join(f'''
        <div class="glass-card" style="margin-bottom:1rem; background: linear-gradient(135deg, {o.get('banner_color', '#4F46E5')}20, transparent);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:2rem;">{o.get('emoji', '🎉')}</span>
                    <h3>{o['title']}</h3>
                    <p>{o['description']}</p>
                    <p><strong>{o['discount_value']}% OFF</strong> on {o['applicable_plans']}</p>
                    <small>Code: {o.get('code', 'N/A')} • Used: {o.get('used_count', 0)}/{o.get('usage_limit', '∞')}</small>
                    <br><small>Ends: {o['end_date'][:10]}</small>
                </div>
                <div>
                    <label class="switch">
                        <input type="checkbox" onchange="toggleOffer('{o['id']}', this.checked)" {'checked' if o.get('is_active') else ''}>
                        <span class="slider"></span>
                    </label>
                    <button onclick="deleteOffer('{o['id']}')" style="background:#EF4444; color:white; border:none; padding:8px 16px; border-radius:20px; margin-top:10px; cursor:pointer;">Delete</button>
                </div>
            </div>
        </div>
        ''' for o in offers)
        
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-tags"></i> Offer Management</h1>
            <div class="glass-card">
                <h3>➕ Create New Offer</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1rem;">
                    <input type="text" id="offerTitle" placeholder="Title (e.g., FLASH SALE!)" style="padding:10px; border-radius:10px; background:#1e1e22; color:white; border:1px solid rgba(255,255,255,0.1);">
                    <input type="text" id="offerDesc" placeholder="Description" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <select id="offerType" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                        <option value="percentage">Percentage (%)</option>
                        <option value="fixed">Fixed Amount ($)</option>
                    </select>
                    <input type="number" id="offerValue" placeholder="Discount Value" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <select id="offerPlans" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                        <option value="all">All Plans</option>
                        <option value="vps">VPS Only</option>
                        <option value="rdp">RDP Only</option>
                        <option value="mc">MC Only</option>
                        <option value="games">Games Only</option>
                        <option value="nitro">Nitro Only</option>
                    </select>
                    <input type="datetime-local" id="offerEndDate" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <input type="color" id="offerColor" value="#4F46E5" style="padding:10px; border-radius:10px;">
                    <input type="text" id="offerEmoji" placeholder="Emoji (e.g., 🔥)" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <input type="text" id="offerCode" placeholder="Coupon Code (optional)" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                </div>
                <button class="buy-btn" onclick="createOffer()" style="margin-top:1rem;">Create Offer →</button>
            </div>
            <div style="margin-top:2rem;"><h3>📋 Current Offers</h3>{offers_html or '<p>No offers created yet.</p>'}</div>
            <script>
            function createOffer() {{
                fetch('/api/create-offer', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        title: document.getElementById('offerTitle').value,
                        description: document.getElementById('offerDesc').value,
                        discount_type: document.getElementById('offerType').value,
                        discount_value: parseFloat(document.getElementById('offerValue').value),
                        applicable_plans: document.getElementById('offerPlans').value,
                        end_date: document.getElementById('offerEndDate').value,
                        banner_color: document.getElementById('offerColor').value,
                        emoji: document.getElementById('offerEmoji').value,
                        code: document.getElementById('offerCode').value
                    }})
                }}).then(() => location.reload());
            }}
            function toggleOffer(id, enabled) {{
                fetch('/api/toggle-offer/' + id, {{ method: 'POST', body: JSON.stringify({{ enabled: enabled }}), headers: {{ 'Content-Type': 'application/json' }} }}).then(() => location.reload());
            }}
            function deleteOffer(id) {{
                if(confirm('Delete this offer?')) fetch('/api/delete-offer/' + id, {{ method: 'POST' }}).then(() => location.reload());
            }}
            </script>
        </div>'''
    
    elif page == 'announcements' and role == 'superadmin':
        announcements = data.get('announcements', [])
        ann_list = ''.join(f'''
        <div class="glass-card" style="margin-bottom:1rem;">
            <div><span style="font-size:1.5rem;">{a["emoji"]}</span> <strong>{a["title"]}</strong></div>
            <p>{a["content"]}</p>
            <div style="margin-top:10px;">
                <label class="switch"><input type="checkbox" onchange="toggleAnnouncement('{a['id']}', this.checked)" {'checked' if a['active'] else ''}><span class="slider"></span></label>
                <button onclick="deleteAnnouncement('{a['id']}')" style="background:#EF4444; color:white; border:none; padding:5px 15px; border-radius:20px; margin-left:10px;">Delete</button>
            </div>
        </div>
        ''' for a in announcements)
        
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-bullhorn"></i> Announcement Manager</h1>
            <div class="glass-card">
                <h3>➕ Create New Announcement</h3>
                <input type="text" id="annTitle" placeholder="Title (with emojis)" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                <textarea id="annContent" placeholder="Announcement content" rows="3" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;"></textarea>
                <select id="annType" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    <option value="success">Success</option><option value="info">Info</option><option value="warning">Warning</option>
                </select>
                <input type="text" id="annEmoji" placeholder="Emoji (e.g., 🎉)" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                <button class="buy-btn" onclick="createAnnouncement()">Create Announcement</button>
            </div>
            <div style="margin-top:2rem;"><h3>📋 Current Announcements</h3>{ann_list or "<p>No announcements</p>"}</div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>🔗 Discord Settings</h3>
                <label>Discord Invite URL:</label>
                <input type="text" id="discordInvite" value="{data['bot_config'].get('discord_invite_url', '')}" style="width:100%; padding:10px; margin:5px 0;">
                <label>Discord Server ID:</label>
                <input type="text" id="discordServerId" value="{data['bot_config'].get('discord_server_id', '')}" style="width:100%; padding:10px; margin:5px 0;">
                <button class="buy-btn" onclick="saveDiscordSettings()">Save Settings</button>
            </div>
            <script>
            function createAnnouncement() {{
                fetch('/api/create-announcement', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        title: document.getElementById('annTitle').value,
                        content: document.getElementById('annContent').value,
                        type: document.getElementById('annType').value,
                        emoji: document.getElementById('annEmoji').value
                    }})
                }}).then(() => location.reload());
            }}
            function toggleAnnouncement(id, enabled) {{
                fetch('/api/toggle-announcement/' + id, {{ method: 'POST', body: JSON.stringify({{ enabled: enabled }}), headers: {{ 'Content-Type': 'application/json' }} }}).then(() => location.reload());
            }}
            function deleteAnnouncement(id) {{
                if(confirm('Delete this announcement?')) fetch('/api/delete-announcement/' + id, {{ method: 'POST' }}).then(() => location.reload());
            }}
            function saveDiscordSettings() {{
                fetch('/api/save-discord-settings', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        discord_invite_url: document.getElementById('discordInvite').value,
                        discord_server_id: document.getElementById('discordServerId').value
                    }})
                }}).then(() => showToast('Settings saved!'));
            }}
            </script>
        </div>'''
    
    elif page == 'stock' and role == 'superadmin':
        stock_files = data.get('stock_files', {})
        plans = []
        for category in ['VPS', 'RDP', 'MC', 'GAMES', 'NITRO', 'TRIAL']:
            for p in data['plans'].get(category, []):
                plans.append(p)
        options_html = ''.join(f'<option value="{p["id"]}">{p["emoji"]} {p["name"]} (${p["price"]})</option>' for p in plans)
        stock_list = ''.join(f'<div class="glass-card" style="margin-bottom:0.5rem; padding:1rem;"><strong>{pid}</strong>: {fname} <button onclick="deleteStock(\'{pid}\')" style="background:#EF4444; color:white; border:none; padding:5px 15px; border-radius:20px; float:right;">Delete</button></div>' for pid,fname in stock_files.items())
        
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-upload"></i> Stock Management</h1>
            <div class="glass-card">
                <h3>📤 Upload Stock File (.txt)</h3>
                <div class="upload-area" id="dropZone" ondragover="event.preventDefault(); this.classList.add('drag-over')" ondragleave="this.classList.remove('drag-over')" ondrop="handleDrop(event)">
                    <i class="fas fa-cloud-upload-alt" style="font-size:3rem;"></i>
                    <p>Drag & drop or click to upload</p>
                    <input type="file" id="fileInput" accept=".txt" style="display:none;">
                </div>
                <select id="planSelect" style="width:100%; padding:12px; margin:1rem 0; border-radius:12px; background:#1e1e22; color:white;">
                    <option value="">Select plan for this stock</option>
                    {options_html}
                </select>
                <button class="buy-btn" onclick="uploadStock()">Upload Stock</button>
            </div>
            <div style="margin-top:2rem;"><h3>📋 Current Stock Files</h3>{stock_list or "<p>No stock files uploaded</p>"}</div>
            <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            dropZone.onclick = () => fileInput.click();
            function handleDrop(e) {{
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                fileInput.files = e.dataTransfer.files;
            }}
            function uploadStock() {{
                const file = fileInput.files[0];
                const planId = document.getElementById('planSelect').value;
                if(!file || !planId) {{ showToast('Select file and plan', 'error'); return; }}
                const formData = new FormData();
                formData.append('stock_file', file);
                formData.append('plan_id', planId);
                fetch('/api/upload-stock', {{ method: 'POST', body: formData }})
                .then(res => res.json())
                .then(data => {{ if(data.success) location.reload(); else showToast('Upload failed', 'error'); }});
            }}
            function deleteStock(planId) {{
                if(confirm('Delete stock for this plan?')) fetch('/api/delete-stock/' + planId, {{ method: 'POST' }}).then(() => location.reload());
            }}
            </script>
        </div>'''
    
    elif page == 'users' and role == 'superadmin':
        users = data['users']
        users_html = ''.join(f'<tr><td style="padding:10px; border-bottom:1px solid rgba(255,255,255,0.1);">{u}</td><td style="padding:10px;">{info["username"]}</td><td style="padding:10px;">{info["role"]}</td><td style="padding:10px;">{info.get("discord_username", "N/A")}</td><td style="padding:10px;">${info.get("balance", 0)}</td><td><button onclick="editUser(\'{u}\')" style="background:{data['dashboard_config']['colors']['primary']}; border:none; padding:5px 10px; border-radius:10px; color:white;">Edit</button></td></tr>' for u, info in users.items())
        
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-users"></i> User Management</h1>
            <div class="glass-card">
                <h3>➕ Create New User</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem;">
                    <input type="email" id="newEmail" placeholder="Email" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <input type="text" id="newUsername" placeholder="Username" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <input type="password" id="newPassword" placeholder="Password" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                    <select id="newRole" style="padding:10px; border-radius:10px; background:#1e1e22; color:white;">
                        <option value="user">User</option>
                        <option value="superadmin">Admin</option>
                    </select>
                </div>
                <button class="buy-btn" onclick="createUser()" style="margin-top:1rem;">Create User →</button>
            </div>
            <div style="margin-top:2rem; overflow-x:auto;">
                <h3>📋 All Users</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="border-bottom:2px solid rgba(255,255,255,0.1);">
                        <th style="padding:10px; text-align:left;">Email</th><th>Username</th><th>Role</th><th>Discord</th><th>Balance</th><th>Actions</th>
                    </tr>
                    {users_html}
                 </table>
            </div>
            <script>
            function createUser() {{
                fetch('/api/create-user', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        email: document.getElementById('newEmail').value,
                        username: document.getElementById('newUsername').value,
                        password: document.getElementById('newPassword').value,
                        role: document.getElementById('newRole').value
                    }})
                }}).then(() => location.reload());
            }}
            function editUser(email) {{
                showModal('Edit User', `
                    <input type="text" id="editUsername" placeholder="Username" style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="number" id="editBalance" placeholder="Balance" step="0.01" style="width:100%; padding:10px; margin:5px 0;"><br>
                    <select id="editRole" style="width:100%; padding:10px; margin:5px 0;">
                        <option value="user">User</option>
                        <option value="superadmin">Admin</option>
                    </select><br>
                    <button onclick="saveUserEdit('${{email}}')" class="buy-btn">Save Changes</button>
                `);
            }}
            function saveUserEdit(email) {{
                fetch('/api/update-user', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        email: email,
                        username: document.getElementById('editUsername').value,
                        balance: parseFloat(document.getElementById('editBalance').value),
                        role: document.getElementById('editRole').value
                    }})
                }}).then(() => {{ closeModal(); location.reload(); }});
            }}
            </script>
        </div>'''
    
    elif page == 'bot' and role == 'superadmin':
        bot_config = data['bot_config']
        return f'''
        <div class="fade-in">
            <h1><i class="fab fa-discord"></i> Discord Bot Control Panel</h1>
            <div class="glass-card">
                <h3>🤖 Bot Configuration</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:1rem;">
                    <div>
                        <label>Bot Token:</label>
                        <input type="password" id="botToken" value="{bot_config.get('bot_token', '')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                        <small>Enter your Discord bot token</small>
                    </div>
                    <div>
                        <label>Bot Prefix:</label>
                        <input type="text" id="botPrefix" value="{bot_config.get('bot_prefix', '!')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    </div>
                    <div>
                        <label>Bot Status:</label>
                        <select id="botStatus" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                            <option value="online" {'selected' if bot_config.get('bot_status') == 'online' else ''}>Online</option>
                            <option value="idle" {'selected' if bot_config.get('bot_status') == 'idle' else ''}>Idle</option>
                            <option value="dnd" {'selected' if bot_config.get('bot_status') == 'dnd' else ''}>Do Not Disturb</option>
                        </select>
                    </div>
                    <div>
                        <label>Activity Type:</label>
                        <select id="botActivityType" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                            <option value="playing" {'selected' if bot_config.get('bot_activity_type') == 'playing' else ''}>Playing</option>
                            <option value="watching" {'selected' if bot_config.get('bot_activity_type') == 'watching' else ''}>Watching</option>
                            <option value="listening" {'selected' if bot_config.get('bot_activity_type') == 'listening' else ''}>Listening</option>
                        </select>
                    </div>
                    <div>
                        <label>Activity Name:</label>
                        <input type="text" id="botActivityName" value="{bot_config.get('bot_activity_name', 'VeCho Hub | !help')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    </div>
                    <div>
                        <label>Welcome Channel ID:</label>
                        <input type="text" id="welcomeChannel" value="{bot_config.get('welcome_channel_id', '')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    </div>
                    <div>
                        <label>Auto Role ID:</label>
                        <input type="text" id="autoRole" value="{bot_config.get('auto_role_id', '')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    </div>
                    <div>
                        <label>Log Channel ID:</label>
                        <input type="text" id="logChannel" value="{bot_config.get('log_channel_id', '')}" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#1e1e22; color:white;">
                    </div>
                </div>
                <div style="margin-top:1rem;">
                    <label class="switch">
                        <input type="checkbox" id="botEnabled" onchange="saveBotConfig()" {'checked' if bot_config.get('bot_enabled') else ''}>
                        <span class="slider"></span>
                    </label>
                    <span style="margin-left:10px;">Enable Discord Bot</span>
                </div>
                <button class="buy-btn" onclick="saveBotConfig()" style="margin-top:1rem;">Save Bot Configuration</button>
                <button class="buy-btn" onclick="restartBot()" style="margin-top:1rem; background:#F59E0B;">Restart Bot</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>📝 DM Message Template</h3>
                <textarea id="dmTemplate" rows="6" style="width:100%; padding:10px; border-radius:10px; background:#1e1e22; color:white;">{bot_config.get('dm_message_template', '')}</textarea>
                <p><small>Available variables: {{plan_name}}, {{price}}, {{order_id}}, {{stock_codes}}, {{discord_invite}}</small></p>
                <button class="buy-btn" onclick="saveDMTemplate()">Save DM Template</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>📊 Bot Statistics</h3>
                <p>Bot Status: <span id="botStatusIndicator" class="{'status-online' if bot_running else 'status-offline'}"></span> <span id="botStatusText">{'Online' if bot_running else 'Offline'}</span></p>
                <p>Commands Loaded: 20+</p>
                <p>Servers: <span id="botGuildCount">-</span></p>
            </div>
            <script>
            function saveBotConfig() {{
                fetch('/api/save-bot-config', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        bot_token: document.getElementById('botToken').value,
                        bot_enabled: document.getElementById('botEnabled').checked,
                        bot_prefix: document.getElementById('botPrefix').value,
                        bot_status: document.getElementById('botStatus').value,
                        bot_activity_type: document.getElementById('botActivityType').value,
                        bot_activity_name: document.getElementById('botActivityName').value,
                        welcome_channel_id: document.getElementById('welcomeChannel').value,
                        auto_role_id: document.getElementById('autoRole').value,
                        log_channel_id: document.getElementById('logChannel').value
                    }})
                }}).then(() => showToast('Bot config saved! Bot will restart automatically'));
            }}
            function saveDMTemplate() {{
                fetch('/api/save-dm-template', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ template: document.getElementById('dmTemplate').value }})
                }}).then(() => showToast('DM template saved!'));
            }}
            function restartBot() {{
                fetch('/api/restart-bot', {{ method: 'POST' }}).then(() => showToast('Bot restarting...'));
            }}
            </script>
        </div>'''
    
    elif page == 'settings' and role == 'superadmin':
        config = data['dashboard_config']
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-sliders-h"></i> Dashboard Settings</h1>
            <div class="glass-card">
                <h3>🏢 General Settings</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1rem;">
                    <div><label>Website Name:</label><input type="text" id="websiteName" value="{config['website_name']}" style="width:100%; padding:10px; border-radius:10px; background:#1e1e22; color:white;"></div>
                    <div><label>Logo URL:</label><input type="text" id="logoUrl" value="{config['logo_url']}" style="width:100%; padding:10px; border-radius:10px; background:#1e1e22; color:white;"></div>
                    <div><label>Primary Color:</label><input type="color" id="primaryColor" value="{config['colors']['primary']}" style="width:100%;"></div>
                    <div><label>Secondary Color:</label><input type="color" id="secondaryColor" value="{config['colors']['secondary']}" style="width:100%;"></div>
                </div>
                <button class="buy-btn" onclick="saveGeneralSettings()" style="margin-top:1rem;">Save Settings</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>🎨 Background Settings</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem;">
                    <div><label>Main Background:</label><input type="color" id="bgMain" value="{config['backgrounds']['dashboard_main']}" style="width:100%;"></div>
                    <div><label>Sidebar Background:</label><input type="color" id="bgSidebar" value="{config['backgrounds']['sidebar']}" style="width:100%;"></div>
                    <div><label>VPS Section:</label><input type="color" id="bgVps" value="{config['backgrounds']['vps_section']}" style="width:100%;"></div>
                    <div><label>RDP Section:</label><input type="color" id="bgRdp" value="{config['backgrounds']['rdp_section']}" style="width:100%;"></div>
                </div>
                <button class="buy-btn" onclick="saveBackgroundSettings()" style="margin-top:1rem;">Save Backgrounds</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>🔧 Maintenance Mode</h3>
                <div>
                    <label class="switch">
                        <input type="checkbox" id="maintenanceMode" onchange="saveMaintenance()" {'checked' if config['maintenance_mode'] else ''}>
                        <span class="slider"></span>
                    </label>
                    <span style="margin-left:10px;">Enable Maintenance Mode</span>
                </div>
                <div style="margin-top:1rem;">
                    <label>Maintenance Message:</label>
                    <textarea id="maintenanceMsg" rows="3" style="width:100%; padding:10px; border-radius:10px; background:#1e1e22; color:white;">{config['maintenance_message']}</textarea>
                </div>
                <button class="buy-btn" onclick="saveMaintenance()">Save Maintenance Settings</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>📊 Stats Customization (Fake Stats)</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem;">
                    <div><label>Total Customers:</label><input type="number" id="statCustomers" value="{config['stats']['total_customers']}" style="width:100%; padding:10px;"></div>
                    <div><label>Active Services:</label><input type="number" id="statServices" value="{config['stats']['active_services']}" style="width:100%; padding:10px;"></div>
                    <div><label>Uptime %:</label><input type="number" step="0.1" id="statUptime" value="{config['stats']['uptime_percentage']}" style="width:100%; padding:10px;"></div>
                    <div><label>Rating:</label><input type="number" step="0.1" id="statRating" value="{config['stats']['rating']}" style="width:100%; padding:10px;"></div>
                </div>
                <button class="buy-btn" onclick="saveStats()">Save Stats</button>
            </div>
            <script>
            function saveGeneralSettings() {{
                fetch('/api/save-settings', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        website_name: document.getElementById('websiteName').value,
                        logo_url: document.getElementById('logoUrl').value,
                        primary_color: document.getElementById('primaryColor').value,
                        secondary_color: document.getElementById('secondaryColor').value
                    }})
                }}).then(() => showToast('Settings saved! Reloading...')).then(() => location.reload());
            }}
            function saveBackgroundSettings() {{
                fetch('/api/save-backgrounds', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        dashboard_main: document.getElementById('bgMain').value,
                        sidebar: document.getElementById('bgSidebar').value,
                        vps_section: document.getElementById('bgVps').value,
                        rdp_section: document.getElementById('bgRdp').value
                    }})
                }}).then(() => showToast('Backgrounds saved! Reloading...')).then(() => location.reload());
            }}
            function saveMaintenance() {{
                fetch('/api/save-maintenance', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        maintenance_mode: document.getElementById('maintenanceMode').checked,
                        maintenance_message: document.getElementById('maintenanceMsg').value
                    }})
                }}).then(() => showToast('Maintenance settings saved!'));
            }}
            function saveStats() {{
                fetch('/api/save-stats', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        total_customers: parseInt(document.getElementById('statCustomers').value),
                        active_services: parseInt(document.getElementById('statServices').value),
                        uptime_percentage: parseFloat(document.getElementById('statUptime').value),
                        rating: parseFloat(document.getElementById('statRating').value)
                    }})
                }}).then(() => showToast('Stats saved! Reloading...')).then(() => location.reload());
            }}
            </script>
        </div>'''
    
    elif page == 'uptime' and role == 'superadmin':
        monitors = data['dashboard_config'].get('uptime_monitors', [])
        monitors_html = ''.join(f'<div class="glass-card"><i class="fas fa-{"globe" if m["type"]=="url" else "robot"}"></i> <strong>{m["name"]}</strong><br>Status: <span class="{"status-online" if m.get("status")=="online" else "status-offline"}"></span> {m.get("status","unknown")}<br>Uptime: {m.get("uptime", 99.9)}%<br><small>Last checked: {m.get("last_check", "Never")}</small></div>' for m in monitors)
        
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-chart-line"></i> Uptime Monitor</h1>
            <div class="glass-card">
                <h3>➕ Add Monitor</h3>
                <div style="display:flex; gap:1rem; flex-wrap:wrap;">
                    <input type="text" id="monitorUrl" placeholder="URL or Discord Bot Token" style="flex:1; padding:12px; border-radius:12px; background:#1e1e22; color:white;">
                    <select id="monitorType" style="padding:12px; border-radius:12px; background:#1e1e22; color:white;">
                        <option value="url">Website URL</option>
                        <option value="discord">Discord Bot</option>
                    </select>
                    <button class="buy-btn" onclick="addMonitor()" style="width:auto;">Add Monitor</button>
                </div>
            </div>
            <div style="margin-top:2rem; display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:1rem;">
                {monitors_html or '<p>No monitors added yet.</p>'}
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <canvas id="uptimeChart" style="max-height:300px;"></canvas>
            </div>
            <script>
            function addMonitor() {{
                fetch('/api/add-monitor', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        url: document.getElementById('monitorUrl').value,
                        type: document.getElementById('monitorType').value
                    }})
                }}).then(() => location.reload());
            }}
            const ctx = document.getElementById('uptimeChart')?.getContext('2d');
            if(ctx) {{
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                        datasets: [{{
                            label: 'Uptime %',
                            data: [99.9, 99.8, 100, 99.9, 99.95, 99.9],
                            borderColor: '{data['dashboard_config']['colors']['primary']}',
                            backgroundColor: 'rgba(79,70,229,0.1)',
                            tension: 0.4,
                            fill: true
                        }}]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: true }}
                }});
            }}
            </script>
        </div>'''
    
    elif page == 'backup' and role == 'superadmin':
        backup_config = data.get('backup_config', {})
        return f'''
        <div class="fade-in">
            <h1><i class="fas fa-database"></i> Backup Management</h1>
            <div class="glass-card">
                <h3>📦 Create Backup</h3>
                <p>Create a full backup of all dashboard data including users, orders, settings, and stock files.</p>
                <button class="buy-btn" onclick="createBackup()">Create Backup Now →</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>⚙️ Auto Backup Settings</h3>
                <div>
                    <label class="switch">
                        <input type="checkbox" id="autoBackup" onchange="saveBackupSettings()" {'checked' if backup_config.get('auto_backup') else ''}>
                        <span class="slider"></span>
                    </label>
                    <span style="margin-left:10px;">Enable Auto Backup</span>
                </div>
                <div style="margin-top:1rem;">
                    <label>Backup Interval (hours):</label>
                    <input type="number" id="backupInterval" value="{backup_config.get('backup_interval', 24)}" style="width:100%; padding:10px; margin-top:5px; border-radius:10px; background:#1e1e22; color:white;">
                </div>
                <div style="margin-top:1rem;">
                    <label>Backup Retention (days):</label>
                    <input type="number" id="backupRetention" value="{backup_config.get('backup_retention', 7)}" style="width:100%; padding:10px; margin-top:5px; border-radius:10px; background:#1e1e22; color:white;">
                </div>
                <button class="buy-btn" onclick="saveBackupSettings()" style="margin-top:1rem;">Save Settings</button>
            </div>
            <div class="glass-card" style="margin-top:1rem;">
                <h3>📋 Available Backups</h3>
                <div id="backupList">Loading...</div>
            </div>
            <script>
            function createBackup() {{
                fetch('/api/create-backup', {{ method: 'POST' }}).then(() => showToast('Backup created!'));
            }}
            function saveBackupSettings() {{
                fetch('/api/save-backup-settings', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        auto_backup: document.getElementById('autoBackup').checked,
                        backup_interval: parseInt(document.getElementById('backupInterval').value),
                        backup_retention: parseInt(document.getElementById('backupRetention').value)
                    }})
                }}).then(() => showToast('Backup settings saved!'));
            }}
            function loadBackups() {{
                fetch('/api/list-backups').then(res => res.json()).then(data => {{
                    if(data.backups && data.backups.length) {{
                        document.getElementById('backupList').innerHTML = data.backups.map(b => `
                            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid rgba(255,255,255,0.1);">
                                <span>📁 ${{b}}</span>
                                <div>
                                    <button onclick="downloadBackup('${{b}}')" style="background:{data['dashboard_config']['colors']['primary']}; border:none; padding:5px 15px; border-radius:20px; color:white;">Download</button>
                                    <button onclick="restoreBackup('${{b}}')" style="background:#F59E0B; border:none; padding:5px 15px; border-radius:20px; color:white; margin-left:10px;">Restore</button>
                                </div>
                            </div>
                        `).join('');
                    }} else {{
                        document.getElementById('backupList').innerHTML = '<p>No backups found.</p>';
                    }}
                }});
            }}
            function downloadBackup(filename) {{ window.location.href = '/api/download-backup/' + filename; }}
            function restoreBackup(filename) {{
                if(confirm('Restoring will overwrite current data. Continue?')) {{
                    fetch('/api/restore-backup/' + filename, {{ method: 'POST' }}).then(() => showToast('Backup restored! Reloading...')).then(() => location.reload());
                }}
            }}
            loadBackups();
            </script>
        </div>'''
    
    elif page in ['vps', 'rdp', 'mc', 'games', 'nitro', 'trial']:
        category_map = {'vps': 'VPS', 'rdp': 'RDP', 'mc': 'MC', 'games': 'GAMES', 'nitro': 'NITRO', 'trial': 'TRIAL'}
        category = category_map.get(page, 'VPS')
        plans = data['plans'].get(category, [])
        offers = get_active_offers(category.lower())
        discount_percent = offers[0]['discount_value'] if offers else 0
        
        title_map = {'vps': '🚀 VPS Hosting Plans', 'rdp': '💻 RDP Plans', 'mc': '⛏️ Minecraft Server Plans', 'games': '🎮 Game Server Plans', 'nitro': '💜 Discord Nitro Plans', 'trial': '🎁 Nitro Trial Plans'}
        
        # Generate offers banner
        offers_html = ''
        for offer in offers:
            offers_html += f'''
            <div class="offer-banner" style="background: linear-gradient(135deg, {offer['banner_color']}, {data['dashboard_config']['colors']['secondary']}); margin-bottom:2rem;">
                <div style="font-size:2rem; text-align:center;">{offer['emoji']}</div>
                <h3 style="text-align:center;">{offer['title']}</h3>
                <p style="text-align:center;">{offer['description']}</p>
                <div style="text-align:center; font-size:1.5rem; font-weight:bold;">{offer['discount_value']}% OFF</div>
                <div class="countdown-timer" id="countdown_{offer['id']}"></div>
            </div>
            <script>
            (function() {{
                const endDate = new Date('{offer['end_date']}').getTime();
                const timer = setInterval(() => {{
                    const now = new Date().getTime();
                    const diff = endDate - now;
                    if(diff <= 0) {{
                        clearInterval(timer);
                        document.getElementById('countdown_{offer['id']}').innerHTML = '<div style="text-align:center;">🎉 Offer Ended!</div>';
                        return;
                    }}
                    const days = Math.floor(diff / (1000*60*60*24));
                    const hours = Math.floor((diff % (86400000)) / 3600000);
                    const minutes = Math.floor((diff % 3600000) / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);
                    document.getElementById('countdown_{offer['id']}').innerHTML = `
                        <div class="countdown-timer">
                            <div class="countdown-item"><div class="countdown-number">${{days}}</div><div>Days</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{hours}}</div><div>Hours</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{minutes}}</div><div>Mins</div></div>
                            <div class="countdown-item"><div class="countdown-number">${{seconds}}</div><div>Secs</div></div>
                        </div>
                    `;
                }}, 1000);
            }})();
            </script>
            '''
        
        plans_html = ''
        for p in plans:
            discounted_price = calculate_discounted_price(p['price'], category.lower())
            popular = '<div class="popular-badge">⭐ POPULAR</div>' if p.get('popular') else ''
            original_price_html = f'<span class="original-price">${p["price"]}</span>' if discount_percent > 0 else ''
            
            features_html = ''
            if 'cpu' in p:
                features_html = f'<li>💻 {p["cpu"]}</li><li>📀 {p["ram"]}</li><li>💾 {p["storage"]}</li><li>🌐 {p.get("bandwidth", "Unlimited")}</li>'
            elif 'slots' in p:
                features_html = f'<li>📀 {p["ram"]}</li><li>👥 {p["slots"]} slots</li><li>🛡️ DDoS Protection</li><li>🔧 Full Control</li>'
            else:
                features_html = f'<li>✨ {p.get("features", "Premium features")}</li>'
            
            if p.get('extras'):
                for extra in p.get('extras', []):
                    features_html += f'<li>➕ {extra}</li>'
            
            bg_key = f"{category.lower()}_section"
            bg_color = data['dashboard_config']['backgrounds'].get(bg_key, '#0F0F0F')
            
            plans_html += f'''
            <div class="glass-card" style="background:{bg_color}; position:relative;">
                {popular}
                <div style="font-size:2.5rem; text-align:center;">{p["emoji"]}</div>
                <h3 style="text-align:center; margin:10px 0;">{p["name"]}</h3>
                <ul class="feature-list">{features_html}</ul>
                <div style="text-align:center;">
                    {original_price_html}
                    <div class="price">${discounted_price}<small>/mo</small></div>
                </div>
                <button class="buy-btn" onclick="buyPlan('{p["id"]}','{p["name"]}',{discounted_price})">Buy Now →</button>
            </div>'''
        
        return f'''
        <div class="fade-in">
            {offers_html}
            <h1>{title_map.get(page, 'Plans')}</h1>
            <p>Choose the perfect plan for your needs</p>
            <div class="cards-grid">{plans_html}</div>
        </div>'''
    
    return '<div class="glass-card">Page not found</div>'

# ==================== API ROUTES ====================
@app.route('/api/purchase', methods=['POST'])
@login_required
def purchase():
    data = load_db()
    plan_id = request.json.get('plan_id')
    plan_name = request.json.get('plan_name')
    price = request.json.get('price')
    coupon_code = request.json.get('coupon_code')
    
    # Find plan type
    plan_type = None
    for category, plans in data['plans'].items():
        for p in plans:
            if p['id'] == plan_id:
                plan_type = category.lower()
                break
    
    # Apply discount
    final_price = calculate_discounted_price(price, plan_type, coupon_code)
    
    # Get stock
    stock_codes = get_stock_for_plan(plan_id)
    if not stock_codes:
        return jsonify({"error": "Out of stock for this plan"}), 400
    
    order_id = secrets.token_hex(8).upper()
    data['orders'].append({
        "id": order_id, "plan_id": plan_id, "plan_name": plan_name, 
        "price": price, "final_price": final_price, "user": session['user'], 
        "stock_codes": stock_codes, "date": datetime.now().isoformat(),
        "coupon": coupon_code
    })
    
    # Send Discord DM
    user_discord_id = data['users'].get(session['user'], {}).get('discord_id')
    if user_discord_id and data['bot_config'].get('bot_enabled'):
        msg = data['bot_config']['dm_message_template'].format(
            plan_name=plan_name, price=final_price, order_id=order_id, 
            stock_codes='\n'.join(stock_codes), 
            discord_invite=data['bot_config'].get('discord_invite_url', '')
        )
        send_discord_dm(user_discord_id, msg)
    
    # Add to activity feed
    data['dashboard_config']['activity_feed'].insert(0, {
        "user": session.get('username'), "action": "purchased", 
        "plan": plan_name, "time": "just now", "amount": final_price
    })
    data['dashboard_config']['activity_feed'] = data['dashboard_config']['activity_feed'][:10]
    
    # Update stats
    data['dashboard_config']['stats']['total_orders'] += 1
    data['dashboard_config']['stats']['total_revenue'] += final_price
    
    save_db(data)
    return jsonify({"success": True, "order_id": order_id, "final_price": final_price})

@app.route('/api/upload-stock', methods=['POST'])
@admin_required
def upload_stock():
    if 'stock_file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['stock_file']
    plan_id = request.form.get('plan_id')
    if file.filename == '' or not plan_id:
        return jsonify({"error": "Missing data"}), 400
    filename = secure_filename(f"{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    filepath = os.path.join(STOCK_FILES_DIR, filename)
    file.save(filepath)
    data = load_db()
    data['stock_files'][plan_id] = filename
    
    # Count total items
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    data.setdefault('stock_counts', {})[plan_id] = len(lines)
    
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/delete-stock/<plan_id>', methods=['POST'])
@admin_required
def delete_stock(plan_id):
    data = load_db()
    if plan_id in data['stock_files']:
        filepath = os.path.join(STOCK_FILES_DIR, data['stock_files'][plan_id])
        if os.path.exists(filepath):
            os.remove(filepath)
        del data['stock_files'][plan_id]
        save_db(data)
    return jsonify({"success": True})

@app.route('/api/create-offer', methods=['POST'])
@admin_required
def create_offer():
    data = load_db()
    offer = {
        "id": secrets.token_hex(8),
        "title": request.json.get('title', 'New Offer'),
        "description": request.json.get('description', ''),
        "discount_type": request.json.get('discount_type', 'percentage'),
        "discount_value": float(request.json.get('discount_value', 10)),
        "applicable_plans": request.json.get('applicable_plans', 'all'),
        "start_date": datetime.now().isoformat(),
        "end_date": request.json.get('end_date', (datetime.now() + timedelta(days=7)).isoformat()),
        "is_active": True,
        "banner_color": request.json.get('banner_color', '#4F46E5'),
        "emoji": request.json.get('emoji', '🎉'),
        "code": request.json.get('code', '').upper(),
        "usage_limit": int(request.json.get('usage_limit', 0)) or 0,
        "used_count": 0,
        "min_purchase": float(request.json.get('min_purchase', 0)),
        "max_discount": float(request.json.get('max_discount', 0)) or None,
        "created_at": datetime.now().isoformat()
    }
    data.setdefault('offers', []).append(offer)
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/toggle-offer/<offer_id>', methods=['POST'])
@admin_required
def toggle_offer(offer_id):
    data = load_db()
    enabled = request.json.get('enabled', False)
    for offer in data.get('offers', []):
        if offer['id'] == offer_id:
            offer['is_active'] = enabled
            break
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/delete-offer/<offer_id>', methods=['POST'])
@admin_required
def delete_offer(offer_id):
    data = load_db()
    data['offers'] = [o for o in data.get('offers', []) if o['id'] != offer_id]
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/create-announcement', methods=['POST'])
@admin_required
def create_announcement():
    data = load_db()
    announcement = {
        "id": secrets.token_hex(8),
        "title": request.json.get('title', 'New Announcement'),
        "content": request.json.get('content', ''),
        "type": request.json.get('type', 'info'),
        "emoji": request.json.get('emoji', '📢'),
        "active": True,
        "created_at": datetime.now().isoformat(),
        "expires_at": None,
        "priority": len(data.get('announcements', [])) + 1
    }
    data.setdefault('announcements', []).append(announcement)
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/toggle-announcement/<ann_id>', methods=['POST'])
@admin_required
def toggle_announcement(ann_id):
    data = load_db()
    enabled = request.json.get('enabled', True)
    for a in data.get('announcements', []):
        if a['id'] == ann_id:
            a['active'] = enabled
            break
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/delete-announcement/<ann_id>', methods=['POST'])
@admin_required
def delete_announcement(ann_id):
    data = load_db()
    data['announcements'] = [a for a in data.get('announcements', []) if a['id'] != ann_id]
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-discord-settings', methods=['POST'])
@admin_required
def save_discord_settings():
    data = load_db()
    data['bot_config']['discord_invite_url'] = request.json.get('discord_invite_url', '')
    data['bot_config']['discord_server_id'] = request.json.get('discord_server_id', '')
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-bot-config', methods=['POST'])
@admin_required
def save_bot_config():
    global bot_running
    data = load_db()
    data['bot_config']['bot_token'] = request.json.get('bot_token', '')
    data['bot_config']['bot_enabled'] = request.json.get('bot_enabled', False)
    data['bot_config']['bot_prefix'] = request.json.get('bot_prefix', '!')
    data['bot_config']['bot_status'] = request.json.get('bot_status', 'online')
    data['bot_config']['bot_activity_type'] = request.json.get('bot_activity_type', 'playing')
    data['bot_config']['bot_activity_name'] = request.json.get('bot_activity_name', 'VeCho Hub | !help')
    data['bot_config']['welcome_channel_id'] = request.json.get('welcome_channel_id', '')
    data['bot_config']['auto_role_id'] = request.json.get('auto_role_id', '')
    data['bot_config']['log_channel_id'] = request.json.get('log_channel_id', '')
    save_db(data)
    
    # Restart bot if enabled
    if data['bot_config']['bot_enabled'] and data['bot_config']['bot_token']:
        if bot_running:
            stop_discord_bot()
        start_discord_bot()
    elif not data['bot_config']['bot_enabled'] and bot_running:
        stop_discord_bot()
    
    return jsonify({"success": True})

@app.route('/api/save-dm-template', methods=['POST'])
@admin_required
def save_dm_template():
    data = load_db()
    data['bot_config']['dm_message_template'] = request.json.get('template', '')
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/restart-bot', methods=['POST'])
@admin_required
def restart_bot():
    global bot_running
    if bot_running:
        stop_discord_bot()
    start_discord_bot()
    return jsonify({"success": True})

@app.route('/api/create-user', methods=['POST'])
@admin_required
def create_user():
    data = load_db()
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role', 'user')
    
    if email in data['users']:
        return jsonify({"error": "User exists"}), 400
    
    data['users'][email] = {
        "password": generate_password_hash(password),
        "username": username,
        "role": role,
        "avatar": "👤",
        "discord_id": None,
        "discord_username": None,
        "discord_avatar": None,
        "created_at": datetime.now().isoformat(),
        "force_password_change": False,
        "balance": 0,
        "purchases": [],
        "api_key": secrets.token_hex(32)
    }
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/update-user', methods=['POST'])
@admin_required
def update_user():
    data = load_db()
    email = request.json.get('email')
    if email in data['users']:
        if request.json.get('username'):
            data['users'][email]['username'] = request.json.get('username')
        if request.json.get('balance') is not None:
            data['users'][email]['balance'] = float(request.json.get('balance'))
        if request.json.get('role'):
            data['users'][email]['role'] = request.json.get('role')
        save_db(data)
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404

@app.route('/api/save-settings', methods=['POST'])
@admin_required
def save_settings():
    data = load_db()
    if request.json.get('website_name'):
        data['dashboard_config']['website_name'] = request.json.get('website_name')
    if request.json.get('logo_url'):
        data['dashboard_config']['logo_url'] = request.json.get('logo_url')
    if request.json.get('primary_color'):
        data['dashboard_config']['colors']['primary'] = request.json.get('primary_color')
    if request.json.get('secondary_color'):
        data['dashboard_config']['colors']['secondary'] = request.json.get('secondary_color')
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-backgrounds', methods=['POST'])
@admin_required
def save_backgrounds():
    data = load_db()
    for key in ['dashboard_main', 'sidebar', 'vps_section', 'rdp_section']:
        if request.json.get(key):
            data['dashboard_config']['backgrounds'][key] = request.json.get(key)
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-maintenance', methods=['POST'])
@admin_required
def save_maintenance():
    data = load_db()
    data['dashboard_config']['maintenance_mode'] = request.json.get('maintenance_mode', False)
    data['dashboard_config']['maintenance_message'] = request.json.get('maintenance_message', 'Under maintenance')
    if request.json.get('maintenance_end_time'):
        data['dashboard_config']['maintenance_end_time'] = request.json.get('maintenance_end_time')
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-stats', methods=['POST'])
@admin_required
def save_stats():
    data = load_db()
    for key in ['total_customers', 'active_services', 'uptime_percentage', 'rating']:
        if request.json.get(key) is not None:
            data['dashboard_config']['stats'][key] = request.json.get(key)
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/add-monitor', methods=['POST'])
@admin_required
def add_monitor():
    data = load_db()
    url = request.json.get('url')
    mtype = request.json.get('type')
    monitor = {
        "id": secrets.token_hex(8),
        "name": url,
        "url": url,
        "type": mtype,
        "status": "unknown",
        "uptime": 100.0,
        "last_check": datetime.now().isoformat(),
        "checks": []
    }
    
    # Initial check
    try:
        if mtype == 'url':
            r = requests.get(url, timeout=5)
            monitor['status'] = 'online' if r.status_code == 200 else 'offline'
        else:
            r = requests.get(f'{DISCORD_API_BASE}/users/@me', headers={'Authorization': f'Bot {url}'}, timeout=5)
            monitor['status'] = 'online' if r.status_code == 200 else 'offline'
    except:
        monitor['status'] = 'offline'
    
    data['dashboard_config']['uptime_monitors'].append(monitor)
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/create-backup', methods=['POST'])
@admin_required
def create_backup_api():
    backup_file = create_backup()
    return jsonify({"success": True, "file": backup_file})

@app.route('/api/list-backups')
@admin_required
def list_backups():
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    backups.sort(reverse=True)
    return jsonify({"backups": backups})

@app.route('/api/download-backup/<filename>')
@admin_required
def download_backup(filename):
    backup_dir = 'backups'
    filepath = os.path.join(backup_dir, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "Backup not found"}), 404

@app.route('/api/restore-backup/<filename>', methods=['POST'])
@admin_required
def restore_backup_api(filename):
    backup_dir = 'backups'
    filepath = os.path.join(backup_dir, filename)
    if os.path.exists(filepath):
        restore_backup(filepath)
        return jsonify({"success": True})
    return jsonify({"error": "Backup not found"}), 404

@app.route('/api/save-backup-settings', methods=['POST'])
@admin_required
def save_backup_settings():
    data = load_db()
    data['backup_config']['auto_backup'] = request.json.get('auto_backup', False)
    data['backup_config']['backup_interval'] = request.json.get('backup_interval', 24)
    data['backup_config']['backup_retention'] = request.json.get('backup_retention', 7)
    save_db(data)
    return jsonify({"success": True})

@app.route('/auth/discord')
def discord_auth():
    return redirect(f'{DISCORD_API_BASE}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20email%20guilds')

@app.route('/auth/discord/callback')
def discord_callback():
    code = request.args.get('code')
    if not code:
        return redirect('/login')
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    
    r = requests.post(f'{DISCORD_API_BASE}/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if r.status_code != 200:
        return redirect('/login')
    
    token_data = r.json()
    user_r = requests.get(f'{DISCORD_API_BASE}/users/@me', headers={'Authorization': f'Bearer {token_data.get("access_token")}'})
    if user_r.status_code != 200:
        return redirect('/login')
    
    user_data = user_r.json()
    discord_id = user_data.get('id')
    username = user_data.get('username')
    avatar = user_data.get('avatar')
    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png" if avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    
    db_data = load_db()
    user_found = None
    for email, info in db_data['users'].items():
        if info.get('discord_id') == discord_id:
            user_found = email
            break
    
    if user_found:
        session['user'] = user_found
        session['username'] = db_data['users'][user_found]['username']
        session['role'] = db_data['users'][user_found]['role']
        session['avatar'] = avatar_url
    else:
        # Auto-create account for Discord users (optional)
        new_email = f"{discord_id}@discord.user"
        db_data['users'][new_email] = {
            "password": generate_password_hash(secrets.token_hex(16)),
            "username": username,
            "role": "user",
            "avatar": avatar_url,
            "discord_id": discord_id,
            "discord_username": username,
            "discord_avatar": avatar,
            "created_at": datetime.now().isoformat(),
            "balance": 0,
            "purchases": [],
            "api_key": secrets.token_hex(32)
        }
        save_db(db_data)
        session['user'] = new_email
        session['username'] = username
        session['role'] = 'user'
        session['avatar'] = avatar_url
    
    return redirect('/')

@app.route('/login')
def login_page():
    return '''
    <div style="min-height:100vh; background:#0A0A0A; display:flex; justify-content:center; align-items:center; font-family:monospace;">
        <div style="background:#1e1e22; padding:2rem; border-radius:24px; width:400px; text-align:center;">
            <h1 style="margin-bottom:1rem;">🚀 VeCho Hub</h1>
            <a href="/auth/discord" style="display:block; background:#5865F2; color:white; padding:12px; border-radius:40px; text-decoration:none; margin:1rem 0;">
                <i class="fab fa-discord"></i> Login with Discord
            </a>
            <hr style="margin:1rem 0;">
            <h3>Email Login</h3>
            <form method="post" action="/email-login">
                <input type="email" name="email" placeholder="Email" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#2a2a2e; color:white; border:none;">
                <input type="password" name="password" placeholder="Password" style="width:100%; padding:10px; margin:5px 0; border-radius:10px; background:#2a2a2e; color:white; border:none;">
                <button type="submit" style="background:#4F46E5; color:white; padding:12px; border:none; border-radius:40px; width:100%; margin-top:1rem; cursor:pointer;">Login</button>
            </form>
            <p style="margin-top:1rem; font-size:0.8rem; opacity:0.7;">Demo: admin@vechohub.com / admin123</p>
        </div>
    </div>
    '''

@app.route('/email-login', methods=['POST'])
def email_login():
    data = load_db()
    email = request.form.get('email')
    password = request.form.get('password')
    
    if email in data['users'] and check_password_hash(data['users'][email]['password'], password):
        session['user'] = email
        session['username'] = data['users'][email]['username']
        session['role'] = data['users'][email]['role']
        session['avatar'] = data['users'][email].get('avatar', '👤')
        return redirect('/')
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Auto backup task (simple threading)
def auto_backup_task():
    while True:
        time.sleep(3600)  # Check every hour
        data = load_db()
        if data['backup_config'].get('auto_backup'):
            last_backup = data['backup_config'].get('last_backup')
            if not last_backup or (datetime.now() - datetime.fromisoformat(last_backup)).total_seconds() > data['backup_config']['backup_interval'] * 3600:
                create_backup()
                # Clean old backups
                backup_dir = 'backups'
                retention_days = data['backup_config']['backup_retention']
                if os.path.exists(backup_dir):
                    for f in os.listdir(backup_dir):
                        fpath = os.path.join(backup_dir, f)
                        if os.path.getmtime(fpath) < (datetime.now() - timedelta(days=retention_days)).timestamp():
                            os.remove(fpath)

# Start auto backup thread
backup_thread = threading.Thread(target=auto_backup_task, daemon=True)
backup_thread.start()

# Start Discord bot if configured
data = load_db()
if data['bot_config'].get('bot_enabled') and data['bot_config'].get('bot_token'):
    start_discord_bot()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
