# app.py - VeCho Hub Complete Dashboard with Small Caps Discord Font
# Features: Bento Grid, Dark/Light Mode, User/Admin Interfaces, Order Management
import os
import json
import secrets
import hashlib
import requests
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, url_for, render_template_string, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(64))
CORS(app, supports_credentials=True)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', 'http://localhost:5000/auth/discord/callback')
DISCORD_API_BASE = 'https://discord.com/api/v10'

DB_FILE = 'vecho_hub.json'

# ============ SMALL CAPS FONT CONVERTER (ᴛʜɪꜱ ꜱᴛʏʟᴇ) ============
def small_caps(text):
    """Convert text to small caps Discord font style - ᴛʜɪꜱ ꜰᴏʀᴍᴀᴛ"""
    small_caps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
        'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
        's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ',
        'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
        'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
        ' ': ' ', '.': '.', ',': ',', '!': '!', '?': '?', '@': '@', '#': '#', '$': '$', '%': '%',
        '&': '&', '*': '*', '(': '(', ')': ')', '-': '-', '_': '_', '+': '+', '=': '=', '/': '/',
        '\\': '\\', '|': '|', ';': ';', ':': ':', "'": "'", '"': '"', '<': '<', '>': '>', '`': '`', '~': '~'
    }
    return ''.join(small_caps_map.get(c, c) for c in text)

def sc(text):
    """Shortcut for small caps"""
    return small_caps(text)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "users": {
            "admin@vechohub.com": {
                "password": generate_password_hash("admin123"),
                "username": sc("SuperAdmin"),
                "role": "superadmin",
                "avatar": "👑",
                "discord_id": None,
                "discord_username": None,
                "created_at": datetime.now().isoformat(),
                "balance": 0,
                "purchased_plans": [],
                "pending_payments": [],
                "approved_payments": [],
                "order_ids": [],
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en"
                }
            }
        },
        "discord_users": {},
        "plans": {
            "VPS": [
                {"id": "vps-1", "name": sc("VPS Starter"), "cpu": sc("1 Core"), "ram": "1GB", "storage": "25GB", "bandwidth": "1TB", "price": 4.99, "popular": False, "emoji": "🖥️", "features": [sc("Basic DDoS"), sc("24/7 Support")]},
                {"id": "vps-2", "name": sc("VPS Pro"), "cpu": sc("2 Cores"), "ram": "2GB", "storage": "50GB", "bandwidth": "2TB", "price": 9.99, "popular": True, "emoji": "⚡", "features": [sc("Advanced DDoS"), sc("Priority Support"), sc("Backup")]},
                {"id": "vps-3", "name": sc("VPS Enterprise"), "cpu": sc("4 Cores"), "ram": "4GB", "storage": "100GB", "bandwidth": "4TB", "price": 19.99, "popular": False, "emoji": "🚀", "features": [sc("Enterprise DDoS"), sc("24/7 Priority"), sc("Auto Backup"), sc("Snapshot")]}
            ],
            "RDP": [
                {"id": "rdp-1", "name": sc("RDP Basic"), "cpu": sc("1 Core"), "ram": "2GB", "storage": "40GB", "price": 9.99, "emoji": "💻"},
                {"id": "rdp-2", "name": sc("RDP Pro"), "cpu": sc("2 Cores"), "ram": "4GB", "storage": "80GB", "price": 19.99, "emoji": "🎮", "popular": True}
            ],
            "MC": [
                {"id": "mc-1", "name": sc("MC Basic"), "ram": "1GB", "slots": 10, "price": 4.99, "emoji": "⛏️"},
                {"id": "mc-2", "name": sc("MC Pro"), "ram": "2GB", "slots": 25, "price": 9.99, "emoji": "⚔️", "popular": True},
                {"id": "mc-3", "name": sc("MC Ultimate"), "ram": "4GB", "slots": 50, "price": 19.99, "emoji": "👑"}
            ],
            "GAMES": [
                {"id": "game-1", "name": sc("Game Server"), "ram": "2GB", "slots": 20, "price": 14.99, "emoji": "🎮"},
                {"id": "game-2", "name": sc("Game Pro"), "ram": "4GB", "slots": 50, "price": 29.99, "emoji": "🎯", "popular": True}
            ],
            "NITRO": [
                {"id": "nitro-1", "name": sc("Nitro Basic"), "duration": sc("1 Month"), "price": 4.99, "emoji": "💜"},
                {"id": "nitro-2", "name": sc("Nitro Premium"), "duration": sc("1 Month"), "price": 9.99, "emoji": "💎", "popular": True}
            ],
            "TRIAL": [
                {"id": "trial-1", "name": sc("Nitro Trial"), "duration": sc("14 Days"), "price": 2.99, "emoji": "🎁", "popular": True}
            ]
        },
        "orders": [],
        "pending_approvals": [],
        "approved_orders": [],
        "dashboard_stats": {
            "total_customers": 12847,
            "active_services": 24391,
            "uptime": 99.9,
            "rating": 4.9,
            "reviews": 8432,
            "response_time_ms": 48,
            "servers_worldwide": 14,
            "ddos_capacity": sc("2TB/s"),
            "monthly_revenue": 847231,
            "growth": 23.5
        },
        "dashboard_config": {
            "website_name": sc("VeCho Hub"),
            "logo_url": "https://img.icons8.com/fluency/96/admin-settings-male.png",
            "maintenance_mode": False,
            "maintenance_message": sc("Under maintenance"),
            "colors": {
                "primary": "#4F46E5",
                "secondary": "#10B981",
                "accent": "#F59E0B"
            }
        },
        "activity_log": [],
        "ai_insights": {
            "trending_plan": sc("VPS Pro"),
            "peak_hours": sc("7 PM - 10 PM"),
            "recommendation": sc("Upgrade server capacity"),
            "predicted_growth": "+32%",
            "best_selling": sc("Nitro Premium")
        },
        "announcements": [
            {
                "id": "ann1",
                "title": sc("Welcome to VeCho Hub"),
                "content": sc("Your premium destination for hosting and Discord services"),
                "type": "success",
                "emoji": "🎉",
                "active": True,
                "created_at": datetime.now().isoformat()
            }
        ],
        "user_sessions": {}
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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

