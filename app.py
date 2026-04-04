# app.py - Modern Website with Advanced Admin Panel (Fully Fixed)
import os
import json
import secrets
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
                {"name": "VPS Mini", "price": "$5", "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "popular": False, "icon": "🖥️"},
                {"name": "VPS Standard", "price": "$20", "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "popular": True, "icon": "⚡"},
                {"name": "VPS Pro", "price": "$80", "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "popular": False, "icon": "🚀"}
            ],
            "NITRO": [
                {"name": "Nitro Basic", "price": "$3", "features": "Custom Emojis, HD Streaming, Profile Badge", "popular": False, "icon": "💜"},
                {"name": "Nitro Full", "price": "$10", "features": "4K Streaming, 2 Boosts, 500MB Upload", "popular": True, "icon": "✨"},
                {"name": "Server Boost", "price": "$4", "features": "1 Server Boost, Server Perks", "popular": False, "icon": "⚡"}
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
        ]
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ==================== MAIN WEBSITE ====================
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
        
        .animate { animation: fadeInUp 0.6s ease forwards; opacity: 0; }
        .delay-1 { animation-delay: 0.1s; }
        .delay-2 { animation-delay: 0.2s; }
        .delay-3 { animation-delay: 0.3s; }
        
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
        .admin-btn {
            background: {{ settings.primary_color }};
            padding: 8px 20px;
            border-radius: 40px;
        }
        .admin-btn:hover { opacity: 0.9; color: white !important; transform: translateY(-2px); }
        
        .hero {
            padding: 100px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
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
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            line-height: 1.2;
        }
        .hero h1 span { color: {{ settings.primary_color }}; }
        .hero p {
            font-size: 1.2rem;
            color: {{ settings.text_secondary }};
            margin-bottom: 30px;
        }
        .hero-buttons {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }
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
        .btn-outline:hover { background: {{ settings.primary_color }}; color: white; transform: translateY(-3px); }
        
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
        .stat-label {
            color: {{ settings.text_secondary }};
            margin-top: 8px;
        }
        
        .section {
            padding: 80px 0;
        }
        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .section-title span { color: {{ settings.primary_color }}; }
        .section-subtitle {
            text-align: center;
            color: {{ settings.text_secondary }};
            margin-bottom: 50px;
            font-size: 1.1rem;
        }
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
            border: 1px solid rgba(255,255,255,0.05);
        }
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: {{ settings.primary_color }};
        }
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        .feature-card h3 { margin-bottom: 12px; }
        .feature-card p { color: {{ settings.text_secondary }}; line-height: 1.6; }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
        }
        .plan-card {
            background: {{ settings.card_background }};
            border-radius: {{ settings.border_radius }};
            padding: 30px;
            transition: 0.3s;
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
            overflow: hidden;
        }
        .plan-card:hover {
            transform: translateY(-5px);
            border-color: {{ settings.primary_color }};
        }
        .plan-card.popular {
            border: 2px solid {{ settings.primary_color }};
        }
        .popular-badge {
            position: absolute;
            top: 20px;
            right: 20px;
            background: {{ settings.primary_color }};
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .plan-icon { font-size: 2.5rem; margin-bottom: 15px; }
        .plan-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 10px; }
        .plan-price {
            font-size: 2rem;
            font-weight: 800;
            margin: 20px 0;
        }
        .plan-price small { font-size: 0.8rem; font-weight: 400; opacity: 0.7; }
        .plan-features {
            list-style: none;
            margin: 20px 0;
        }
        .plan-features li {
            padding: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: {{ settings.text_secondary }};
        }
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
        
        .testimonials-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .testimonial-card {
            background: {{ settings.card_background }};
            border-radius: {{ settings.border_radius }};
            padding: 30px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .testimonial-content {
            font-style: italic;
            line-height: 1.6;
            margin-bottom: 20px;
            color: {{ settings.text_secondary }};
        }
        .testimonial-author {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .testimonial-author img {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
        }
        .testimonial-stars { color: {{ settings.accent_color }}; margin-bottom: 10px; }
        
        .newsletter {
            background: linear-gradient(135deg, {{ settings.primary_color }}15, {{ settings.secondary_color }}15);
            border-radius: {{ settings.border_radius }};
            padding: 60px;
            text-align: center;
        }
        .newsletter h3 { margin-bottom: 16px; }
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
        .footer-logo img { width: 40px; margin-bottom: 15px; }
        .social-links {
            display: flex;
            gap: 16px;
            margin-top: 20px;
        }
        .social-links a {
            color: {{ settings.text_secondary }};
            font-size: 1.3rem;
            transition: 0.3s;
        }
        .social-links a:hover { color: {{ settings.primary_color }}; }
        .footer-bottom {
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: {{ settings.text_secondary }};
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .navbar .container { flex-direction: column; gap: 15px; }
            .newsletter { padding: 30px; }
        }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container">
        <div class="logo">
            <img src="{{ settings.logo_url }}" alt="logo" onerror="this.src='https://img.icons8.com/fluency/96/admin-settings-male.png'">
            <span>{{ settings.website_name }}</span>
        </div>
        <div class="nav-links">
            <a href="#home">Home</a>
            <a href="#features">Features</a>
            <a href="#plans">Plans</a>
            <a href="#testimonials">Reviews</a>
            <a href="#contact">Contact</a>
            <a href="/admin/login" class="admin-btn"><i class="fas fa-lock"></i> Admin</a>
        </div>
    </div>
</nav>

<section id="home" class="hero">
    <div class="container">
        <h1 class="animate">{{ settings.hero_title }}<br><span>{{ settings.website_tagline }}</span></h1>
        <p class="animate delay-1">{{ settings.hero_subtitle }}</p>
        <div class="hero-buttons animate delay-2">
            <a href="{{ settings.hero_button_link }}" class="btn-primary">{{ settings.hero_button_text }} →</a>
            <a href="#contact" class="btn-outline">Contact Us</a>
        </div>
    </div>
</section>

{% if settings.stats_show %}
<section class="stats-section">
    <div class="container">
        <div class="stats-grid">
            <div><div class="stat-number">{{ settings.stats_customers }}</div><div class="stat-label">Happy Customers</div></div>
            <div><div class="stat-number">{{ settings.stats_uptime }}</div><div class="stat-label">Uptime</div></div>
            <div><div class="stat-number">{{ settings.stats_rating }}</div><div class="stat-label">Rating</div></div>
            <div><div class="stat-number">{{ settings.stats_servers }}</div><div class="stat-label">Worldwide Servers</div></div>
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
                <button class="buy-btn" onclick="alert('🎉 Order system coming soon! Contact support for details.')">Order Now →</button>
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
                <button class="buy-btn" onclick="alert('🎉 Order system coming soon! Contact support for details.')">Claim Now →</button>
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
                <div class="testimonial-stars">
                    {% for i in range(t.rating) %}★{% endfor %}
                </div>
                <div class="testimonial-content">"{{ t.content }}"</div>
                <div class="testimonial-author">
                    <img src="{{ t.avatar }}" alt="{{ t.name }}">
                    <div>
                        <strong>{{ t.name }}</strong>
                        <div style="color: {{ settings.text_secondary }}; font-size: 0.8rem;">{{ t.role }}</div>
                    </div>
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
                    <li><a href="#home" style="color: {{ settings.text_secondary }}; text-decoration: none;">Home</a></li>
                    <li><a href="#plans" style="color: {{ settings.text_secondary }}; text-decoration: none;">Plans</a></li>
                    <li><a href="#features" style="color: {{ settings.text_secondary }}; text-decoration: none;">Features</a></li>
                </ul>
            </div>
            <div>
                <h4>Contact</h4>
                <ul style="list-style: none; margin-top: 15px;">
                    <li><i class="fas fa-envelope"></i> <a href="mailto:{{ settings.contact_email }}" style="color: {{ settings.text_secondary }}; text-decoration: none;">{{ settings.contact_email }}</a></li>
                    <li><i class="fab fa-discord"></i> <a href="{{ settings.contact_discord }}" style="color: {{ settings.text_secondary }}; text-decoration: none;">Join Discord</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>{{ settings.footer_text }}</p>
        </div>
    </div>
</footer>

<script>
    // Intersection Observer for animations
    const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
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
        @media (max-width: 768px) {
            .grid-2 { grid-template-columns: 1fr; }
            .sidebar { width: 80px; padding: 15px; position: fixed; }
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
            <div class="nav-item" data-tab="password"><i class="fas fa-key"></i> <span>Password</span></div>
            <div class="nav-item" onclick="window.location.href='/admin/logout'"><i class="fas fa-sign-out-alt"></i> <span>Logout</span></div>
        </div>
        
        <div class="main-content">
            <div id="general-tab">
                <div class="card">
                    <h3>🏢 General Settings</h3>
                    <form id="generalForm">
                        <label>Website Name</label>
                        <input type="text" name="website_name" value="{{ settings.website_name }}">
                        <label>Website Tagline</label>
                        <input type="text" name="website_tagline" value="{{ settings.website_tagline }}">
                        <label>Logo URL</label>
                        <input type="text" name="logo_url" value="{{ settings.logo_url }}">
                        <label>Favicon URL</label>
                        <input type="text" name="favicon_url" value="{{ settings.favicon_url }}">
                        <label>Border Radius (px)</label>
                        <input type="text" name="border_radius" value="{{ settings.border_radius }}">
                        <label>Animation Enabled</label>
                        <select name="animation_enabled">
                            <option value="True" {% if settings.animation_enabled %}selected{% endif %}>Yes</option>
                            <option value="False" {% if not settings.animation_enabled %}selected{% endif %}>No</option>
                        </select>
                        <button type="submit">Save Changes</button>
                    </form>
                    <div id="generalMsg"></div>
                </div>
            </div>
            
            <div id="colors-tab" style="display:none;">
                <div class="card">
                    <h3>🎨 Color Settings</h3>
                    <form id="colorsForm">
                        <div class="grid-2">
                            <div><label>Primary Color</label><input type="color" name="primary_color" value="{{ settings.primary_color }}"></div>
                            <div><label>Secondary Color</label><input type="color" name="secondary_color" value="{{ settings.secondary_color }}"></div>
                            <div><label>Accent Color</label><input type="color" name="accent_color" value="{{ settings.accent_color }}"></div>
                            <div><label>Background Color</label><input type="color" name="background_color" value="{{ settings.background_color }}"></div>
                            <div><label>Card Background</label><input type="color" name="card_background" value="{{ settings.card_background }}"></div>
                            <div><label>Text Color</label><input type="color" name="text_color" value="{{ settings.text_color }}"></div>
                        </div>
                        <button type="submit">Save Colors</button>
                    </form>
                    <div id="colorsMsg"></div>
                </div>
            </div>
            
            <div id="hero-tab" style="display:none;">
                <div class="card">
                    <h3>🌟 Hero Section</h3>
                    <form id="heroForm">
                        <label>Hero Title</label><input type="text" name="hero_title" value="{{ settings.hero_title }}">
                        <label>Hero Subtitle</label><input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle }}">
                        <label>Button Text</label><input type="text" name="hero_button_text" value="{{ settings.hero_button_text }}">
                        <label>Button Link</label><input type="text" name="hero_button_link" value="{{ settings.hero_button_link }}">
                        <label>Hero Background Image URL</label><input type="text" name="hero_bg_image" value="{{ settings.hero_bg_image }}">
                        <button type="submit">Save Hero</button>
                    </form>
                    <div id="heroMsg"></div>
                </div>
            </div>
            
            <div id="stats-tab" style="display:none;">
                <div class="card">
                    <h3>📊 Statistics Settings</h3>
                    <form id="statsForm">
                        <label>Show Stats Section</label>
                        <select name="stats_show"><option value="True" {% if settings.stats_show %}selected{% endif %}>Yes</option><option value="False" {% if not settings.stats_show %}selected{% endif %}>No</option></select>
                        <label>Customers Count</label><input type="text" name="stats_customers" value="{{ settings.stats_customers }}">
                        <label>Uptime Percentage</label><input type="text" name="stats_uptime" value="{{ settings.stats_uptime }}">
                        <label>Rating</label><input type="text" name="stats_rating" value="{{ settings.stats_rating }}">
                        <label>Servers Count</label><input type="text" name="stats_servers" value="{{ settings.stats_servers }}">
                        <button type="submit">Save Stats</button>
                    </form>
                    <div id="statsMsg"></div>
                </div>
            </div>
            
            <div id="features-tab" style="display:none;">
                <div class="card">
                    <h3>✨ Features Section</h3>
                    <form id="featuresForm">
                        <label>Features Title</label><input type="text" name="features_title" value="{{ settings.features_title }}">
                        <label>Features Subtitle</label><input type="text" name="features_subtitle" value="{{ settings.features_subtitle }}">
                        <button type="submit">Save Features Title</button>
                    </form>
                </div>
                <div class="card">
                    <h3>Manage Features</h3>
                    <div id="featuresList">
                        {% for f in features %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ f.icon }} {{ f.title }}</strong>
                            <p>{{ f.description }}</p>
                            <button onclick="editFeature({{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                            <button onclick="deleteFeature({{ loop.index0 }})" style="background:#EF4444;">Delete</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addFeature()">+ Add Feature</button>
                </div>
            </div>
            
            <div id="plans-tab" style="display:none;">
                <div class="card">
                    <h3>📦 Manage VPS Plans</h3>
                    <div id="vpsPlansList">
                        {% for plan in plans.VPS %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.name }}</strong> - {{ plan.price }}/mo
                            <button onclick="editPlan('VPS', {{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('VPS')">+ Add VPS Plan</button>
                </div>
                <div class="card">
                    <h3>💜 Manage Nitro Plans</h3>
                    <div id="nitroPlansList">
                        {% for plan in plans.NITRO %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.name }}</strong> - {{ plan.price }}/mo
                            <button onclick="editPlan('NITRO', {{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('NITRO')">+ Add Nitro Plan</button>
                </div>
            </div>
            
            <div id="testimonials-tab" style="display:none;">
                <div class="card">
                    <h3>⭐ Testimonials Settings</h3>
                    <form id="testimonialsForm">
                        <label>Show Testimonials</label>
                        <select name="testimonials_enabled"><option value="True" {% if settings.testimonials_enabled %}selected{% endif %}>Yes</option><option value="False" {% if not settings.testimonials_enabled %}selected{% endif %}>No</option></select>
                        <button type="submit">Save</button>
                    </form>
                </div>
                <div class="card">
                    <h3>Manage Testimonials</h3>
                    <div id="testimonialsList">
                        {% for t in testimonials %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ t.name }}</strong> - {{ t.role }}
                            <p>{{ t.content }}</p>
                            <button onclick="editTestimonial({{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                            <button onclick="deleteTestimonial({{ loop.index0 }})" style="background:#EF4444;">Delete</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addTestimonial()">+ Add Testimonial</button>
                </div>
            </div>
            
            <div id="footer-tab" style="display:none;">
                <div class="card">
                    <h3>📋 Footer & Social Links</h3>
                    <form id="footerForm">
                        <label>Footer Text</label><input type="text" name="footer_text" value="{{ settings.footer_text }}">
                        <label>Contact Email</label><input type="email" name="contact_email" value="{{ settings.contact_email }}">
                        <label>Discord Invite Link</label><input type="text" name="contact_discord" value="{{ settings.contact_discord }}">
                        <label>Twitter/X Link</label><input type="text" name="contact_twitter" value="{{ settings.contact_twitter }}">
                        <label>GitHub Link</label><input type="text" name="contact_github" value="{{ settings.contact_github }}">
                        <label>Newsletter Enabled</label>
                        <select name="newsletter_enabled"><option value="True" {% if settings.newsletter_enabled %}selected{% endif %}>Yes</option><option value="False" {% if not settings.newsletter_enabled %}selected{% endif %}>No</option></select>
                        <label>Newsletter Text</label><input type="text" name="newsletter_text" value="{{ settings.newsletter_text }}">
                        <label>Social Links Enabled</label>
                        <select name="social_links_enabled"><option value="True" {% if settings.social_links_enabled %}selected{% endif %}>Yes</option><option value="False" {% if not settings.social_links_enabled %}selected{% endif %}>No</option></select>
                        <button type="submit">Save Footer</button>
                    </form>
                    <div id="footerMsg"></div>
                </div>
            </div>
            
            <div id="password-tab" style="display:none;">
                <div class="card">
                    <h3>🔐 Change Admin Password</h3>
                    <form id="passwordForm">
                        <label>Current Password</label><input type="password" name="current_password" required>
                        <label>New Password</label><input type="password" name="new_password" required>
                        <label>Confirm Password</label><input type="password" name="confirm_password" required>
                        <button type="submit">Change Password</button>
                    </form>
                    <div id="passwordMsg"></div>
                </div>
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
            const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if (msgElement) msgElement.innerHTML = '<div class="success">✅ Saved! Page will refresh...</div>';
            setTimeout(() => location.reload(), 1000);
        }
        
        document.getElementById('generalForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            postData('/admin/api/save-general', data, document.getElementById('generalMsg'));
        });
        
        document.getElementById('colorsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            postData('/admin/api/save-colors', data, document.getElementById('colorsMsg'));
        });
        
        document.getElementById('heroForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            postData('/admin/api/save-hero', data, document.getElementById('heroMsg'));
        });
        
        document.getElementById('statsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            postData('/admin/api/save-stats', data, document.getElementById('statsMsg'));
        });
        
        document.getElementById('featuresForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            fetch('/admin/api/save-features-title', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(() => location.reload());
        });
        
        document.getElementById('testimonialsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            fetch('/admin/api/save-testimonials-settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(() => location.reload());
        });
        
        document.getElementById('footerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            postData('/admin/api/save-footer', data, document.getElementById('footerMsg'));
        });
        
        document.getElementById('passwordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            if (data.new_password !== data.confirm_password) {
                document.getElementById('passwordMsg').innerHTML = '<div class="error" style="color:#ED4245;">❌ Passwords do not match!</div>';
                return;
            }
            const res = await fetch('/admin/api/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            if (result.success) {
                document.getElementById('passwordMsg').innerHTML = '<div class="success">✅ Password changed!</div>';
                e.target.reset();
            } else {
                document.getElementById('passwordMsg').innerHTML = '<div class="error" style="color:#ED4245;">❌ Current password is incorrect!</div>';
            }
        });
        
        function editFeature(index) {
            const newTitle = prompt('Enter new feature title:');
            const newDesc = prompt('Enter new feature description:');
            if (newTitle && newDesc) {
                fetch('/admin/api/edit-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index, title: newTitle, description: newDesc }) }).then(() => location.reload());
            }
        }
        function deleteFeature(index) {
            if (confirm('Delete this feature?')) {
                fetch('/admin/api/delete-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index }) }).then(() => location.reload());
            }
        }
        function addFeature() {
            const newTitle = prompt('Enter feature title:');
            const newDesc = prompt('Enter feature description:');
            if (newTitle && newDesc) {
                fetch('/admin/api/add-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newTitle, description: newDesc, icon: '✨' }) }).then(() => location.reload());
            }
        }
        
        function editPlan(category, index) {
            const newName = prompt('Enter new plan name:');
            const newPrice = prompt('Enter new price:');
            if (newName && newPrice) {
                fetch('/admin/api/edit-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, index, name: newName, price: newPrice }) }).then(() => location.reload());
            }
        }
        function addPlan(category) {
            const newName = prompt('Enter plan name:');
            const newPrice = prompt('Enter price:');
            if (newName && newPrice) {
                fetch('/admin/api/add-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, name: newName, price: newPrice }) }).then(() => location.reload());
            }
        }
        
        function editTestimonial(index) {
            const newName = prompt('Enter name:');
            const newRole = prompt('Enter role:');
            const newContent = prompt('Enter testimonial:');
            if (newName && newRole && newContent) {
                fetch('/admin/api/edit-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index, name: newName, role: newRole, content: newContent }) }).then(() => location.reload());
            }
        }
        function deleteTestimonial(index) {
            if (confirm('Delete this testimonial?')) {
                fetch('/admin/api/delete-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index }) }).then(() => location.reload());
            }
        }
        function addTestimonial() {
            const newName = prompt('Enter name:');
            const newRole = prompt('Enter role:');
            const newContent = prompt('Enter testimonial:');
            if (newName && newRole && newContent) {
                fetch('/admin/api/add-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newName, role: newRole, content: newContent }) }).then(() => location.reload());
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
    return render_template_string(WEBSITE_TEMPLATE, settings=data['settings'], plans=data['plans'], features=data['features'], testimonials=data['testimonials'])

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
    return render_template_string(ADMIN_PANEL_TEMPLATE, settings=data['settings'], plans=data['plans'], features=data['features'], testimonials=data['testimonials'])

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
    data['settings']['animation_enabled'] = request.json.get('animation_enabled') == 'True'
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-colors', methods=['POST'])
def save_colors():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['primary_color'] = request.json.get('primary_color')
    data['settings']['secondary_color'] = request.json.get('secondary_color')
    data['settings']['accent_color'] = request.json.get('accent_color')
    data['settings']['background_color'] = request.json.get('background_color')
    data['settings']['card_background'] = request.json.get('card_background')
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
    data['settings']['stats_show'] = request.json.get('stats_show') == 'True'
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
    data['settings']['newsletter_enabled'] = request.json.get('newsletter_enabled') == 'True'
    data['settings']['newsletter_text'] = request.json.get('newsletter_text')
    data['settings']['social_links_enabled'] = request.json.get('social_links_enabled') == 'True'
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-testimonials-settings', methods=['POST'])
def save_testimonials_settings():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['testimonials_enabled'] = request.json.get('testimonials_enabled') == 'True'
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
    if category in data['plans']:
        if category == 'VPS':
            data['plans'][category].append({"name": request.json.get('name'), "price": request.json.get('price'), "cpu": "2 Core", "ram": "2GB", "storage": "50GB SSD", "bandwidth": "2TB", "popular": False, "icon": "💻"})
        else:
            data['plans'][category].append({"name": request.json.get('name'), "price": request.json.get('price'), "features": "Premium features", "popular": False, "icon": "💜"})
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/edit-feature', methods=['POST'])
def edit_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    index = request.json.get('index')
    if 0 <= index < len(data['features']):
        data['features'][index]['title'] = request.json.get('title')
        data['features'][index]['description'] = request.json.get('description')
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/delete-feature', methods=['POST'])
def delete_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    index = request.json.get('index')
    if 0 <= index < len(data['features']):
        data['features'].pop(index)
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-feature', methods=['POST'])
def add_feature():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['features'].append({"icon": request.json.get('icon', '✨'), "title": request.json.get('title'), "description": request.json.get('description')})
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/edit-testimonial', methods=['POST'])
def edit_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    index = request.json.get('index')
    if 0 <= index < len(data['testimonials']):
        data['testimonials'][index]['name'] = request.json.get('name')
        data['testimonials'][index]['role'] = request.json.get('role')
        data['testimonials'][index]['content'] = request.json.get('content')
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/delete-testimonial', methods=['POST'])
def delete_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    index = request.json.get('index')
    if 0 <= index < len(data['testimonials']):
        data['testimonials'].pop(index)
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-testimonial', methods=['POST'])
def add_testimonial():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['testimonials'].append({"name": request.json.get('name'), "role": request.json.get('role'), "content": request.json.get('content'), "rating": 5, "avatar": "https://randomuser.me/api/portraits/men/99.jpg"})
    save_db(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
