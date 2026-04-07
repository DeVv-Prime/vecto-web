# app.py - Prime Web Complete Integrated Platform (2000+ Lines)
import os
import json
import secrets
import requests
import threading
import asyncio
import hashlib
import hmac
import time
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, render_template_string, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import discord
from discord.ext import commands, tasks
from discord import app_commands
import nest_asyncio

nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(64))
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

DB_FILE = 'primeweb_data.json'
bot_instance = None
bot_thread = None
bot_running = False

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {
        "admin": {
            "email": "admin@primeweb.com",
            "password": generate_password_hash("admin123"),
            "main_admin_id": None,
            "main_admin_dm": True,
            "created_at": datetime.now().isoformat()
        },
        "bot_config": {
            "bot_token": "",
            "bot_status": "stopped",
            "bot_presence": "online",
            "bot_activity": "Prime Web",
            "bot_activity_type": "watching",
            "webhook_url": "",
            "webhook_channel_id": "",
            "webhook_enabled": False,
            "approval_buttons": True,
            "dm_admin_on_order": True,
            "welcome_message": "Welcome to Prime Web! Use /help for commands.",
            "embed_color": 0x4F46E5,
            "support_channel_id": None,
            "ticket_category_id": None
        },
        "payment_config": {
            "upi_id": "primeweb@okhdfcbank",
            "upi_qr_url": "",
            "bank_name": "Prime Bank",
            "account_number": "XXXXXXXXXX1234",
            "ifsc_code": "PRIME123",
            "payment_instructions": "Send payment to the UPI ID above and share screenshot for confirmation.",
            "auto_approve": False
        },
        "settings": {
            "website_name": "Prime Web",
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
            "footer_text": "© 2024 Prime Web. All rights reserved.",
            "footer_copyright": "Prime Web",
            "contact_email": "support@primeweb.com",
            "contact_discord": "https://discord.gg/primeweb",
            "contact_twitter": "",
            "contact_github": "",
            "newsletter_enabled": True,
            "newsletter_text": "Subscribe to our newsletter for updates and exclusive offers",
            "testimonials_enabled": True,
            "social_links_enabled": True
        },
        "plans": {
            "VPS": [
                {"id": "vps_mini", "name": "VPS Mini", "price": 5, "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "popular": False, "icon": "🖥️", "stock": 50},
                {"id": "vps_standard", "name": "VPS Standard", "price": 20, "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "popular": True, "icon": "⚡", "stock": 30},
                {"id": "vps_pro", "name": "VPS Pro", "price": 80, "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "popular": False, "icon": "🚀", "stock": 15}
            ],
            "NITRO": [
                {"id": "nitro_basic", "name": "Nitro Basic", "price": 3, "features": "Custom Emojis, HD Streaming, Profile Badge", "popular": False, "icon": "💜", "stock": 100},
                {"id": "nitro_full", "name": "Nitro Full", "price": 10, "features": "4K Streaming, 2 Boosts, 500MB Upload", "popular": True, "icon": "✨", "stock": 50},
                {"id": "boost_1", "name": "Server Boost", "price": 4, "features": "1 Server Boost, Server Perks", "popular": False, "icon": "⚡", "stock": 200}
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
        "cart": {},
        "tickets": [],
        "users": {},
        "audit_logs": []
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_discord_webhook(webhook_url, title, description, color=0x4F46E5, fields=None, buttons=None):
    if not webhook_url:
        return False
    try:
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Prime Web - Premium Digital Services"}
        }
        if fields:
            embed["fields"] = fields
        
        payload = {"embeds": [embed]}
        
        if buttons:
            components = [{
                "type": 1,
                "components": [
                    {"type": 2, "style": 3, "label": btn["label"], "custom_id": btn["custom_id"], "emoji": {"name": btn["emoji"]}}
                    for btn in buttons
                ]
            }]
            payload["components"] = components
        
        response = requests.post(webhook_url, json=payload)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Webhook error: {e}")
        return False

# ==================== DISCORD BOT ====================
class PrimeWebBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix='/', intents=intents, help_command=None)
    
    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Bot commands synced!")
    
    async def on_ready(self):
        print(f'✅ Bot is online! Logged in as {self.user}')
        print(f'📊 Serving {len(self.guilds)} guilds')
        
        data = load_db()
        presence = data['bot_config'].get('bot_presence', 'online')
        activity_type = data['bot_config'].get('bot_activity_type', 'watching')
        activity_name = data['bot_config'].get('bot_activity', 'Prime Web')
        
        activity_map = {
            'watching': discord.ActivityType.watching,
            'playing': discord.ActivityType.playing,
            'listening': discord.ActivityType.listening,
            'competing': discord.ActivityType.competing
        }
        
        activity = discord.Activity(type=activity_map.get(activity_type, discord.ActivityType.watching), name=activity_name)
        status_map = {'online': discord.Status.online, 'idle': discord.Status.idle, 'dnd': discord.Status.dnd, 'invisible': discord.Status.invisible}
        await self.change_presence(activity=activity, status=status_map.get(presence, discord.Status.online))
        
        data['bot_config']['bot_status'] = 'online'
        data['bot_config']['bot_enabled'] = True
        save_db(data)
        
        # Start background tasks
        self.update_status.start()
    
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Use `/help` to see available commands.")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
    
    @tasks.loop(minutes=5)
    async def update_status(self):
        """Update bot status every 5 minutes"""
        data = load_db()
        activity_name = data['bot_config'].get('bot_activity', 'Prime Web')
        activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
        await self.change_presence(activity=activity)

def create_bot_instance():
    bot = PrimeWebBot()
    
    # ==================== BASIC COMMANDS ====================
    @bot.tree.command(name="ping", description="Check bot latency")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", description=f"Latency: `{latency}ms`\nWebSocket: `{latency}ms`", color=0x4F46E5)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="plans", description="View all hosting plans (syncs with website)")
    async def plans(interaction: discord.Interaction):
        data = load_db()
        embed = discord.Embed(title="📦 Available Plans", description="Here are our current hosting plans:", color=data['bot_config'].get('embed_color', 0x4F46E5))
        
        vps_plans = data['plans'].get('VPS', [])
        vps_text = "\n".join([f"• **${p['price']}/mo** - {p['name']}\n  └ {p['cpu']} | {p['ram']} | {p['storage']}" for p in vps_plans])
        embed.add_field(name="🖥️ VPS Hosting", value=vps_text or "No plans available", inline=False)
        
        nitro_plans = data['plans'].get('NITRO', [])
        nitro_text = "\n".join([f"• **${p['price']}/mo** - {p['name']}\n  └ {p['features']}" for p in nitro_plans])
        embed.add_field(name="💜 Discord Nitro", value=nitro_text or "No plans available", inline=False)
        
        embed.set_footer(text="Visit our website to purchase! Use /website for link")
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="website", description="Get website link")
    async def website(interaction: discord.Interaction):
        data = load_db()
        embed = discord.Embed(title="🌐 Prime Web Website", description=f"[Click here to visit](http://localhost:5000)", color=data['bot_config'].get('embed_color', 0x4F46E5))
        embed.add_field(name="Features", value="• VPS Hosting\n• Discord Nitro\n• 24/7 Support\n• Instant Setup", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="support", description="Get support link")
    async def support(interaction: discord.Interaction):
        data = load_db()
        embed = discord.Embed(title="🎫 Support", description=f"Join our Discord server for support:\n{data['settings']['contact_discord']}", color=data['bot_config'].get('embed_color', 0x4F46E5))
        embed.add_field(name="Support Hours", value="24/7 - We're always here to help!", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="status", description="Change bot status (Admin only)")
    @app_commands.describe(status="online, idle, dnd, invisible")
    async def status_cmd(interaction: discord.Interaction, status: str):
        data = load_db()
        admin_id = data['admin'].get('main_admin_id')
        if interaction.user.id != admin_id:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        valid_status = ['online', 'idle', 'dnd', 'invisible']
        if status not in valid_status:
            await interaction.response.send_message(f"❌ Invalid status! Choose from: {', '.join(valid_status)}", ephemeral=True)
            return
        
        data['bot_config']['bot_presence'] = status
        save_db(data)
        
        status_map = {'online': discord.Status.online, 'idle': discord.Status.idle, 'dnd': discord.Status.dnd, 'invisible': discord.Status.invisible}
        await bot.change_presence(status=status_map[status])
        await interaction.response.send_message(f"✅ Bot status changed to **{status}**!")
    
    @bot.tree.command(name="activity", description="Change bot activity (Admin only)")
    @app_commands.describe(activity_type="watching, playing, listening", name="Activity name")
    async def activity_cmd(interaction: discord.Interaction, activity_type: str, name: str):
        data = load_db()
        admin_id = data['admin'].get('main_admin_id')
        if interaction.user.id != admin_id:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        valid_types = ['watching', 'playing', 'listening', 'competing']
        if activity_type not in valid_types:
            await interaction.response.send_message(f"❌ Invalid type! Choose from: {', '.join(valid_types)}", ephemeral=True)
            return
        
        data['bot_config']['bot_activity_type'] = activity_type
        data['bot_config']['bot_activity'] = name
        save_db(data)
        
        type_map = {'watching': discord.ActivityType.watching, 'playing': discord.ActivityType.playing, 'listening': discord.ActivityType.listening, 'competing': discord.ActivityType.competing}
        activity = discord.Activity(type=type_map[activity_type], name=name)
        await bot.change_presence(activity=activity)
        await interaction.response.send_message(f"✅ Bot activity changed to **{activity_type} {name}**!")
    
    @bot.tree.command(name="help", description="Show all commands")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Prime Web Bot Commands", description="Here are all available commands:", color=0x4F46E5)
        commands_list = [
            "**/ping** - Check bot latency",
            "**/plans** - View hosting plans (syncs with website)",
            "**/website** - Get website link",
            "**/support** - Get support link",
            "**/status** <status> - Change bot status (Admin)",
            "**/activity** <type> <name> - Change bot activity (Admin)",
            "**/ticket** - Create a support ticket",
            "**/close** - Close current ticket",
            "**/server** <action> - Server management",
            "**/help** - Show this menu"
        ]
        embed.add_field(name="📋 Commands", value="\n".join(commands_list), inline=False)
        embed.set_footer(text="Prime Web - Premium Digital Services")
        await interaction.response.send_message(embed=embed)
    
    # ==================== TICKET SYSTEM ====================
    @bot.tree.command(name="ticket", description="Create a support ticket")
    async def ticket(interaction: discord.Interaction):
        data = load_db()
        support_channel_id = data['bot_config'].get('support_channel_id')
        ticket_category_id = data['bot_config'].get('ticket_category_id')
        
        category = None
        if ticket_category_id:
            category = discord.utils.get(interaction.guild.categories, id=int(ticket_category_id))
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name}-{secrets.token_hex(4)}",
            category=category,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title="🎫 Support Ticket Created",
            description=f"Hello {interaction.user.mention},\n\nPlease describe your issue and a staff member will assist you shortly.",
            color=0x4F46E5,
            timestamp=datetime.now()
        )
        embed.add_field(name="📌 Instructions", value="1. Explain your issue in detail\n2. Attach any relevant screenshots\n3. Wait for staff response", inline=False)
        embed.set_footer(text=f"Ticket ID: {secrets.token_hex(8)}")
        
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(f"{interaction.user.mention} Staff will be with you shortly!")
        
        data['tickets'].append({
            "channel_id": ticket_channel.id,
            "user_id": interaction.user.id,
            "created_at": datetime.now().isoformat(),
            "status": "open"
        })
        save_db(data)
        
        await interaction.response.send_message(f"✅ Support ticket created! Check {ticket_channel.mention}", ephemeral=True)
    
    @bot.tree.command(name="close", description="Close current ticket")
    async def close_ticket(interaction: discord.Interaction):
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return
        
        embed = discord.Embed(title="🔒 Ticket Closing", description="This ticket will be closed in 5 seconds...", color=0xF59E0B)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()
    
    # ==================== SERVER MANAGEMENT ====================
    @bot.tree.command(name="server", description="Server management commands")
    @app_commands.describe(action="start, stop, restart, status")
    async def server_cmd(interaction: discord.Interaction, action: str):
        data = load_db()
        admin_id = data['admin'].get('main_admin_id')
        if interaction.user.id != admin_id:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        valid_actions = ['start', 'stop', 'restart', 'status']
        if action not in valid_actions:
            await interaction.response.send_message(f"❌ Invalid action! Choose from: {', '.join(valid_actions)}", ephemeral=True)
            return
        
        embed = discord.Embed(title="🖥️ Server Management", description=f"Action: **{action.upper()}**\nStatus: Processing...", color=0x4F46E5)
        await interaction.response.send_message(embed=embed)
        
        # Simulate server action (would connect to actual server API)
        await asyncio.sleep(2)
        
        embed.description = f"Action: **{action.upper()}**\nStatus: ✅ Completed successfully!"
        await interaction.edit_original_response(embed=embed)
    
    # ==================== USER INFO ====================
    @bot.tree.command(name="userinfo", description="Get user information")
    async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"👤 User Info - {member.name}", color=0x4F46E5, timestamp=datetime.now())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Roles", value=", ".join([r.mention for r in member.roles[1:5]]) or "None", inline=False)
        await interaction.response.send_message(embed=embed)
    
    return bot