# ============ HTML TEMPLATE ============
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>{{ site_name }} | ᴘʀᴇᴍɪᴜᴍ ʜᴏꜱᴛɪɴɢ</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #4F46E5;
            --primary-dark: #4338CA;
            --secondary: #10B981;
            --secondary-dark: #059669;
            --accent: #F59E0B;
            --danger: #EF4444;
            --warning: #F59E0B;
            --info: #3B82F6;
            --success: #10B981;
            --dark-bg: #0A0A0A;
            --dark-card: #1A1A2E;
            --dark-sidebar: #111111;
            --dark-text: #E2E8F0;
            --dark-text-secondary: #94A3B8;
            --light-bg: #F8FAFC;
            --light-card: #FFFFFF;
            --light-sidebar: #F1F5F9;
            --light-text: #0F172A;
            --light-text-secondary: #475569;
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --radius-2xl: 24px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--dark-bg);
            color: var(--dark-text);
            transition: background var(--transition-normal), color var(--transition-normal);
            overflow-x: hidden;
        }
        
        body.light-mode {
            background: var(--light-bg);
            color: var(--light-text);
        }
        
        /* Small Caps Text Style - The Discord Font! */
        .sc, h1, h2, h3, h4, .nav-item, .plan-name, .price, .kpi-value, .btn, .badge, .stat-number {
            font-variant: small-caps;
            letter-spacing: 0.5px;
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
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .loading-number {
            font-size: 4rem;
            font-weight: 800;
            font-variant: small-caps;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .loading-bar-container {
            width: 320px;
            height: 6px;
            background: rgba(79, 70, 229, 0.2);
            border-radius: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .loading-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            width: 0%;
            transition: width 0.15s ease;
        }
        
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
        
        .welcome-screen.hidden {
            opacity: 0;
            pointer-events: none;
        }
        
        .welcome-stats {
            display: flex;
            gap: 2rem;
            margin: 2rem 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-xl);
            padding: 1.5rem;
            text-align: center;
            min-width: 180px;
            border: 1px solid rgba(79, 70, 229, 0.3);
            animation: fadeInUp 0.6s ease forwards;
            opacity: 0;
        }
        
        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            font-variant: small-caps;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .begin-btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            padding: 1rem 2.5rem;
            font-size: 1.2rem;
            font-weight: 600;
            font-variant: small-caps;
            border-radius: 50px;
            cursor: pointer;
            transition: all var(--transition-normal);
            margin-top: 2rem;
        }
        
        .begin-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 30px rgba(79, 70, 229, 0.4);
        }
        
        /* Dashboard Container */
        .dashboard-container {
            display: flex;
            min-height: 100vh;
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .dashboard-container.visible {
            opacity: 1;
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--dark-sidebar);
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            transition: all var(--transition-normal);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            z-index: 100;
        }
        
        body.light-mode .sidebar {
            background: var(--light-sidebar);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        .sidebar-header {
            padding: 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .sidebar-header img {
            width: 45px;
            height: 45px;
            border-radius: var(--radius-md);
            object-fit: cover;
        }
        
        .sidebar-header h2 {
            font-size: 1.3rem;
            font-variant: small-caps;
            background: linear-gradient(135deg, #fff, var(--primary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .nav-item {
            padding: 12px 20px;
            margin: 6px 12px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            gap: 14px;
            cursor: pointer;
            transition: all var(--transition-fast);
            color: var(--dark-text-secondary);
            font-variant: small-caps;
            font-weight: 500;
        }
        
        body.light-mode .nav-item {
            color: var(--light-text-secondary);
        }
        
        .nav-item i {
            width: 24px;
            font-size: 1.1rem;
        }
        
        .nav-item.active, .nav-item:hover {
            background: rgba(79, 70, 229, 0.15);
            color: white;
        }
        
        body.light-mode .nav-item.active,
        body.light-mode .nav-item:hover {
            background: rgba(79, 70, 229, 0.1);
            color: var(--primary);
        }
        
        .nav-item.admin-only {
            border-left: 3px solid var(--accent);
        }
        
        /* Theme Toggle */
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1000;
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-lg);
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            margin-left: 280px;
            padding: 1.5rem;
        }
        
        /* Bento Grid Layout */
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .bento-card {
            background: var(--dark-card);
            border-radius: var(--radius-xl);
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all var(--transition-normal);
            cursor: pointer;
        }
        
        body.light-mode .bento-card {
            background: var(--light-card);
            border: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        .bento-card:hover {
            transform: translateY(-4px);
            border-color: var(--primary);
            box-shadow: var(--shadow-xl);
        }
        
        .bento-card.large {
            grid-column: span 2;
        }
        
        .bento-card.full {
            grid-column: span 4;
        }
        
        /* KPI Cards */
        .kpi-value {
            font-size: 2.5rem;
            font-weight: 800;
            font-variant: small-caps;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .kpi-label {
            font-size: 0.85rem;
            font-variant: small-caps;
            color: var(--dark-text-secondary);
            margin-top: 0.5rem;
        }
        
        body.light-mode .kpi-label {
            color: var(--light-text-secondary);
        }
        
        .trend-up {
            color: var(--success);
            font-size: 0.8rem;
        }
        
        /* Plans Grid */
        .plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .plan-card {
            background: var(--dark-card);
            border-radius: var(--radius-xl);
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all var(--transition-normal);
            position: relative;
        }
        
        body.light-mode .plan-card {
            background: var(--light-card);
        }
        
        .plan-card:hover {
            transform: translateY(-4px);
            border-color: var(--primary);
            box-shadow: var(--shadow-xl);
        }
        
        .popular-badge {
            position: absolute;
            top: -10px;
            right: 20px;
            background: var(--accent);
            color: #1a1a1a;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            font-variant: small-caps;
        }
        
        .plan-name {
            font-size: 1.5rem;
            font-weight: 700;
            font-variant: small-caps;
            margin: 1rem 0 0.5rem;
        }
        
        .plan-price {
            font-size: 2rem;
            font-weight: 800;
            font-variant: small-caps;
            color: var(--primary);
            margin: 1rem 0;
        }
        
        .feature-list {
            list-style: none;
            margin: 1rem 0;
        }
        
        .feature-list li {
            padding: 6px 0;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
        }
        
        /* Buttons */
        .btn {
            padding: 10px 20px;
            border-radius: var(--radius-md);
            font-weight: 600;
            font-variant: small-caps;
            cursor: pointer;
            transition: all var(--transition-fast);
            border: none;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 20px rgba(79, 70, 229, 0.3);
        }
        
        .btn-outline {
            background: transparent;
            border: 1px solid var(--primary);
            color: var(--primary);
        }
        
        /* Orders Table */
        .orders-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .orders-table th,
        .orders-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        body.light-mode .orders-table th,
        body.light-mode .orders-table td {
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            font-variant: small-caps;
        }
        
        .status-approved {
            background: rgba(16, 185, 129, 0.2);
            color: #10B981;
        }
        
        .status-pending {
            background: rgba(245, 158, 11, 0.2);
            color: #F59E0B;
        }
        
        /* Status Indicator */
        .status-online {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #10B981;
            animation: pulse 2s infinite;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* Toast Notifications */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--dark-card);
            border-left: 4px solid var(--primary);
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
            box-shadow: var(--shadow-lg);
        }
        
        body.light-mode .toast {
            background: var(--light-card);
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Responsive Design */
        @media (max-width: 1200px) {
            .bento-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                position: fixed;
                z-index: 200;
            }
            
            .sidebar.mobile-open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
                padding: 1rem;
            }
            
            .hamburger {
                display: block;
                position: fixed;
                top: 1rem;
                left: 1rem;
                z-index: 201;
                background: var(--dark-card);
                padding: 10px 12px;
                border-radius: var(--radius-md);
                cursor: pointer;
            }
            
            .bento-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .bento-card.large,
            .bento-card.full {
                grid-column: span 1;
            }
            
            .plans-grid {
                grid-template-columns: 1fr;
            }
            
            .welcome-stats {
                gap: 1rem;
            }
            
            .stat-card {
                min-width: 140px;
                padding: 1rem;
            }
            
            .stat-number {
                font-size: 1.8rem;
            }
        }
        
        @media (min-width: 769px) {
            .hamburger {
                display: none;
            }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(79, 70, 229, 0.5);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(79, 70, 229, 0.8);
        }
    </style>
</head>
<body>
<div class="loading-screen" id="loadingScreen">
    <div class="loading-logo">🚀</div>
    <div class="loading-number" id="loadingNumber">0</div>
    <div class="loading-bar-container"><div class="loading-bar" id="loadingProgress"></div></div>
    <div class="loading-text" id="loadingText">{{ sc("Initializing VeCho Hub") }}...</div>
</div>

<div class="welcome-screen" id="welcomeScreen">
    <h1 style="font-size:3rem; margin-bottom:1rem; font-variant:small-caps;">🚀 {{ site_name }}</h1>
    <p style="font-size:1.2rem; opacity:0.8;">{{ sc("Premium Hosting & Discord Services") }}</p>
    <div class="welcome-stats">
        <div class="stat-card"><div class="stat-number">{{ stats.total_customers }}+</div><div>{{ sc("Active Buyers") }}</div></div>
        <div class="stat-card"><div class="stat-number">{{ stats.uptime }}%</div><div>{{ sc("Uptime") }}</div></div>
        <div class="stat-card"><div class="stat-number">{{ stats.rating }}/5</div><div>{{ sc("Rating") }} ({{ stats.reviews }} {{ sc("reviews") }})</div></div>
        <div class="stat-card"><div class="stat-number">{{ sc("Never Down") }}</div><div>{{ sc("Since Jan 2024") }}</div></div>
    </div>
    <button class="begin-btn" onclick="startDashboard()">{{ sc("Let's Begin") }} →</button>
</div>

<div class="dashboard-container" id="dashboardContainer">
    <div class="hamburger" onclick="toggleSidebar()">☰</div>
    
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <img src="{{ logo_url }}" alt="logo" onerror="this.src='https://img.icons8.com/fluency/96/admin-settings-male.png'">
            <h2>{{ site_name }}</h2>
        </div>
        <div class="nav-item active" data-page="dashboard"><i class="fas fa-tachometer-alt"></i> {{ sc("Dashboard") }}</div>
        <div class="nav-item" data-page="vps"><i class="fas fa-server"></i> {{ sc("VPS Plans") }}</div>
        <div class="nav-item" data-page="rdp"><i class="fas fa-desktop"></i> {{ sc("RDP Plans") }}</div>
        <div class="nav-item" data-page="mc"><i class="fas fa-cube"></i> {{ sc("MC Plans") }}</div>
        <div class="nav-item" data-page="games"><i class="fas fa-gamepad"></i> {{ sc("Game Plans") }}</div>
        <div class="nav-item" data-page="nitro"><i class="fab fa-discord"></i> {{ sc("Nitro Plans") }}</div>
        <div class="nav-item" data-page="trial"><i class="fas fa-gift"></i> {{ sc("Nitro Trial") }}</div>
        <div class="nav-item" data-page="my-orders"><i class="fas fa-shopping-cart"></i> {{ sc("My Orders") }}</div>
        {% if session.role == 'superadmin' %}
        <div style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
            <div class="nav-item admin-only" data-page="admin"><i class="fas fa-crown"></i> {{ sc("Admin Panel") }}</div>
            <div class="nav-item admin-only" data-page="pending"><i class="fas fa-clock"></i> {{ sc("Pending Approvals") }}</div>
            <div class="nav-item admin-only" data-page="approved"><i class="fas fa-check-circle"></i> {{ sc("Approved Payments") }}</div>
            <div class="nav-item admin-only" data-page="users"><i class="fas fa-users"></i> {{ sc("User Management") }}</div>
            <div class="nav-item admin-only" data-page="settings"><i class="fas fa-sliders-h"></i> {{ sc("Settings") }}</div>
        </div>
        {% endif %}
        <div class="nav-item" data-page="logout"><i class="fas fa-sign-out-alt"></i> {{ sc("Logout") }}</div>
    </div>
    
    <div class="main-content" id="mainContent">
        <div id="pageContent">{{ sc("Loading") }}...</div>
    </div>
</div>

<div class="theme-toggle" onclick="toggleTheme()">
    <i class="fas fa-moon" id="themeIcon"></i>
</div>

<div id="toastContainer"></div>

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
        setTimeout(() => { 
            document.getElementById('loadingScreen').style.display = 'none'; 
        }, 500);
    }
}, 35);

