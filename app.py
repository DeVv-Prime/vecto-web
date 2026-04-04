# app.py - Complete Website with Discord Bot, Stock Management, Approval System
import os
import json
import secrets
import requests
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request, session, redirect, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

DB_FILE = 'website_data.json'
STOCK_FILES_DIR = 'stock_files'
os.makedirs(STOCK_FILES_DIR, exist_ok=True)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "admin": {
            "email": "admin@vedant.com",
            "password": generate_password_hash("vedant9090")
        },
        "discord_config": {
            "bot_token": "",
            "webhook_url": "",
            "approval_channel_id": "",
            "log_channel_id": "",
            "dm_on_purchase": True,
            "require_approval": True,
            "discord_invite": "https://discord.gg/vechohub"
        },
        "settings": {
            "website_name": "VeCho Hub",
            "website_tagline": "Premium Digital Services",
            "logo_url": "https://img.icons8.com/fluency/96/admin-settings-male.png",
            "favicon_url": "https://img.icons8.com/color/48/admin-settings-male.png",
            "primary_color": "#4F46E5",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
            "background_color": "#0A0A0A",
            "card_background": "#1A1A1A",
            "text_color": "#FFFFFF",
            "hero_title": "Premium Hosting & Discord Services",
            "hero_subtitle": "Lightning Fast • 99.9% Uptime • 24/7 Support",
            "contact_email": "support@vechohub.com",
            "contact_discord": "https://discord.gg/vechohub"
        },
        "plans": {
            "VPS": [
                {"id": "vps_mini", "name": "VPS Mini", "price": 5, "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "popular": False, "icon": "🖥️"},
                {"id": "vps_standard", "name": "VPS Standard", "price": 20, "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "popular": True, "icon": "⚡"},
                {"id": "vps_pro", "name": "VPS Pro", "price": 80, "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "popular": False, "icon": "🚀"}
            ],
            "NITRO": [
                {"id": "nitro_basic", "name": "Nitro Basic", "price": 3, "features": "Custom Emojis, HD Streaming", "popular": False, "icon": "💜"},
                {"id": "nitro_full", "name": "Nitro Full", "price": 10, "features": "4K Streaming, 2 Boosts", "popular": True, "icon": "✨"},
                {"id": "boost_1", "name": "1 Server Boost", "price": 4, "features": "Server Boost", "popular": False, "icon": "⚡"}
            ]
        },
        "stock_files": {},
        "orders": [],
        "pending_orders": []
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_stock_for_plan(plan_id, quantity=1):
    """Get stock codes from uploaded file"""
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

def send_discord_approval(order):
    """Send approval buttons to Discord channel"""
    data = load_db()
    webhook_url = data['discord_config'].get('webhook_url')
    if not webhook_url:
        return False
    
    items_text = '\n'.join([f"• {item['quantity']}x {item['name']} - ${item['price']}" for item in order['items']])
    
    embed = {
        "title": "🛒 NEW ORDER - PENDING APPROVAL",
        "description": f"**Order ID:** `{order['id']}`\n**Customer:** {order['customer_name']}\n**Discord ID:** {order.get('discord_id', 'N/A')}\n\n**Items:**\n{items_text}\n\n**Total:** ${order['total']}",
        "color": 0xFEE75C,
        "timestamp": datetime.now().isoformat(),
        "footer": {"text": "Click a button to approve or reject"}
    }
    
    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 3,
                    "label": "✅ APPROVE",
                    "custom_id": f"approve_{order['id']}",
                    "emoji": {"name": "✅"}
                },
                {
                    "type": 2,
                    "style": 4,
                    "label": "❌ REJECT",
                    "custom_id": f"reject_{order['id']}",
                    "emoji": {"name": "❌"}
                }
            ]
        }
    ]
    
    payload = {
        "embeds": [embed],
        "components": components
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code in [200, 204]
    except:
        return False

def send_discord_dm(user_discord_id, message):
    """Send DM to user using bot token"""
    data = load_db()
    bot_token = data['discord_config'].get('bot_token')
    if not bot_token:
        return False
    
    headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
    
    # Create DM channel
    dm_response = requests.post('https://discord.com/api/v10/users/@me/channels', 
                                headers=headers, json={'recipient_id': user_discord_id})
    if dm_response.status_code != 200:
        return False
    
    channel_id = dm_response.json().get('id')
    
    # Send message
    msg_response = requests.post(f'https://discord.com/api/v10/channels/{channel_id}/messages',
                                  headers=headers, json={'content': message})
    return msg_response.status_code == 200

def update_order_status(order_id, status, stock_codes=None):
    """Update order status and send DM to user"""
    data = load_db()
    for order in data['orders']:
        if order['id'] == order_id:
            order['status'] = status
            if status == 'approved' and stock_codes:
                order['stock_codes'] = stock_codes
            break
    
    for i, pending in enumerate(data['pending_orders']):
        if pending['id'] == order_id:
            data['pending_orders'].pop(i)
            break
    
    save_db(data)
    
    # Send DM to user if approved
    if status == 'approved' and stock_codes:
        order = next((o for o in data['orders'] if o['id'] == order_id), None)
        if order and order.get('discord_id'):
            stock_text = '\n'.join([f"`{code}`" for code in stock_codes])
            message = f"""✅ **ORDER APPROVED!** ✅

**Order ID:** `{order_id}`
**Items:** {len(order['items'])} item(s)
**Total:** ${order['total']}

**Your Stock/Details:**
{stock_text}

Thank you for shopping with {data['settings']['website_name']}!
Need help? Join our Discord: {data['discord_config'].get('discord_invite', '')}"""
            send_discord_dm(order['discord_id'], message)
    
    return True

# ==================== HTML TEMPLATE ====================
WEBSITE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ settings.website_name }} | Premium Services</title>
    <link rel="icon" href="{{ settings.favicon_url }}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: {{ settings.background_color }};
            color: {{ settings.text_color }};
            scroll-behavior: smooth;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        
        /* Navbar */
        .navbar {
            padding: 20px 0;
            position: sticky;
            top: 0;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .navbar .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .logo { display: flex; align-items: center; gap: 12px; }
        .logo img { width: 40px; height: 40px; border-radius: 12px; }
        .logo span { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #fff, {{ settings.primary_color }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-links { display: flex; gap: 32px; align-items: center; flex-wrap: wrap; }
        .nav-links a { color: {{ settings.text_color }}; text-decoration: none; transition: 0.3s; font-weight: 500; }
        .nav-links a:hover { color: {{ settings.primary_color }}; }
        .admin-btn { background: {{ settings.primary_color }}; padding: 8px 20px; border-radius: 40px; }
        
        /* Hero */
        .hero { padding: 100px 0; text-align: center; }
        .hero h1 { font-size: 3.5rem; font-weight: 800; margin-bottom: 20px; }
        .hero h1 span { color: {{ settings.primary_color }}; }
        .hero p { font-size: 1.2rem; color: #A1A1AA; margin-bottom: 30px; }
        .btn-primary {
            background: {{ settings.primary_color }};
            color: white;
            padding: 14px 36px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(79,70,229,0.3); }
        
        /* Stats */
        .stats-section { padding: 60px 0; border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; text-align: center; }
        .stat-number { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        
        /* Plans */
        .section { padding: 80px 0; }
        .section-title { text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 16px; }
        .section-title span { color: {{ settings.primary_color }}; }
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px; margin-top: 40px; }
        .plan-card {
            background: {{ settings.card_background }};
            border-radius: {{ settings.border_radius }};
            padding: 30px;
            transition: 0.3s;
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
        }
        .plan-card:hover { transform: translateY(-5px); border-color: {{ settings.primary_color }}; }
        .plan-card.popular { border: 2px solid {{ settings.primary_color }}; }
        .popular-badge {
            position: absolute;
            top: 20px;
            right: 20px;
            background: {{ settings.primary_color }};
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
        }
        .plan-icon { font-size: 2.5rem; margin-bottom: 15px; }
        .plan-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 10px; }
        .plan-price { font-size: 2rem; font-weight: 800; margin: 20px 0; }
        .buy-btn {
            background: {{ settings.primary_color }};
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 50px;
            width: 100%;
            cursor: pointer;
            font-weight: 600;
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
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: {{ settings.card_background }};
            border-radius: 24px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
        }
        .modal-content input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.5);
            color: white;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: {{ settings.secondary_color }};
            color: white;
            padding: 12px 24px;
            border-radius: 40px;
            z-index: 2000;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .footer { padding: 60px 0 30px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .navbar .container { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container">
        <div class="logo">
            <img src="{{ settings.logo_url }}" alt="logo">
            <span>{{ settings.website_name }}</span>
        </div>
        <div class="nav-links">
            <a href="#home">Home</a>
            <a href="#plans">Plans</a>
            <a href="#contact">Contact</a>
            <a href="/admin/login" class="admin-btn"><i class="fas fa-lock"></i> Admin</a>
        </div>
    </div>
</nav>

<section id="home" class="hero">
    <div class="container">
        <h1>{{ settings.hero_title }}<br><span>{{ settings.website_tagline }}</span></h1>
        <p>{{ settings.hero_subtitle }}</p>
        <a href="#plans" class="btn-primary">Explore Plans →</a>
    </div>
</section>

<section class="stats-section">
    <div class="container">
        <div class="stats-grid">
            <div><div class="stat-number">{{ settings.stats_customers }}</div><div>Happy Customers</div></div>
            <div><div class="stat-number">{{ settings.stats_uptime }}</div><div>Uptime</div></div>
            <div><div class="stat-number">{{ settings.stats_rating }}</div><div>Rating</div></div>
            <div><div class="stat-number">{{ settings.stats_servers }}</div><div>Servers</div></div>
        </div>
    </div>
</section>

<section id="plans" class="section">
    <div class="container">
        <h2 class="section-title"><span>🚀</span> VPS Hosting Plans</h2>
        <div class="cards-grid">
            {% for plan in plans.VPS %}
            <div class="plan-card {% if plan.popular %}popular{% endif %}">
                {% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}
                <div class="plan-icon">{{ plan.icon }}</div>
                <h3 class="plan-name">{{ plan.name }}</h3>
                <div class="plan-price">${{ plan.price }}<small>/mo</small></div>
                <button class="buy-btn" onclick="openPurchaseModal('{{ plan.id }}', '{{ plan.name }}', {{ plan.price }})">Buy Now →</button>
            </div>
            {% endfor %}
        </div>
        
        <h2 class="section-title" style="margin-top: 60px;"><span>💜</span> Discord Nitro</h2>
        <div class="cards-grid">
            {% for plan in plans.NITRO %}
            <div class="plan-card {% if plan.popular %}popular{% endif %}">
                {% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}
                <div class="plan-icon">{{ plan.icon }}</div>
                <h3 class="plan-name">{{ plan.name }}</h3>
                <div class="plan-price">${{ plan.price }}<small>/mo</small></div>
                <button class="buy-btn" onclick="openPurchaseModal('{{ plan.id }}', '{{ plan.name }}', {{ plan.price }})">Buy Now →</button>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<footer id="contact" class="footer">
    <div class="container">
        <p>📧 <a href="mailto:{{ settings.contact_email }}" style="color: {{ settings.primary_color }};">{{ settings.contact_email }}</a></p>
        <p>💬 <a href="{{ settings.contact_discord }}" style="color: {{ settings.primary_color }};">Join our Discord</a></p>
        <p style="margin-top: 20px;">{{ settings.footer_text }}</p>
    </div>
</footer>

<!-- Purchase Modal -->
<div id="purchaseModal" class="modal">
    <div class="modal-content">
        <h2>🛒 Complete Purchase</h2>
        <form id="purchaseForm">
            <input type="text" id="customerName" placeholder="Your Name" required>
            <input type="text" id="discordId" placeholder="Discord ID (for delivery)" required>
            <input type="email" id="customerEmail" placeholder="Email (optional)">
            <input type="hidden" id="planId">
            <input type="hidden" id="planName">
            <input type="hidden" id="planPrice">
            <button type="submit" class="btn-primary" style="width:100%;">Place Order</button>
        </form>
        <button onclick="closeModal()" style="margin-top: 10px; background: #EF4444; color: white; border: none; padding: 10px; border-radius: 40px; width:100%; cursor:pointer;">Cancel</button>
    </div>
</div>

<script>
    let currentPlan = {};
    
    function openPurchaseModal(planId, planName, price) {
        currentPlan = { id: planId, name: planName, price: price };
        document.getElementById('planId').value = planId;
        document.getElementById('planName').value = planName;
        document.getElementById('planPrice').value = price;
        document.getElementById('purchaseModal').style.display = 'flex';
    }
    
    function closeModal() {
        document.getElementById('purchaseModal').style.display = 'none';
    }
    
    document.getElementById('purchaseForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            plan_id: document.getElementById('planId').value,
            plan_name: document.getElementById('planName').value,
            price: parseFloat(document.getElementById('planPrice').value),
            customer_name: document.getElementById('customerName').value,
            discord_id: document.getElementById('discordId').value,
            email: document.getElementById('customerEmail').value
        };
        
        const res = await fetch('/api/purchase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (result.success) {
            showToast('✅ Order placed! Waiting for admin approval.');
            closeModal();
            document.getElementById('purchaseForm').reset();
        } else {
            showToast('❌ ' + result.error);
        }
    });
    
    function showToast(msg) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('purchaseModal');
        if (event.target === modal) closeModal();
    }