def run_bot():
    global bot_running
    data = load_db()
    token = data['bot_config'].get('bot_token', '')
    if not token or token == "":
        print("❌ No bot token found! Please set token in admin panel.")
        return
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = create_bot_instance()
    bot_running = True
    
    try:
        loop.run_until_complete(bot.start(token))
    except Exception as e:
        print(f"❌ Bot error: {e}")
        data = load_db()
        data['bot_config']['bot_status'] = 'error'
        data['bot_config']['bot_enabled'] = False
        save_db(data)
        bot_running = False
    finally:
        bot_running = False

def start_bot_thread():
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        return False
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    return True

def stop_bot():
    global bot_running
    bot_running = False
    return True

# ==================== WEBSITE TEMPLATE ====================
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
        @keyframes float {
            0%,100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes pulse {
            0%,100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .animate { animation: fadeInUp 0.6s ease forwards; opacity: 0; }
        .delay-1 { animation-delay: 0.1s; }
        .delay-2 { animation-delay: 0.2s; }
        .delay-3 { animation-delay: 0.3s; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        
        /* Navbar */
        .navbar {
            padding: 20px 0;
            position: sticky;
            top: 0;
            background: rgba(10,10,10,0.95);
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
        .admin-btn:hover { opacity: 0.9; color: white !important; transform: translateY(-2px); }
        
        /* Hero Section */
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
        
        /* Stats Section */
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
        
        /* Features Section */
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
        
        /* Plans Grid */
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
        
        /* Testimonials */
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
        
        /* Newsletter */
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
        
        /* Toast */
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
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Footer */
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
            .cart-sidebar { width: 100%; right: -100%; }
            .newsletter { padding: 30px; }
        }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container">
        <div class="logo" onclick="window.location.href='/'">
            <img src="{{ settings.logo_url }}" alt="logo" onerror="this.src='https://img.icons8.com/fluency/96/admin-settings-male.png'">
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
                <div class="plan-price">${{ plan.price }}<small>/mo</small></div>
                <ul class="plan-features">
                    <li><i class="fas fa-microchip"></i> {{ plan.cpu }}</li>
                    <li><i class="fas fa-memory"></i> {{ plan.ram }}</li>
                    <li><i class="fas fa-hdd"></i> {{ plan.storage }}</li>
                    <li><i class="fas fa-globe"></i> {{ plan.bandwidth }}</li>
                </ul>
                <button class="buy-btn" onclick="addToCart('{{ plan.id }}', '{{ plan.name }}', {{ plan.price }}, '{{ plan.icon }}')">Add to Cart →</button>
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
                <ul class="plan-features">
                    <li><i class="fab fa-discord"></i> {{ plan.features }}</li>
                </ul>
                <button class="buy-btn" onclick="addToCart('{{ plan.id }}', '{{ plan.name }}', {{ plan.price }}, '{{ plan.icon }}')">Add to Cart →</button>
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
    let cart = JSON.parse(localStorage.getItem('cart') || '{}');
    
    function updateCartDisplay() {
        let count = 0;
        let total = 0;
        let html = '';
        for (let id in cart) {
            count += cart[id].quantity;
            total += cart[id].price * cart[id].quantity;
            html += `<div class="cart-item">
                <div><span style="font-size:1.5rem;">${cart[id].icon}</span> ${cart[id].name} x${cart[id].quantity}</div>
                <div>$${cart[id].price * cart[id].quantity} <button class="cart-item-remove" onclick="removeFromCart('${id}')">Remove</button></div>
            </div>`;
        }
        document.getElementById('cartCount').innerText = count;
        document.getElementById('cartItems').innerHTML = html || '<p>Cart is empty</p>';
        document.getElementById('cartTotal').innerHTML = `<strong>Total: $${total}</strong>`;
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
            items.push({ id, name: cart[id].name, price: cart[id].price, quantity: cart[id].quantity });
            total += cart[id].price * cart[id].quantity;
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
                observer.unobserve(entry.target);
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
    <title>Prime Web Admin Login</title>
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
        <h1>🔐 Prime Web Admin</h1>
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
    <title>Prime Web Admin Panel</title>
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
        .bot-status {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
        }
        .status-online { background: #10B981; }
        .status-offline { background: #EF4444; }
        .order-item { border-bottom: 1px solid rgba(255,255,255,0.1); padding: 15px 0; }
        .badge-pending { background: #F59E0B; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-approved { background: #10B981; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
        .badge-rejected { background: #EF4444; padding: 4px 8px; border-radius: 20px; font-size: 0.7rem; }
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
            <h2>⚙️ Prime Web</h2>
            <div class="nav-item active" data-tab="dashboard"><i class="fas fa-tachometer-alt"></i> <span>Dashboard</span></div>
            <div class="nav-item" data-tab="bot"><i class="fab fa-discord"></i> <span>Bot Control</span></div>
            <div class="nav-item" data-tab="plans"><i class="fas fa-box"></i> <span>Plans</span></div>
            <div class="nav-item" data-tab="payment"><i class="fas fa-credit-card"></i> <span>Payment</span></div>
            <div class="nav-item" data-tab="orders"><i class="fas fa-shopping-cart"></i> <span>Orders</span></div>
            <div class="nav-item" data-tab="settings"><i class="fas fa-sliders-h"></i> <span>Settings</span></div>
            <div class="nav-item" data-tab="features"><i class="fas fa-star"></i> <span>Features</span></div>
            <div class="nav-item" data-tab="testimonials"><i class="fas fa-comment"></i> <span>Testimonials</span></div>
            <div class="nav-item" data-tab="password"><i class="fas fa-key"></i> <span>Password</span></div>
            <div class="nav-item" onclick="window.location.href='/admin/logout'"><i class="fas fa-sign-out-alt"></i> <span>Logout</span></div>
        </div>
        
        <div class="main-content">
            <!-- Dashboard Tab -->
            <div id="dashboard-tab">
                <div class="card">
                    <h3>📊 Dashboard Stats</h3>
                    <div class="grid-2">
                        <div><h2>{{ orders|length }}</h2><p>Total Orders</p></div>
                        <div><h2>{{ plans.VPS|length + plans.NITRO|length }}</h2><p>Total Plans</p></div>
                        <div><h2>{{ features|length }}</h2><p>Features</p></div>
                        <div><h2>{{ testimonials|length }}</h2><p>Testimonials</p></div>
                    </div>
                </div>
                <div class="card">
                    <h3>🤖 Bot Status</h3>
                    <p>Status: <span class="bot-status {% if bot_config.bot_status == 'online' %}status-online{% else %}status-offline{% endif %}">{{ bot_config.bot_status|upper }}</span></p>
                    <p>Token: {% if bot_config.bot_token %}✅ Configured{% else %}❌ Not Set{% endif %}</p>
                    <p>Presence: {{ bot_config.bot_presence|upper }}</p>
                    <p>Activity: {{ bot_config.bot_activity_type }} {{ bot_config.bot_activity }}</p>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button onclick="startBot()" style="background:#10B981;">▶️ Start Bot</button>
                        <button onclick="stopBot()" style="background:#EF4444;">⏹️ Stop Bot</button>
                    </div>
                    <div id="botMsg"></div>
                </div>
            </div>
            
            <!-- Bot Control Tab -->
            <div id="bot-tab" style="display:none;">
                <div class="card">
                    <h3>🤖 Discord Bot Configuration</h3>
                    <form id="botForm">
                        <label>Bot Token</label>
                        <input type="password" name="bot_token" value="{{ bot_config.bot_token }}" placeholder="Discord Bot Token">
                        <label>Bot Presence</label>
                        <select name="bot_presence">
                            <option value="online" {% if bot_config.bot_presence == 'online' %}selected{% endif %}>🟢 Online</option>
                            <option value="idle" {% if bot_config.bot_presence == 'idle' %}selected{% endif %}>🟡 Idle</option>
                            <option value="dnd" {% if bot_config.bot_presence == 'dnd' %}selected{% endif %}>🔴 Do Not Disturb</option>
                            <option value="invisible" {% if bot_config.bot_presence == 'invisible' %}selected{% endif %}>👻 Invisible</option>
                        </select>
                        <label>Activity Type</label>
                        <select name="bot_activity_type">
                            <option value="watching" {% if bot_config.bot_activity_type == 'watching' %}selected{% endif %}>Watching</option>
                            <option value="playing" {% if bot_config.bot_activity_type == 'playing' %}selected{% endif %}>Playing</option>
                            <option value="listening" {% if bot_config.bot_activity_type == 'listening' %}selected{% endif %}>Listening</option>
                            <option value="competing" {% if bot_config.bot_activity_type == 'competing' %}selected{% endif %}>Competing</option>
                        </select>
                        <label>Activity Name</label>
                        <input type="text" name="bot_activity" value="{{ bot_config.bot_activity }}">
                        <label>Webhook URL (for order notifications)</label>
                        <input type="text" name="webhook_url" value="{{ bot_config.webhook_url }}" placeholder="Discord Webhook URL">
                        <label>Main Admin ID (for DM notifications)</label>
                        <input type="text" name="main_admin_id" value="{{ admin.main_admin_id or '' }}" placeholder="Your Discord User ID">
                        <label>Support Channel ID</label>
                        <input type="text" name="support_channel_id" value="{{ bot_config.support_channel_id or '' }}" placeholder="Channel ID for tickets">
                        <label>Embed Color (Hex)</label>
                        <input type="color" name="embed_color" value="{{ '#' + bot_config.embed_color|string if bot_config.embed_color else '#4F46E5' }}">
                        <button type="submit">Save Bot Settings</button>
                    </form>
                    <div id="botConfigMsg"></div>
                </div>
                <div class="card">
                    <h3>📖 Bot Commands Available</h3>
                    <ul style="margin-left: 20px; line-height: 1.8;">
                        <li><code>/ping</code> - Check bot latency</li>
                        <li><code>/plans</code> - View all hosting plans (syncs with website)</li>
                        <li><code>/website</code> - Get website link</li>
                        <li><code>/support</code> - Get support link</li>
                        <li><code>/status &lt;status&gt;</code> - Change bot status (Admin)</li>
                        <li><code>/activity &lt;type&gt; &lt;name&gt;</code> - Change bot activity (Admin)</li>
                        <li><code>/ticket</code> - Create a support ticket</li>
                        <li><code>/close</code> - Close current ticket</li>
                        <li><code>/server &lt;action&gt;</code> - Server management (Admin)</li>
                        <li><code>/userinfo [member]</code> - Get user information</li>
                        <li><code>/help</code> - Show all commands</li>
                    </ul>
                </div>
            </div>
            
            <!-- Plans Tab -->
            <div id="plans-tab" style="display:none;">
                <div class="card">
                    <h3>📦 VPS Plans</h3>
                    <div id="vpsPlans">
                        {% for plan in plans.VPS %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.icon }} {{ plan.name }}</strong> - ${{ plan.price }}/mo
                            <p style="color:#A1A1AA; font-size:0.8rem;">{{ plan.cpu }} | {{ plan.ram }} | {{ plan.storage }} | {{ plan.bandwidth }}</p>
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
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ plan.icon }} {{ plan.name }}</strong> - ${{ plan.price }}/mo
                            <p style="color:#A1A1AA; font-size:0.8rem;">{{ plan.features }}</p>
                            <button onclick="editPlan('NITRO', {{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addPlan('NITRO')">+ Add Nitro Plan</button>
                </div>
            </div>
            
            <!-- Payment Tab -->
            <div id="payment-tab" style="display:none;">
                <div class="card">
                    <h3>💳 Payment Configuration</h3>
                    <form id="paymentForm">
                        <label>UPI ID</label>
                        <input type="text" name="upi_id" value="{{ payment_config.upi_id }}" placeholder="yourname@okhdfcbank">
                        <label>UPI QR Code URL</label>
                        <input type="text" name="upi_qr_url" value="{{ payment_config.upi_qr_url }}" placeholder="https://...">
                        <label>Bank Name</label>
                        <input type="text" name="bank_name" value="{{ payment_config.bank_name }}">
                        <label>Account Number</label>
                        <input type="text" name="account_number" value="{{ payment_config.account_number }}">
                        <label>IFSC Code</label>
                        <input type="text" name="ifsc_code" value="{{ payment_config.ifsc_code }}">
                        <label>Payment Instructions</label>
                        <textarea name="payment_instructions" rows="3">{{ payment_config.payment_instructions }}</textarea>
                        <label>Auto Approve Orders</label>
                        <select name="auto_approve">
                            <option value="True" {% if payment_config.auto_approve %}selected{% endif %}>Yes</option>
                            <option value="False" {% if not payment_config.auto_approve %}selected{% endif %}>No</option>
                        </select>
                        <button type="submit">Save Payment Settings</button>
                    </form>
                    <div id="paymentMsg"></div>
                </div>
            </div>
            
            <!-- Orders Tab -->
            <div id="orders-tab" style="display:none;">
                <div class="card">
                    <h3>📋 Pending Orders</h3>
                    <div id="pendingOrders">
                        {% for order in orders if order.status == 'pending' %}
                        <div class="order-item">
                            <strong>🆔 {{ order.id }}</strong> <span class="badge-pending">PENDING</span>
                            <p>👤 {{ order.customer_name }} | Discord: {{ order.discord_id }}</p>
                            <p>💰 Total: ${{ order.total }}</p>
                            <p>📅 {{ order.date[:19] if order.date else 'Just now' }}</p>
                            <div style="margin-top: 10px;">
                                <button onclick="approveOrder('{{ order.id }}')" style="background:#10B981;">✅ Approve</button>
                                <button onclick="rejectOrder('{{ order.id }}')" style="background:#EF4444;">❌ Reject</button>
                                <button onclick="contactCustomer('{{ order.discord_id }}')" style="background:#5865F2;">💬 Contact</button>
                            </div>
                        </div>
                        {% else %}
                        <p>No pending orders</p>
                        {% endfor %}
                    </div>
                </div>
                <div class="card">
                    <h3>📦 All Orders History</h3>
                    <div id="allOrders">
                        {% for order in orders %}
                        <div class="order-item">
                            <strong>{{ order.id }}</strong> - {{ order.customer_name }} - ${{ order.total }}
                            <span class="badge-{{ order.status }}">{{ order.status|upper }}</span>
                            <p style="font-size:0.7rem;">{{ order.date[:19] if order.date else 'Unknown' }}</p>
                        </div>
                        {% else %}
                        <p>No orders yet</p>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Settings Tab -->
            <div id="settings-tab" style="display:none;">
                <div class="card">
                    <h3>🎨 Website Settings</h3>
                    <form id="settingsForm">
                        <div class="grid-2">
                            <div>
                                <label>Website Name</label>
                                <input type="text" name="website_name" value="{{ settings.website_name }}">
                                <label>Website Tagline</label>
                                <input type="text" name="website_tagline" value="{{ settings.website_tagline }}">
                                <label>Logo URL</label>
                                <input type="text" name="logo_url" value="{{ settings.logo_url }}">
                                <label>Favicon URL</label>
                                <input type="text" name="favicon_url" value="{{ settings.favicon_url }}">
                                <label>Primary Color</label>
                                <input type="color" name="primary_color" value="{{ settings.primary_color }}">
                                <label>Background Color</label>
                                <input type="color" name="background_color" value="{{ settings.background_color }}">
                            </div>
                            <div>
                                <label>Hero Title</label>
                                <input type="text" name="hero_title" value="{{ settings.hero_title }}">
                                <label>Hero Subtitle</label>
                                <input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle }}">
                                <label>Hero Button Text</label>
                                <input type="text" name="hero_button_text" value="{{ settings.hero_button_text }}">
                                <label>Hero Background Image</label>
                                <input type="text" name="hero_bg_image" value="{{ settings.hero_bg_image }}">
                                <label>Contact Email</label>
                                <input type="email" name="contact_email" value="{{ settings.contact_email }}">
                                <label>Discord Invite</label>
                                <input type="text" name="contact_discord" value="{{ settings.contact_discord }}">
                            </div>
                        </div>
                        <button type="submit">Save All Settings</button>
                    </form>
                    <div id="settingsMsg"></div>
                </div>
                <div class="card">
                    <h3>📊 Statistics Settings</h3>
                    <form id="statsForm">
                        <div class="grid-2">
                            <div><label>Customers Count</label><input type="text" name="stats_customers" value="{{ settings.stats_customers }}"></div>
                            <div><label>Uptime Percentage</label><input type="text" name="stats_uptime" value="{{ settings.stats_uptime }}"></div>
                            <div><label>Rating</label><input type="text" name="stats_rating" value="{{ settings.stats_rating }}"></div>
                            <div><label>Servers Count</label><input type="text" name="stats_servers" value="{{ settings.stats_servers }}"></div>
                        </div>
                        <button type="submit">Save Statistics</button>
                    </form>
                    <div id="statsMsg"></div>
                </div>
            </div>
            
            <!-- Features Tab -->
            <div id="features-tab" style="display:none;">
                <div class="card">
                    <h3>✨ Features Section</h3>
                    <form id="featuresTitleForm">
                        <label>Features Title</label>
                        <input type="text" name="features_title" value="{{ settings.features_title }}">
                        <label>Features Subtitle</label>
                        <input type="text" name="features_subtitle" value="{{ settings.features_subtitle }}">
                        <button type="submit">Save Title</button>
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
            
            <!-- Testimonials Tab -->
            <div id="testimonials-tab" style="display:none;">
                <div class="card">
                    <h3>⭐ Testimonials Settings</h3>
                    <form id="testimonialsForm">
                        <label>Show Testimonials</label>
                        <select name="testimonials_enabled">
                            <option value="True" {% if settings.testimonials_enabled %}selected{% endif %}>Yes</option>
                            <option value="False" {% if not settings.testimonials_enabled %}selected{% endif %}>No</option>
                        </select>
                        <button type="submit">Save</button>
                    </form>
                </div>
                <div class="card">
                    <h3>Manage Testimonials</h3>
                    <div id="testimonialsList">
                        {% for t in testimonials %}
                        <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding:15px 0;">
                            <strong>{{ t.name }}</strong> - {{ t.role }}
                            <p>"{{ t.content }}"</p>
                            <div class="testimonial-stars">{% for i in range(t.rating) %}⭐{% endfor %}</div>
                            <button onclick="editTestimonial({{ loop.index0 }})" style="background:#F59E0B;">Edit</button>
                            <button onclick="deleteTestimonial({{ loop.index0 }})" style="background:#EF4444;">Delete</button>
                        </div>
                        {% endfor %}
                    </div>
                    <button onclick="addTestimonial()">+ Add Testimonial</button>
                </div>
            </div>
            
            <!-- Password Tab -->
            <div id="password-tab" style="display:none;">
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
        
        async function postData(url, data, msgElement) {
            const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            if(msgElement) msgElement.innerHTML = '<div class="success">✅ Saved! Refreshing...</div>';
            setTimeout(() => location.reload(), 1000);
        }
        
        function startBot() {
            fetch('/admin/api/start-bot', { method: 'POST' }).then(() => {
                document.getElementById('botMsg').innerHTML = '<div class="success">✅ Bot starting...</div>';
                setTimeout(() => location.reload(), 2000);
            });
        }
        
        function stopBot() {
            fetch('/admin/api/stop-bot', { method: 'POST' }).then(() => {
                document.getElementById('botMsg').innerHTML = '<div class="success">⏹️ Bot stopping...</div>';
                setTimeout(() => location.reload(), 2000);
            });
        }
        
        document.getElementById('botForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            data.main_admin_id = parseInt(data.main_admin_id) || null;
            data.embed_color = parseInt(data.embed_color.replace('#', ''), 16) || 0x4F46E5;
            postData('/admin/api/save-bot', data, document.getElementById('botConfigMsg'));
        });
        
        document.getElementById('paymentForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            data.auto_approve = data.auto_approve === 'True';
            postData('/admin/api/save-payment', data, document.getElementById('paymentMsg'));
        });
        
        document.getElementById('settingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            postData('/admin/api/save-settings', Object.fromEntries(new FormData(e.target)), document.getElementById('settingsMsg'));
        });
        
        document.getElementById('statsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            postData('/admin/api/save-stats', Object.fromEntries(new FormData(e.target)), document.getElementById('statsMsg'));
        });
        
        document.getElementById('featuresTitleForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            postData('/admin/api/save-features-title', Object.fromEntries(new FormData(e.target)));
        });
        
        document.getElementById('testimonialsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            postData('/admin/api/save-testimonials-settings', Object.fromEntries(new FormData(e.target)));
        });
        
        document.getElementById('passwordForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(e.target));
            if(data.new_password !== data.confirm_password) {
                document.getElementById('passwordMsg').innerHTML = '<div class="success" style="background:#EF4444;">❌ Passwords do not match</div>';
                return;
            }
            const res = await fetch('/admin/api/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            const result = await res.json();
            document.getElementById('passwordMsg').innerHTML = result.success ? '<div class="success">✅ Password changed!</div>' : '<div class="success" style="background:#EF4444;">❌ Current password incorrect</div>';
        });
        
        // Plan management
        function editPlan(cat, idx) {
            const name = prompt('New plan name:');
            const price = prompt('New price (number only):');
            if(name && price) {
                fetch('/admin/api/edit-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, index: idx, name, price: parseInt(price) }) })
                    .then(() => location.reload());
            }
        }
        
        function addPlan(cat) {
            const name = prompt('Plan name:');
            const price = prompt('Price (number only):');
            if(name && price) {
                fetch('/admin/api/add-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat, name, price: parseInt(price) }) })
                    .then(() => location.reload());
            }
        }
        
        // Feature management
        function editFeature(idx) {
            const title = prompt('Feature title:');
            const desc = prompt('Feature description:');
            if(title && desc) {
                fetch('/admin/api/edit-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx, title, description: desc }) })
                    .then(() => location.reload());
            }
        }
        
        function deleteFeature(idx) {
            if(confirm('Delete this feature?')) {
                fetch('/admin/api/delete-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx }) })
                    .then(() => location.reload());
            }
        }
        
        function addFeature() {
            const title = prompt('Feature title:');
            const desc = prompt('Feature description:');
            if(title && desc) {
                fetch('/admin/api/add-feature', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, description: desc, icon: '✨' }) })
                    .then(() => location.reload());
            }
        }
        
        // Testimonial management
        function editTestimonial(idx) {
            const name = prompt('Customer name:');
            const content = prompt('Testimonial content:');
            if(name && content) {
                fetch('/admin/api/edit-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx, name, content }) })
                    .then(() => location.reload());
            }
        }
        
        function deleteTestimonial(idx) {
            if(confirm('Delete this testimonial?')) {
                fetch('/admin/api/delete-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ index: idx }) })
                    .then(() => location.reload());
            }
        }
        
        function addTestimonial() {
            const name = prompt('Customer name:');
            const content = prompt('Testimonial content:');
            if(name && content) {
                fetch('/admin/api/add-testimonial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, content, role: 'Customer' }) })
                    .then(() => location.reload());
            }
        }
        
        // Order management
        function approveOrder(id) {
            fetch('/admin/api/approve-order/' + id, { method: 'POST' }).then(() => location.reload());
        }
        
        function rejectOrder(id) {
            fetch('/admin/api/reject-order/' + id, { method: 'POST' }).then(() => location.reload());
        }
        
        function contactCustomer(discordId) {
            if(discordId && discordId !== 'N/A') {
                window.open('https://discord.com/users/' + discordId, '_blank');
            } else {
                alert('No Discord ID provided for this customer');
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
    
    # Send webhook notification if configured
    webhook_url = data['bot_config'].get('webhook_url')
    if webhook_url:
        items_text = "\n".join([f"• {item['quantity']}x {item['name']} - ${item['price']}" for item in order['items']])
        description = f"**Order ID:** `{order_id}`\n**Customer:** {order['customer_name']}\n**Discord ID:** {order['discord_id']}\n\n**Items:**\n{items_text}\n\n**Total:** ${order['total']}"
        buttons = [
            {"label": "✅ Approve", "custom_id": f"approve_{order_id}", "emoji": "✅"},
            {"label": "❌ Reject", "custom_id": f"reject_{order_id}", "emoji": "❌"}
        ] if data['bot_config'].get('approval_buttons', True) else None
        send_discord_webhook(webhook_url, "🛒 New Order - Pending Approval", description, 0xF59E0B, buttons=buttons)
    
    return jsonify({"success": True, "order_id": order_id})

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
    return render_template_string(ADMIN_PANEL_TEMPLATE, settings=data['settings'], plans=data['plans'], features=data['features'], testimonials=data['testimonials'], orders=data['orders'], bot_config=data['bot_config'], payment_config=data['payment_config'], admin=data['admin'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

# API Routes
@app.route('/admin/api/start-bot', methods=['POST'])
def start_bot_api():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    start_bot_thread()
    data = load_db()
    data['bot_config']['bot_status'] = 'starting'
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/stop-bot', methods=['POST'])
def stop_bot_api():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    stop_bot()
    data = load_db()
    data['bot_config']['bot_status'] = 'stopped'
    data['bot_config']['bot_enabled'] = False
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-bot', methods=['POST'])
def save_bot():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['bot_config']['bot_token'] = request.json.get('bot_token')
    data['bot_config']['bot_presence'] = request.json.get('bot_presence')
    data['bot_config']['bot_activity_type'] = request.json.get('bot_activity_type')
    data['bot_config']['bot_activity'] = request.json.get('bot_activity')
    data['bot_config']['webhook_url'] = request.json.get('webhook_url')
    data['bot_config']['support_channel_id'] = request.json.get('support_channel_id')
    data['bot_config']['embed_color'] = request.json.get('embed_color', 0x4F46E5)
    data['admin']['main_admin_id'] = request.json.get('main_admin_id')
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
    data['payment_config']['auto_approve'] = request.json.get('auto_approve', False)
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    for key in ['website_name', 'website_tagline', 'logo_url', 'favicon_url', 'primary_color', 'background_color', 'hero_title', 'hero_subtitle', 'hero_button_text', 'hero_bg_image', 'contact_email', 'contact_discord']:
        if key in request.json:
            data['settings'][key] = request.json.get(key)
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
    print("=" * 50)
    print("🚀 Prime Web - Complete Platform Starting...")
    print("=" * 50)
    print("📱 Website: http://localhost:5000")
    print("🔐 Admin Login: admin@primeweb.com / admin123")
    print("🤖 Bot Status: Use Admin Panel to configure and start")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