function startDashboard() {
    document.getElementById('welcomeScreen').classList.add('hidden');
    localStorage.setItem('welcomeSeen', 'true');
    document.getElementById('dashboardContainer').classList.add('visible');
    loadPage('dashboard');
}

function loadPage(page) {
    fetch(`/api/page/${page}`)
        .then(res => res.text())
        .then(html => {
            document.getElementById('pageContent').innerHTML = html;
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
                if(item.dataset.page === page) item.classList.add('active');
            });
            window.scrollTo(0, 0);
            if (typeof initCharts === 'function') initCharts();
        })
        .catch(err => console.error('Page load error:', err));
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('mobile-open');
}

function toggleTheme() {
    document.body.classList.toggle('light-mode');
    const icon = document.getElementById('themeIcon');
    if (document.body.classList.contains('light-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        localStorage.setItem('theme', 'light');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        localStorage.setItem('theme', 'dark');
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function buyPlan(planId, planName, price) {
    canvasConfetti({
        particleCount: 200,
        spread: 100,
        origin: { y: 0.6 },
        colors: ['#4F46E5', '#10B981', '#F59E0B']
    });
    
    fetch('/api/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: planId, plan_name: planName, price: price })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(`✅ ${data.message}`);
            loadPage('my-orders');
        } else {
            showToast(`❌ ${data.error}`, 'error');
        }
    });
}

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
    document.getElementById('themeIcon').classList.remove('fa-moon');
    document.getElementById('themeIcon').classList.add('fa-sun');
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        if (page === 'logout') {
            window.location.href = '/logout';
        } else {
            loadPage(page);
        }
        if (window.innerWidth <= 768) toggleSidebar();
    });
});