</script>
</body>
</html>
'''

# ==================== ADMIN PANEL ====================
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0A0A0A;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-box {
            background: rgba(255,255,255,0.05);
            border-radius: 24px;
            padding: 40px;
            width: 400px;
        }
        .login-box h1 { color: white; text-align: center; margin-bottom: 30px; }
        .login-box input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.5);
            color: white;
        }
        .login-box button {
            width: 100%;
            padding: 12px;
            background: #4F46E5;
            color: white;
            border: none;
            border-radius: 40px;
            cursor: pointer;
            margin-top: 20px;
        }
        .error { color: #EF4444; text-align: center; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Admin Login</h1>
        <form method="post">
            <input type="email" name="email" placeholder="Admin Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
'''

ADMIN_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0A0A0A;
            color: white;
        }
        .admin-container { display: flex; min-height: 100vh; }
        .sidebar {
            width: 280px;
            background: #111111;
            border-right: 1px solid rgba(255,255,255,0.1);
            padding: 30px;
            position: fixed;
            height: 100vh;
        }
        .sidebar h2 { margin-bottom: 30px; }
        .sidebar .nav-item {
            padding: 12px;
            margin: 5px 0;
            border-radius: 12px;
            cursor: pointer;
            transition: 0.3s;
        }
        .sidebar .nav-item:hover, .sidebar .nav-item.active {
            background: rgba(79,70,229,0.2);
            color: #4F46E5;
        }
        .main-content {
            flex: 1;
            margin-left: 280px;
            padding: 30px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
        }
        .card h3 { margin-bottom: 20px; }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.5);
            color: white;
        }
        button {
            background: #4F46E5;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 40px;
            cursor: pointer;
            margin-top: 10px;
        }
        .success { background: #10B981; padding: 10px; border-radius: 12px; margin-bottom: 20px; }
        .order-item {
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 15px 0;
        }
        .badge-pending { background: #F59E0B; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-approved { background: #10B981; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-rejected { background: #EF4444; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .upload-area {
            border: 2px dashed rgba(79,70,229,0.5);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        }
        @media (max-width: 768px) {
            .sidebar { width: 80px; padding: 15px; }
            .sidebar span { display: none; }
            .main-content { margin-left: 80px; }
        }
    </style>
</head>
<body>
    <div class="admin-container">
        <div class="sidebar">
            <h2>⚙️ Admin</h2>
            <div class="nav-item active" data-tab="dashboard"><i class="fas fa-tachometer-alt"></i> <span>Dashboard</span></div>
            <div class="nav-item" data-tab="orders"><i class="fas fa-shopping-cart"></i> <span>Orders</span></div>
            <div class="nav-item" data-tab="stock"><i class="fas fa-upload"></i> <span>Stock</span></div>
            <div class="nav-item" data-tab="discord"><i class="fab fa-discord"></i> <span>Discord Bot</span></div>
            <div class="nav-item" data-tab="plans"><i class="fas fa-box"></i> <span>Plans</span></div>
            <div class="nav-item" data-tab="settings"><i class="fas fa-sliders-h"></i> <span>Settings</span></div>
            <div class="nav-item" onclick="window.location.href='/admin/logout'"><i class="fas fa-sign-out-alt"></i> <span>Logout</span></div>
        </div>
        
        <div class="main-content">
            <!-- Dashboard Tab -->
            <div id="dashboard-tab">
                <div class="card">
                    <h3>📊 Dashboard Stats</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div><h2>{{ orders|length }}</h2><p>Total Orders</p></div>
                        <div><h2>{{ pending_orders|length }}</h2><p>Pending Approval</p></div>
                        <div><h2>{{ stock_files|length }}</h2><p>Stock Files</p></div>
                    </div>
                </div>
                <div class="card">
                    <h3>🤖 Bot Status</h3>
                    <p>Bot Token: {% if discord_config.bot_token %}✅ Configured{% else %}❌ Not Set{% endif %}</p>
                    <p>Webhook URL: {% if discord_config.webhook_url %}✅ Configured{% else %}❌ Not Set{% endif %}</p>
                    <p>Approval Channel: {% if discord_config.approval_channel_id %}✅ Set{% else %}❌ Not Set{% endif %}</p>
                </div>
            </div>
            
            <!-- Orders Tab -->
            <div id="orders-tab" style="display:none;">
                <div class="card">
                    <h3>📋 Pending Orders</h3>
                    {% for order in pending_orders %}
                    <div class="order-item">
                        <strong>🆔 {{ order.id }}</strong>
                        <span class="badge-pending">PENDING</span>
                        <p>👤 {{ order.customer_name }} | Discord: {{ order.discord_id }}</p>
                        <p>📦 {% for item in order.items %}{{ item.quantity }}x {{ item.name }} (${% if item.price %}{{ item.price }}{% else %}{{ item.plan_price }}{% endif %}) {% endfor %}</p>
                        <p>💰 Total: ${{ order.total }}</p>
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <button onclick="approveOrder('{{ order.id }}')" style="background:#10B981;">✅ Approve</button>
                            <button onclick="rejectOrder('{{ order.id }}')" style="background:#EF4444;">❌ Reject</button>
                        </div>
                    </div>
                    {% else %}
                    <p>No pending orders</p>
                    {% endfor %}
                </div>
                <div class="card">
                    <h3>📦 All Orders</h3>
                    {% for order in orders %}
                    <div class="order-item">
                        <strong>🆔 {{ order.id }}</strong>
                        <span class="badge-{{ order.status }}">{{ order.status|upper }}</span>
                        <p>👤 {{ order.customer_name }} | 💰 ${{ order.total }}</p>
                        <small>{{ order.date }}</small>
                    </div>
                    {% else %}
                    <p>No orders yet</p>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Stock Tab -->
            <div id="stock-tab" style="display:none;">
                <div class="card">
                    <h3>📤 Upload Stock File</h3>
                    <div class="upload-area" id="dropZone">
                        <i class="fas fa-cloud-upload-alt" style="font-size:3rem;"></i>
                        <p>Drag & drop or click to upload .txt file</p>
                        <input type="file" id="fileInput" accept=".txt" style="display:none;">
                    </div>
                    <select id="planSelect" style="width:100%; padding:12px; margin:1rem 0;">
                        <option value="">Select Plan</option>
                        <option value="vps_mini">VPS Mini</option>
                        <option value="vps_standard">VPS Standard</option>
                        <option value="vps_pro">VPS Pro</option>
                        <option value="nitro_basic">Nitro Basic</option>
                        <option value="nitro_full">Nitro Full</option>
                        <option value="boost_1">Server Boost</option>
                    </select>
                    <button onclick="uploadStock()">Upload Stock</button>
                </div>
                <div class="card">
                    <h3>📋 Current Stock Files</h3>
                    <div id="stockList">
                        {% for plan_id, filename in stock_files.items() %}
                        <div><strong>{{ plan_id }}</strong>: {{ filename }} <button onclick="deleteStock('{{ plan_id }}')" style="background:#EF4444;">Delete</button></div>
                        {% else %}
                        <p>No stock files uploaded</p>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Discord Bot Tab -->
            <div id="discord-tab" style="display:none;">
                <div class="card">
                    <h3>🤖 Discord Bot Configuration</h3>
                    <form id="discordForm">
                        <label>Bot Token</label>
                        <input type="password" name="bot_token" value="{{ discord_config.bot_token }}" placeholder="Discord Bot Token">
                        <label>Webhook URL (for approval buttons)</label>
                        <input type="text" name="webhook_url" value="{{ discord_config.webhook_url }}" placeholder="Discord Webhook URL">
                        <label>Approval Channel ID</label>
                        <input type="text" name="approval_channel_id" value="{{ discord_config.approval_channel_id }}" placeholder="Channel ID for approvals">
                        <label>Require Approval Before Delivery</label>
                        <select name="require_approval">
                            <option value="True" {% if discord_config.require_approval %}selected{% endif %}>Yes</option>
                            <option value="False" {% if not discord_config.require_approval %}selected{% endif %}>No</option>
                        </select>
                        <label>Discord Invite Link</label>
                        <input type="text" name="discord_invite" value="{{ discord_config.discord_invite }}">
                        <button type="submit">Save Discord Settings</button>
                    </form>
                    <div id="discordMsg"></div>
                </div>
                <div class="card">
                    <h3>📖 How to Setup Discord Bot</h3>
                    <ol style="margin-left: 20px; color: #A1A1AA;">
                        <li>Go to <a href="https://discord.com/developers/applications" target="_blank">Discord Developer Portal</a></li>
                        <li>Create a new Application → Bot → Copy Token</li>
                        <li>Enable MESSAGE CONTENT intent and SERVER MEMBERS intent</li>
                        <li>Invite bot with scope: bot, applications.commands</li>
                        <li>Create a Webhook in your Discord channel → Copy Webhook URL</li>
                        <li>Paste both in the fields above and save</li>
                    </ol>
                </div>
            </div>
            
            <!-- Plans Tab -->
            <div id="plans-tab" style="display:none;">
                <div class="card">
                    <h3>📦 VPS Plans</h3>
                    <div id="vpsPlans">
                        {% for plan in plans.VPS %}
                        <div style="margin-bottom: 15px;">
                            <strong>{{ plan.name }}</strong> - ${{ plan.price }}/mo
                            <button onclick="editPlan('VPS', {{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('VPS')">+ Add VPS Plan</button>
                </div>
                <div class="card">
                    <h3>💜 Nitro Plans</h3>
                    <div id="nitroPlans">
                        {% for plan in plans.NITRO %}
                        <div style="margin-bottom: 15px;">
                            <strong>{{ plan.name }}</strong> - ${{ plan.price }}/mo
                            <button onclick="editPlan('NITRO', {{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('NITRO')">+ Add Nitro Plan</button>
                </div>
            </div>
            
            <!-- Settings Tab -->
            <div id="settings-tab" style="display:none;">
                <div class="card">
                    <h3>🎨 Website Settings</h3>
                    <form id="settingsForm">
                        <label>Website Name</label>
                        <input type="text" name="website_name" value="{{ settings.website_name }}">
                        <label>Logo URL</label>
                        <input type="text" name="logo_url" value="{{ settings.logo_url }}">
                        <label>Primary Color</label>
                        <input type="color" name="primary_color" value="{{ settings.primary_color }}">
                        <label>Background Color</label>
                        <input type="color" name="background_color" value="{{ settings.background_color }}">
                        <label>Hero Title</label>
                        <input type="text" name="hero_title" value="{{ settings.hero_title }}">
                        <label>Contact Email</label>
                        <input type="email" name="contact_email" value="{{ settings.contact_email }}">
                        <label>Discord Invite</label>
                        <input type="text" name="contact_discord" value="{{ settings.contact_discord }}">
                        <button type="submit">Save Settings</button>
                    </form>
                    <div id="settingsMsg"></div>
                </div>
                <div class="card">
                    <h3>🔐 Change Admin Password</h3>
                    <form id="passwordForm">
                        <input type="password" name="current_password" placeholder="Current Password" required>
                        <input type="password" name="new_password" placeholder="New Password" required>
                        <input type="password" name="confirm_password" placeholder="Confirm Password" required>
                        <button type="submit">Change Password</button>
                    </form>
                    <div id="passwordMsg"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                const tab = item.dataset.tab;
                document.querySelectorAll('[id$="-tab"]').forEach(t => t.style.display = 'none');
                document.getElementById(`${tab}-tab`).style.display = 'block';
            });
        });
        
        // Discord Form
        document.getElementById('discordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            data.require_approval = data.require_approval === 'True';
            const res = await fetch('/admin/api/save-discord', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if (res.ok) document.getElementById('discordMsg').innerHTML = '<div class="success">✅ Discord settings saved!</div>';
        });
        
        // Settings Form
        document.getElementById('settingsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            const res = await fetch('/admin/api/save-settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if (res.ok) document.getElementById('settingsMsg').innerHTML = '<div class="success">✅ Settings saved! Refresh to see changes.</div>';
        });
        
        // Password Form
        document.getElementById('passwordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            if (data.new_password !== data.confirm_password) {
                document.getElementById('passwordMsg').innerHTML = '<div class="error" style="color:#EF4444;">Passwords do not match!</div>';
                return;
            }
            const res = await fetch('/admin/api/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            if (result.success) {
                document.getElementById('passwordMsg').innerHTML = '<div class="success">✅ Password changed!</div>';
                e.target.reset();
            } else {
                document.getElementById('passwordMsg').innerHTML = '<div class="error" style="color:#EF4444;">Current password incorrect!</div>';
            }
        });
        
        // Stock upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        if(dropZone) {
            dropZone.onclick = () => fileInput.click();
            dropZone.ondragover = (e) => { e.preventDefault(); dropZone.style.borderColor = '#4F46E5'; };
            dropZone.ondragleave = () => dropZone.style.borderColor = 'rgba(79,70,229,0.5)';
            dropZone.ondrop = (e) => { e.preventDefault(); fileInput.files = e.dataTransfer.files; };
        }
        
        function uploadStock() {
            const file = fileInput.files[0];
            const planId = document.getElementById('planSelect').value;
            if(!file || !planId) { alert('Select file and plan'); return; }
            const formData = new FormData();
            formData.append('stock_file', file);
            formData.append('plan_id', planId);
            fetch('/admin/api/upload-stock', { method: 'POST', body: formData }).then(() => location.reload());
        }
        
        function deleteStock(planId) {
            fetch('/admin/api/delete-stock/' + planId, { method: 'POST' }).then(() => location.reload());
        }
        
        function approveOrder(orderId) {
            fetch('/admin/api/approve-order/' + orderId, { method: 'POST' }).then(() => location.reload());
        }
        
        function rejectOrder(orderId) {
            fetch('/admin/api/reject-order/' + orderId, { method: 'POST' }).then(() => location.reload());
        }
        
        function editPlan(category, index) {
            const newName = prompt('New plan name:');
            const newPrice = prompt('New price:');
            if(newName && newPrice) {
                fetch('/admin/api/edit-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, index, name: newName, price: newPrice }) })
                    .then(() => location.reload());
            }
        }
        
        function addPlan(category) {
            const newName = prompt('Plan name:');
            const newPrice = prompt('Price:');
            if(newName && newPrice) {
                fetch('/admin/api/add-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, name: newName, price: newPrice }) })
                    .then(() => location.reload());
            }
        }
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================
@app.route('/')
def index():
    data = load_db()
    return render_template_string(WEBSITE_TEMPLATE, settings=data['settings'], plans=data['plans'])

@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = load_db()
    plan_id = request.json.get('plan_id')
    plan_name = request.json.get('plan_name')
    price = request.json.get('price')
    customer_name = request.json.get('customer_name')
    discord_id = request.json.get('discord_id')
    email = request.json.get('email')
    
    # Check stock
    stock = get_stock_for_plan(plan_id)
    if not stock and data['discord_config'].get('require_approval'):
        # No stock available, but allow order with approval
        pass
    
    order_id = secrets.token_hex(8).upper()
    order = {
        "id": order_id,
        "plan_id": plan_id,
        "items": [{"name": plan_name, "price": price, "quantity": 1}],
        "total": price,
        "customer_name": customer_name,
        "discord_id": discord_id,
        "email": email,
        "status": "pending",
        "date": datetime.now().isoformat()
    }
    
    data['pending_orders'].append(order)
    data['orders'].append(order)
    save_db(data)
    
    # Send approval request to Discord
    if data['discord_config'].get('webhook_url'):
        send_discord_approval(order)
    
    return jsonify({"success": True, "order_id": order_id})

@app.route('/admin/api/approve-order/<order_id>', methods=['POST'])
def api_approve_order(order_id):
    data = load_db()
    order = None
    for o in data['pending_orders']:
        if o['id'] == order_id:
            order = o
            break
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    plan_id = order['plan_id']
    stock = get_stock_for_plan(plan_id)
    
    if not stock:
        return jsonify({"error": "Out of stock for this plan"}), 400
    
    update_order_status(order_id, 'approved', stock)
    return jsonify({"success": True})

@app.route('/admin/api/reject-order/<order_id>', methods=['POST'])
def api_reject_order(order_id):
    update_order_status(order_id, 'rejected')
    return jsonify({"success": True})

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = load_db()
        email = request.form.get('email')
        password = request.form.get('password')
        if email == data['admin']['email'] and check_password_hash(data['admin']['password'], password):
            session['admin_logged_in'] = True
            return redirect('/admin/panel')
        return render_template_string(ADMIN_LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(ADMIN_LOGIN_TEMPLATE, error=None)

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    data = load_db()
    return render_template_string(ADMIN_PANEL_TEMPLATE, 
                                  settings=data['settings'], 
                                  plans=data['plans'],
                                  orders=data['orders'],
                                  pending_orders=data['pending_orders'],
                                  stock_files=data['stock_files'],
                                  discord_config=data['discord_config'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

# Admin API Routes
@app.route('/admin/api/save-discord', methods=['POST'])
def save_discord():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['discord_config']['bot_token'] = request.json.get('bot_token')
    data['discord_config']['webhook_url'] = request.json.get('webhook_url')
    data['discord_config']['approval_channel_id'] = request.json.get('approval_channel_id')
    data['discord_config']['require_approval'] = request.json.get('require_approval')
    data['discord_config']['discord_invite'] = request.json.get('discord_invite')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    for key in ['website_name', 'logo_url', 'primary_color', 'background_color', 'hero_title', 'contact_email', 'contact_discord']:
        if key in request.json:
            data['settings'][key] = request.json.get(key)
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/change-password', methods=['POST'])
def change_password():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    current = request.json.get('current_password')
    new = request.json.get('new_password')
    if check_password_hash(data['admin']['password'], current):
        data['admin']['password'] = generate_password_hash(new)
        save_db(data)
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/admin/api/upload-stock', methods=['POST'])
def upload_stock():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if 'stock_file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['stock_file']
    plan_id = request.form.get('plan_id')
    if not plan_id:
        return jsonify({"error": "No plan ID"}), 400
    filename = secure_filename(f"{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    filepath = os.path.join(STOCK_FILES_DIR, filename)
    file.save(filepath)
    data = load_db()
    data['stock_files'][plan_id] = filename
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/delete-stock/<plan_id>', methods=['POST'])
def delete_stock(plan_id):
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    if plan_id in data['stock_files']:
        filepath = os.path.join(STOCK_FILES_DIR, data['stock_files'][plan_id])
        if os.path.exists(filepath): os.remove(filepath)
        del data['stock_files'][plan_id]
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/edit-plan', methods=['POST'])
def edit_plan():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    index = request.json.get('index')
    if category in data['plans'] and 0 <= index < len(data['plans'][category]):
        data['plans'][category][index]['name'] = request.json.get('name')
        data['plans'][category][index]['price'] = float(request.json.get('price'))
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-plan', methods=['POST'])
def add_plan():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    if category == 'VPS':
        data['plans'][category].append({
            "id": f"vps_{secrets.token_hex(4)}",
            "name": request.json.get('name'),
            "price": float(request.json.get('price')),
            "cpu": "2 Core", "ram": "2GB", "storage": "50GB SSD",
            "bandwidth": "2TB", "popular": False, "icon": "💻"
        })
    else:
        data['plans'][category].append({
            "id": f"nitro_{secrets.token_hex(4)}",
            "name": request.json.get('name'),
            "price": float(request.json.get('price')),
            "features": "Premium features", "popular": False, "icon": "💜"
        })
    save_db(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
