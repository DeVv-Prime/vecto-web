# app.py - Complete Website with Bot System, Payment Methods, Cart, Orders (Updated)
import os
import json
import secrets
import requests
from datetime import datetime
from flask import Flask, jsonify, request, session, redirect, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

DB_FILE = 'website_data.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "admin": {
            "email": "admin@vedant.com",
            "password": generate_password_hash("vedant9090")
        },
        "bot_config": {
            "bot_token": "",
            "webhook_url": "",
            "bot_enabled": False,
            "welcome_message": "Welcome to VeCho Hub! Use /help for commands.",
            "commands": ["/plans", "/order", "/support", "/website", "/ping", "/help"]
        },
        "payment_config": {
            "upi_id": "yourname@okhdfcbank",
            "upi_qr_url": "",
            "bank_name": "Example Bank",
            "account_number": "XXXXXXXXXX1234",
            "ifsc_code": "EXAMPLE123",
            "payment_instructions": "Send payment to the UPI ID above and share screenshot for confirmation."
        },
        "settings": {
            "website_name": "VeCho Hub",
            "website_tagline": "Premium Digital Services",
            "logo_url": "https://img.icons8.com/fluency/96/admin-settings-male.png",
            "favicon_url": "https://img.icons8.com/color/48/admin-settings-male.png",
            "primary_color": "#4F46E5",
            "secondary_color": "#10B981",
            "accent_color": "#F59E0B",
            "danger_color": "#EF4444",
            "background_color": "#0A0A0A",
            "card_background": "#1A1A1A",
            "text_color": "#FFFFFF",
            "text_secondary": "#A1A1AA",
            "border_radius": "24px",
            "animation_enabled": True,
            "hero_title": "Premium Hosting & Discord Services",
            "hero_subtitle": "Lightning Fast • 99.9% Uptime • 24/7 Support",
            "hero_button_text": "Explore Plans",
            "hero_button_link": "#plans",
            "hero_bg_image": "",
            "stats_show": True,
            "stats_customers": "12,847+",
            "stats_uptime": "99.9%",
            "stats_rating": "4.9/5",
            "stats_servers": "14",
            "features_title": "Why Choose Us",
            "features_subtitle": "Experience the best in class services",
            "footer_text": "© 2024 VeCho Hub. All rights reserved.",
            "footer_copyright": "VeCho Hub",
            "contact_email": "support@vechohub.com",
            "contact_discord": "https://discord.gg/vechohub",
            "contact_twitter": "",
            "contact_github": "",
            "newsletter_enabled": True,
            "newsletter_text": "Subscribe to our newsletter for updates and exclusive offers",
            "testimonials_enabled": True,
            "social_links_enabled": True
        },
        "plans": {
            "VPS": [
                {"id": "vps_mini", "name": "VPS Mini", "price": "$5", "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "popular": False, "icon": "🖥️"},
                {"id": "vps_standard", "name": "VPS Standard", "price": "$20", "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "popular": True, "icon": "⚡"},
                {"id": "vps_pro", "name": "VPS Pro", "price": "$80", "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "popular": False, "icon": "🚀"}
            ],
            "NITRO": [
                {"id": "nitro_basic", "name": "Nitro Basic", "price": "$3", "features": "Custom Emojis, HD Streaming, Profile Badge", "popular": False, "icon": "💜"},
                {"id": "nitro_full", "name": "Nitro Full", "price": "$10", "features": "4K Streaming, 2 Boosts, 500MB Upload", "popular": True, "icon": "✨"},
                {"id": "boost_1", "name": "Server Boost", "price": "$4", "features": "1 Server Boost, Server Perks", "popular": False, "icon": "⚡"}
            ]
        },
        "features": [
            {"icon": "⚡", "title": "Lightning Fast", "description": "NVMe SSD storage and premium network"},
            {"icon": "🛡️", "title": "DDoS Protection", "description": "Enterprise-grade security protection"},
            {"icon": "📞", "title": "24/7 Support", "description": "Expert support team always ready"},
            {"icon": "🔄", "title": "Instant Setup", "description": "Get started in under 5 minutes"}
        ],
        "testimonials": [
            {"name": "Alex Chen", "role": "Game Developer", "content": "Amazing service! The VPS performance is incredible.", "rating": 5, "avatar": "https://randomuser.me/api/portraits/men/1.jpg"},
            {"name": "Sarah Johnson", "role": "Discord Server Owner", "content": "Best Nitro prices I've found anywhere. Highly recommend!", "rating": 5, "avatar": "https://randomuser.me/api/portraits/women/1.jpg"},
            {"name": "Mike Rodriguez", "role": "Startup Founder", "content": "Reliable hosting with great support. 10/10!", "rating": 5, "avatar": "https://randomuser.me/api/portraits/men/2.jpg"}
        ],
        "orders": [],
        "cart": {}
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_discord_notification(webhook_url, message, title="🛒 New Order"):
    if not webhook_url:
        return False
    try:
        embed = {"title": title, "description": message, "color": 0x4F46E5, "timestamp": datetime.now().isoformat()}
        response = requests.post(webhook_url, json={"embeds": [embed]})
        return response.status_code in [200, 204]
    except:
        return False

# ==================== MAIN WEBSITE WITH CART ====================
WEBSITE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ settings.website_name }} | {{ settings.website_tagline }}</title>
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
            overflow-x: hidden;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: {{ settings.background_color }}; }
        ::-webkit-scrollbar-thumb { background: {{ settings.primary_color }}; border-radius: 10px; }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .animate { animation: fadeInUp 0.6s ease forwards; opacity: 0; }
        .delay-1 { animation-delay: 0.1s; }
        .delay-2 { animation-delay: 0.2s; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        
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
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
        }
        .logo img { width: 40px; height: 40px; border-radius: 12px; }
        .logo span { 
            font-size: 1.5rem; 
            font-weight: 700;
            background: linear-gradient(135deg, #fff, {{ settings.primary_color }});
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .nav-links { display: flex; gap: 32px; align-items: center; flex-wrap: wrap; }
        .nav-links a { 
            color: {{ settings.text_color }}; 
            text-decoration: none; 
            transition: 0.3s;
            font-weight: 500;
        }
        .nav-links a:hover { color: {{ settings.primary_color }}; }
        .cart-icon {
            position: relative;
            cursor: pointer;
            padding: 8px;
        }
        .cart-count {
            position: absolute;
            top: -5px;
            right: -5px;
            background: {{ settings.danger_color }};
            color: white;
            border-radius: 50%;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            min-width: 18px;
            text-align: center;
        }
        .admin-btn {
            background: {{ settings.primary_color }};
            padding: 8px 20px;
            border-radius: 40px;
        }
        
        /* Cart Sidebar */
        .cart-sidebar {
            position: fixed;
            right: -400px;
            top: 0;
            width: 400px;
            height: 100vh;
            background: {{ settings.card_background }};
            z-index: 2000;
            padding: 20px;
            transition: right 0.3s ease;
            box-shadow: -5px 0 20px rgba(0,0,0,0.3);
            overflow-y: auto;
        }
        .cart-sidebar.open { right: 0; }
        .close-cart {
            position: absolute;
            right: 20px;
            top: 20px;
            cursor: pointer;
            font-size: 1.5rem;
        }
        .cart-item {
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 15px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .cart-item-remove {
            background: {{ settings.danger_color }};
            border: none;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            cursor: pointer;
        }
        
        /* Payment Modal */
        .payment-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 3000;
            justify-content: center;
            align-items: center;
        }
        .payment-content {
            background: {{ settings.card_background }};
            border-radius: 24px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .hero {
            padding: 100px 0;
            text-align: center;
            position: relative;
        }
        {% if settings.hero_bg_image %}
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('{{ settings.hero_bg_image }}') center/cover;
            opacity: 0.3;
            z-index: 0;
        }
        {% endif %}
        .hero .container { position: relative; z-index: 1; }
        .hero h1 { font-size: 3.5rem; font-weight: 800; margin-bottom: 20px; }
        .hero h1 span { color: {{ settings.primary_color }}; }
        .hero p { font-size: 1.2rem; color: {{ settings.text_secondary }}; margin-bottom: 30px; }
        
        .btn-primary {
            background: {{ settings.primary_color }};
            color: white;
            padding: 14px 36px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: 0.3s;
            display: inline-block;
            border: none;
            cursor: pointer;
        }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(79,70,229,0.3); }
        .btn-outline {
            background: transparent;
            border: 2px solid {{ settings.primary_color }};
            color: {{ settings.text_color }};
            padding: 12px 34px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: 0.3s;
        }
        .btn-outline:hover { background: {{ settings.primary_color }}; color: white; }
        
        .stats-section {
            padding: 60px 0;
            border-top: 1px solid rgba(255,255,255,0.05);
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 30px;
            text-align: center;
        }
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }});
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        .section { padding: 80px 0; }
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .section-title span { color: {{ settings.primary_color }}; }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }
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
        .plan-price small { font-size: 0.8rem; font-weight: 400; opacity: 0.7; }
        .plan-features { list-style: none; margin: 20px 0; }
        .plan-features li { padding: 8px 0; display: flex; align-items: center; gap: 10px; color: {{ settings.text_secondary }}; }
        .buy-btn {
            background: {{ settings.primary_color }};
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 50px;
            width: 100%;
            cursor: pointer;
            font-weight: 600;
            transition: 0.3s;
        }
        .buy-btn:hover { opacity: 0.9; transform: scale(1.02); }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }
        .feature-card {
            background: {{ settings.card_background }};
            border-radius: {{ settings.border_radius }};
            padding: 30px;
            text-align: center;
            transition: 0.3s;
        }
        .feature-card:hover { transform: translateY(-5px); border-color: {{ settings.primary_color }}; }
        .feature-icon { font-size: 3rem; margin-bottom: 20px; }
        
        .testimonials-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .testimonial-card {
            background: {{ settings.card_background }};
            border-radius: {{ settings.border_radius }};
            padding: 30px;
        }
        .testimonial-stars { color: {{ settings.accent_color }}; margin-bottom: 10px; }
        
        .newsletter {
            background: linear-gradient(135deg, {{ settings.primary_color }}15, {{ settings.secondary_color }}15);
            border-radius: {{ settings.border_radius }};
            padding: 60px;
            text-align: center;
        }
        .newsletter-form {
            display: flex;
            gap: 16px;
            max-width: 500px;
            margin: 30px auto 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        .newsletter-form input {
            flex: 1;
            padding: 14px 20px;
            border-radius: 50px;
            border: 1px solid rgba(255,255,255,0.1);
            background: {{ settings.card_background }};
            color: white;
        }
        
        .footer {
            padding: 60px 0 30px;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
        }
        .footer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
        }
        .social-links { display: flex; gap: 16px; margin-top: 20px; }
        .social-links a { color: {{ settings.text_secondary }}; font-size: 1.3rem; transition: 0.3s; }
        .social-links a:hover { color: {{ settings.primary_color }}; }
        .footer-bottom {
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: {{ settings.text_secondary }};
        }
        
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: {{ settings.secondary_color }};
            color: white;
            padding: 12px 24px;
            border-radius: 40px;
            z-index: 4000;
            animation: slideIn 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .cart-sidebar { width: 100%; right: -100%; }
            .navbar .container { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container">
        <div class="logo" onclick="window.location.href='/'">
            <img src="{{ settings.logo_url }}" alt="logo">
            <span>{{ settings.website_name }}</span>
        </div>
        <div class="nav-links">
            <a href="#home">Home</a>
            <a href="#features">Features</a>
            <a href="#plans">Plans</a>
            <a href="#testimonials">Reviews</a>
            <a href="#contact">Contact</a>
            <div class="cart-icon" onclick="toggleCart()">
                <i class="fas fa-shopping-cart"></i>
                <span class="cart-count" id="cartCount">0</span>
            </div>
            <a href="/admin/login" class="admin-btn"><i class="fas fa-lock"></i> Admin</a>
        </div>
    </div>
</nav>

<!-- Cart Sidebar -->
<div class="cart-sidebar" id="cartSidebar">
    <div class="close-cart" onclick="toggleCart()">✕</div>
    <h2>🛒 Your Cart</h2>
    <div id="cartItems"></div>
    <div id="cartTotal" style="font-weight: 800; margin-top: 20px;"></div>
    <button class="btn-primary" onclick="proceedToPayment()" style="width:100%; margin-top:20px;">Proceed to Payment →</button>
    <button onclick="window.open('{{ settings.contact_discord }}', '_blank')" style="width:100%; margin-top:10px; background:#5865F2; color:white; border:none; padding:12px; border-radius:40px; cursor:pointer;">
        <i class="fab fa-discord"></i> Need Help? Contact Support
    </button>
</div>

<!-- Payment Modal -->
<div id="paymentModal" class="payment-modal">
    <div class="payment-content">
        <h2>💳 Complete Payment</h2>
        <div style="margin: 20px 0;">
            <h3>Payment Details:</h3>
            <p><strong>UPI ID:</strong> {{ payment_config.upi_id }}</p>
            {% if payment_config.upi_qr_url %}
            <img src="{{ payment_config.upi_qr_url }}" style="width:200px; margin:10px 0;">
            {% endif %}
            <p><strong>Bank:</strong> {{ payment_config.bank_name }}</p>
            <p><strong>Account:</strong> {{ payment_config.account_number }}</p>
            <p><strong>IFSC:</strong> {{ payment_config.ifsc_code }}</p>
            <p><strong>Instructions:</strong> {{ payment_config.payment_instructions }}</p>
        </div>
        <form id="paymentForm">
            <input type="text" id="customerName" placeholder="Your Name" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px;">
            <input type="text" id="discordId" placeholder="Discord ID (for delivery)" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px;">
            <input type="email" id="customerEmail" placeholder="Email (optional)" style="width:100%; padding:12px; margin:10px 0; border-radius:12px;">
            <input type="text" id="transactionId" placeholder="Transaction ID / Screenshot Link" required style="width:100%; padding:12px; margin:10px 0; border-radius:12px;">
            <button type="submit" class="btn-primary" style="width:100%;">Submit Order</button>
        </form>
        <button onclick="closePaymentModal()" style="width:100%; margin-top:10px; background:#EF4444; color:white; border:none; padding:12px; border-radius:40px; cursor:pointer;">Cancel</button>
    </div>
</div>

<section id="home" class="hero">
    <div class="container">
        <h1 class="animate">{{ settings.hero_title }}<br><span>{{ settings.website_tagline }}</span></h1>
        <p class="animate delay-1">{{ settings.hero_subtitle }}</p>
        <div class="animate delay-2">
            <a href="#plans" class="btn-primary">{{ settings.hero_button_text }} →</a>
            <a href="#contact" class="btn-outline" style="margin-left: 16px;">Contact Us</a>
        </div>
    </div>
</section>

{% if settings.stats_show %}
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
{% endif %}

<section id="features" class="section">
    <div class="container">
        <h2 class="section-title"><span>⚡</span> {{ settings.features_title }}</h2>
        <p class="section-subtitle">{{ settings.features_subtitle }}</p>
        <div class="features-grid">
            {% for feature in features %}
            <div class="feature-card">
                <div class="feature-icon">{{ feature.icon }}</div>
                <h3>{{ feature.title }}</h3>
                <p>{{ feature.description }}</p>
            </div>
            {% endfor %}
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
                <div class="plan-price">{{ plan.price }}<small>/mo</small></div>
                <ul class="plan-features">
                    <li><i class="fas fa-microchip"></i> {{ plan.cpu }}</li>
                    <li><i class="fas fa-memory"></i> {{ plan.ram }}</li>
                    <li><i class="fas fa-hdd"></i> {{ plan.storage }}</li>
                    <li><i class="fas fa-globe"></i> {{ plan.bandwidth }}</li>
                </ul>
                <button class="buy-btn" onclick="addToCart('{{ plan.id }}', '{{ plan.name }}', '{{ plan.price }}', '{{ plan.icon }}')">Add to Cart →</button>
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
                <div class="plan-price">{{ plan.price }}<small>/mo</small></div>
                <ul class="plan-features">
                    <li><i class="fab fa-discord"></i> {{ plan.features }}</li>
                </ul>
                <button class="buy-btn" onclick="addToCart('{{ plan.id }}', '{{ plan.name }}', '{{ plan.price }}', '{{ plan.icon }}')">Add to Cart →</button>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

{% if settings.testimonials_enabled %}
<section id="testimonials" class="section">
    <div class="container">
        <h2 class="section-title"><span>⭐</span> What Our Customers Say</h2>
        <div class="testimonials-grid">
            {% for t in testimonials %}
            <div class="testimonial-card">
                <div class="testimonial-stars">★★★★★</div>
                <div class="testimonial-content">"{{ t.content }}"</div>
                <div class="testimonial-author">
                    <strong>{{ t.name }}</strong> - {{ t.role }}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
{% endif %}

{% if settings.newsletter_enabled %}
<section class="section">
    <div class="container">
        <div class="newsletter">
            <h3>📧 {{ settings.newsletter_text }}</h3>
            <form class="newsletter-form" onsubmit="alert('Thank you for subscribing!'); return false;">
                <input type="email" placeholder="Your email address" required>
                <button type="submit" class="btn-primary">Subscribe</button>
            </form>
        </div>
    </div>
</section>
{% endif %}

<footer id="contact" class="footer">
    <div class="container">
        <div class="footer-grid">
            <div>
                <div class="footer-logo">
                    <img src="{{ settings.logo_url }}" alt="logo" width="40">
                    <h3>{{ settings.website_name }}</h3>
                </div>
                <p style="color: {{ settings.text_secondary }}; margin-top: 15px;">{{ settings.website_tagline }}</p>
                {% if settings.social_links_enabled %}
                <div class="social-links">
                    {% if settings.contact_discord %}<a href="{{ settings.contact_discord }}" target="_blank"><i class="fab fa-discord"></i></a>{% endif %}
                    {% if settings.contact_twitter %}<a href="{{ settings.contact_twitter }}" target="_blank"><i class="fab fa-twitter"></i></a>{% endif %}
                    {% if settings.contact_github %}<a href="{{ settings.contact_github }}" target="_blank"><i class="fab fa-github"></i></a>{% endif %}
                </div>
                {% endif %}
            </div>
            <div>
                <h4>Quick Links</h4>
                <ul style="list-style: none; margin-top: 15px;">
                    <li><a href="#home" style="color: {{ settings.text_secondary }};">Home</a></li>
                    <li><a href="#plans" style="color: {{ settings.text_secondary }};">Plans</a></li>
                    <li><a href="#features" style="color: {{ settings.text_secondary }};">Features</a></li>
                </ul>
            </div>
            <div>
                <h4>Contact</h4>
                <ul style="list-style: none; margin-top: 15px;">
                    <li><i class="fas fa-envelope"></i> <a href="mailto:{{ settings.contact_email }}" style="color: {{ settings.text_secondary }};">{{ settings.contact_email }}</a></li>
                    <li><i class="fab fa-discord"></i> <a href="{{ settings.contact_discord }}" style="color: {{ settings.text_secondary }};">Join Discord</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>{{ settings.footer_text }}</p>
        </div>
    </div>
</footer>

<script>
    let cart = JSON.parse(localStorage.getItem('cart') || '{}');
    
    function updateCartDisplay() {
        let count = 0;
        let total = 0;
        let html = '';
        for (let id in cart) {
            let priceNum = parseFloat(cart[id].price.replace('$', ''));
            count += cart[id].quantity;
            total += priceNum * cart[id].quantity;
            html += `<div class="cart-item">
                <div><span style="font-size:1.5rem;">${cart[id].icon}</span> ${cart[id].name} x${cart[id].quantity}</div>
                <div>$${priceNum * cart[id].quantity} <button class="cart-item-remove" onclick="removeFromCart('${id}')">Remove</button></div>
            </div>`;
        }
        document.getElementById('cartCount').innerText = count;
        document.getElementById('cartItems').innerHTML = html || '<p>Cart is empty</p>';
        document.getElementById('cartTotal').innerHTML = `<strong>Total: $${total.toFixed(2)}</strong>`;
        localStorage.setItem('cart', JSON.stringify(cart));
    }
    
    function addToCart(id, name, price, icon) {
        if (cart[id]) cart[id].quantity++;
        else cart[id] = { name, price, icon, quantity: 1 };
        updateCartDisplay();
        showToast(`✅ Added ${name} to cart`);
    }
    
    function removeFromCart(id) {
        if (cart[id]) {
            cart[id].quantity--;
            if (cart[id].quantity <= 0) delete cart[id];
            updateCartDisplay();
            showToast('🗑️ Removed from cart');
        }
    }
    
    function toggleCart() {
        document.getElementById('cartSidebar').classList.toggle('open');
    }
    
    function proceedToPayment() {
        if (Object.keys(cart).length === 0) {
            showToast('Cart is empty!');
            return;
        }
        document.getElementById('paymentModal').style.display = 'flex';
        toggleCart();
    }
    
    function closePaymentModal() {
        document.getElementById('paymentModal').style.display = 'none';
    }
    
    function showToast(msg) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    
    document.getElementById('paymentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const items = [];
        let total = 0;
        for (let id in cart) {
            let priceNum = parseFloat(cart[id].price.replace('$', ''));
            items.push({ id, name: cart[id].name, price: priceNum, quantity: cart[id].quantity });
            total += priceNum * cart[id].quantity;
        }
        
        const orderData = {
            items: items,
            total: total,
            customer_name: document.getElementById('customerName').value,
            discord_id: document.getElementById('discordId').value,
            email: document.getElementById('customerEmail').value,
            transaction_id: document.getElementById('transactionId').value
        };
        
        const res = await fetch('/api/place-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        const result = await res.json();
        if (result.success) {
            showToast('✅ Order placed! Admin will approve soon.');
            cart = {};
            updateCartDisplay();
            closePaymentModal();
            document.getElementById('paymentForm').reset();
        } else {
            showToast('❌ ' + result.error);
        }
    });
    
    updateCartDisplay();
    
    // Intersection Observer for animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.feature-card, .plan-card, .testimonial-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
</script>
</body>
</html>
'''

# ==================== ADMIN PANEL ====================
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            border: 1px solid rgba(255,255,255,0.1);
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
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
        }
        .error { color: #ED4245; text-align: center; margin-top: 15px; }
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
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

ADMIN_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - {{ settings.website_name }}</title>
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
            overflow-y: auto;
        }
        .sidebar h2 { margin-bottom: 30px; font-size: 1.3rem; }
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
            border: 1px solid rgba(255,255,255,0.1);
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
            font-weight: 600;
            margin-top: 10px;
        }
        .success { background: #10B981; padding: 10px; border-radius: 12px; margin-bottom: 20px; }
        .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .order-item { border-bottom: 1px solid rgba(255,255,255,0.1); padding: 15px 0; }
        .badge-pending { background: #F59E0B; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-approved { background: #10B981; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-rejected { background: #EF4444; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        @media (max-width: 768px) {
            .grid-2 { grid-template-columns: 1fr; }
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
            <div class="nav-item active" data-tab="general"><i class="fas fa-sliders-h"></i> <span>General</span></div>
            <div class="nav-item" data-tab="colors"><i class="fas fa-palette"></i> <span>Colors</span></div>
            <div class="nav-item" data-tab="hero"><i class="fas fa-home"></i> <span>Hero Section</span></div>
            <div class="nav-item" data-tab="stats"><i class="fas fa-chart-line"></i> <span>Statistics</span></div>
            <div class="nav-item" data-tab="features"><i class="fas fa-star"></i> <span>Features</span></div>
            <div class="nav-item" data-tab="plans"><i class="fas fa-box"></i> <span>Plans</span></div>
            <div class="nav-item" data-tab="testimonials"><i class="fas fa-comment"></i> <span>Testimonials</span></div>
            <div class="nav-item" data-tab="footer"><i class="fas fa-footer"></i> <span>Footer & Social</span></div>
            <div class="nav-item" data-tab="botsystem"><i class="fab fa-discord"></i> <span>Bot System</span></div>
            <div class="nav-item" data-tab="payment"><i class="fas fa-credit-card"></i> <span>Payment Methods</span></div>
            <div class="nav-item" data-tab="orders"><i class="fas fa-shopping-cart"></i> <span>Orders</span></div>
            <div class="nav-item" data-tab="password"><i class="fas fa-key"></i> <span>Password</span></div>
            <div class="nav-item" onclick="window.location.href='/admin/logout'"><i class="fas fa-sign-out-alt"></i> <span>Logout</span></div>
        </div>
        
        <div class="main-content">
            <!-- General Tab -->
            <div id="general-tab">
                <div class="card"><h3>🏢 General Settings</h3><form id="generalForm"><input type="text" name="website_name" value="{{ settings.website_name }}"><input type="text" name="website_tagline" value="{{ settings.website_tagline }}"><input type="text" name="logo_url" value="{{ settings.logo_url }}"><input type="text" name="favicon_url" value="{{ settings.favicon_url }}"><input type="text" name="border_radius" value="{{ settings.border_radius }}"><button type="submit">Save</button></form><div id="generalMsg"></div></div>
            </div>
            
            <!-- Colors Tab -->
            <div id="colors-tab" style="display:none;">
                <div class="card"><h3>🎨 Color Settings</h3><form id="colorsForm"><div class="grid-2"><div><label>Primary</label><input type="color" name="primary_color" value="{{ settings.primary_color }}"></div><div><label>Secondary</label><input type="color" name="secondary_color" value="{{ settings.secondary_color }}"></div><div><label>Background</label><input type="color" name="background_color" value="{{ settings.background_color }}"></div><div><label>Text</label><input type="color" name="text_color" value="{{ settings.text_color }}"></div></div><button type="submit">Save</button></form><div id="colorsMsg"></div></div>
            </div>
            
            <!-- Hero Tab -->
            <div id="hero-tab" style="display:none;">
                <div class="card"><h3>🌟 Hero Section</h3><form id="heroForm"><input type="text" name="hero_title" value="{{ settings.hero_title }}"><input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle }}"><input type="text" name="hero_button_text" value="{{ settings.hero_button_text }}"><input type="text" name="hero_button_link" value="{{ settings.hero_button_link }}"><input type="text" name="hero_bg_image" value="{{ settings.hero_bg_image }}"><button type="submit">Save</button></form><div id="heroMsg"></div></div>
            </div>
            
            <!-- Stats Tab -->
            <div id="stats-tab" style="display:none;">
                <div class="card"><h3>📊 Statistics</h3><form id="statsForm"><input type="text" name="stats_customers" value="{{ settings.stats_customers }}"><input type="text" name="stats_uptime" value="{{ settings.stats_uptime }}"><input type="text" name="stats_rating" value="{{ settings.stats_rating }}"><input type="text" name="stats_servers" value="{{ settings.stats_servers }}"><button type="submit">Save</button></form><div id="statsMsg"></div></div>
            </div>
            
            <!-- Features Tab -->
            <div id="features-tab" style="display:none;">
                <div class="card"><h3>✨ Features</h3><form id="featuresForm"><input type="text" name="features_title" value="{{ settings.features_title }}"><input type="text" name="features_subtitle" value="{{ settings.features_subtitle }}"><button type="submit">Save</button></form></div>
                <div class="card"><h3>Manage Features</h3><div id="featuresList">{% for f in features %}<div style="padding:10px 0;"><strong>{{ f.icon }} {{ f.title }}</strong><p>{{ f.description }}</p><button onclick="editFeature({{ loop.index0 }})" style="background:#F59E0B;">Edit</button><button onclick="deleteFeature({{ loop.index0 }})" style="background:#EF4444;">Delete</button></div>{% endfor %}</div><button onclick="addFeature()">+ Add Feature</button></div>
            </div>
            
            <!-- Plans Tab -->
            <div id="plans-tab" style="display:none;">
                <div class="card"><h3>📦 VPS Plans</h3><div id="vpsPlans">{% for plan in plans.VPS %}<div><strong>{{ plan.name }}</strong> - {{ plan.price }}/mo <button onclick="editPlan('VPS',{{ loop.index0 }})" style="background:#F59E0B;">Edit</button></div>{% endfor %}</div><button onclick="addPlan('VPS')">+ Add VPS</button></div>
                <div class="card"><h3>💜 Nitro Plans</h3><div id="nitroPlans">{% for plan in plans.NITRO %}<div><strong>{{ plan.name }}</strong> - {{ plan.price }}/mo <button onclick="editPlan('NITRO',{{ loop.index0 }})" style="background:#F59E0B;">Edit</button></div>{% endfor %}</div><button onclick="addPlan('NITRO')">+ Add Nitro</button></div>
            </div>
            
            <!-- Testimonials Tab -->
            <div id="testimonials-tab" style="display:none;">
                <div class="card"><h3>⭐ Testimonials</h3><form id="testimonialsForm"><select name="testimonials_enabled"><option value="True" {% if settings.testimonials_enabled %}selected{% endif %}>Show</option><option value="False">Hide</option></select><button type="submit">Save</button></form></div>
                <div class="card"><h3>Manage Testimonials</h3><div id="testimonialsList">{% for t in testimonials %}<div><strong>{{ t.name }}</strong><p>{{ t.content }}</p><button onclick="editTestimonial({{ loop.index0 }})" style="background:#F59E0B;">Edit</button><button onclick="deleteTestimonial({{ loop.index0 }})" style="background:#EF4444;">Delete</button></div>{% endfor %}</div><button onclick="addTestimonial()">+ Add Testimonial</button></div>
            </div>
            
            <!-- Footer Tab -->
            <div id="footer-tab" style="display:none;">
                <div class="card"><h3>📋 Footer</h3><form id="footerForm"><input type="text" name="footer_text" value="{{ settings.footer_text }}"><input type="email" name="contact_email" value="{{ settings.contact_email }}"><input type="text" name="contact_discord" value="{{ settings.contact_discord }}"><input type="text" name="contact_twitter" value="{{ settings.contact_twitter }}"><input type="text" name="contact_github" value="{{ settings.contact_github }}"><button type="submit">Save</button></form><div id="footerMsg"></div></div>
            </div>
            
            <!-- Bot System Tab -->
            <div id="botsystem-tab" style="display:none;">
                <div class="card"><h3>🤖 Discord Bot Configuration</h3><form id="botForm"><label>Bot Token</label><input type="password" name="bot_token" value="{{ bot_config.bot_token }}"><label>Webhook URL</label><input type="text" name="webhook_url" value="{{ bot_config.webhook_url }}"><label>Enable Bot</label><select name="bot_enabled"><option value="True" {% if bot_config.bot_enabled %}selected{% endif %}>Yes</option><option value="False">No</option></select><label>Welcome Message</label><textarea name="welcome_message" rows="3">{{ bot_config.welcome_message }}</textarea><button type="submit">Save</button></form><div id="botMsg"></div></div>
                <div class="card"><h3>📖 Available Commands</h3><ul><li><code>/plans</code> - Show all plans</li><li><code>/order [ID]</code> - Check order status</li><li><code>/support</code> - Get support link</li><li><code>/website</code> - Website link</li><li><code>/ping</code> - Bot latency</li><li><code>/help</code> - All commands</li></ul></div>
            </div>
            
            <!-- Payment Methods Tab -->
            <div id="payment-tab" style="display:none;">
                <div class="card"><h3>💳 Payment Configuration</h3><form id="paymentForm"><label>UPI ID</label><input type="text" name="upi_id" value="{{ payment_config.upi_id }}"><label>UPI QR URL</label><input type="text" name="upi_qr_url" value="{{ payment_config.upi_qr_url }}"><label>Bank Name</label><input type="text" name="bank_name" value="{{ payment_config.bank_name }}"><label>Account Number</label><input type="text" name="account_number" value="{{ payment_config.account_number }}"><label>IFSC Code</label><input type="text" name="ifsc_code" value="{{ payment_config.ifsc_code }}"><label>Instructions</label><textarea name="payment_instructions" rows="3">{{ payment_config.payment_instructions }}</textarea><button type="submit">Save</button></form><div id="paymentMsg"></div></div>
            </div>
            
            <!-- Orders Tab -->
            <div id="orders-tab" style="display:none;">
                <div class="card"><h3>📋 Pending Orders</h3><div id="pendingOrders">{% for order in orders if order.status == 'pending' %}<div class="order-item"><strong>🆔 {{ order.id }}</strong> <span class="badge-pending">PENDING</span><p>👤 {{ order.customer_name }} | Discord: {{ order.discord_id }}</p><p>💰 Total: ${{ order.total }}</p><div><button onclick="approveOrder('{{ order.id }}')" style="background:#10B981;">✅ Approve</button><button onclick="rejectOrder('{{ order.id }}')" style="background:#EF4444;">❌ Reject</button><button onclick="contactCustomer('{{ order.discord_id }}')" style="background:#5865F2;">💬 Contact</button></div></div>{% else %}<p>No pending orders</p>{% endfor %}</div></div>
                <div class="card"><h3>📦 All Orders</h3><div id="allOrders">{% for order in orders %}<div class="order-item"><strong>{{ order.id }}</strong> - {{ order.customer_name }} - ${{ order.total }} - <span class="badge-{{ order.status }}">{{ order.status }}</span></div>{% else %}<p>No orders</p>{% endfor %}</div></div>
            </div>
            
            <!-- Password Tab -->
            <div id="password-tab" style="display:none;">
                <div class="card"><h3>🔐 Change Password</h3><form id="passwordForm"><input type="password" name="current_password" placeholder="Current Password"><input type="password" name="new_password" placeholder="New Password"><input type="password" name="confirm_password" placeholder="Confirm Password"><button type="submit">Change</button></form><div id="passwordMsg"></div></div>
            </div>
        </div>
    </div>
    
    <script>
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                const tab = item.dataset.tab;
                document.querySelectorAll('[id$="-tab"]').forEach(t => t.style.display = 'none');
                document.getElementById(`${tab}-tab`).style.display = 'block';
            });
        });
        
        async function postData(url, data, msgElement) {
            await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if(msgElement) msgElement.innerHTML = '<div class="success">✅ Saved! Refreshing...</div>';
            setTimeout(() => location.reload(), 1000);
        }
        
        document.getElementById('generalForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-general', Object.fromEntries(new FormData(e.target)), document.getElementById('generalMsg')); });
        document.getElementById('colorsForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-colors', Object.fromEntries(new FormData(e.target)), document.getElementById('colorsMsg')); });
        document.getElementById('heroForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-hero', Object.fromEntries(new FormData(e.target)), document.getElementById('heroMsg')); });
        document.getElementById('statsForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-stats', Object.fromEntries(new FormData(e.target)), document.getElementById('statsMsg')); });
        document.getElementById('featuresForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-features-title', Object.fromEntries(new FormData(e.target)), null); });
        document.getElementById('testimonialsForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-testimonials-settings', Object.fromEntries(new FormData(e.target)), null); });
        document.getElementById('footerForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-footer', Object.fromEntries(new FormData(e.target)), document.getElementById('footerMsg')); });
        document.getElementById('botForm')?.addEventListener('submit', (e) => { e.preventDefault(); const data = Object.fromEntries(new FormData(e.target)); data.bot_enabled = data.bot_enabled === 'True'; postData('/admin/api/save-bot', data, document.getElementById('botMsg')); });
        document.getElementById('paymentForm')?.addEventListener('submit', (e) => { e.preventDefault(); postData('/admin/api/save-payment', Object.fromEntries(new FormData(e.target)), document.getElementById('paymentMsg')); });
        
        document.getElementById('passwordForm')?.addEventListener('submit', async (e) => {
            e.preventDefault(); const data = Object.fromEntries(new FormData(e.target));
            if(data.new_password !== data.confirm_password) { document.getElementById('passwordMsg').innerHTML = '<div class="success" style="background:#EF4444;">❌ Passwords do not match</div>'; return; }
            const res = await fetch('/admin/api/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            document.getElementById('passwordMsg').innerHTML = result.success ? '<div class="success">✅ Password changed!</div>' : '<div class="success" style="background:#EF4444;">❌ Current password incorrect</div>';
        });
        
        function editPlan(cat, idx) { const name = prompt('New name:'); const price = prompt('New price:'); if(name && price) fetch('/admin/api/edit-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, index: idx, name, price }) }).then(() => location.reload()); }
        function addPlan(cat) { const name = prompt('Plan name:'); const price = prompt('Price:'); if(name && price) fetch('/admin/api/add-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, name, price }) }).then(() => location.reload()); }
        function editFeature(idx) { const title = prompt('Title:'); const desc = prompt('Description:'); if(title && desc) fetch('/admin/api/edit-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx, title, description: desc }) }).then(() => location.reload()); }
        function deleteFeature(idx) { if(confirm('Delete?')) fetch('/admin/api/delete-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx }) }).then(() => location.reload()); }
        function addFeature() { const title = prompt('Title:'); const desc = prompt('Description:'); if(title && desc) fetch('/admin/api/add-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, description: desc, icon: '✨' }) }).then(() => location.reload()); }
        function editTestimonial(idx) { const name = prompt('Name:'); const content = prompt('Content:'); if(name && content) fetch('/admin/api/edit-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx, name, content }) }).then(() => location.reload()); }
        function deleteTestimonial(idx) { if(confirm('Delete?')) fetch('/admin/api/delete-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx }) }).then(() => location.reload()); }
        function addTestimonial() { const name = prompt('Name:'); const content = prompt('Content:'); if(name && content) fetch('/admin/api/add-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, content, role: 'Customer' }) }).then(() => location.reload()); }
        function approveOrder(id) { fetch('/admin/api/approve-order/' + id, { method: 'POST' }).then(() => location.reload()); }
        function rejectOrder(id) { fetch('/admin/api/reject-order/' + id, { method: 'POST' }).then(() => location.reload()); }
        function contactCustomer(discordId) { window.open('https://discord.com/users/' + discordId, '_blank'); }
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================
@app.route('/')
def index():
    data = load_db()
    return render_template_string(WEBSITE_TEMPLATE, settings=data['settings'], plans=data['plans'], features=data['features'], testimonials=data['testimonials'], payment_config=data['payment_config'])

@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = load_db()
    order_id = secrets.token_hex(8).upper()
    order = {
        "id": order_id,
        "items": request.json.get('items', []),
        "total": request.json.get('total', 0),
        "customer_name": request.json.get('customer_name'),
        "discord_id": request.json.get('discord_id'),
        "email": request.json.get('email'),
        "transaction_id": request.json.get('transaction_id'),
        "status": "pending",
        "date": datetime.now().isoformat()
    }
    data['orders'].insert(0, order)
    save_db(data)
    
    if data['bot_config'].get('webhook_url'):
        msg = f"**New Order!**\nOrder ID: `{order_id}`\nCustomer: {order['customer_name']}\nTotal: ${order['total']}\nDiscord: {order['discord_id']}"
        send_discord_notification(data['bot_config']['webhook_url'], msg)
    
    return jsonify({"success": True, "order_id": order_id})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = load_db()
        if request.form.get('email') == data['admin']['email'] and check_password_hash(data['admin']['password'], request.form.get('password')):
            session['admin_logged_in'] = True
            return redirect('/admin/panel')
        return render_template_string(ADMIN_LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(ADMIN_LOGIN_TEMPLATE, error=None)

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    data = load_db()
    return render_template_string(ADMIN_PANEL_TEMPLATE, settings=data['settings'], plans=data['plans'], features=data['features'], testimonials=data['testimonials'], orders=data['orders'], bot_config=data['bot_config'], payment_config=data['payment_config'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

# API Routes
@app.route('/admin/api/save-general', methods=['POST'])
def save_general():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['website_name'] = request.json.get('website_name')
    data['settings']['website_tagline'] = request.json.get('website_tagline')
    data['settings']['logo_url'] = request.json.get('logo_url')
    data['settings']['favicon_url'] = request.json.get('favicon_url')
    data['settings']['border_radius'] = request.json.get('border_radius')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-colors', methods=['POST'])
def save_colors():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['primary_color'] = request.json.get('primary_color')
    data['settings']['secondary_color'] = request.json.get('secondary_color')
    data['settings']['background_color'] = request.json.get('background_color')
    data['settings']['text_color'] = request.json.get('text_color')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-hero', methods=['POST'])
def save_hero():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['hero_title'] = request.json.get('hero_title')
    data['settings']['hero_subtitle'] = request.json.get('hero_subtitle')
    data['settings']['hero_button_text'] = request.json.get('hero_button_text')
    data['settings']['hero_button_link'] = request.json.get('hero_button_link')
    data['settings']['hero_bg_image'] = request.json.get('hero_bg_image')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-stats', methods=['POST'])
def save_stats():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['stats_customers'] = request.json.get('stats_customers')
    data['settings']['stats_uptime'] = request.json.get('stats_uptime')
    data['settings']['stats_rating'] = request.json.get('stats_rating')
    data['settings']['stats_servers'] = request.json.get('stats_servers')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-features-title', methods=['POST'])
def save_features_title():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['features_title'] = request.json.get('features_title')
    data['settings']['features_subtitle'] = request.json.get('features_subtitle')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-footer', methods=['POST'])
def save_footer():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['footer_text'] = request.json.get('footer_text')
    data['settings']['contact_email'] = request.json.get('contact_email')
    data['settings']['contact_discord'] = request.json.get('contact_discord')
    data['settings']['contact_twitter'] = request.json.get('contact_twitter')
    data['settings']['contact_github'] = request.json.get('contact_github')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-testimonials-settings', methods=['POST'])
def save_testimonials_settings():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['testimonials_enabled'] = request.json.get('testimonials_enabled') == 'True'
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-bot', methods=['POST'])
def save_bot():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['bot_config']['bot_token'] = request.json.get('bot_token')
    data['bot_config']['webhook_url'] = request.json.get('webhook_url')
    data['bot_config']['bot_enabled'] = request.json.get('bot_enabled')
    data['bot_config']['welcome_message'] = request.json.get('welcome_message')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-payment', methods=['POST'])
def save_payment():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['payment_config']['upi_id'] = request.json.get('upi_id')
    data['payment_config']['upi_qr_url'] = request.json.get('upi_qr_url')
    data['payment_config']['bank_name'] = request.json.get('bank_name')
    data['payment_config']['account_number'] = request.json.get('account_number')
    data['payment_config']['ifsc_code'] = request.json.get('ifsc_code')
    data['payment_config']['payment_instructions'] = request.json.get('payment_instructions')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/change-password', methods=['POST'])
def change_password():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    if check_password_hash(data['admin']['password'], request.json.get('current_password')):
        data['admin']['password'] = generate_password_hash(request.json.get('new_password'))
        save_db(data)
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/admin/api/edit-plan', methods=['POST'])
def edit_plan():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    index = request.json.get('index')
    if category in data['plans'] and 0 <= index < len(data['plans'][category]):
        data['plans'][category][index]['name'] = request.json.get('name')
        data['plans'][category][index]['price'] = request.json.get('price')
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-plan', methods=['POST'])
def add_plan():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    new_id = secrets.token_hex(6)
    new_plan = {"id": new_id, "name": request.json.get('name'), "price": request.json.get('price'), "popular": False, "icon": "🖥️"}
    if category == 'VPS':
        new_plan.update({"cpu": "2 Core", "ram": "2GB", "storage": "50GB SSD", "bandwidth": "2TB"})
        data['plans'][category].append(new_plan)
    else:
        new_plan.update({"features": "Premium features"})
        data['plans'][category].append(new_plan)
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/edit-feature', methods=['POST'])
def edit_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    idx = request.json.get('index')
    if 0 <= idx < len(data['features']):
        data['features'][idx]['title'] = request.json.get('title')
        data['features'][idx]['description'] = request.json.get('description')
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/delete-feature', methods=['POST'])
def delete_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    idx = request.json.get('index')
    if 0 <= idx < len(data['features']):
        data['features'].pop(idx)
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-feature', methods=['POST'])
def add_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['features'].append({"icon": "✨", "title": request.json.get('title'), "description": request.json.get('description')})
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/edit-testimonial', methods=['POST'])
def edit_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    idx = request.json.get('index')
    if 0 <= idx < len(data['testimonials']):
        data['testimonials'][idx]['name'] = request.json.get('name')
        data['testimonials'][idx]['content'] = request.json.get('content')
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/delete-testimonial', methods=['POST'])
def delete_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    idx = request.json.get('index')
    if 0 <= idx < len(data['testimonials']):
        data['testimonials'].pop(idx)
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-testimonial', methods=['POST'])
def add_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['testimonials'].append({"name": request.json.get('name'), "role": "Customer", "content": request.json.get('content'), "rating": 5, "avatar": "https://randomuser.me/api/portraits/men/99.jpg"})
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/approve-order/<order_id>', methods=['POST'])
def approve_order(order_id):
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    for order in data['orders']:
        if order['id'] == order_id:
            order['status'] = 'approved'
            break
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/reject-order/<order_id>', methods=['POST'])
def reject_order(order_id):
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    for order in data['orders']:
        if order['id'] == order_id:
            order['status'] = 'rejected'
            break
    save_db(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