if (welcomeSeen === 'true') {
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('dashboardContainer').classList.add('visible');
    loadPage('dashboard');
}
</script>
</body>
</html>
'''

# ============ HELPER FUNCTIONS ============
def generate_plans_html(plans, category):
    """Generate HTML for plans page"""
    html = f'''
    <div class="fade-in">
        <h1 style="font-variant: small-caps;">{sc(category)} {sc("Hosting Plans")}</h1>
        <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc("Choose the perfect plan for your needs")}</p>
        <div class="plans-grid">
    '''
    
    for p in plans:
        popular = '<div class="popular-badge">⭐ POPULAR</div>' if p.get('popular') else ''
        
        features_html = ''
        if 'cpu' in p:
            features_html = f'<li>💻 {p["cpu"]}</li><li>📀 {p["ram"]}</li><li>💾 {p["storage"]}</li><li>🌐 {p.get("bandwidth", sc("Unlimited"))}</li>'
        elif 'slots' in p:
            features_html = f'<li>📀 {p["ram"]}</li><li>👥 {p["slots"]} {sc("slots")}</li><li>🛡️ {sc("DDoS Protection")}</li><li>🔧 {sc("Full Control")}</li>'
        else:
            features_html = f'<li>✨ {p.get("features", sc("Premium features"))}</li>'
        
        if p.get('features'):
            for f in p.get('features', []):
                if isinstance(f, str):
                    features_html += f'<li>✨ {f}</li>'
        
        html += f'''
        <div class="plan-card">
            {popular}
            <div style="font-size: 2.5rem; text-align: center;">{p["emoji"]}</div>
            <h3 class="plan-name" style="text-align: center;">{p["name"]}</h3>
            <ul class="feature-list">{features_html}</ul>
            <div class="plan-price" style="text-align: center;">${p["price"]}<small style="font-size: 0.8rem;">/{sc("mo")}</small></div>
            <button class="btn btn-primary" style="width: 100%;" onclick="buyPlan('{p["id"]}','{p["name"]}',{p["price"]})">{sc("Buy Now")} →</button>
        </div>
        '''
    
    html += '</div></div>'
    return html

# ============ ROUTES ============
@app.route('/')
def index():
    data = load_db()
    if data['dashboard_config'].get('maintenance_mode') and session.get('role') != 'superadmin':
        return f'<body style="background:#0A0A0A;color:white;text-align:center;padding:4rem;"><h1>🔧 {data["dashboard_config"]["maintenance_message"]}</h1></body>'
    
    return render_template_string(HTML_TEMPLATE, 
        site_name=data['dashboard_config']['website_name'],
        logo_url=data['dashboard_config']['logo_url'],
        stats=data['dashboard_stats'],
        session=session,
        sc=sc)

@app.route('/api/page/<page>')
def get_page(page):
    data = load_db()
    role = session.get('role', 'user')
    user_email = session.get('user')
    user_data = data['users'].get(user_email, {})
    
    # DASHBOARD PAGE
    if page == 'dashboard':
        stats = data['dashboard_stats']
        announcements = data.get('announcements', [])
        ai_insights = data.get('ai_insights', {})
        
        ann_html = ''.join(f'''
        <div class="bento-card" style="border-left: 4px solid var(--primary);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">{a['emoji']}</span>
                <div>
                    <h3 style="font-variant: small-caps;">{a['title']}</h3>
                    <p style="font-size: 0.85rem; opacity: 0.8;">{a['content']}</p>
                </div>
            </div>
        </div>
        ''' for a in announcements[:2])
        
        return f'''
        <div class="fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <div>
                    <h1 style="font-variant: small-caps;">{sc('Welcome back')}, {session.get('username', sc('User'))}!</h1>
                    <p style="opacity: 0.7;">{sc('Your services are all online')}. 🟢</p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <div style="background: rgba(79,70,229,0.1); padding: 8px 16px; border-radius: 20px;">
                        <i class="fas fa-chart-line"></i> {sc('Last 30 days')}
                    </div>
                </div>
            </div>
            
            <div class="bento-grid">
                <div class="bento-card">
                    <i class="fas fa-users" style="font-size: 2rem; color: var(--primary);"></i>
                    <div class="kpi-value">{stats['total_customers']:,}</div>
                    <div class="kpi-label">{sc('Total Customers')}</div>
                    <span class="trend-up"><i class="fas fa-arrow-up"></i> +{stats['growth']}%</span>
                </div>
                <div class="bento-card">
                    <i class="fas fa-server" style="font-size: 2rem; color: var(--secondary);"></i>
                    <div class="kpi-value">{stats['active_services']:,}</div>
                    <div class="kpi-label">{sc('Active Services')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-chart-line" style="font-size: 2rem; color: var(--accent);"></i>
                    <div class="kpi-value">{stats['uptime']}%</div>
                    <div class="kpi-label">{sc('Uptime')}</div>
                    <span class="trend-up"><i class="fas fa-arrow-up"></i> +0.5%</span>
                </div>
                <div class="bento-card">
                    <i class="fas fa-dollar-sign" style="font-size: 2rem; color: #10B981;"></i>
                    <div class="kpi-value">${stats['monthly_revenue']:,}</div>
                    <div class="kpi-label">{sc('Monthly Revenue')}</div>
                    <span class="trend-up"><i class="fas fa-arrow-up"></i> +{stats['growth']}%</span>
                </div>
            </div>
            
            <div class="bento-grid">
                <div class="bento-card large">
                    <h3 style="font-variant: small-caps; margin-bottom: 1rem;">📊 {sc('Performance Overview')}</h3>
                    <canvas id="performanceChart" style="max-height: 250px; width: 100%;"></canvas>
                </div>
                <div class="bento-card">
                    <h3 style="font-variant: small-caps; margin-bottom: 1rem;">🤖 {sc('AI Insights')}</h3>
                    <div style="margin-bottom: 1rem;">
                        <div style="background: rgba(79,70,229,0.1); padding: 0.8rem; border-radius: var(--radius-md);">
                            <i class="fas fa-fire"></i> {sc('Trending')}: <strong>{ai_insights.get('trending_plan', sc('VPS Pro'))}</strong>
                        </div>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <div style="background: rgba(16,185,129,0.1); padding: 0.8rem; border-radius: var(--radius-md);">
                            <i class="fas fa-clock"></i> {sc('Peak Hours')}: <strong>{ai_insights.get('peak_hours', sc('7 PM - 10 PM'))}</strong>
                        </div>
                    </div>
                    <div>
                        <div style="background: rgba(245,158,11,0.1); padding: 0.8rem; border-radius: var(--radius-md);">
                            <i class="fas fa-chart-line"></i> {sc('Predicted Growth')}: <strong>{ai_insights.get('predicted_growth', '+32%')}</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            {ann_html}
            
            <div class="bento-card full" style="margin-top: 1rem;">
                <h3 style="font-variant: small-caps; margin-bottom: 1rem;">🟢 {sc('System Status')}</h3>
                <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                    <div><span class="status-online"></span> {sc('All Systems Operational')}</div>
                    <div><i class="fas fa-globe"></i> {sc('Response Time')}: &lt;{stats['response_time_ms']}ms</div>
                    <div><i class="fas fa-shield-alt"></i> {sc('DDoS Protection')}: {stats['ddos_capacity']}</div>
                    <div><i class="fab fa-discord"></i> {sc('Discord')}: <a href="#" style="color: var(--primary);">{sc('Join our Community')}</a></div>
                </div>
            </div>
        </div>
        
        <script>
        function initCharts() {{
            const ctx = document.getElementById('performanceChart')?.getContext('2d');
            if(ctx) {{
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                        datasets: [
                            {{
                                label: '{sc("Revenue")}',
                                data: [45000, 52000, 61000, 78000, 82000, 94700],
                                borderColor: '#4F46E5',
                                backgroundColor: 'rgba(79,70,229,0.1)',
                                tension: 0.4,
                                fill: true
                            }},
                            {{
                                label: '{sc("Orders")}',
                                data: [1200, 1450, 1700, 2100, 2350, 2800],
                                borderColor: '#10B981',
                                backgroundColor: 'rgba(16,185,129,0.1)',
                                tension: 0.4,
                                fill: true
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                position: 'top',
                            }}
                        }}
                    }}
                }});
            }}
        }}
        initCharts();
        </script>
        '''
    
    # MY ORDERS PAGE
    elif page == 'my-orders':
        user_orders = [o for o in data['orders'] if o.get('user_email') == user_email]
        approved_orders = [o for o in data['approved_orders'] if o.get('user_email') == user_email]
        pending_orders = [o for o in data['pending_approvals'] if o.get('user_email') == user_email]
        
        orders_html = ''
        for order in user_orders + approved_orders + pending_orders:
            status = order.get('status', 'pending')
            status_class = 'status-approved' if status == 'approved' else 'status-pending'
            status_text = sc('Approved') if status == 'approved' else sc('Pending')
            
            orders_html += f'''
            <tr>
                <td>#{order.get('id', 'N/A')[:8]}</td>
                <td>{order.get('plan_name', 'N/A')}</td>
                <td>${order.get('final_price', order.get('price', 0))}</td>
                <td><span class="status-badge {status_class}">{status_text}</span></td>
                <td>{order.get('date', 'N/A')[:10] if order.get('date') else 'N/A'}</td>
                <td>{order.get('stock_codes', ['-'])[0] if order.get('stock_codes') else '-'}</td>
            </tr>
            '''
        
        if not orders_html:
            orders_html = f'<tr><td colspan="6" style="text-align: center; padding: 2rem;">📦 {sc("No orders found")}. {sc("Buy your first plan")}!</td></tr>'
        
        total_spent = sum(o.get('final_price', o.get('price', 0)) for o in user_orders)
        
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps; margin-bottom: 0.5rem;">📦 {sc('My Orders')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('View all your purchased plans and their status')}</p>
            
            <div class="bento-card full">
                <h3 style="font-variant: small-caps; margin-bottom: 1rem;">{sc('Order History')}</h3>
                <div style="overflow-x: auto;">
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>{sc('Order ID')}</th>
                                <th>{sc('Plan')}</th>
                                <th>{sc('Amount')}</th>
                                <th>{sc('Status')}</th>
                                <th>{sc('Date')}</th>
                                <th>{sc('Stock Code')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders_html}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="bento-grid" style="margin-top: 1.5rem;">
                <div class="bento-card">
                    <i class="fas fa-shopping-cart" style="font-size: 2rem; color: var(--primary);"></i>
                    <div class="kpi-value">{len(user_orders)}</div>
                    <div class="kpi-label">{sc('Total Orders')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-check-circle" style="font-size: 2rem; color: var(--success);"></i>
                    <div class="kpi-value">{len(approved_orders)}</div>
                    <div class="kpi-label">{sc('Approved')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-clock" style="font-size: 2rem; color: var(--warning);"></i>
                    <div class="kpi-value">{len(pending_orders)}</div>
                    <div class="kpi-label">{sc('Pending')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-dollar-sign" style="font-size: 2rem; color: var(--secondary);"></i>
                    <div class="kpi-value">${total_spent}</div>
                    <div class="kpi-label">{sc('Total Spent')}</div>
                </div>
            </div>
        </div>
        '''
    
    # PLANS PAGES
    elif page == 'vps':
        return generate_plans_html(data['plans']['VPS'], 'VPS')
    elif page == 'rdp':
        return generate_plans_html(data['plans']['RDP'], 'RDP')
    elif page == 'mc':
        return generate_plans_html(data['plans']['MC'], 'MC')
    elif page == 'games':
        return generate_plans_html(data['plans']['GAMES'], 'GAMES')
    elif page == 'nitro':
        return generate_plans_html(data['plans']['NITRO'], 'NITRO')
    elif page == 'trial':
        return generate_plans_html(data['plans']['TRIAL'], 'TRIAL')
    
    # ADMIN PAGES
    elif page == 'admin' and role == 'superadmin':
        users_count = len(data['users'])
        orders_count = len(data['orders'])
        pending_count = len(data['pending_approvals'])
        approved_count = len(data['approved_orders'])
        revenue = sum(o.get('price', 0) for o in data['orders'])
        
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps;">👑 {sc('Admin Dashboard')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('Manage your entire platform from here')}</p>
            
            <div class="bento-grid">
                <div class="bento-card">
                    <i class="fas fa-users" style="font-size: 2rem;"></i>
                    <div class="kpi-value">{users_count}</div>
                    <div class="kpi-label">{sc('Total Users')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-shopping-cart" style="font-size: 2rem;"></i>
                    <div class="kpi-value">{orders_count}</div>
                    <div class="kpi-label">{sc('Total Orders')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-clock" style="font-size: 2rem;"></i>
                    <div class="kpi-value">{pending_count}</div>
                    <div class="kpi-label">{sc('Pending Approvals')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-check-circle" style="font-size: 2rem; color: var(--success);"></i>
                    <div class="kpi-value">{approved_count}</div>
                    <div class="kpi-label">{sc('Approved')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-dollar-sign" style="font-size: 2rem;"></i>
                    <div class="kpi-value">${revenue:,}</div>
                    <div class="kpi-label">{sc('Total Revenue')}</div>
                </div>
                <div class="bento-card">
                    <i class="fas fa-chart-line" style="font-size: 2rem;"></i>
                    <div class="kpi-value">{data['dashboard_stats']['growth']}%</div>
                    <div class="kpi-label">{sc('Growth Rate')}</div>
                </div>
            </div>
            
            <div class="bento-card full">
                <h3>{sc('Quick Actions')}</h3>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem;">
                    <button class="btn btn-primary" onclick="loadPage('pending')">📋 {sc('View Pending Approvals')}</button>
                    <button class="btn btn-primary" onclick="loadPage('approved')">✅ {sc('View Approved Payments')}</button>
                    <button class="btn btn-primary" onclick="loadPage('users')">👥 {sc('Manage Users')}</button>
                    <button class="btn btn-primary" onclick="loadPage('settings')">⚙️ {sc('Settings')}</button>
                </div>
            </div>
        </div>
        '''
    
    elif page == 'pending' and role == 'superadmin':
        pending = data['pending_approvals']
        pending_html = ''
        for p in pending:
            pending_html += f'''
            <div class="bento-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h3>{p.get('plan_name', 'N/A')}</h3>
                        <p>{sc('User')}: {p.get('user_email', 'N/A')} | {sc('Amount')}: ${p.get('price', 0)}</p>
                        <p>{sc('Order ID')}: {p.get('id', 'N/A')}</p>
                        <p>{sc('Stock Codes')}: {', '.join(p.get('stock_codes', []))}</p>
                    </div>
                    <div>
                        <button class="btn btn-primary" onclick="approveOrder('{p.get('id')}')" style="margin-right: 10px;">✅ {sc('Approve')}</button>
                        <button class="btn btn-outline" onclick="rejectOrder('{p.get('id')}')">❌ {sc('Reject')}</button>
                    </div>
                </div>
            </div>
            '''
        
        if not pending_html:
            pending_html = f'<div class="bento-card full"><p style="text-align: center;">✅ {sc("No pending approvals")}</p></div>'
        
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps;">📋 {sc('Pending Approvals')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('Review and approve customer orders')}</p>
            {pending_html}
        </div>
        <script>
        function approveOrder(orderId) {{
            fetch('/api/approve-order', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ order_id: orderId }})
            }}).then(() => location.reload());
        }}
        function rejectOrder(orderId) {{
            fetch('/api/reject-order', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ order_id: orderId }})
            }}).then(() => location.reload());
        }}
        </script>
        '''
    
    elif page == 'approved' and role == 'superadmin':
        approved = data['approved_orders']
        approved_html = ''
        for a in approved:
            approved_html += f'''
            <tr>
                <td>#{a.get('id', 'N/A')[:8]}</td>
                <td>{a.get('user_email', 'N/A')}</td>
                <td>{a.get('plan_name', 'N/A')}</td>
                <td>${a.get('final_price', a.get('price', 0))}</td>
                <td>{a.get('date', 'N/A')[:10] if a.get('date') else 'N/A'}</td>
                <td>{', '.join(a.get('stock_codes', []))}</td>
            </tr>
            '''
        
        if not approved_html:
            approved_html = f'<tr><td colspan="6" style="text-align: center; padding: 2rem;">📦 {sc("No approved orders")}</td></tr>'
        
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps;">✅ {sc('Approved Payments')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('All approved customer orders')}</p>
            
            <div class="bento-card full">
                <div style="overflow-x: auto;">
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>{sc('Order ID')}</th>
                                <th>{sc('User')}</th>
                                <th>{sc('Plan')}</th>
                                <th>{sc('Amount')}</th>
                                <th>{sc('Date')}</th>
                                <th>{sc('Stock Codes')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {approved_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    
    elif page == 'users' and role == 'superadmin':
        users_html = ''
        for email, u in data['users'].items():
            users_html += f'''
            <tr>
                <td>{email}</td>
                <td>{u.get('username', 'N/A')}</td>
                <td>{u.get('role', 'user')}</td>
                <td>{u.get('discord_username', 'N/A')}</td>
                <td>${u.get('balance', 0)}</td>
                <td><button class="btn btn-outline" style="padding: 4px 12px;" onclick="editUser('{email}')">{sc('Edit')}</button></td>
            </tr>
            '''
        
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps;">👥 {sc('User Management')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('Manage all registered users')}</p>
            
            <div class="bento-card full">
                <h3>{sc('Create New User')}</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <input type="email" id="newEmail" placeholder="{sc('Email')}" style="padding: 10px; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                    <input type="text" id="newUsername" placeholder="{sc('Username')}" style="padding: 10px; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                    <input type="password" id="newPassword" placeholder="{sc('Password')}" style="padding: 10px; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                    <select id="newRole" style="padding: 10px; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <option value="user">{sc('User')}</option>
                        <option value="superadmin">{sc('Admin')}</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="createUser()" style="margin-top: 1rem;">➕ {sc('Create User')}</button>
            </div>
            
            <div class="bento-card full" style="margin-top: 1rem;">
                <h3>{sc('All Users')}</h3>
                <div style="overflow-x: auto;">
                    <table class="orders-table">
                        <thead>
                            <tr><th>{sc('Email')}</th><th>{sc('Username')}</th><th>{sc('Role')}</th><th>{sc('Discord')}</th><th>{sc('Balance')}</th><th>{sc('Actions')}</th></tr>
                        </thead>
                        <tbody>{users_html}</tbody>
                    </table>
                </div>
            </div>
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
            const newBalance = prompt('{sc("Enter new balance")}:');
            if(newBalance) {{
                fetch('/api/update-balance', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: email, balance: parseFloat(newBalance) }})
                }}).then(() => location.reload());
            }}
        }}
        </script>
        '''
    
    elif page == 'settings' and role == 'superadmin':
        config = data['dashboard_config']
        return f'''
        <div class="fade-in">
            <h1 style="font-variant: small-caps;">⚙️ {sc('Settings')}</h1>
            <p style="opacity: 0.7; margin-bottom: 1.5rem;">{sc('Customize your dashboard')}</p>
            
            <div class="bento-grid">
                <div class="bento-card">
                    <h3>{sc('General Settings')}</h3>
                    <div style="margin-top: 1rem;">
                        <label>{sc('Website Name')}:</label>
                        <input type="text" id="siteName" value="{config['website_name']}" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <label>{sc('Logo URL')}:</label>
                        <input type="text" id="logoUrl" value="{config['logo_url']}" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <button class="btn btn-primary" onclick="saveGeneralSettings()" style="margin-top: 1rem;">{sc('Save Changes')}</button>
                    </div>
                </div>
                
                <div class="bento-card">
                    <h3>{sc('Maintenance Mode')}</h3>
                    <div style="margin-top: 1rem;">
                        <label class="switch">
                            <input type="checkbox" id="maintenanceMode" {'checked' if config['maintenance_mode'] else ''}>
                            <span class="slider"></span>
                        </label>
                        <label>{sc('Message')}:</label>
                        <textarea id="maintenanceMsg" rows="3" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">{config['maintenance_message']}</textarea>
                        <button class="btn btn-primary" onclick="saveMaintenance()">{sc('Save')}</button>
                    </div>
                </div>
                
                <div class="bento-card">
                    <h3>{sc('Colors')}</h3>
                    <div style="margin-top: 1rem;">
                        <label>{sc('Primary Color')}:</label>
                        <input type="color" id="primaryColor" value="{config['colors']['primary']}" style="width: 100%; margin: 8px 0;">
                        <label>{sc('Secondary Color')}:</label>
                        <input type="color" id="secondaryColor" value="{config['colors']['secondary']}" style="width: 100%; margin: 8px 0;">
                        <button class="btn btn-primary" onclick="saveColors()">{sc('Save Colors')}</button>
                    </div>
                </div>
                
                <div class="bento-card">
                    <h3>{sc('Stats (Fake Stats)')}</h3>
                    <div style="margin-top: 1rem;">
                        <label>{sc('Total Customers')}:</label>
                        <input type="number" id="statCustomers" value="{data['dashboard_stats']['total_customers']}" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <label>{sc('Active Services')}:</label>
                        <input type="number" id="statServices" value="{data['dashboard_stats']['active_services']}" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <label>{sc('Uptime %')}:</label>
                        <input type="number" step="0.1" id="statUptime" value="{data['dashboard_stats']['uptime']}" style="width: 100%; padding: 8px; margin: 8px 0; border-radius: var(--radius-md); background: var(--dark-card); border: 1px solid rgba(255,255,255,0.1); color: white;">
                        <button class="btn btn-primary" onclick="saveStats()">{sc('Save Stats')}</button>
                    </div>
                </div>
            </div>
        </div>
        <script>
        function saveGeneralSettings() {{
            fetch('/api/save-settings', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    website_name: document.getElementById('siteName').value,
                    logo_url: document.getElementById('logoUrl').value
                }})
            }}).then(() => location.reload());
        }}
        function saveMaintenance() {{
            fetch('/api/save-maintenance', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    maintenance_mode: document.getElementById('maintenanceMode').checked,
                    maintenance_message: document.getElementById('maintenanceMsg').value
                }})
            }}).then(() => location.reload());
        }}
        function saveColors() {{
            fetch('/api/save-colors', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    primary: document.getElementById('primaryColor').value,
                    secondary: document.getElementById('secondaryColor').value
                }})
            }}).then(() => location.reload());
        }}
        function saveStats() {{
            fetch('/api/save-stats', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    total_customers: parseInt(document.getElementById('statCustomers').value),
                    active_services: parseInt(document.getElementById('statServices').value),
                    uptime: parseFloat(document.getElementById('statUptime').value)
                }})
            }}).then(() => location.reload());
        }}
        </script>
        '''
    
    return '<div class="bento-card full"><p style="text-align: center;">Page not found</p></div>'

# ============ API ROUTES ============
@app.route('/api/purchase', methods=['POST'])
@login_required
def purchase():
    data = load_db()
    plan_id = request.json.get('plan_id')
    plan_name = request.json.get('plan_name')
    price = request.json.get('price')
    user_email = session.get('user')
    
    # Find plan details
    plan_details = None
    for category, plans in data['plans'].items():
        for p in plans:
            if p['id'] == plan_id:
                plan_details = p
                break
    
    order_id = secrets.token_hex(8).upper()
    stock_codes = [f"STOCK-{secrets.token_hex(4).upper()}" for _ in range(1)]
    
    order = {
        "id": order_id,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "price": price,
        "final_price": price,
        "user_email": user_email,
        "stock_codes": stock_codes,
        "date": datetime.now().isoformat(),
        "status": "pending"
    }
    
    data['pending_approvals'].append(order)
    save_db(data)
    
    return jsonify({"success": True, "message": f"Order placed! Waiting for admin approval. Order ID: {order_id}"})

@app.route('/api/approve-order', methods=['POST'])
@admin_required
def approve_order():
    data = load_db()
    order_id = request.json.get('order_id')
    
    for i, order in enumerate(data['pending_approvals']):
        if order.get('id') == order_id:
            order['status'] = 'approved'
            order['approved_at'] = datetime.now().isoformat()
            data['approved_orders'].append(order)
            data['pending_approvals'].pop(i)
            save_db(data)
            return jsonify({"success": True})
    
    return jsonify({"error": "Order not found"}), 404

@app.route('/api/reject-order', methods=['POST'])
@admin_required
def reject_order():
    data = load_db()
    order_id = request.json.get('order_id')
    
    for i, order in enumerate(data['pending_approvals']):
        if order.get('id') == order_id:
            data['pending_approvals'].pop(i)
            save_db(data)
            return jsonify({"success": True})
    
    return jsonify({"error": "Order not found"}), 404

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
        "created_at": datetime.now().isoformat(),
        "balance": 0,
        "purchased_plans": [],
        "order_ids": []
    }
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/update-balance', methods=['POST'])
@admin_required
def update_balance():
    data = load_db()
    email = request.json.get('email')
    balance = request.json.get('balance')
    
    if email in data['users']:
        data['users'][email]['balance'] = balance
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
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-maintenance', methods=['POST'])
@admin_required
def save_maintenance():
    data = load_db()
    data['dashboard_config']['maintenance_mode'] = request.json.get('maintenance_mode', False)
    data['dashboard_config']['maintenance_message'] = request.json.get('maintenance_message', sc("Under maintenance"))
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-colors', methods=['POST'])
@admin_required
def save_colors():
    data = load_db()
    if request.json.get('primary'):
        data['dashboard_config']['colors']['primary'] = request.json.get('primary')
    if request.json.get('secondary'):
        data['dashboard_config']['colors']['secondary'] = request.json.get('secondary')
    save_db(data)
    return jsonify({"success": True})

@app.route('/api/save-stats', methods=['POST'])
@admin_required
def save_stats():
    data = load_db()
    if request.json.get('total_customers'):
        data['dashboard_stats']['total_customers'] = request.json.get('total_customers')
    if request.json.get('active_services'):
        data['dashboard_stats']['active_services'] = request.json.get('active_services')
    if request.json.get('uptime'):
        data['dashboard_stats']['uptime'] = request.json.get('uptime')
    save_db(data)
    return jsonify({"success": True})

# ============ AUTH ROUTES ============
@app.route('/auth/discord')
def discord_auth():
    if not DISCORD_CLIENT_ID:
        return redirect('/login')
    return redirect(f'{DISCORD_API_BASE}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20email')

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
        # Auto-create account for Discord users
        new_email = f"{discord_id}@discord.user"
        db_data['users'][new_email] = {
            "password": generate_password_hash(secrets.token_hex(16)),
            "username": username,
            "role": "user",
            "avatar": avatar_url,
            "discord_id": discord_id,
            "discord_username": username,
            "created_at": datetime.now().isoformat(),
            "balance": 0,
            "purchased_plans": [],
            "order_ids": []
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
            <h1 style="margin-bottom:1rem; font-variant:small-caps;">🚀 VeCho Hub</h1>
            <a href="/auth/discord" style="display:block; background:#5865F2; color:white; padding:12px; border-radius:40px; text-decoration:none; margin:1rem 0;">
                <i class="fab fa-discord"></i> Login with Discord
            </a>
            <hr style="margin:1rem 0;">
            <h3 style="font-variant:small-caps;">Email Login</h3>
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
