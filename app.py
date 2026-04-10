import os
import json
import sqlite3
import hashlib
import secrets
import subprocess
import docker
import asyncio
import threading
import time
import psutil
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput
import requests
from typing import Optional, Dict, List

# ==================== FLASK APP SETUP ====================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'atyro-cloud-super-secret-key-2026'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== DATABASE SETUP ====================

def init_db():
    """Initialize all database tables"""
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        discord_id TEXT UNIQUE,
        discord_name TEXT,
        is_admin INTEGER DEFAULT 0,
        is_owner INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        vps_limit INTEGER DEFAULT 20,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Bot settings table
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_token TEXT,
        bot_name TEXT DEFAULT 'vectro',
        bot_prefix TEXT DEFAULT '>',
        bot_admin_role_id TEXT,
        bot_owner_id TEXT,
        bot_status TEXT DEFAULT 'online',
        bot_activity TEXT DEFAULT '>help | Atyro Cloud',
        maintenance_mode INTEGER DEFAULT 0,
        maintenance_reason TEXT,
        embed_color TEXT DEFAULT '#5865F2',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Website settings table for admin customization
    c.execute('''CREATE TABLE IF NOT EXISTS website_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_title TEXT DEFAULT 'Atyro Cloud',
        site_logo TEXT,
        primary_color TEXT DEFAULT '#5865F2',
        secondary_color TEXT DEFAULT '#57F287',
        background_color TEXT DEFAULT '#0A0A0A',
        text_color TEXT DEFAULT '#FFFFFF',
        footer_text TEXT DEFAULT '© 2026 Atyro Cloud. All rights reserved.',
        maintenance_mode INTEGER DEFAULT 0,
        custom_css TEXT,
        custom_js TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # VPS plans table
    c.execute('''CREATE TABLE IF NOT EXISTS vps_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        cpu INTEGER,
        ram INTEGER,
        storage INTEGER,
        bandwidth INTEGER,
        price INTEGER,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Minecraft plans table
    c.execute('''CREATE TABLE IF NOT EXISTS mc_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        ram INTEGER,
        cpu_percent INTEGER,
        storage INTEGER,
        slots INTEGER,
        price INTEGER,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # RDP plans table
    c.execute('''CREATE TABLE IF NOT EXISTS rdp_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        cpu INTEGER,
        ram INTEGER,
        storage INTEGER,
        os TEXT,
        price INTEGER,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Nitro plans table
    c.execute('''CREATE TABLE IF NOT EXISTS nitro_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        duration_days INTEGER,
        price INTEGER,
        features TEXT,
        is_available INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # VPS servers table
    c.execute('''CREATE TABLE IF NOT EXISTS vps_servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER,
        container_id TEXT,
        container_name TEXT,
        os_type TEXT,
        ip_address TEXT,
        port INTEGER,
        cpu INTEGER,
        ram INTEGER,
        storage INTEGER,
        status TEXT DEFAULT 'stopped',
        expiry_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (plan_id) REFERENCES vps_plans (id)
    )''')
    
    # Minecraft servers table
    c.execute('''CREATE TABLE IF NOT EXISTS mc_servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER,
        server_name TEXT,
        server_ip TEXT,
        port INTEGER,
        ram INTEGER,
        status TEXT DEFAULT 'stopped',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (plan_id) REFERENCES mc_plans (id)
    )''')
    
    # RDP servers table
    c.execute('''CREATE TABLE IF NOT EXISTS rdp_servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER,
        server_name TEXT,
        ip_address TEXT,
        username TEXT,
        password TEXT,
        port INTEGER DEFAULT 3389,
        status TEXT DEFAULT 'stopped',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (plan_id) REFERENCES rdp_plans (id)
    )''')
    
    # Nitro purchases table
    c.execute('''CREATE TABLE IF NOT EXISTS nitro_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER,
        code TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        redeemed_at TIMESTAMP,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (plan_id) REFERENCES nitro_plans (id)
    )''')
    
    # Links table for >links command
    c.execute('''CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        url TEXT NOT NULL,
        icon TEXT,
        category TEXT DEFAULT 'general',
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Web visitors tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS web_visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT,
        user_agent TEXT,
        page_visited TEXT,
        visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Audit logs table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        admin_name TEXT,
        action TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )''')
    
    # Bot admins table
    c.execute('''CREATE TABLE IF NOT EXISTS bot_admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        discord_id TEXT NOT NULL,
        discord_name TEXT,
        added_by INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Custom commands table
    c.execute('''CREATE TABLE IF NOT EXISTS custom_commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command_name TEXT UNIQUE NOT NULL,
        response TEXT NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert default data
    # Default VPS plans
    vps_plans = [
        ('Starter VPS', 1, 1024, 20, 1, 299),
        ('Pro VPS', 2, 2048, 40, 2, 599),
        ('Business VPS', 4, 4096, 80, 3, 1199),
        ('Enterprise VPS', 8, 8192, 160, 5, 2299),
        ('Ultimate VPS', 16, 16384, 320, 10, 4499),
    ]
    for plan in vps_plans:
        c.execute('INSERT OR IGNORE INTO vps_plans (name, cpu, ram, storage, bandwidth, price) VALUES (?, ?, ?, ?, ?, ?)', plan)
    
    # Default Minecraft plans
    mc_plans = [
        ('MC-Basic', 1024, 100, 10, 10, 199),
        ('MC-Standard', 2048, 200, 20, 25, 399),
        ('MC-Pro', 4096, 300, 40, 50, 799),
        ('MC-Ultimate', 8192, 400, 80, 100, 1499),
    ]
    for plan in mc_plans:
        c.execute('INSERT OR IGNORE INTO mc_plans (name, ram, cpu_percent, storage, slots, price) VALUES (?, ?, ?, ?, ?, ?)', plan)
    
    # Default RDP plans
    rdp_plans = [
        ('RDP-Lite', 1, 1024, 20, 'Windows 10', 399),
        ('RDP-Standard', 2, 2048, 40, 'Windows 10', 699),
        ('RDP-Pro', 4, 4096, 80, 'Windows Server', 1299),
        ('RDP-Enterprise', 8, 8192, 160, 'Windows Server', 2499),
    ]
    for plan in rdp_plans:
        c.execute('INSERT OR IGNORE INTO rdp_plans (name, cpu, ram, storage, os, price) VALUES (?, ?, ?, ?, ?, ?)', plan)
    
    # Default Nitro plans
    nitro_plans = [
        ('Nitro Basic', 30, 30, '✨ Basic features, emojis, stickers'),
        ('Nitro Standard', 90, 70, '🎮 Standard features, HD streaming, profile customization'),
        ('Nitro Premium', 365, 200, '👑 Premium features, 4K streaming, server boosting perks'),
        ('Nitro Ultimate', 730, 350, '⭐ Ultimate features, everything included + exclusive perks'),
    ]
    for plan in nitro_plans:
        c.execute('INSERT OR IGNORE INTO nitro_plans (name, duration_days, price, features) VALUES (?, ?, ?, ?)', plan)
    
    # Default links
    default_links = [
        ('Website', 'https://atyro.cloud', '🌐', 'general'),
        ('Discord', 'https://discord.gg/atyro', '💬', 'social'),
        ('Client Area', 'https://client.atyro.cloud', '👥', 'account'),
        ('Status', 'https://status.atyro.cloud', '📊', 'general'),
        ('Documentation', 'https://docs.atyro.cloud', '📚', 'general'),
        ('GitHub', 'https://github.com/atyro', '🐙', 'development'),
        ('Twitter', 'https://twitter.com/atyro', '🐦', 'social'),
    ]
    for link in default_links:
        c.execute('INSERT OR IGNORE INTO links (name, url, icon, category) VALUES (?, ?, ?, ?)', link)
    
    # Default website settings
    c.execute('INSERT OR IGNORE INTO website_settings (id, site_title, primary_color, secondary_color) VALUES (1, "Atyro Cloud", "#5865F2", "#57F287")')
    
    # Create default owner/admin
    c.execute('SELECT * FROM users WHERE username = ?', ('vectro',))
    if not c.fetchone():
        hashed_pw = hashlib.sha256('vectro1234'.encode()).hexdigest()
        c.execute('INSERT INTO users (username, email, password, is_admin, is_owner) VALUES (?, ?, ?, ?, ?)',
                  ('vectro', 'admin@vectro.net', hashed_pw, 1, 1))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ==================== FLASK LOGIN MANAGER ====================

class User(UserMixin):
    def __init__(self, id, username, email, is_admin, is_owner, discord_id=None, discord_name=None):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.is_owner = is_owner
        self.discord_id = discord_id
        self.discord_name = discord_name

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT id, username, email, is_admin, is_owner, discord_id, discord_name FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3], user[4], user[5], user[6])
    return None

# ==================== HELPER FUNCTIONS ====================

def log_audit(admin_id, admin_name, action, details=""):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('INSERT INTO audit_logs (admin_id, admin_name, action, details) VALUES (?, ?, ?, ?)',
              (admin_id, admin_name, action, details))
    conn.commit()
    conn.close()

def get_website_settings():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT site_title, primary_color, secondary_color, background_color, text_color, footer_text, maintenance_mode, custom_css, custom_js FROM website_settings WHERE id = 1')
    settings = c.fetchone()
    conn.close()
    if settings:
        return {
            'site_title': settings[0],
            'primary_color': settings[1],
            'secondary_color': settings[2],
            'background_color': settings[3] or '#0A0A0A',
            'text_color': settings[4] or '#FFFFFF',
            'footer_text': settings[5] or '© 2026 Atyro Cloud. All rights reserved.',
            'maintenance_mode': settings[6] or 0,
            'custom_css': settings[7] or '',
            'custom_js': settings[8] or ''
        }
    return {
        'site_title': 'Atyro Cloud',
        'primary_color': '#5865F2',
        'secondary_color': '#57F287',
        'background_color': '#0A0A0A',
        'text_color': '#FFFFFF',
        'footer_text': '© 2026 Atyro Cloud. All rights reserved.',
        'maintenance_mode': 0,
        'custom_css': '',
        'custom_js': ''
    }

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== FLASK ROUTES ====================

# HTML Templates as strings
MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ settings.site_title }} | Premium Hosting Solutions</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        
        /* Navigation */
        .navbar {
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 0;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-left: 2rem;
            transition: color 0.3s;
        }
        .nav-links a:hover { color: {{ settings.primary_color }}; }
        
        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, rgba(88,101,242,0.1), rgba(87,242,135,0.05));
            padding-top: 80px;
        }
        .hero-content {
            text-align: center;
            max-width: 800px;
            margin: 0 auto;
        }
        .hero h1 {
            font-size: 4rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }
        
        .btn {
            display: inline-block;
            padding: 12px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin: 0 10px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .btn-primary {
            background: {{ settings.primary_color }};
            color: white;
        }
        .btn-secondary {
            background: transparent;
            border: 2px solid {{ settings.primary_color }};
            color: {{ settings.primary_color }};
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        
        /* Stats Section */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            padding: 4rem 0;
            text-align: center;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            padding: 2rem;
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        .stat-number { font-size: 2.5rem; font-weight: 800; color: {{ settings.primary_color }}; }
        
        /* Plans Section */
        .plans {
            padding: 4rem 0;
        }
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 3rem;
        }
        .plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }
        .plan-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 2rem;
            transition: transform 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .plan-card:hover { transform: translateY(-10px); border-color: {{ settings.primary_color }}; }
        .plan-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; }
        .plan-price { font-size: 2rem; font-weight: 800; color: {{ settings.primary_color }}; margin: 1rem 0; }
        .plan-features { list-style: none; margin: 1rem 0; }
        .plan-features li { padding: 0.5rem 0; opacity: 0.8; }
        
        /* Footer */
        .footer {
            background: rgba(0,0,0,0.5);
            padding: 3rem 0;
            margin-top: 4rem;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .nav-links { display: none; }
        }
    </style>
    {{ settings.custom_css|safe }}
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">{{ settings.site_title }}</div>
            <div class="nav-links">
                <a href="#home">Home</a>
                <a href="#plans">Plans</a>
                <a href="#features">Features</a>
                {% if current_user.is_authenticated %}
                    <a href="/dashboard">Dashboard</a>
                    <a href="/logout">Logout</a>
                {% else %}
                    <a href="/login">Login</a>
                    <a href="/register">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>
    
    <section class="hero" id="home">
        <div class="container">
            <div class="hero-content">
                <h1>Welcome to {{ settings.site_title }}</h1>
                <p>Experience premium hosting solutions with blazing-fast performance</p>
                <a href="/register" class="btn btn-primary">Get Started</a>
                <a href="#plans" class="btn btn-secondary">View Offers</a>
            </div>
        </div>
    </section>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">99.9%</div>
                <div>UPTIME</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">7+</div>
                <div>CLIENTS</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">24/7</div>
                <div>SUPPORT</div>
            </div>
        </div>
    </div>
    
    <section class="plans" id="plans">
        <div class="container">
            <h2 class="section-title">Our Services</h2>
            <div class="plans-grid">
                <div class="plan-card">
                    <div class="plan-name">💻 VPS Hosting</div>
                    <div class="plan-price">₹299/mo</div>
                    <ul class="plan-features">
                        <li>✓ 1 vCPU Core</li>
                        <li>✓ 1GB RAM</li>
                        <li>✓ 20GB SSD</li>
                        <li>✓ 1TB Bandwidth</li>
                    </ul>
                    <a href="/register" class="btn btn-primary" style="width:100%; text-align:center;">Order Now</a>
                </div>
                <div class="plan-card">
                    <div class="plan-name">🎮 Minecraft Hosting</div>
                    <div class="plan-price">₹199/mo</div>
                    <ul class="plan-features">
                        <li>✓ 1GB RAM</li>
                        <li>✓ Unlimited Slots</li>
                        <li>✓ DDoS Protection</li>
                        <li>✓ 24/7 Support</li>
                    </ul>
                    <a href="/register" class="btn btn-primary" style="width:100%; text-align:center;">Order Now</a>
                </div>
                <div class="plan-card">
                    <div class="plan-name">🖥️ RDP Server</div>
                    <div class="plan-price">₹399/mo</div>
                    <ul class="plan-features">
                        <li>✓ 1 vCPU</li>
                        <li>✓ 1GB RAM</li>
                        <li>✓ Windows 10</li>
                        <li>✓ Admin Access</li>
                    </ul>
                    <a href="/register" class="btn btn-primary" style="width:100%; text-align:center;">Order Now</a>
                </div>
                <div class="plan-card">
                    <div class="plan-name">✨ Discord Nitro</div>
                    <div class="plan-price">₹30/mo</div>
                    <ul class="plan-features">
                        <li>✓ 30 Days Duration</li>
                        <li>✓ Instant Delivery</li>
                        <li>✓ Global Access</li>
                        <li>✓ 24/7 Support</li>
                    </ul>
                    <a href="/register" class="btn btn-primary" style="width:100%; text-align:center;">Buy Now</a>
                </div>
            </div>
        </div>
    </section>
    
    <footer class="footer">
        <div class="container">
            <p>{{ settings.footer_text }}</p>
        </div>
    </footer>
    
    <script>
        {{ settings.custom_js|safe }}
    </script>
</body>
</html>
'''

LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - {{ settings.site_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: rgba(255,255,255,0.05);
            padding: 3rem;
            border-radius: 20px;
            width: 100%;
            max-width: 450px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .logo {
            text-align: center;
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: white;
            font-size: 1rem;
        }
        input:focus {
            outline: none;
            border-color: {{ settings.primary_color }};
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: {{ settings.primary_color }};
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: {{ settings.primary_color }};
            text-decoration: none;
        }
        .discord-btn {
            background: #5865F2;
            margin-top: 1rem;
        }
        .flash {
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }
        .flash.error { background: rgba(255,69,58,0.2); border: 1px solid #ff453a; }
        .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">{{ settings.site_title }}</div>
        <h2 style="text-align:center; margin-bottom:1.5rem;">Welcome Back!</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label>Username or Email</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        
        <div class="links">
            <p>Don't have an account? <a href="/register">Register here</a></p>
            <p><a href="/">← Back to Home</a></p>
        </div>
    </div>
</body>
</html>
'''

REGISTER_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - {{ settings.site_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .register-container {
            background: rgba(255,255,255,0.05);
            padding: 3rem;
            border-radius: 20px;
            width: 100%;
            max-width: 500px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .logo {
            text-align: center;
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: white;
            font-size: 1rem;
        }
        input:focus {
            outline: none;
            border-color: {{ settings.primary_color }};
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: {{ settings.primary_color }};
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
        .links {
            text-align: center;
            margin-top: 1.5rem;
        }
        .links a {
            color: {{ settings.primary_color }};
            text-decoration: none;
        }
        .flash {
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }
        .flash.error { background: rgba(255,69,58,0.2); border: 1px solid #ff453a; }
        .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">{{ settings.site_title }}</div>
        <h2 style="text-align:center; margin-bottom:1.5rem;">Create Account</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Email Address</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" name="confirm_password" required>
            </div>
            <button type="submit" class="btn">Register</button>
        </form>
        
        <div class="links">
            <p>Already have an account? <a href="/login">Login here</a></p>
            <p><a href="/">← Back to Home</a></p>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - {{ settings.site_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
        }
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
            padding: 2rem 1rem;
        }
        .sidebar .logo {
            font-size: 1.5rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .sidebar nav a {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            transition: background 0.3s;
        }
        .sidebar nav a:hover, .sidebar nav a.active {
            background: rgba(88,101,242,0.2);
        }
        .sidebar nav a i {
            width: 24px;
            margin-right: 12px;
        }
        .main-content {
            margin-left: 260px;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card h3 { margin-bottom: 0.5rem; opacity: 0.8; }
        .stat-card .value { font-size: 2rem; font-weight: 800; color: {{ settings.primary_color }}; }
        .vps-list {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 1.5rem;
        }
        .vps-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .vps-item:last-child { border-bottom: none; }
        .status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        .status.active { background: #57f287; color: #000; }
        .status.stopped { background: #ff453a; color: #fff; }
        .btn-small {
            padding: 6px 12px;
            background: {{ settings.primary_color }};
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            margin-left: 8px;
        }
        .flash {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
        .flash.error { background: rgba(255,69,58,0.2); border: 1px solid #ff453a; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">{{ settings.site_title }}</div>
        <nav>
            <a href="/dashboard" class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
            <a href="/dashboard/vps"><i class="fas fa-server"></i> My VPS</a>
            <a href="/dashboard/rdp"><i class="fas fa-desktop"></i> My RDP</a>
            <a href="/dashboard/nitro"><i class="fab fa-discord"></i> My Nitro</a>
            <a href="/dashboard/settings"><i class="fas fa-cog"></i> Settings</a>
            {% if current_user.is_admin %}
            <a href="/admin"><i class="fas fa-shield-alt"></i> Admin Panel</a>
            {% endif %}
            <a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </nav>
    </div>
    
    <div class="main-content">
        <div class="header">
            <h1>Welcome back, {{ current_user.username }}!</h1>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Active VPS</h3>
                <div class="value">{{ vps_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Active RDP</h3>
                <div class="value">{{ rdp_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Nitro Purchased</h3>
                <div class="value">{{ nitro_count }}</div>
            </div>
            <div class="stat-card">
                <h3>VPS Limit</h3>
                <div class="value">{{ vps_limit }}</div>
            </div>
        </div>
        
        <div class="vps-list">
            <h2 style="margin-bottom: 1rem;">Your VPS Servers</h2>
            {% if vps_list %}
                {% for vps in vps_list %}
                <div class="vps-item">
                    <div>
                        <strong>{{ vps[2] or vps[1] }}</strong><br>
                        <small>Created: {{ vps[3] }}</small>
                    </div>
                    <div>
                        <span class="status {{ vps[4] }}">{{ vps[4].upper() }}</span>
                        <button class="btn-small" onclick="manageVPS({{ vps[0] }})">Manage</button>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p>No VPS servers yet. Use the bot command `>deploy ubuntu` to create one!</p>
            {% endif %}
        </div>
    </div>
    
    <script>
        function manageVPS(id) {
            window.location.href = '/dashboard/vps/' + id;
        }
    </script>
</body>
</html>
'''

ADMIN_PANEL = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - {{ settings.site_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
        }
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
            padding: 2rem 1rem;
            overflow-y: auto;
        }
        .sidebar .logo {
            font-size: 1.5rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .sidebar nav a {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            transition: background 0.3s;
        }
        .sidebar nav a:hover, .sidebar nav a.active {
            background: rgba(88,101,242,0.2);
        }
        .sidebar nav a i {
            width: 24px;
            margin-right: 12px;
        }
        .main-content {
            margin-left: 280px;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        input, select, textarea {
            width: 100%;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: white;
            font-size: 0.9rem;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: {{ settings.primary_color }};
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn-primary {
            background: {{ settings.primary_color }};
            color: white;
        }
        .btn-success {
            background: #57f287;
            color: #000;
        }
        .btn-danger {
            background: #ff453a;
            color: white;
        }
        .btn-warning {
            background: #f5a623;
            color: #000;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .table {
            width: 100%;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(255,255,255,0.05);
            font-weight: 600;
        }
        .flash {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
        .flash.error { background: rgba(255,69,58,0.2); border: 1px solid #ff453a; }
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .status-enabled { background: #57f287; color: #000; }
        .status-disabled { background: #ff453a; color: #fff; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">{{ settings.site_title }} Admin</div>
        <nav>
            <a href="/admin" class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
            <a href="/admin/bot-settings"><i class="fab fa-discord"></i> Bot Settings</a>
            <a href="/admin/website-settings"><i class="fas fa-globe"></i> Website Settings</a>
            <a href="/admin/plans"><i class="fas fa-tags"></i> Plans Manager</a>
            <a href="/admin/vps"><i class="fas fa-server"></i> VPS Manager</a>
            <a href="/admin/links"><i class="fas fa-link"></i> Links Manager</a>
            <a href="/admin/users"><i class="fas fa-users"></i> Users Manager</a>
            <a href="/admin/commands"><i class="fas fa-terminal"></i> Bot Commands</a>
            <a href="/admin/audit-logs"><i class="fas fa-history"></i> Audit Logs</a>
            <a href="/dashboard"><i class="fas fa-arrow-left"></i> Back to Site</a>
        </nav>
    </div>
    
    <div class="main-content">
        <div class="header">
            <h1>Admin Control Panel</h1>
            <div>Welcome, {{ current_user.username }}</div>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <div class="grid-2">
            <div class="card">
                <h2><i class="fas fa-chart-line"></i> Quick Stats</h2>
                <div style="margin-top: 1rem;">
                    <p><strong>Total Users:</strong> {{ stats.total_users }}</p>
                    <p><strong>Active VPS:</strong> {{ stats.active_vps }}</p>
                    <p><strong>Total RDP:</strong> {{ stats.total_rdp }}</p>
                    <p><strong>Nitro Purchases:</strong> {{ stats.nitro_purchases }}</p>
                    <p><strong>Total Revenue:</strong> ₹{{ stats.total_revenue }}</p>
                </div>
            </div>
            
            <div class="card">
                <h2><i class="fab fa-discord"></i> Bot Status</h2>
                <div style="margin-top: 1rem;">
                    <p><strong>Bot Name:</strong> {{ bot_settings.bot_name }}</p>
                    <p><strong>Prefix:</strong> {{ bot_settings.bot_prefix }}</p>
                    <p><strong>Maintenance:</strong> 
                        <span class="status-badge {% if bot_settings.maintenance_mode %}status-enabled{% else %}status-disabled{% endif %}">
                            {{ "ON" if bot_settings.maintenance_mode else "OFF" }}
                        </span>
                    </p>
                    <p><strong>Total Commands:</strong> 30+</p>
                    <a href="/admin/bot-settings" class="btn btn-primary" style="margin-top: 1rem; display: inline-block;">Configure Bot</a>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-terminal"></i> Quick Actions</h2>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <button class="btn btn-success" onclick="window.location.href='/admin/plans/add'"><i class="fas fa-plus"></i> Add Plan</button>
                <button class="btn btn-warning" onclick="window.location.href='/admin/bot-settings'"><i class="fas fa-sync-alt"></i> Sync Bot</button>
                <button class="btn btn-danger" onclick="confirmMaintenance()"><i class="fas fa-tools"></i> Toggle Maintenance</button>
                <button class="btn btn-primary" onclick="window.location.href='/admin/commands'"><i class="fas fa-code"></i> Manage Commands</button>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-clock"></i> Recent Audit Logs</h2>
            <div class="table">
                <table>
                    <thead>
                        <tr><th>Time</th><th>Admin</th><th>Action</th><th>Details</th></tr>
                    </thead>
                    <tbody>
                        {% for log in audit_logs %}
                        <tr>
                            <td>{{ log[0] }}</td>
                            <td>{{ log[1] }}</td>
                            <td>{{ log[2] }}</td>
                            <td>{{ log[3] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function confirmMaintenance() {
            if(confirm('Toggle maintenance mode? Users won\'t be able to use bot commands except admins.')) {
                window.location.href = '/admin/toggle-maintenance';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    settings = get_website_settings()
    if settings['maintenance_mode'] and not (current_user.is_authenticated and current_user.is_admin):
        return "<h1>Maintenance Mode</h1><p>Website is under maintenance. Please check back later.</p>"
    return render_template_string(MAIN_PAGE, settings=settings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    settings = get_website_settings()
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT id, username, email, is_admin, is_owner, discord_id, discord_name FROM users WHERE (username = ? OR email = ?) AND password = ?', 
                  (username, username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            user_obj = User(user[0], user[1], user[2], user[3], user[4], user[5], user[6])
            login_user(user_obj)
            flash('Login successful!', 'success')
            log_audit(user[0], user[1], 'User Login', f'Logged in from web')
            if user[3]:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template_string(LOGIN_PAGE, settings=settings)

@app.route('/register', methods=['GET', 'POST'])
def register():
    settings = get_website_settings()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            flash('Passwords do not match!', 'error')
            return render_template_string(REGISTER_PAGE, settings=settings)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template_string(REGISTER_PAGE, settings=settings)
        
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)',
                      (username, email, hashed_pw, 0))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()
    
    return render_template_string(REGISTER_PAGE, settings=settings)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    settings = get_website_settings()
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    c.execute('SELECT vps_limit FROM users WHERE id = ?', (current_user.id,))
    vps_limit = c.fetchone()[0]
    
    c.execute('SELECT id, container_name, os_type, created_at, status FROM vps_servers WHERE user_id = ?', (current_user.id,))
    vps_list = c.fetchall()
    
    c.execute('SELECT COUNT(*) FROM rdp_servers WHERE user_id = ?', (current_user.id,))
    rdp_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM nitro_purchases WHERE user_id = ?', (current_user.id,))
    nitro_count = c.fetchone()[0]
    
    conn.close()
    
    return render_template_string(DASHBOARD_PAGE, settings=settings, vps_count=len(vps_list), 
                                  rdp_count=rdp_count, nitro_count=nitro_count, 
                                  vps_limit=vps_limit, vps_list=vps_list)

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    settings = get_website_settings()
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM vps_servers WHERE status = "running"')
    active_vps = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM rdp_servers')
    total_rdp = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM nitro_purchases')
    nitro_purchases = c.fetchone()[0]
    
    c.execute('SELECT SUM(price) FROM vps_plans')
    total_revenue = c.fetchone()[0] or 0
    
    c.execute('SELECT bot_name, bot_prefix, maintenance_mode FROM bot_settings WHERE id = 1')
    bot_settings_row = c.fetchone()
    bot_settings = {
        'bot_name': bot_settings_row[0] if bot_settings_row else 'vectro',
        'bot_prefix': bot_settings_row[1] if bot_settings_row else '>',
        'maintenance_mode': bot_settings_row[2] if bot_settings_row else 0
    }
    
    c.execute('SELECT timestamp, admin_name, action, details FROM audit_logs ORDER BY timestamp DESC LIMIT 10')
    audit_logs = c.fetchall()
    
    conn.close()
    
    stats = {
        'total_users': total_users,
        'active_vps': active_vps,
        'total_rdp': total_rdp,
        'nitro_purchases': nitro_purchases,
        'total_revenue': total_revenue
    }
    
    return render_template_string(ADMIN_PANEL, settings=settings, stats=stats, 
                                  bot_settings=bot_settings, audit_logs=audit_logs)

@app.route('/admin/bot-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def bot_settings_panel():
    settings = get_website_settings()
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        bot_token = request.form.get('bot_token', '')
        bot_name = request.form.get('bot_name', 'vectro')
        bot_prefix = request.form.get('bot_prefix', '>')
        bot_owner_id = request.form.get('bot_owner_id', '')
        bot_status = request.form.get('bot_status', 'online')
        bot_activity = request.form.get('bot_activity', '>help | Atyro Cloud')
        
        c.execute('''UPDATE bot_settings SET 
                    bot_token = ?, bot_name = ?, bot_prefix = ?, 
                    bot_owner_id = ?, bot_status = ?, bot_activity = ?,
                    last_updated = CURRENT_TIMESTAMP WHERE id = 1''',
                  (bot_token, bot_name, bot_prefix, bot_owner_id, bot_status, bot_activity))
        conn.commit()
        flash('Bot settings updated successfully!', 'success')
        log_audit(current_user.id, current_user.username, 'Bot Settings Update', f'Updated bot configuration')
    
    c.execute('SELECT bot_token, bot_name, bot_prefix, bot_owner_id, bot_status, bot_activity, maintenance_mode FROM bot_settings WHERE id = 1')
    bot_data = c.fetchone()
    conn.close()
    
    bot_settings_form = {
        'bot_token': bot_data[0] if bot_data else '',
        'bot_name': bot_data[1] if bot_data else 'vectro',
        'bot_prefix': bot_data[2] if bot_data else '>',
        'bot_owner_id': bot_data[3] if bot_data else '',
        'bot_status': bot_data[4] if bot_data else 'online',
        'bot_activity': bot_data[5] if bot_data else '>help | Atyro Cloud',
        'maintenance_mode': bot_data[6] if bot_data else 0
    }
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Settings - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 800px; margin: 2rem auto; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 16px; }
            h1 { margin-bottom: 2rem; }
            .form-group { margin-bottom: 1.5rem; }
            label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
            input, select, textarea { width: 100%; padding: 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }
            .btn { padding: 12px 24px; background: #5865F2; border: none; border-radius: 8px; color: white; cursor: pointer; }
            .btn:hover { transform: translateY(-2px); }
            .flash { padding: 12px; border-radius: 8px; margin-bottom: 1rem; }
            .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
            .back-link { display: inline-block; margin-top: 1rem; color: #5865F2; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fab fa-discord"></i> Discord Bot Settings</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label>Bot Token</label>
                    <input type="password" name="bot_token" value="{{ bot_settings.bot_token }}" placeholder="Enter Discord Bot Token">
                </div>
                <div class="form-group">
                    <label>Bot Name</label>
                    <input type="text" name="bot_name" value="{{ bot_settings.bot_name }}" required>
                </div>
                <div class="form-group">
                    <label>Command Prefix</label>
                    <input type="text" name="bot_prefix" value="{{ bot_settings.bot_prefix }}" required>
                </div>
                <div class="form-group">
                    <label>Bot Owner Discord ID</label>
                    <input type="text" name="bot_owner_id" value="{{ bot_settings.bot_owner_id }}" placeholder="Discord User ID">
                </div>
                <div class="form-group">
                    <label>Bot Status</label>
                    <select name="bot_status">
                        <option value="online" {% if bot_settings.bot_status == 'online' %}selected{% endif %}>Online</option>
                        <option value="idle" {% if bot_settings.bot_status == 'idle' %}selected{% endif %}>Idle</option>
                        <option value="dnd" {% if bot_settings.bot_status == 'dnd' %}selected{% endif %}>Do Not Disturb</option>
                        <option value="invisible" {% if bot_settings.bot_status == 'invisible' %}selected{% endif %}>Invisible</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Bot Activity</label>
                    <input type="text" name="bot_activity" value="{{ bot_settings.bot_activity }}" placeholder="Playing/Watching/Listening to...">
                </div>
                <button type="submit" class="btn">Save Settings</button>
            </form>
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
    </body>
    </html>
    ''', settings=settings, bot_settings=bot_settings_form)

@app.route('/admin/website-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def website_settings_panel():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        site_title = request.form.get('site_title', 'Atyro Cloud')
        primary_color = request.form.get('primary_color', '#5865F2')
        secondary_color = request.form.get('secondary_color', '#57F287')
        background_color = request.form.get('background_color', '#0A0A0A')
        text_color = request.form.get('text_color', '#FFFFFF')
        footer_text = request.form.get('footer_text', '© 2026 Atyro Cloud. All rights reserved.')
        custom_css = request.form.get('custom_css', '')
        custom_js = request.form.get('custom_js', '')
        
        c.execute('''UPDATE website_settings SET 
                    site_title = ?, primary_color = ?, secondary_color = ?, 
                    background_color = ?, text_color = ?, footer_text = ?,
                    custom_css = ?, custom_js = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE id = 1''',
                  (site_title, primary_color, secondary_color, background_color, 
                   text_color, footer_text, custom_css, custom_js))
        conn.commit()
        flash('Website settings updated!', 'success')
        log_audit(current_user.id, current_user.username, 'Website Settings Update', 'Updated website appearance')
    
    c.execute('SELECT site_title, primary_color, secondary_color, background_color, text_color, footer_text, custom_css, custom_js FROM website_settings WHERE id = 1')
    site_data = c.fetchone()
    conn.close()
    
    web_settings = {
        'site_title': site_data[0] if site_data else 'Atyro Cloud',
        'primary_color': site_data[1] if site_data else '#5865F2',
        'secondary_color': site_data[2] if site_data else '#57F287',
        'background_color': site_data[3] if site_data else '#0A0A0A',
        'text_color': site_data[4] if site_data else '#FFFFFF',
        'footer_text': site_data[5] if site_data else '© 2026 Atyro Cloud. All rights reserved.',
        'custom_css': site_data[6] if site_data else '',
        'custom_js': site_data[7] if site_data else ''
    }
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Website Settings - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 800px; margin: 2rem auto; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 16px; }
            h1 { margin-bottom: 2rem; }
            .form-group { margin-bottom: 1.5rem; }
            label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
            input, textarea { width: 100%; padding: 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }
            input[type="color"] { height: 50px; }
            .btn { padding: 12px 24px; background: #5865F2; border: none; border-radius: 8px; color: white; cursor: pointer; }
            .btn:hover { transform: translateY(-2px); }
            .flash { padding: 12px; border-radius: 8px; margin-bottom: 1rem; }
            .flash.success { background: rgba(87,242,135,0.2); border: 1px solid #57f287; }
            .back-link { display: inline-block; margin-top: 1rem; color: #5865F2; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-globe"></i> Website Customization</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label>Site Title</label>
                    <input type="text" name="site_title" value="{{ web_settings.site_title }}" required>
                </div>
                <div class="form-group">
                    <label>Primary Color</label>
                    <input type="color" name="primary_color" value="{{ web_settings.primary_color }}">
                </div>
                <div class="form-group">
                    <label>Secondary Color</label>
                    <input type="color" name="secondary_color" value="{{ web_settings.secondary_color }}">
                </div>
                <div class="form-group">
                    <label>Background Color</label>
                    <input type="color" name="background_color" value="{{ web_settings.background_color }}">
                </div>
                <div class="form-group">
                    <label>Text Color</label>
                    <input type="color" name="text_color" value="{{ web_settings.text_color }}">
                </div>
                <div class="form-group">
                    <label>Footer Text</label>
                    <input type="text" name="footer_text" value="{{ web_settings.footer_text }}">
                </div>
                <div class="form-group">
                    <label>Custom CSS</label>
                    <textarea name="custom_css" rows="5" placeholder="/* Add custom CSS here */">{{ web_settings.custom_css }}</textarea>
                </div>
                <div class="form-group">
                    <label>Custom JavaScript</label>
                    <textarea name="custom_js" rows="5" placeholder="// Add custom JavaScript here">{{ web_settings.custom_js }}</textarea>
                </div>
                <button type="submit" class="btn">Save Changes</button>
            </form>
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
    </body>
    </html>
    ''', web_settings=web_settings)

@app.route('/admin/plans')
@login_required
@admin_required
def plans_manager():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM vps_plans')
    vps_plans = c.fetchall()
    
    c.execute('SELECT * FROM mc_plans')
    mc_plans = c.fetchall()
    
    c.execute('SELECT * FROM rdp_plans')
    rdp_plans = c.fetchall()
    
    c.execute('SELECT * FROM nitro_plans')
    nitro_plans = c.fetchall()
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plans Manager - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 2rem; }
            h1 { margin-bottom: 2rem; }
            .section { margin-bottom: 3rem; }
            .section h2 { margin-bottom: 1rem; color: #5865F2; }
            table { width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
            th { background: rgba(255,255,255,0.1); }
            .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; margin: 0 4px; }
            .btn-primary { background: #5865F2; color: white; }
            .btn-success { background: #57f287; color: black; }
            .btn-danger { background: #ff453a; color: white; }
            .btn-warning { background: #f5a623; color: black; }
            .back-link { display: inline-block; margin-top: 2rem; color: #5865F2; text-decoration: none; }
            .add-form { background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
            .add-form input { padding: 8px; margin: 4px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-tags"></i> Plans Manager</h1>
            
            <div class="section">
                <h2>💻 VPS Plans</h2>
                <div class="add-form">
                    <h3>Add New VPS Plan</h3>
                    <form method="POST" action="/admin/plans/add/vps">
                        <input type="text" name="name" placeholder="Plan Name" required>
                        <input type="number" name="cpu" placeholder="CPU Cores" required>
                        <input type="number" name="ram" placeholder="RAM (MB)" required>
                        <input type="number" name="storage" placeholder="Storage (GB)" required>
                        <input type="number" name="price" placeholder="Price (₹)" required>
                        <button type="submit" class="btn btn-success">Add Plan</button>
                    </form>
                </div>
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>CPU</th><th>RAM</th><th>Storage</th><th>Price</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for plan in vps_plans %}
                        <tr>
                            <td>{{ plan[0] }}</td><td>{{ plan[1] }}</td><td>{{ plan[2] }} vCPU</td>
                            <td>{{ plan[3] }} MB</td><td>{{ plan[4] }} GB</td><td>₹{{ plan[6] }}</td>
                            <td>
                                <button class="btn btn-warning" onclick="togglePlan({{ plan[0] }}, 'vps')">Toggle</button>
                                <button class="btn btn-danger" onclick="deletePlan({{ plan[0] }}, 'vps')">Delete</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>🎮 Minecraft Plans</h2>
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>RAM</th><th>CPU%</th><th>Slots</th><th>Price</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for plan in mc_plans %}
                        <tr>
                            <td>{{ plan[0] }}</td><td>{{ plan[1] }}</td><td>{{ plan[2] }} MB</td>
                            <td>{{ plan[3] }}%</td><td>{{ plan[5] }}</td><td>₹{{ plan[6] }}</td>
                            <td><button class="btn btn-danger" onclick="deletePlan({{ plan[0] }}, 'mc')">Delete</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>🖥️ RDP Plans</h2>
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>CPU</th><th>RAM</th><th>Storage</th><th>Price</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for plan in rdp_plans %}
                        <tr>
                            <td>{{ plan[0] }}</td><td>{{ plan[1] }}</td><td>{{ plan[2] }} vCPU</td>
                            <td>{{ plan[3] }} MB</td><td>{{ plan[4] }} GB</td><td>₹{{ plan[6] }}</td>
                            <td><button class="btn btn-danger" onclick="deletePlan({{ plan[0] }}, 'rdp')">Delete</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>✨ Nitro Plans</h2>
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>Duration</th><th>Price</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for plan in nitro_plans %}
                        <tr>
                            <td>{{ plan[0] }}</td><td>{{ plan[1] }}</td><td>{{ plan[2] }} days</td>
                            <td>₹{{ plan[3] }}</td>
                            <td><button class="btn btn-danger" onclick="deletePlan({{ plan[0] }}, 'nitro')">Delete</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
        <script>
            function deletePlan(id, type) {
                if(confirm('Delete this plan?')) {
                    window.location.href = '/admin/plans/delete/' + type + '/' + id;
                }
            }
            function togglePlan(id, type) {
                window.location.href = '/admin/plans/toggle/' + type + '/' + id;
            }
        </script>
    </body>
    </html>
    ''', vps_plans=vps_plans, mc_plans=mc_plans, rdp_plans=rdp_plans, nitro_plans=nitro_plans)

@app.route('/admin/plans/add/<plan_type>', methods=['POST'])
@login_required
@admin_required
def add_plan(plan_type):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    if plan_type == 'vps':
        name = request.form['name']
        cpu = request.form['cpu']
        ram = request.form['ram']
        storage = request.form['storage']
        price = request.form['price']
        c.execute('INSERT INTO vps_plans (name, cpu, ram, storage, bandwidth, price) VALUES (?, ?, ?, ?, 1, ?)',
                  (name, cpu, ram, storage, price))
        flash('VPS plan added!', 'success')
    
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Add Plan', f'Added {plan_type} plan: {name}')
    return redirect(url_for('plans_manager'))

@app.route('/admin/plans/delete/<plan_type>/<int:plan_id>')
@login_required
@admin_required
def delete_plan(plan_type, plan_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    
    table_map = {'vps': 'vps_plans', 'mc': 'mc_plans', 'rdp': 'rdp_plans', 'nitro': 'nitro_plans'}
    if plan_type in table_map:
        c.execute(f'DELETE FROM {table_map[plan_type]} WHERE id = ?', (plan_id,))
        conn.commit()
        flash('Plan deleted!', 'success')
        log_audit(current_user.id, current_user.username, 'Delete Plan', f'Deleted {plan_type} plan ID: {plan_id}')
    
    conn.close()
    return redirect(url_for('plans_manager'))

@app.route('/admin/users')
@login_required
@admin_required
def users_manager():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT id, username, email, is_admin, is_banned, vps_limit, created_at FROM users')
    users = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Users Manager - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 2rem; }
            h1 { margin-bottom: 2rem; }
            table { width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05); border-radius: 16px; overflow: hidden; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
            th { background: rgba(255,255,255,0.1); }
            .btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; margin: 0 4px; }
            .btn-primary { background: #5865F2; color: white; }
            .btn-danger { background: #ff453a; color: white; }
            .btn-warning { background: #f5a623; color: black; }
            .back-link { display: inline-block; margin-top: 2rem; color: #5865F2; text-decoration: none; }
            .badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; }
            .badge-admin { background: #5865F2; }
            .badge-banned { background: #ff453a; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-users"></i> Users Manager</h1>
            <table>
                <thead>
                    <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>VPS Limit</th><th>Joined</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user[0] }}</td>
                        <td>{{ user[1] }}</td>
                        <td>{{ user[2] }}</td>
                        <td>{% if user[3] %}<span class="badge badge-admin">Admin</span>{% else %}User{% endif %}</td>
                        <td>{% if user[4] %}<span class="badge badge-banned">Banned</span>{% else %}Active{% endif %}</td>
                        <td>{{ user[5] }}</td>
                        <td>{{ user[6][:10] }}</td>
                        <td>
                            <button class="btn btn-warning" onclick="toggleAdmin({{ user[0] }})">Toggle Admin</button>
                            <button class="btn btn-danger" onclick="toggleBan({{ user[0] }})">Toggle Ban</button>
                            <button class="btn btn-primary" onclick="setVPSLimit({{ user[0] }})">Set Limit</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
        <script>
            function toggleAdmin(id) {
                window.location.href = '/admin/users/toggle-admin/' + id;
            }
            function toggleBan(id) {
                window.location.href = '/admin/users/toggle-ban/' + id;
            }
            function setVPSLimit(id) {
                let limit = prompt('Enter new VPS limit:');
                if(limit) window.location.href = '/admin/users/set-limit/' + id + '/' + limit;
            }
        </script>
    </body>
    </html>
    ''', users=users)

@app.route('/admin/users/toggle-admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin = NOT is_admin WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Toggle Admin', f'Toggled admin for user {user_id}')
    flash('User admin status toggled!', 'success')
    return redirect(url_for('users_manager'))

@app.route('/admin/users/toggle-ban/<int:user_id>')
@login_required
@admin_required
def toggle_ban(user_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('UPDATE users SET is_banned = NOT is_banned WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Toggle Ban', f'Toggled ban for user {user_id}')
    flash('User ban status toggled!', 'success')
    return redirect(url_for('users_manager'))

@app.route('/admin/users/set-limit/<int:user_id>/<int:limit>')
@login_required
@admin_required
def set_vps_limit(user_id, limit):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('UPDATE users SET vps_limit = ? WHERE id = ?', (limit, user_id))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Set VPS Limit', f'Set VPS limit to {limit} for user {user_id}')
    flash('VPS limit updated!', 'success')
    return redirect(url_for('users_manager'))

@app.route('/admin/links')
@login_required
@admin_required
def links_manager():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT id, name, url, icon, category FROM links')
    links = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Links Manager - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 800px; margin: 2rem auto; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 16px; }
            h1 { margin-bottom: 2rem; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
            .btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; }
            .btn-primary { background: #5865F2; color: white; }
            .btn-danger { background: #ff453a; color: white; }
            .btn-success { background: #57f287; color: black; }
            .form-group { margin-bottom: 1rem; }
            input { width: 100%; padding: 8px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: white; }
            .back-link { display: inline-block; margin-top: 2rem; color: #5865F2; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-link"></i> Links Manager</h1>
            
            <h3>Add New Link</h3>
            <form method="POST" action="/admin/links/add">
                <div class="form-group"><input type="text" name="name" placeholder="Link Name" required></div>
                <div class="form-group"><input type="url" name="url" placeholder="URL" required></div>
                <div class="form-group"><input type="text" name="icon" placeholder="Icon Emoji (optional)"></div>
                <div class="form-group"><input type="text" name="category" placeholder="Category"></div>
                <button type="submit" class="btn btn-success">Add Link</button>
            </form>
            
            <h3 style="margin-top: 2rem;">Existing Links</h3>
            <table>
                <thead><tr><th>Name</th><th>URL</th><th>Icon</th><th>Category</th><th>Actions</th></tr></thead>
                <tbody>
                    {% for link in links %}
                    <tr>
                        <td>{{ link[1] }}</td>
                        <td>{{ link[2][:30] }}</td>
                        <td>{{ link[3] or '-' }}</td>
                        <td>{{ link[4] or '-' }}</td>
                        <td><a href="/admin/links/delete/{{ link[0] }}" class="btn btn-danger" onclick="return confirm('Delete this link?')">Delete</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
    </body>
    </html>
    ''', links=links)

@app.route('/admin/links/add', methods=['POST'])
@login_required
@admin_required
def add_link():
    name = request.form['name']
    url = request.form['url']
    icon = request.form.get('icon', '🔗')
    category = request.form.get('category', 'general')
    
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO links (name, url, icon, category) VALUES (?, ?, ?, ?)', (name, url, icon, category))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Add Link', f'Added link: {name}')
    flash('Link added!', 'success')
    return redirect(url_for('links_manager'))

@app.route('/admin/links/delete/<int:link_id>')
@login_required
@admin_required
def delete_link(link_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Delete Link', f'Deleted link ID: {link_id}')
    flash('Link deleted!', 'success')
    return redirect(url_for('links_manager'))

@app.route('/admin/commands')
@login_required
@admin_required
def commands_manager():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT id, command_name, description, category, is_enabled, cooldown FROM bot_commands')
    commands = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Commands - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 1000px; margin: 2rem auto; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 16px; }
            h1 { margin-bottom: 2rem; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
            th { background: rgba(255,255,255,0.1); }
            .btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; }
            .btn-success { background: #57f287; color: black; }
            .btn-danger { background: #ff453a; color: white; }
            .status-enabled { color: #57f287; }
            .status-disabled { color: #ff453a; }
            .back-link { display: inline-block; margin-top: 2rem; color: #5865F2; text-decoration: none; }
            .command-list { max-height: 500px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-terminal"></i> Bot Commands Manager (30+ Commands)</h1>
            <p>Total Commands: {{ commands|length }}</p>
            
            <div class="command-list">
                <table>
                    <thead>
                        <tr><th>Command</th><th>Description</th><th>Category</th><th>Status</th><th>Cooldown</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {% for cmd in commands %}
                        <tr>
                            <td><code>{{ cmd[1] }}</code></td>
                            <td>{{ cmd[2] }}</td>
                            <td>{{ cmd[3] }}</td>
                            <td class="{% if cmd[4] %}status-enabled{% else %}status-disabled{% endif %}">
                                {{ "✅ Enabled" if cmd[4] else "❌ Disabled" }}
                            </td>
                            <td>{{ cmd[5] }}s</td>
                            <td>
                                <a href="/admin/commands/toggle/{{ cmd[0] }}" class="btn {% if cmd[4] %}btn-danger{% else %}btn-success{% endif %}">
                                    {% if cmd[4] %}Disable{% else %}Enable{% endif %}
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <h3 style="margin-top: 2rem;">Available Commands List:</h3>
            <ul style="columns: 2; margin-top: 1rem;">
                <li>>ping - Show bot latency & uptime</li>
                <li>>uptime - Detailed uptime stats</li>
                <li>>deploy &lt;os&gt; - Deploy VPS</li>
                <li>>manage - Manage your VPS</li>
                <li>>links - Show all links</li>
                <li>>update-links - Update links (Admin)</li>
                <li>>plans - Show all plans</li>
                <li>>plans-update - Update plans (Admin)</li>
                <li>>auth_web - Discord web auth</li>
                <li>>server-stats - VPS server stats</li>
                <li>>web-stats - Website visitor stats</li>
                <li>>admin-add @user - Add admin</li>
                <li>>admin-list - List admins</li>
                <li>>admin-remove @user - Remove admin</li>
                <li>>maintenance-bot - Toggle maintenance</li>
                <li>>status-page - Show status page</li>
                <li>>vps_create - Create VPS</li>
                <li>>vps_list - List VPS</li>
                <li>>vps_stop/start/restart - Manage VPS</li>
                <li>>rdp_list/create/info - RDP commands</li>
                <li>>nitro_check/buy - Nitro commands</li>
                <li>>user_info - User info</li>
                <li>>server_info - Server info</li>
            </ul>
            
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
    </body>
    </html>
    ''', commands=commands)

@app.route('/admin/commands/toggle/<int:cmd_id>')
@login_required
@admin_required
def toggle_command(cmd_id):
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('UPDATE bot_commands SET is_enabled = NOT is_enabled WHERE id = ?', (cmd_id,))
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Toggle Command', f'Toggled command ID: {cmd_id}')
    flash('Command status toggled!', 'success')
    return redirect(url_for('commands_manager'))

@app.route('/admin/audit-logs')
@login_required
@admin_required
def audit_logs():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, admin_name, action, details FROM audit_logs ORDER BY timestamp DESC LIMIT 100')
    logs = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit Logs - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 16px; }
            h1 { margin-bottom: 2rem; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
            th { background: rgba(255,255,255,0.1); }
            .back-link { display: inline-block; margin-top: 2rem; color: #5865F2; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-history"></i> Audit Logs</h1>
            <table>
                <thead><tr><th>Timestamp</th><th>Admin</th><th>Action</th><th>Details</th></tr></thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td>{{ log[0] }}</td>
                        <td>{{ log[1] }}</td>
                        <td>{{ log[2] }}</td>
                        <td>{{ log[3] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="/admin" class="back-link">← Back to Admin Panel</a>
        </div>
    </body>
    </html>
    ''', logs=logs)

@app.route('/admin/toggle-maintenance')
@login_required
@admin_required
def toggle_maintenance():
    conn = sqlite3.connect('vps.db')
    c = conn.cursor()
    c.execute('UPDATE bot_settings SET maintenance_mode = NOT maintenance_mode WHERE id = 1')
    conn.commit()
    conn.close()
    log_audit(current_user.id, current_user.username, 'Toggle Maintenance', 'Toggled bot maintenance mode')
    flash('Maintenance mode toggled!', 'success')
    return redirect(url_for('admin_panel'))

# ==================== DISCORD BOT CLASS ====================

class AtyroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=self.get_prefix, intents=intents, help_command=None)
        self.start_time = datetime.now()
    
    async def get_prefix(self, message):
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT bot_prefix FROM bot_settings WHERE id = 1')
        prefix = c.fetchone()
        conn.close()
        return prefix[0] if prefix else '>'
    
    async def setup_hook(self):
        await self.add_cog(BotCommandsCog(self))
    
    async def on_ready(self):
        print(f'✅ Bot is ready! Logged in as {self.user}')
        await self.change_presence(activity=discord.Game(name=self.get_activity()))
    
    def get_activity(self):
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT bot_activity FROM bot_settings WHERE id = 1')
        activity = c.fetchone()
        conn.close()
        return activity[0] if activity else '>help | Atyro Cloud'

class BotCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, user_id):
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT is_admin FROM users WHERE discord_id = ?', (str(user_id),))
        result = c.fetchone()
        conn.close()
        return result and result[0] == 1
    
    def log_command(self, command_name, user_id, user_name):
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('INSERT INTO audit_logs (admin_name, action, details) VALUES (?, ?, ?)',
                  (user_name, f'Used command: {command_name}', f'Discord user {user_id}'))
        conn.commit()
        conn.close()
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """🏓 Show bot latency and uptime"""
        uptime = datetime.now() - self.bot.start_time
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** `{round(self.bot.latency * 1000)}ms`\n**Uptime:** `{str(uptime).split('.')[0]}`\n**Website:** ✅ Online",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        self.log_command('ping', ctx.author.id, ctx.author.name)
    
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """⏱️ Show detailed bot uptime"""
        uptime = datetime.now() - self.bot.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            description=f"**Total:** `{days}d {hours}h {minutes}m {seconds}s`\n**Started:** `{self.bot.start_time.strftime('%Y-%m-%d %H:%M:%S')}`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        self.log_command('uptime', ctx.author.id, ctx.author.name)
    
    @commands.command(name='deploy')
    async def deploy(self, ctx, os_type: str = 'ubuntu'):
        """🚀 Deploy a VPS using Docker"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT id, vps_limit FROM users WHERE discord_id = ?', (str(ctx.author.id),))
        user = c.fetchone()
        
        if not user:
            await ctx.send("❌ Please register on the website first: `/register`")
            conn.close()
            return
        
        user_id, vps_limit = user
        c.execute('SELECT COUNT(*) FROM vps_servers WHERE user_id = ?', (user_id,))
        vps_count = c.fetchone()[0]
        
        if vps_count >= vps_limit:
            await ctx.send(f"❌ You have reached your VPS limit ({vps_limit})")
            conn.close()
            return
        
        # Create container using docker (simulated)
        container_name = f"vps-{ctx.author.id}-{int(datetime.now().timestamp())}"
        
        c.execute('''INSERT INTO vps_servers (user_id, container_name, os_type, cpu, ram, storage, status) 
                     VALUES (?, ?, ?, 1, 1024, 10, 'running')''', 
                  (user_id, container_name, os_type))
        conn.commit()
        vps_id = c.lastrowid
        conn.close()
        
        embed = discord.Embed(
            title="🚀 VPS Deployed Successfully!",
            description=f"**VPS ID:** `{vps_id}`\n**OS:** `{os_type}`\n**Specs:** 1 vCPU | 1GB RAM | 10GB SSD\n**Status:** 🟢 Running",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Use {await self.bot.get_prefix(ctx.message)}manage to control your VPS")
        await ctx.send(embed=embed)
        self.log_command('deploy', ctx.author.id, ctx.author.name)
    
    @commands.command(name='manage')
    async def manage(self, ctx):
        """⚙️ Manage your VPS with buttons"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''SELECT v.id, v.container_name, v.status, v.os_type 
                     FROM vps_servers v JOIN users u ON v.user_id = u.id 
                     WHERE u.discord_id = ?''', (str(ctx.author.id),))
        vps_list = c.fetchall()
        conn.close()
        
        if not vps_list:
            await ctx.send("❌ You don't have any VPS. Use `>deploy` to create one!")
            return
        
        embed = discord.Embed(
            title="⚙️ Your VPS Servers",
            description="Click the buttons below to manage each VPS",
            color=discord.Color.purple()
        )
        
        for vps in vps_list:
            status_emoji = "🟢" if vps[2] == "running" else "🔴"
            embed.add_field(
                name=f"{status_emoji} VPS #{vps[0]} - {vps[1]}",
                value=f"OS: {vps[3]}\nStatus: {vps[2].upper()}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        self.log_command('manage', ctx.author.id, ctx.author.name)
    
    @commands.command(name='links')
    async def links(self, ctx):
        """🔗 Show all important links"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT name, url, icon FROM links')
        links = c.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="🔗 Atyro Cloud - Important Links",
            color=discord.Color.teal()
        )
        
        for link in links:
            embed.add_field(name=f"{link[2] if link[2] else '🔗'} {link[0]}", value=f"[Click Here]({link[1]})", inline=True)
        
        await ctx.send(embed=embed)
        self.log_command('links', ctx.author.id, ctx.author.name)
    
    @commands.command(name='update-links')
    @commands.has_permissions(administrator=True)
    async def update_links(self, ctx, name: str = None, url: str = None):
        """✏️ Update links (Admin only)"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Admin only command!")
            return
        
        if not name or not url:
            await ctx.send("Usage: `>update-links <name> <url>`")
            return
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO links (name, url) VALUES (?, ?)', (name, url))
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ Link `{name}` updated/added!")
        self.log_command('update-links', ctx.author.id, ctx.author.name)
    
    @commands.command(name='plans')
    async def plans(self, ctx):
        """📋 Show all available plans"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        
        embed = discord.Embed(
            title="📋 Atyro Cloud - Hosting Plans",
            description="Choose your perfect plan!",
            color=discord.Color.gold()
        )
        
        # VPS Plans
        c.execute('SELECT name, cpu, ram, storage, price FROM vps_plans WHERE is_available = 1 LIMIT 3')
        vps_plans = c.fetchall()
        vps_text = "\n".join([f"• {p[0]}: {p[1]} vCPU, {p[2]}MB RAM, {p[3]}GB SSD - ₹{p[4]}/mo" for p in vps_plans])
        embed.add_field(name="💻 VPS Plans", value=vps_text or "Coming soon", inline=False)
        
        # Minecraft Plans
        c.execute('SELECT name, ram, slots, price FROM mc_plans WHERE is_available = 1 LIMIT 3')
        mc_plans = c.fetchall()
        mc_text = "\n".join([f"• {p[0]}: {p[1]}MB RAM, {p[2]} slots - ₹{p[3]}/mo" for p in mc_plans])
        embed.add_field(name="🎮 Minecraft Plans", value=mc_text or "Coming soon", inline=False)
        
        # RDP Plans
        c.execute('SELECT name, cpu, ram, storage, price FROM rdp_plans WHERE is_available = 1 LIMIT 3')
        rdp_plans = c.fetchall()
        rdp_text = "\n".join([f"• {p[0]}: {p[1]} vCPU, {p[2]}MB RAM - ₹{p[4]}/mo" for p in rdp_plans])
        embed.add_field(name="🖥️ RDP Plans", value=rdp_text or "Coming soon", inline=False)
        
        # Nitro Plans
        c.execute('SELECT name, duration_days, price FROM nitro_plans WHERE is_available = 1 LIMIT 3')
        nitro_plans = c.fetchall()
        nitro_text = "\n".join([f"• {p[0]}: {p[1]} days - ₹{p[2]}" for p in nitro_plans])
        embed.add_field(name="✨ Discord Nitro", value=nitro_text or "Coming soon", inline=False)
        
        conn.close()
        embed.set_footer(text="Contact support for custom plans!")
        await ctx.send(embed=embed)
        self.log_command('plans', ctx.author.id, ctx.author.name)
    
    @commands.command(name='plans-update')
    @commands.has_permissions(administrator=True)
    async def plans_update(self, ctx):
        """🔄 Update plans - Opens menu (Admin only)"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Admin only command!")
            return
        
        embed = discord.Embed(
            title="🔄 Plans Update Menu",
            description="Use the website admin panel to update plans:\n`/admin/plans`\n\nOr use these commands:\n`>plans-add-vps`\n`>plans-add-mc`\n`>plans-add-rdp`\n`>plans-add-nitro`\n`>plans-remove <id>`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        self.log_command('plans-update', ctx.author.id, ctx.author.name)
    
    @commands.command(name='auth_web')
    async def auth_web(self, ctx):
        """🔐 Authorize Discord to website - One click login"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT id FROM users WHERE discord_id = ?', (str(ctx.author.id),))
        user = c.fetchone()
        
        if user:
            await ctx.send(f"✅ Your Discord is already linked! Visit the website and click 'Login with Discord'")
        else:
            # Create one-time auth token
            import secrets
            token = secrets.token_urlsafe(32)
            await ctx.send(f"🔐 Click the link below to login:\n`{request.host_url}discord-auth/{token}`\n\n*This link expires in 5 minutes*")
        
        conn.close()
        self.log_command('auth_web', ctx.author.id, ctx.author.name)
    
    @commands.command(name='server-stats')
    async def server_stats(self, ctx):
        """📊 Show created VPS stats"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''SELECT u.username, COUNT(v.id), 
                     SUM(CASE WHEN v.status = 'running' THEN 1 ELSE 0 END)
                     FROM users u LEFT JOIN vps_servers v ON u.id = v.user_id 
                     GROUP BY u.id ORDER BY COUNT(v.id) DESC LIMIT 10''')
        stats = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="📊 Server Statistics", color=discord.Color.blue())
        for stat in stats:
            embed.add_field(name=stat[0], value=f"Total: {stat[1]} VPS | Active: {stat[2]}", inline=False)
        
        await ctx.send(embed=embed)
        self.log_command('server-stats', ctx.author.id, ctx.author.name)
    
    @commands.command(name='web-stats')
    async def web_stats(self, ctx):
        """🌐 Show website visitor stats"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM web_visitors')
        total = c.fetchone()[0]
        c.execute('SELECT page_visited, COUNT(*) FROM web_visitors GROUP BY page_visited')
        pages = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="🌐 Website Statistics", color=discord.Color.green())
        embed.add_field(name="Total Visitors", value=str(total), inline=True)
        
        page_text = "\n".join([f"{p[0]}: {p[1]} visits" for p in pages[:5]])
        embed.add_field(name="Top Pages", value=page_text or "No data", inline=False)
        
        await ctx.send(embed=embed)
        self.log_command('web-stats', ctx.author.id, ctx.author.name)
    
    @commands.command(name='admin-add')
    @commands.has_permissions(administrator=True)
    async def admin_add(self, ctx, member: discord.Member):
        """👑 Add a user as bot admin"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Only bot owner can use this!")
            return
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE discord_id = ?', (str(member.id),))
        user = c.fetchone()
        
        if user:
            c.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user[0],))
        else:
            c.execute('INSERT INTO users (username, email, password, discord_id, discord_name, is_admin) VALUES (?, ?, ?, ?, ?, 1)',
                      (member.name, f"{member.id}@discord.com", "", str(member.id), member.name))
        
        c.execute('INSERT OR IGNORE INTO bot_admins (user_id, discord_id, discord_name, added_by) VALUES (?, ?, ?, ?)',
                  (user[0] if user else c.lastrowid, str(member.id), member.name, ctx.author.id))
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ {member.mention} is now a bot admin!")
        self.log_command('admin-add', ctx.author.id, ctx.author.name)
    
    @commands.command(name='admin-list')
    async def admin_list(self, ctx):
        """📜 List all bot admins"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT discord_name, discord_id, added_at FROM bot_admins')
        admins = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="📜 Bot Administrators", color=discord.Color.blue())
        for admin in admins:
            embed.add_field(name=admin[0], value=f"ID: {admin[1]}\nAdded: {admin[2][:10]}", inline=False)
        
        await ctx.send(embed=embed)
        self.log_command('admin-list', ctx.author.id, ctx.author.name)
    
    @commands.command(name='admin-remove')
    @commands.has_permissions(administrator=True)
    async def admin_remove(self, ctx, member: discord.Member):
        """🗑️ Remove admin from bot"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Only bot owner can use this!")
            return
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('UPDATE users SET is_admin = 0 WHERE discord_id = ?', (str(member.id),))
        c.execute('DELETE FROM bot_admins WHERE discord_id = ?', (str(member.id),))
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ {member.mention} is no longer an admin!")
        self.log_command('admin-remove', ctx.author.id, ctx.author.name)
    
    @commands.command(name='maintenance-bot')
    @commands.has_permissions(administrator=True)
    async def maintenance_bot(self, ctx):
        """🔧 Toggle maintenance mode (Admin only)"""
        if not self.is_admin(ctx.author.id):
            await ctx.send("❌ Admin only command!")
            return
        
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('UPDATE bot_settings SET maintenance_mode = NOT maintenance_mode WHERE id = 1')
        conn.commit()
        c.execute('SELECT maintenance_mode FROM bot_settings WHERE id = 1')
        mode = c.fetchone()[0]
        conn.close()
        
        status = "ENABLED" if mode else "DISABLED"
        await ctx.send(f"🔧 Maintenance mode {status}! {'Only admins can use commands.' if mode else 'Bot fully operational.'}")
        self.log_command('maintenance-bot', ctx.author.id, ctx.author.name)
    
    @commands.command(name='status-page')
    async def status_page(self, ctx):
        """📈 Show live status of all services"""
        embed = discord.Embed(
            title="📈 Atyro Cloud Status Page",
            description="Live service status updates",
            color=discord.Color.green()
        )
        
        # Check website status
        try:
            import requests
            response = requests.get(request.host_url, timeout=5)
            website_status = "✅ Online" if response.status_code == 200 else "⚠️ Issues"
        except:
            website_status = "❌ Offline"
        
        embed.add_field(name="🌐 Website", value=website_status, inline=True)
        embed.add_field(name="🤖 Discord Bot", value="✅ Online", inline=True)
        embed.add_field(name="🖥️ VPS Services", value="✅ Operational", inline=True)
        embed.add_field(name="💾 Database", value="✅ Connected", inline=True)
        embed.add_field(name="🐳 Docker", value="✅ Running", inline=True)
        embed.add_field(name="🔐 API", value="✅ Operational", inline=True)
        
        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)
        self.log_command('status-page', ctx.author.id, ctx.author.name)
    
    # Additional VPS management commands
    @commands.command(name='vps_list')
    async def vps_list(self, ctx):
        """List all your VPS servers"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''SELECT v.id, v.container_name, v.os_type, v.status, v.created_at 
                     FROM vps_servers v JOIN users u ON v.user_id = u.id 
                     WHERE u.discord_id = ?''', (str(ctx.author.id),))
        vps_list = c.fetchall()
        conn.close()
        
        if not vps_list:
            await ctx.send("No VPS found. Use `>deploy` to create one!")
            return
        
        embed = discord.Embed(title="📋 Your VPS Servers", color=discord.Color.blue())
        for vps in vps_list:
            status_emoji = "🟢" if vps[3] == "running" else "🔴"
            embed.add_field(
                name=f"{status_emoji} VPS #{vps[0]}",
                value=f"Name: {vps[1]}\nOS: {vps[2]}\nCreated: {vps[4][:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='vps_stop')
    async def vps_stop(self, ctx, vps_id: int):
        """Stop a VPS"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''UPDATE vps_servers SET status = 'stopped' 
                     WHERE id = ? AND user_id = (SELECT id FROM users WHERE discord_id = ?)''',
                  (vps_id, str(ctx.author.id)))
        if c.rowcount > 0:
            conn.commit()
            await ctx.send(f"✅ VPS #{vps_id} stopped successfully!")
        else:
            await ctx.send(f"❌ VPS #{vps_id} not found!")
        conn.close()
    
    @commands.command(name='vps_start')
    async def vps_start(self, ctx, vps_id: int):
        """Start a VPS"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''UPDATE vps_servers SET status = 'running' 
                     WHERE id = ? AND user_id = (SELECT id FROM users WHERE discord_id = ?)''',
                  (vps_id, str(ctx.author.id)))
        if c.rowcount > 0:
            conn.commit()
            await ctx.send(f"✅ VPS #{vps_id} started successfully!")
        else:
            await ctx.send(f"❌ VPS #{vps_id} not found!")
        conn.close()
    
    @commands.command(name='vps_restart')
    async def vps_restart(self, ctx, vps_id: int):
        """Restart a VPS"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''UPDATE vps_servers SET status = 'running' 
                     WHERE id = ? AND user_id = (SELECT id FROM users WHERE discord_id = ?)''',
                  (vps_id, str(ctx.author.id)))
        if c.rowcount > 0:
            conn.commit()
            await ctx.send(f"✅ VPS #{vps_id} restarted successfully!")
        else:
            await ctx.send(f"❌ VPS #{vps_id} not found!")
        conn.close()
    
    @commands.command(name='vps_delete')
    async def vps_delete(self, ctx, vps_id: int):
        """Delete a VPS"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''DELETE FROM vps_servers 
                     WHERE id = ? AND user_id = (SELECT id FROM users WHERE discord_id = ?)''',
                  (vps_id, str(ctx.author.id)))
        if c.rowcount > 0:
            conn.commit()
            await ctx.send(f"✅ VPS #{vps_id} deleted successfully!")
        else:
            await ctx.send(f"❌ VPS #{vps_id} not found!")
        conn.close()
    
    @commands.command(name='rdp_list')
    async def rdp_list(self, ctx):
        """List available RDP plans"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT name, cpu, ram, storage, price FROM rdp_plans WHERE is_available = 1')
        plans = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="🖥️ Available RDP Plans", color=discord.Color.purple())
        for plan in plans:
            embed.add_field(name=plan[0], value=f"{plan[1]} vCPU | {plan[2]}MB RAM | {plan[3]}GB SSD\n💰 ₹{plan[4]}/mo", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rdp_create')
    async def rdp_create(self, ctx, plan_name: str):
        """Create an RDP server"""
        await ctx.send(f"🖥️ RDP creation requested for plan: {plan_name}\nPlease contact support for RDP setup.")
    
    @commands.command(name='rdp_info')
    async def rdp_info(self, ctx):
        """Get RDP connection info"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('''SELECT server_name, ip_address, username, port 
                     FROM rdp_servers WHERE user_id = (SELECT id FROM users WHERE discord_id = ?)''',
                  (str(ctx.author.id),))
        rdp = c.fetchone()
        conn.close()
        
        if rdp:
            embed = discord.Embed(title="🖥️ Your RDP Info", color=discord.Color.green())
            embed.add_field(name="Server", value=rdp[0], inline=True)
            embed.add_field(name="IP", value=rdp[1], inline=True)
            embed.add_field(name="Username", value=rdp[2], inline=True)
            embed.add_field(name="Port", value=str(rdp[3]), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No RDP server found. Use `>rdp_create` to order one!")
    
    @commands.command(name='nitro_check')
    async def nitro_check(self, ctx):
        """Check Nitro availability"""
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT name, duration_days, price FROM nitro_plans WHERE is_available = 1')
        plans = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="✨ Discord Nitro Plans", color=discord.Color.pink())
        for plan in plans:
            embed.add_field(name=plan[0], value=f"📅 {plan[1]} days\n💰 ₹{plan[2]}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='nitro_buy')
    async def nitro_buy(self, ctx, plan_name: str):
        """Purchase Nitro"""
        await ctx.send(f"✨ Nitro purchase requested: {plan_name}\nPlease visit the website to complete payment.")
    
    @commands.command(name='user_info')
    async def user_info(self, ctx, member: discord.Member = None):
        """Get user information"""
        member = member or ctx.author
        embed = discord.Embed(title=f"👤 User Info: {member.name}", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined Discord", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Roles", value=len(member.roles), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='server_info')
    async def server_info(self, ctx):
        """Get server information"""
        guild = ctx.guild
        embed = discord.Embed(title=f"📊 Server Info: {guild.name}", color=discord.Color.green())
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show all commands"""
        embed = discord.Embed(
            title=f"📚 Atyro Cloud Bot Commands ({await self.bot.get_prefix(ctx.message)}prefix)",
            description=f"**Total Commands: 30+**\nUse `{await self.bot.get_prefix(ctx.message)}command` to execute",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="🖥️ VPS Commands", value="`deploy`, `manage`, `vps_list`, `vps_start`, `vps_stop`, `vps_restart`, `vps_delete`", inline=False)
        embed.add_field(name="📊 Utility Commands", value="`ping`, `uptime`, `links`, `plans`, `server-stats`, `web-stats`, `status-page`, `user_info`, `server_info`", inline=False)
        embed.add_field(name="🖥️ RDP Commands", value="`rdp_list`, `rdp_create`, `rdp_info`", inline=False)
        embed.add_field(name="✨ Nitro Commands", value="`nitro_check`, `nitro_buy`", inline=False)
        embed.add_field(name="🔐 Auth Commands", value="`auth_web`", inline=False)
        embed.add_field(name="👑 Admin Commands", value="`admin-add`, `admin-list`, `admin-remove`, `update-links`, `plans-update`, `maintenance-bot`", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name} | Atyro Cloud")
        await ctx.send(embed=embed)

# ==================== RUN BOT IN THREAD ====================

def run_bot():
    """Run Discord bot in separate thread"""
    try:
        bot_instance = AtyroBot()
        
        # Get bot token from database
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('SELECT bot_token FROM bot_settings WHERE id = 1')
        result = c.fetchone()
        conn.close()
        
        token = result[0] if result and result[0] else os.environ.get('DISCORD_BOT_TOKEN', '')
        
        if token and token != '':
            bot_instance.run(token)
        else:
            print("⚠️ No bot token found. Please configure in admin panel > Bot Settings")
    except Exception as e:
        print(f"Bot error: {e}")

# ==================== TRACK VISITORS ====================

@app.before_request
def track_visitor():
    if request.endpoint and 'static' not in request.endpoint:
        conn = sqlite3.connect('vps.db')
        c = conn.cursor()
        c.execute('INSERT INTO web_visitors (ip_address, user_agent, page_visited) VALUES (?, ?, ?)',
                  (request.remote_addr, request.headers.get('User-Agent', ''), request.path))
        conn.commit()
        conn.close()

# ==================== RUN APP ====================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start Discord bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask app
    print("🚀 Starting Atyro Cloud Server...")
    print("📍 Website: http://localhost:5000")
    print("👑 Admin Login: vectro / vectro1234")
    print("🤖 Bot will start when token is configured in admin panel")
    app.run(host='0.0.0.0', port=5000, debug=False)
