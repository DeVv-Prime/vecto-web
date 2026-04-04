# app.py - Simple Website with Admin Panel (No Dashboard)
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
            "email": "admin@vechohub.com",
            "password": generate_password_hash("admin123")
        },
        "settings": {
            "website_name": "VeCho Hub",
            "logo_url": "https://img.icons8.com/fluency/96/admin-settings-male.png",
            "favicon_url": "https://img.icons8.com/color/48/admin-settings-male.png",
            "primary_color": "#4F46E5",
            "secondary_color": "#10B981",
            "background_color": "#0A0A0A",
            "text_color": "#FFFFFF",
            "hero_title": "Premium Hosting & Discord Services",
            "hero_subtitle": "VPS | RDP | Minecraft | Discord Nitro",
            "footer_text": "© 2024 VeCho Hub. All rights reserved.",
            "contact_email": "support@vechohub.com",
            "contact_discord": "https://discord.gg/vechohub"
        },
        "plans": {
            "VPS": [
                {"name": "VPS Mini", "price": "$5", "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "popular": False},
                {"name": "VPS Standard", "price": "$20", "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "popular": True},
                {"name": "VPS Pro", "price": "$80", "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "popular": False}
            ],
            "NITRO": [
                {"name": "Nitro Basic", "price": "$3", "features": "Custom Emojis, HD Streaming", "popular": False},
                {"name": "Nitro Full", "price": "$10", "features": "4K Streaming, 2 Boosts, 500MB Upload", "popular": True},
                {"name": "Server Boost", "price": "$4", "features": "1 Server Boost", "popular": False}
            ]
        }
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
    <title>{{ settings.website_name }}</title>
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
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        
        /* Navbar */
        .navbar {
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: sticky;
            top: 0;
            background: {{ settings.background_color }};
            z-index: 100;
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
        .logo img { width: 40px; height: 40px; }
        .logo span { font-size: 1.5rem; font-weight: 700; }
        .nav-links { display: flex; gap: 30px; align-items: center; flex-wrap: wrap; }
        .nav-links a { color: white; text-decoration: none; transition: 0.3s; }
        .nav-links a:hover { color: {{ settings.primary_color }}; }
        .admin-btn {
            background: {{ settings.primary_color }};
            padding: 8px 20px;
            border-radius: 40px;
        }
        .admin-btn:hover { opacity: 0.9; color: white !important; }
        
        /* Hero Section */
        .hero {
            text-align: center;
            padding: 80px 0;
        }
        .hero h1 { font-size: 3rem; margin-bottom: 20px; }
        .hero h1 span { color: {{ settings.primary_color }}; }
        .hero p { font-size: 1.2rem; opacity: 0.8; margin-bottom: 30px; }
        .btn-primary {
            background: {{ settings.primary_color }};
            color: white;
            padding: 12px 32px;
            border-radius: 40px;
            text-decoration: none;
            display: inline-block;
            transition: 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn-primary:hover { transform: scale(1.05); opacity: 0.9; }
        
        /* Sections */
        .section {
            padding: 60px 0;
        }
        .section-title {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 40px;
        }
        .section-title span { color: {{ settings.primary_color }}; }
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 24px;
            padding: 30px;
            transition: 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: {{ settings.primary_color }};
        }
        .popular-badge {
            background: {{ settings.secondary_color }};
            color: #1a1a1a;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 15px;
        }
        .price {
            font-size: 2rem;
            font-weight: 800;
            margin: 15px 0;
        }
        .feature-list {
            list-style: none;
            margin: 20px 0;
        }
        .feature-list li {
            padding: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .buy-btn {
            background: {{ settings.primary_color }};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 40px;
            width: 100%;
            cursor: pointer;
            font-weight: 600;
        }
        
        /* Contact Section */
        .contact-info {
            text-align: center;
            background: rgba(255,255,255,0.03);
            border-radius: 24px;
            padding: 40px;
        }
        .contact-info a {
            color: {{ settings.primary_color }};
            text-decoration: none;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .navbar .container { flex-direction: column; gap: 15px; }
            .hero h1 { font-size: 2rem; }
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
            <a href="#vps">VPS</a>
            <a href="#nitro">Nitro</a>
            <a href="#contact">Contact</a>
            <a href="/admin/login" class="admin-btn"><i class="fas fa-lock"></i> Admin</a>
        </div>
    </div>
</nav>

<section id="home" class="hero">
    <div class="container">
        <h1>Welcome to <span>{{ settings.website_name }}</span></h1>
        <p>{{ settings.hero_title }}<br>{{ settings.hero_subtitle }}</p>
        <a href="#vps" class="btn-primary">Get Started →</a>
    </div>
</section>

<section id="vps" class="section">
    <div class="container">
        <h2 class="section-title"><span>🚀</span> VPS Hosting Plans</h2>
        <div class="cards-grid">
            {% for plan in plans.VPS %}
            <div class="card">
                {% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}
                <h3>{{ plan.name }}</h3>
                <div class="price">{{ plan.price }}<small>/mo</small></div>
                <ul class="feature-list">
                    <li><i class="fas fa-microchip"></i> {{ plan.cpu }}</li>
                    <li><i class="fas fa-memory"></i> {{ plan.ram }}</li>
                    <li><i class="fas fa-hdd"></i> {{ plan.storage }}</li>
                </ul>
                <button class="buy-btn" onclick="alert('Order system coming soon! Contact support.')">Order Now →</button>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<section id="nitro" class="section">
    <div class="container">
        <h2 class="section-title"><span>💜</span> Discord Nitro</h2>
        <div class="cards-grid">
            {% for plan in plans.NITRO %}
            <div class="card">
                {% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}
                <h3>{{ plan.name }}</h3>
                <div class="price">{{ plan.price }}<small>/mo</small></div>
                <ul class="feature-list">
                    <li><i class="fab fa-discord"></i> {{ plan.features }}</li>
                </ul>
                <button class="buy-btn" onclick="alert('Order system coming soon! Contact support.')">Claim Now →</button>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<section id="contact" class="section">
    <div class="container">
        <h2 class="section-title"><span>📞</span> Contact Us</h2>
        <div class="contact-info">
            <p><i class="fas fa-envelope"></i> Email: <a href="mailto:{{ settings.contact_email }}">{{ settings.contact_email }}</a></p>
            <p><i class="fab fa-discord"></i> Discord: <a href="{{ settings.contact_discord }}" target="_blank">Join our Discord Server</a></p>
        </div>
    </div>
</section>

<footer class="footer">
    <div class="container">
        <p>{{ settings.footer_text }}</p>
    </div>
</footer>

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
            padding: 30px;
            overflow-y: auto;
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
        .color-preview {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            margin-top: 10px;
        }
        .success { background: #10B981; padding: 10px; border-radius: 12px; margin-bottom: 20px; }
        .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } .sidebar { width: 80px; padding: 15px; } .sidebar span { display: none; } }
    </style>
</head>
<body>
    <div class="admin-container">
        <div class="sidebar">
            <h2>⚙️ Admin</h2>
            <div class="nav-item active" data-tab="general"><i class="fas fa-sliders-h"></i> <span>General</span></div>
            <div class="nav-item" data-tab="colors"><i class="fas fa-palette"></i> <span>Colors</span></div>
            <div class="nav-item" data-tab="content"><i class="fas fa-edit"></i> <span>Content</span></div>
            <div class="nav-item" data-tab="plans"><i class="fas fa-box"></i> <span>Plans</span></div>
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
                        <label>Logo URL</label>
                        <input type="text" name="logo_url" value="{{ settings.logo_url }}">
                        <label>Favicon URL</label>
                        <input type="text" name="favicon_url" value="{{ settings.favicon_url }}">
                        <label>Footer Text</label>
                        <input type="text" name="footer_text" value="{{ settings.footer_text }}">
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
                            <div>
                                <label>Primary Color</label>
                                <input type="color" name="primary_color" value="{{ settings.primary_color }}">
                                <div class="color-preview" style="background:{{ settings.primary_color }}"></div>
                            </div>
                            <div>
                                <label>Secondary Color</label>
                                <input type="color" name="secondary_color" value="{{ settings.secondary_color }}">
                                <div class="color-preview" style="background:{{ settings.secondary_color }}"></div>
                            </div>
                            <div>
                                <label>Background Color</label>
                                <input type="color" name="background_color" value="{{ settings.background_color }}">
                            </div>
                            <div>
                                <label>Text Color</label>
                                <input type="color" name="text_color" value="{{ settings.text_color }}">
                            </div>
                        </div>
                        <button type="submit">Save Colors</button>
                    </form>
                    <div id="colorsMsg"></div>
                </div>
            </div>
            
            <div id="content-tab" style="display:none;">
                <div class="card">
                    <h3>📝 Content Settings</h3>
                    <form id="contentForm">
                        <label>Hero Title</label>
                        <input type="text" name="hero_title" value="{{ settings.hero_title }}">
                        <label>Hero Subtitle</label>
                        <input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle }}">
                        <label>Contact Email</label>
                        <input type="email" name="contact_email" value="{{ settings.contact_email }}">
                        <label>Discord Invite Link</label>
                        <input type="text" name="contact_discord" value="{{ settings.contact_discord }}">
                        <button type="submit">Save Content</button>
                    </form>
                    <div id="contentMsg"></div>
                </div>
            </div>
            
            <div id="plans-tab" style="display:none;">
                <div class="card">
                    <h3>📦 Manage VPS Plans</h3>
                    <div id="vpsPlansList">
                        {% for plan in plans.VPS %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.name }}</strong> - {{ plan.price }}/mo
                            <button onclick="editPlan('VPS', {{ loop.index0 }})" style="background:#F59E0B; padding:5px 15px; margin-left:10px;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('VPS')" style="margin-top:20px;">+ Add VPS Plan</button>
                </div>
                <div class="card">
                    <h3>💜 Manage Nitro Plans</h3>
                    <div id="nitroPlansList">
                        {% for plan in plans.NITRO %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.name }}</strong> - {{ plan.price }}/mo
                            <button onclick="editPlan('NITRO', {{ loop.index0 }})" style="background:#F59E0B; padding:5px 15px; margin-left:10px;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('NITRO')" style="margin-top:20px;">+ Add Nitro Plan</button>
                </div>
            </div>
            
            <div id="password-tab" style="display:none;">
                <div class="card">
                    <h3>🔐 Change Admin Password</h3>
                    <form id="passwordForm">
                        <label>Current Password</label>
                        <input type="password" name="current_password" required>
                        <label>New Password</label>
                        <input type="password" name="new_password" required>
                        <label>Confirm Password</label>
                        <input type="password" name="confirm_password" required>
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
        
        // General Form
        document.getElementById('generalForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const res = await fetch('/admin/api/save-general', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            document.getElementById('generalMsg').innerHTML = '<div class="success">✅ Settings saved! Page will refresh...</div>';
            setTimeout(() => location.reload(), 1000);
        });
        
        // Colors Form
        document.getElementById('colorsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const res = await fetch('/admin/api/save-colors', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            document.getElementById('colorsMsg').innerHTML = '<div class="success">✅ Colors saved! Page will refresh...</div>';
            setTimeout(() => location.reload(), 1000);
        });
        
        // Content Form
        document.getElementById('contentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const res = await fetch('/admin/api/save-content', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            document.getElementById('contentMsg').innerHTML = '<div class="success">✅ Content saved! Page will refresh...</div>';
            setTimeout(() => location.reload(), 1000);
        });
        
        // Password Form
        document.getElementById('passwordForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
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
        
        function editPlan(category, index) {
            const newName = prompt('Enter new plan name:');
            const newPrice = prompt('Enter new price (e.g., $10):');
            if (newName && newPrice) {
                fetch('/admin/api/edit-plan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category, index, name: newName, price: newPrice })
                }).then(() => location.reload());
            }
        }
        
        function addPlan(category) {
            const newName = prompt('Enter plan name:');
            const newPrice = prompt('Enter price (e.g., $15):');
            if (newName && newPrice) {
                fetch('/admin/api/add-plan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category, name: newName, price: newPrice })
                }).then(() => location.reload());
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
    return render_template_string(ADMIN_PANEL_TEMPLATE, settings=data['settings'], plans=data['plans'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

# API Routes for Admin
@app.route('/admin/api/save-general', methods=['POST'])
def save_general():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['website_name'] = request.json.get('website_name')
    data['settings']['logo_url'] = request.json.get('logo_url')
    data['settings']['favicon_url'] = request.json.get('favicon_url')
    data['settings']['footer_text'] = request.json.get('footer_text')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-colors', methods=['POST'])
def save_colors():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['primary_color'] = request.json.get('primary_color')
    data['settings']['secondary_color'] = request.json.get('secondary_color')
    data['settings']['background_color'] = request.json.get('background_color')
    data['settings']['text_color'] = request.json.get('text_color')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-content', methods=['POST'])
def save_content():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['hero_title'] = request.json.get('hero_title')
    data['settings']['hero_subtitle'] = request.json.get('hero_subtitle')
    data['settings']['contact_email'] = request.json.get('contact_email')
    data['settings']['contact_discord'] = request.json.get('contact_discord')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/change-password', methods=['POST'])
def change_password():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    current = request.json.get('current_password')
    new = request.json.get('new_password')
    if check_password_hash(data['admin']['password'], current):
        data['admin']['password'] = generate_password_hash(new)
        save_db(data)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Wrong password"}), 401

@app.route('/admin/api/edit-plan', methods=['POST'])
def edit_plan():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    index = request.json.get('index')
    name = request.json.get('name')
    price = request.json.get('price')
    if category in data['plans'] and 0 <= index < len(data['plans'][category]):
        data['plans'][category][index]['name'] = name
        data['plans'][category][index]['price'] = price
        save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/add-plan', methods=['POST'])
def add_plan():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    category = request.json.get('category')
    name = request.json.get('name')
    price = request.json.get('price')
    if category in data['plans']:
        if category == 'VPS':
            data['plans'][category].append({"name": name, "price": price, "cpu": "2 Core", "ram": "2GB", "storage": "50GB SSD", "popular": False})
        else:
            data['plans'][category].append({"name": name, "price": price, "features": "Premium features", "popular": False})
        save_db(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
