# app.py - Prime Web Ultimate Platform (3000+ Lines) - Premium Colored Admin Panel
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
import uuid
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, render_template_string, make_response, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Select, View, Button, Modal, TextInput
import nest_asyncio

nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(64))
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

DB_FILE = 'primeweb_data.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "login_ip": None,
            "two_factor_enabled": False,
            "two_factor_secret": None
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
            "ticket_category_id": None,
            "auto_response": True,
            "auto_response_message": "Thank you for contacting support! A staff member will assist you shortly.",
            "log_channel_id": None,
            "announcement_channel_id": None
        },
        "payment_config": {
            "upi_id": "primeweb@okhdfcbank",
            "upi_qr_url": "",
            "bank_name": "Prime Bank",
            "account_number": "XXXXXXXXXX1234",
            "ifsc_code": "PRIME123",
            "payment_instructions": "Send payment to the UPI ID above and share screenshot for confirmation.",
            "auto_approve": False,
            "crypto_enabled": False,
            "btc_address": "",
            "eth_address": "",
            "usdt_address": ""
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
            "info_color": "#3B82F6",
            "warning_color": "#F59E0B",
            "success_color": "#10B981",
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
                {"id": "vps_mini", "name": "VPS Mini", "price": 5, "cpu": "1 Core", "ram": "1GB", "storage": "20GB SSD", "bandwidth": "1TB", "popular": False, "icon": "🖥️", "stock": 50, "location": "USA East", "setup_time": "5 min"},
                {"id": "vps_standard", "name": "VPS Standard", "price": 20, "cpu": "4 Core", "ram": "4GB", "storage": "100GB SSD", "bandwidth": "4TB", "popular": True, "icon": "⚡", "stock": 30, "location": "Europe", "setup_time": "3 min"},
                {"id": "vps_pro", "name": "VPS Pro", "price": 80, "cpu": "12 Core", "ram": "16GB", "storage": "400GB SSD", "bandwidth": "15TB", "popular": False, "icon": "🚀", "stock": 15, "location": "Asia", "setup_time": "2 min"}
            ],
            "NITRO": [
                {"id": "nitro_basic", "name": "Nitro Basic", "price": 3, "features": "Custom Emojis, HD Streaming, Profile Badge", "popular": False, "icon": "💜", "stock": 100, "delivery": "Instant"},
                {"id": "nitro_full", "name": "Nitro Full", "price": 10, "features": "4K Streaming, 2 Boosts, 500MB Upload", "popular": True, "icon": "✨", "stock": 50, "delivery": "Instant"},
                {"id": "boost_1", "name": "Server Boost", "price": 4, "features": "1 Server Boost, Server Perks", "popular": False, "icon": "⚡", "stock": 200, "delivery": "Instant"}
            ]
        },
        "features": [
            {"icon": "⚡", "title": "Lightning Fast", "description": "NVMe SSD storage and premium network"},
            {"icon": "🛡️", "title": "DDoS Protection", "description": "Enterprise-grade security protection"},
            {"icon": "📞", "title": "24/7 Support", "description": "Expert support team always ready"},
            {"icon": "🔄", "title": "Instant Setup", "description": "Get started in under 5 minutes"},
            {"icon": "🌍", "title": "Global Network", "description": "14 data centers worldwide"},
            {"icon": "💰", "title": "Best Pricing", "description": "Premium quality at competitive prices"}
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
        "audit_logs": [],
        "announcements": [],
        "affiliates": [],
        "coupons": []
    }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_discord_webhook(webhook_url, title, description, color=0x4F46E5, fields=None, buttons=None):
    if not webhook_url:
        return False
    try:
        embed = {"title": title, "description": description, "color": color, "timestamp": datetime.now().isoformat(), "footer": {"text": "Prime Web • Premium Digital Services"}}
        if fields:
            embed["fields"] = fields
        payload = {"embeds": [embed]}
        if buttons:
            components = [{"type": 1, "components": [{"type": 2, "style": btn["style"], "label": btn["label"], "custom_id": btn["custom_id"], "emoji": {"name": btn["emoji"]}} for btn in buttons]}]
            payload["components"] = components
        response = requests.post(webhook_url, json=payload)
        return response.status_code in [200, 204]
    except:
        return False

# ==================== DISCORD BOT WITH ENHANCED COMMANDS ====================
class PlanSelect(Select):
    def __init__(self, plans, plan_type):
        options = []
        for plan in plans:
            options.append(discord.SelectOption(label=f"{plan['name']} - ${plan['price']}/mo", description=f"{plan.get('cpu', plan.get('features', 'Premium'))[:50]}", value=plan['id'], emoji=plan['icon']))
        super().__init__(placeholder=f"˖᯽ Select a {plan_type} plan ˖᯽", options=options, min_values=1, max_values=1)
        self.plans = plans
        self.plan_type = plan_type
    
    async def callback(self, interaction: discord.Interaction):
        selected_plan = next((p for p in self.plans if p['id'] == self.values[0]), None)
        if selected_plan:
            embed = discord.Embed(title=f"╭╭┈➤ {selected_plan['icon']} {selected_plan['name']}", description=f"•〢 **Price:** ${selected_plan['price']}/month\n•〢 **Details:** {selected_plan.get('cpu', selected_plan.get('features', 'Premium'))}\n•〢 **Stock:** {selected_plan.get('stock', 'Available')}\n•〢 **Setup:** {selected_plan.get('setup_time', selected_plan.get('delivery', 'Instant'))}", color=0x4F46E5)
            embed.set_footer(text=f"✦ Prime Web • Use /buy to purchase")
            view = BuyView(selected_plan)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class BuyView(View):
    def __init__(self, plan):
        super().__init__(timeout=60)
        self.plan = plan
    
    @discord.ui.button(label="🛒 Buy Now", style=discord.ButtonStyle.success, emoji="🛒")
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PurchaseModal(self.plan)
        await interaction.response.send_modal(modal)

class PurchaseModal(discord.ui.Modal, title="˖᯽ Complete Your Purchase ˖᯽"):
    def __init__(self, plan):
        super().__init__()
        self.plan = plan
    
    name = discord.ui.TextInput(label="•〢 Your Name", placeholder="Enter your full name", required=True)
    discord_id = discord.ui.TextInput(label="•〢 Discord ID", placeholder="Your Discord username#0000", required=True)
    email = discord.ui.TextInput(label="•〢 Email", placeholder="your@email.com", required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        order_id = secrets.token_hex(8).upper()
        data = load_db()
        order = {"id": order_id, "items": [{"name": self.plan['name'], "price": self.plan['price'], "quantity": 1}], "total": self.plan['price'], "customer_name": self.name.value, "discord_id": self.discord_id.value, "email": self.email.value, "status": "pending", "date": datetime.now().isoformat(), "source": "discord"}
        data['orders'].append(order)
        save_db(data)
        embed = discord.Embed(title="✅ Order Placed Successfully!", description=f"╭╭┈➤ **Order ID:** `{order_id}`\n•〢 **Plan:** {self.plan['name']}\n•〢 **Total:** ${self.plan['price']}\n\n✦ Our team will review your order shortly. You will receive a DM when approved!", color=0x10B981)
        embed.set_footer(text="Prime Web • Premium Digital Services")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        main_admin_id = data['admin'].get('main_admin_id')
        if main_admin_id:
            try:
                admin_user = await interaction.client.fetch_user(int(main_admin_id))
                admin_embed = discord.Embed(title="🛒 New Order from Discord!", description=f"╭╭┈➤ **Order ID:** `{order_id}`\n•〢 **Customer:** {self.name.value}\n•〢 **Discord:** {self.discord_id.value}\n•〢 **Plan:** {self.plan['name']}\n•〢 **Total:** ${self.plan['price']}", color=0xF59E0B, timestamp=datetime.now())
                await admin_user.send(embed=admin_embed)
            except:
                pass

class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📋 Commands", description="View all bot commands", value="commands", emoji="📋"),
            discord.SelectOption(label="📦 Plans", description="View hosting plans", value="plans", emoji="📦"),
            discord.SelectOption(label="🛒 Purchase", description="How to purchase", value="purchase", emoji="🛒"),
            discord.SelectOption(label="🎫 Ticket", description="Create support ticket", value="ticket", emoji="🎫"),
            discord.SelectOption(label="🌐 Website", description="Visit our website", value="website", emoji="🌐"),
            discord.SelectOption(label="ℹ️ About", description="About Prime Web", value="about", emoji="ℹ️"),
        ]
        super().__init__(placeholder="˖᯽ Select an option ˖᯽", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        data = load_db()
        if self.values[0] == "commands":
            embed = discord.Embed(title="╭╭┈➤ Bot Commands", description="•〢 **/ping** - Check bot latency\n•〢 **/plans** - View hosting plans\n•〢 **/website** - Get website link\n•〢 **/support** - Get support link\n•〢 **/status** - Change bot status (Admin)\n•〢 **/activity** - Change bot activity (Admin)\n•〢 **/ticket** - Create support ticket\n•〢 **/close** - Close ticket\n•〢 **/userinfo** - Get user info\n•〢 **/server** - Server management\n•〢 **/announce** - Make announcement\n•〢 **/help** - Show this menu", color=0x4F46E5)
            embed.set_footer(text="✦ Prime Web • Premium Digital Services")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "plans":
            embed = discord.Embed(title="╭╭┈➤ Available Plans", color=0x4F46E5)
            vps_text = "\n".join([f"•〢 **{p['name']}** - ${p['price']}/mo\n  └ {p['cpu']} | {p['ram']} | {p['storage']}" for p in data['plans']['VPS']])
            embed.add_field(name="🖥️ VPS Hosting", value=vps_text, inline=False)
            nitro_text = "\n".join([f"•〢 **{p['name']}** - ${p['price']}/mo\n  └ {p['features']}" for p in data['plans']['NITRO']])
            embed.add_field(name="💜 Discord Nitro", value=nitro_text, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "purchase":
            embed = discord.Embed(title="╭╭┈➤ How to Purchase", description="•〢 **Step 1:** Use `/plans` to view available plans\n•〢 **Step 2:** Click on any plan to see details\n•〢 **Step 3:** Click the Buy button\n•〢 **Step 4:** Fill in your details\n•〢 **Step 5:** Wait for admin approval\n\n✦ You will receive a DM when your order is approved!", color=0x10B981)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "ticket":
            embed = discord.Embed(title="╭╭┈➤ Create a Ticket", description="•〢 Use `/ticket` to create a support ticket\n•〢 A staff member will assist you shortly\n•〢 Please provide all relevant details", color=0x4F46E5)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "website":
            embed = discord.Embed(title="╭╭┈➤ Website", description="•〢 Visit our website: [Click Here](http://localhost:5000)\n•〢 Check out our latest plans and offers!", color=0x4F46E5)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.values[0] == "about":
            embed = discord.Embed(title="╭╭┈➤ About Prime Web", description="•〢 **Founded:** 2024\n•〢 **Services:** VPS Hosting, Discord Nitro\n•〢 **Support:** 24/7\n•〢 **Uptime:** 99.9%\n•〢 **Customers:** 12,847+", color=0x4F46E5)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(HelpSelect())

class PlansView(View):
    def __init__(self):
        super().__init__(timeout=60)
        data = load_db()
        self.add_item(PlanSelect(data['plans']['VPS'], "VPS"))
        self.add_item(PlanSelect(data['plans']['NITRO'], "NITRO"))
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_db()
        self.clear_items()
        self.add_item(PlanSelect(data['plans']['VPS'], "VPS"))
        self.add_item(PlanSelect(data['plans']['NITRO'], "NITRO"))
        self.add_item(self.refresh_button)
        await interaction.response.edit_message(view=self)

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
        activity_map = {'watching': discord.ActivityType.watching, 'playing': discord.ActivityType.playing, 'listening': discord.ActivityType.listening, 'competing': discord.ActivityType.competing}
        activity = discord.Activity(type=activity_map.get(activity_type, discord.ActivityType.watching), name=f"˖᯽ {activity_name} ˖᯽")
        status_map = {'online': discord.Status.online, 'idle': discord.Status.idle, 'dnd': discord.Status.dnd, 'invisible': discord.Status.invisible}
        await self.change_presence(activity=activity, status=status_map.get(presence, discord.Status.online))
        data['bot_config']['bot_status'] = 'online'
        data['bot_config']['bot_enabled'] = True
        save_db(data)

def create_bot_instance():
    bot = PrimeWebBot()
    
    @bot.tree.command(name="ping", description="Check bot latency")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", description=f"╭╭┈➤ **Latency:** `{latency}ms`\n•〢 **WebSocket:** `{latency}ms`\n•〢 **Status:** 🟢 Online", color=0x4F46E5)
        embed.set_footer(text="✦ Prime Web • Premium Digital Services")
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="plans", description="View all hosting plans with interactive menu")
    async def plans(interaction: discord.Interaction):
        embed = discord.Embed(title="˖᯽ Prime Web Hosting Plans ˖᯽", description="╭╭┈➤ Select a plan from the dropdown menu below to view details and purchase!\n\n•〢 **VPS Plans** - High-performance virtual servers\n•〢 **Nitro Plans** - Discord Nitro & Boosts", color=0x4F46E5)
        embed.set_footer(text="✦ Click the dropdown to see available plans")
        view = PlansView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="website", description="Get website link")
    async def website(interaction: discord.Interaction):
        embed = discord.Embed(title="🌐 Prime Web Website", description="•〢 [Click here to visit our website](http://localhost:5000)\n•〢 Check out our latest plans and exclusive offers!", color=0x4F46E5)
        embed.add_field(name="✦ Features", value="• VPS Hosting\n• Discord Nitro\n• 24/7 Support\n• Instant Setup", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="support", description="Get support link")
    async def support(interaction: discord.Interaction):
        data = load_db()
        embed = discord.Embed(title="🎫 Prime Web Support", description=f"╭╭┈➤ **Discord Server:** {data['settings']['contact_discord']}\n•〢 **Email:** {data['settings']['contact_email']}\n•〢 **Ticket:** Use `/ticket` to create a support ticket", color=0x4F46E5)
        embed.set_footer(text="✦ Our team is available 24/7")
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
        embed = discord.Embed(title="✅ Bot Status Updated", description=f"╭╭┈➤ **New Status:** `{status.upper()}`\n•〢 The bot's presence has been updated successfully!", color=0x10B981)
        await interaction.response.send_message(embed=embed)
    
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
        activity = discord.Activity(type=type_map[activity_type], name=f"˖᯽ {name} ˖᯽")
        await bot.change_presence(activity=activity)
        embed = discord.Embed(title="✅ Bot Activity Updated", description=f"╭╭┈➤ **New Activity:** `{activity_type} {name}`\n•〢 The bot's activity has been updated successfully!", color=0x10B981)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="ticket", description="Create a support ticket")
    async def ticket(interaction: discord.Interaction):
        data = load_db()
        support_channel_id = data['bot_config'].get('support_channel_id')
        ticket_category_id = data['bot_config'].get('ticket_category_id')
        category = None
        if ticket_category_id:
            category = discord.utils.get(interaction.guild.categories, id=int(ticket_category_id))
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ticket_channel = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}-{secrets.token_hex(4)}", category=category, overwrites=overwrites)
        embed = discord.Embed(title="🎫 Support Ticket Created", description=f"Hello {interaction.user.mention},\n\nPlease describe your issue and a staff member will assist you shortly.", color=0x4F46E5, timestamp=datetime.now())
        embed.add_field(name="📌 Instructions", value="1. Explain your issue in detail\n2. Attach any relevant screenshots\n3. Wait for staff response", inline=False)
        embed.set_footer(text=f"Ticket ID: {secrets.token_hex(8)}")
        await ticket_channel.send(embed=embed)
        await ticket_channel.send(f"{interaction.user.mention} Staff will be with you shortly!")
        data['tickets'].append({"channel_id": ticket_channel.id, "user_id": interaction.user.id, "created_at": datetime.now().isoformat(), "status": "open"})
        save_db(data)
        await interaction.response.send_message(f"✅ Support ticket created! Check {ticket_channel.mention}", ephemeral=True)
    
    @bot.tree.command(name="close", description="Close current ticket")
    async def close_ticket(interaction: discord.Interaction):
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return
        embed = discord.Embed(title="🔒 Ticket Closing", description="╭╭┈➤ This ticket will be closed in 5 seconds...\n•〢 Thank you for contacting support!", color=0xF59E0B)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()
    
    @bot.tree.command(name="userinfo", description="Get user information")
    async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"👤 User Info - {member.name}", description=f"╭╭┈➤ **ID:** `{member.id}`\n•〢 **Joined Server:** {member.joined_at.strftime('%Y-%m-%d')}\n•〢 **Account Created:** {member.created_at.strftime('%Y-%m-%d')}\n•〢 **Top Role:** {member.top_role.mention}", color=0x4F46E5, timestamp=datetime.now())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="server", description="Server management (Admin only)")
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
        embed = discord.Embed(title="🖥️ Server Management", description=f"╭╭┈➤ Action: **{action.upper()}**\n•〢 Status: Processing...", color=0x4F46E5)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(2)
        embed.description = f"╭╭┈➤ Action: **{action.upper()}**\n•〢 Status: ✅ Completed successfully!"
        await interaction.edit_original_response(embed=embed)
    
    @bot.tree.command(name="announce", description="Make an announcement (Admin only)")
    @app_commands.describe(channel="Channel to announce in", message="Announcement message")
    async def announce(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        data = load_db()
        admin_id = data['admin'].get('main_admin_id')
        if interaction.user.id != admin_id:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        embed = discord.Embed(title="📢 Announcement", description=message, color=0x4F46E5, timestamp=datetime.now())
        embed.set_footer(text=f"Announced by {interaction.user.name}")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
    
    @bot.tree.command(name="help", description="Show all commands with interactive menu")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(title="˖᯽ Prime Web Bot Help ˖᯽", description="╭╭┈➤ Welcome to Prime Web Bot! Use the dropdown menu below to explore available options.\n\n•〢 **Quick Commands:**\n  └ /ping - Check latency\n  └ /plans - View plans\n  └ /website - Website link\n  └ /support - Support link\n  └ /ticket - Create ticket\n  └ /close - Close ticket\n  └ /userinfo - User info\n  └ /server - Server management\n  └ /announce - Make announcement", color=0x4F46E5)
        embed.set_footer(text="✦ Select an option from the dropdown menu")
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)
    
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
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes glow { 0%,100% { box-shadow: 0 0 5px {{ settings.primary_color }}; } 50% { box-shadow: 0 0 20px {{ settings.primary_color }}; } }
        .animate { animation: fadeInUp 0.6s ease forwards; opacity: 0; }
        .delay-1 { animation-delay: 0.1s; }
        .delay-2 { animation-delay: 0.2s; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        .navbar {
            padding: 20px 0;
            position: sticky;
            top: 0;
            background: rgba(10,10,10,0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .navbar .container { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
        .logo { display: flex; align-items: center; gap: 12px; cursor: pointer; }
        .logo img { width: 40px; height: 40px; border-radius: 12px; }
        .logo span { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #fff, {{ settings.primary_color }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .nav-links { display: flex; gap: 32px; align-items: center; flex-wrap: wrap; }
        .nav-links a { color: {{ settings.text_color }}; text-decoration: none; transition: 0.3s; font-weight: 500; }
        .nav-links a:hover { color: {{ settings.primary_color }}; }
        .cart-icon { position: relative; cursor: pointer; padding: 8px; }
        .cart-count { position: absolute; top: -5px; right: -5px; background: {{ settings.danger_color }}; color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; font-weight: bold; }
        .admin-btn { background: {{ settings.primary_color }}; padding: 8px 20px; border-radius: 40px; }
        .hero { padding: 120px 0; text-align: center; position: relative; overflow: hidden; }
        .hero::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 30% 50%, rgba(79,70,229,0.15), transparent 50%); z-index: 0; }
        .hero .container { position: relative; z-index: 1; }
        .hero h1 { font-size: 4rem; font-weight: 800; margin-bottom: 20px; }
        .hero h1 span { color: {{ settings.primary_color }}; }
        .hero p { font-size: 1.2rem; color: {{ settings.text_secondary }}; margin-bottom: 30px; max-width: 600px; margin-left: auto; margin-right: auto; }
        .btn-primary { background: {{ settings.primary_color }}; color: white; padding: 14px 36px; border-radius: 50px; text-decoration: none; font-weight: 600; transition: 0.3s; display: inline-block; border: none; cursor: pointer; }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(79,70,229,0.3); }
        .stats-section { padding: 60px 0; background: rgba(255,255,255,0.02); }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; text-align: center; }
        .stat-card { background: rgba(255,255,255,0.03); border-radius: 20px; padding: 30px; backdrop-filter: blur(10px); transition: 0.3s; }
        .stat-card:hover { transform: translateY(-5px); background: rgba(255,255,255,0.05); }
        .stat-number { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, {{ settings.primary_color }}, {{ settings.secondary_color }}); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .section { padding: 80px 0; }
        .section-title { text-align: center; font-size: 2.5rem; font-weight: 700; margin-bottom: 16px; }
        .section-title span { color: {{ settings.primary_color }}; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .feature-card { background: rgba(255,255,255,0.03); border-radius: {{ settings.border_radius }}; padding: 40px 30px; text-align: center; transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); }
        .feature-card:hover { transform: translateY(-8px); border-color: {{ settings.primary_color }}; background: rgba(79,70,229,0.05); }
        .feature-icon { font-size: 3rem; margin-bottom: 20px; }
        .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; }
        .plan-card { background: rgba(255,255,255,0.03); border-radius: {{ settings.border_radius }}; padding: 35px; transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); position: relative; }
        .plan-card:hover { transform: translateY(-8px); border-color: {{ settings.primary_color }}; }
        .plan-card.popular { border: 2px solid {{ settings.primary_color }}; transform: scale(1.02); }
        .popular-badge { position: absolute; top: 20px; right: 20px; background: {{ settings.primary_color }}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; }
        .plan-icon { font-size: 3rem; margin-bottom: 20px; }
        .plan-price { font-size: 2.5rem; font-weight: 800; margin: 20px 0; }
        .buy-btn { background: {{ settings.primary_color }}; color: white; border: none; padding: 14px 24px; border-radius: 50px; width: 100%; cursor: pointer; font-weight: 600; transition: 0.3s; }
        .buy-btn:hover { opacity: 0.9; transform: scale(1.02); }
        .testimonials-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px; }
        .testimonial-card { background: rgba(255,255,255,0.03); border-radius: {{ settings.border_radius }}; padding: 30px; border: 1px solid rgba(255,255,255,0.05); }
        .cart-sidebar { position: fixed; right: -450px; top: 0; width: 450px; height: 100vh; background: {{ settings.card_background }}; z-index: 2000; padding: 25px; transition: right 0.3s ease; box-shadow: -5px 0 30px rgba(0,0,0,0.5); overflow-y: auto; }
        .cart-sidebar.open { right: 0; }
        .payment-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 3000; justify-content: center; align-items: center; }
        .payment-content { background: {{ settings.card_background }}; border-radius: 24px; padding: 40px; max-width: 500px; width: 90%; }
        .toast { position: fixed; bottom: 25px; right: 25px; background: {{ settings.secondary_color }}; color: white; padding: 14px 28px; border-radius: 50px; z-index: 4000; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .footer { padding: 60px 0 30px; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 60px; }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .cart-sidebar { width: 100%; right: -100%; }
            .cards-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<nav class="navbar"><div class="container"><div class="logo" onclick="window.location.href='/'"><img src="{{ settings.logo_url }}" alt="logo"><span>{{ settings.website_name }}</span></div><div class="nav-links"><a href="#home">Home</a><a href="#features">Features</a><a href="#plans">Plans</a><a href="#testimonials">Reviews</a><a href="#contact">Contact</a><div class="cart-icon" onclick="toggleCart()"><i class="fas fa-shopping-cart"></i><span class="cart-count" id="cartCount">0</span></div><a href="/admin/login" class="admin-btn"><i class="fas fa-lock"></i> Admin</a></div></div></nav>
<div class="cart-sidebar" id="cartSidebar"><div class="close-cart" onclick="toggleCart()">✕</div><h2>🛒 Your Cart</h2><div id="cartItems"></div><div id="cartTotal" style="font-weight:800;margin-top:20px;"></div><button class="btn-primary" onclick="proceedToPayment()" style="width:100%;margin-top:20px;">Proceed to Payment →</button><button onclick="window.open('{{ settings.contact_discord }}','_blank')" style="width:100%;margin-top:10px;background:#5865F2;color:white;border:none;padding:12px;border-radius:40px;cursor:pointer;"><i class="fab fa-discord"></i> Need Help?</button></div>
<div id="paymentModal" class="payment-modal"><div class="payment-content"><h2>💳 Complete Payment</h2><div style="margin:20px 0;padding:15px;background:rgba(255,255,255,0.05);border-radius:16px;"><p><strong>UPI ID:</strong> {{ payment_config.upi_id }}</p><p><strong>Bank:</strong> {{ payment_config.bank_name }}</p><p><strong>Instructions:</strong> {{ payment_config.payment_instructions }}</p></div><form id="paymentForm"><input type="text" id="customerName" placeholder="Your Name" required><input type="text" id="discordId" placeholder="Discord ID" required><input type="email" id="customerEmail" placeholder="Email"><input type="text" id="transactionId" placeholder="Transaction ID" required><button type="submit" class="btn-primary" style="width:100%;">Submit Order</button></form><button onclick="closePaymentModal()" style="width:100%;margin-top:10px;background:#EF4444;color:white;border:none;padding:14px;border-radius:40px;cursor:pointer;">Cancel</button></div></div>
<section id="home" class="hero"><div class="container"><h1 class="animate">{{ settings.hero_title }}<br><span>{{ settings.website_tagline }}</span></h1><p class="animate delay-1">{{ settings.hero_subtitle }}</p><div class="animate delay-2"><a href="#plans" class="btn-primary">{{ settings.hero_button_text }} →</a></div></div></section>
<section class="stats-section"><div class="container"><div class="stats-grid"><div class="stat-card"><div class="stat-number">{{ settings.stats_customers }}</div><div>Happy Customers</div></div><div class="stat-card"><div class="stat-number">{{ settings.stats_uptime }}</div><div>Uptime</div></div><div class="stat-card"><div class="stat-number">{{ settings.stats_rating }}</div><div>Rating</div></div><div class="stat-card"><div class="stat-number">{{ settings.stats_servers }}</div><div>Servers</div></div></div></div></section>
<section id="features" class="section"><div class="container"><h2 class="section-title"><span>⚡</span> {{ settings.features_title }}</h2><div class="features-grid">{% for f in features %}<div class="feature-card"><div class="feature-icon">{{ f.icon }}</div><h3>{{ f.title }}</h3><p>{{ f.description }}</p></div>{% endfor %}</div></div></section>
<section id="plans" class="section"><div class="container"><h2 class="section-title"><span>🚀</span> VPS Hosting Plans</h2><div class="cards-grid">{% for plan in plans.VPS %}<div class="plan-card {% if plan.popular %}popular{% endif %}">{% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}<div class="plan-icon">{{ plan.icon }}</div><h3>{{ plan.name }}</h3><div class="plan-price">${{ plan.price }}<small>/mo</small></div><button class="buy-btn" onclick="addToCart('{{ plan.id }}','{{ plan.name }}',{{ plan.price }},'{{ plan.icon }}')">Add to Cart →</button></div>{% endfor %}</div><h2 class="section-title" style="margin-top:60px;"><span>💜</span> Discord Nitro</h2><div class="cards-grid">{% for plan in plans.NITRO %}<div class="plan-card {% if plan.popular %}popular{% endif %}">{% if plan.popular %}<div class="popular-badge">⭐ POPULAR</div>{% endif %}<div class="plan-icon">{{ plan.icon }}</div><h3>{{ plan.name }}</h3><div class="plan-price">${{ plan.price }}<small>/mo</small></div><button class="buy-btn" onclick="addToCart('{{ plan.id }}','{{ plan.name }}',{{ plan.price }},'{{ plan.icon }}')">Add to Cart →</button></div>{% endfor %}</div></div></section>
<footer id="contact" class="footer"><div class="container"><p>📧 <a href="mailto:{{ settings.contact_email }}">{{ settings.contact_email }}</a></p><p>💬 <a href="{{ settings.contact_discord }}">Join our Discord</a></p><p>{{ settings.footer_text }}</p></div></footer>
<script>
let cart=JSON.parse(localStorage.getItem('cart')||'{}');
function updateCartDisplay(){let count=0,total=0,html='';for(let id in cart){count+=cart[id].quantity;total+=cart[id].price*cart[id].quantity;html+=`<div class="cart-item"><div>${cart[id].icon} ${cart[id].name} x${cart[id].quantity}</div><div>$${cart[id].price*cart[id].quantity} <button class="cart-item-remove" onclick="removeFromCart('${id}')">Remove</button></div></div>`;}
document.getElementById('cartCount').innerText=count;document.getElementById('cartItems').innerHTML=html||'<p>Cart is empty</p>';document.getElementById('cartTotal').innerHTML=`<strong>Total: $${total}</strong>`;localStorage.setItem('cart',JSON.stringify(cart));}
function addToCart(id,name,price,icon){if(cart[id])cart[id].quantity++;else cart[id]={name,price,icon,quantity:1};updateCartDisplay();showToast(`✅ Added ${name} to cart`);}
function removeFromCart(id){if(cart[id]){cart[id].quantity--;if(cart[id].quantity<=0)delete cart[id];updateCartDisplay();showToast('🗑️ Removed from cart');}}
function toggleCart(){document.getElementById('cartSidebar').classList.toggle('open');}
function proceedToPayment(){if(Object.keys(cart).length===0){showToast('Cart is empty!');return;}document.getElementById('paymentModal').style.display='flex';toggleCart();}
function closePaymentModal(){document.getElementById('paymentModal').style.display='none';}
function showToast(msg){const toast=document.createElement('div');toast.className='toast';toast.innerHTML=msg;document.body.appendChild(toast);setTimeout(()=>toast.remove(),3000);}
document.getElementById('paymentForm').addEventListener('submit',async(e)=>{e.preventDefault();let items=[],total=0;for(let id in cart){items.push({id,name:cart[id].name,price:cart[id].price,quantity:cart[id].quantity});total+=cart[id].price*cart[id].quantity;}
const res=await fetch('/api/place-order',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items,total,customer_name:document.getElementById('customerName').value,discord_id:document.getElementById('discordId').value,email:document.getElementById('customerEmail').value,transaction_id:document.getElementById('transactionId').value})});const result=await res.json();if(result.success){showToast('✅ Order placed! Admin will approve soon.');cart={};updateCartDisplay();closePaymentModal();document.getElementById('paymentForm').reset();}else{showToast('❌ '+result.error);}});
updateCartDisplay();
const observer=new IntersectionObserver((entries)=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.style.opacity='1';entry.target.style.transform='translateY(0)';}})},{threshold:0.1});
document.querySelectorAll('.feature-card, .plan-card, .stat-card').forEach(el=>{el.style.opacity='0';el.style.transform='translateY(30px)';el.style.transition='all 0.6s ease';observer.observe(el);});
</script>
</body>
</html>
'''

# ==================== ADMIN PANEL ====================
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Prime Web Admin</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box;}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0A0A0A,#1A1A2E);min-height:100vh;display:flex;justify-content:center;align-items:center;}
.login-container{background:rgba(255,255,255,0.03);backdrop-filter:blur(10px);border-radius:32px;padding:50px;width:450px;border:1px solid rgba(255,255,255,0.1);}
.login-container h1{text-align:center;background:linear-gradient(135deg,#fff,#4F46E5);-webkit-background-clip:text;background-clip:text;color:transparent;margin-bottom:10px;}
.login-container input{width:100%;padding:14px;margin:12px 0;border-radius:16px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.5);color:white;}
.login-container button{width:100%;padding:14px;background:linear-gradient(135deg,#4F46E5,#6366F1);color:white;border:none;border-radius:40px;cursor:pointer;font-weight:600;}
.error{color:#EF4444;text-align:center;margin-top:20px;}
</style></head>
<body><div class="login-container"><h1>Prime Web Admin</h1><p style="text-align:center;margin-bottom:20px;">Enter your credentials</p><form method="post"><input type="email" name="email" placeholder="admin@primeweb.com" required><input type="password" name="password" placeholder="••••••••" required><button type="submit">Login to Dashboard</button></form>{% if error %}<div class="error">{{ error }}</div>{% endif %}</div></body></html>
'''

ADMIN_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Prime Web Admin Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0A0A0A; color: white; overflow-x: hidden; }
        .admin-container { display: flex; min-height: 100vh; }
        .sidebar { width: 280px; background: linear-gradient(180deg, #0F0F12 0%, #0A0A0A 100%); border-right: 1px solid rgba(255,255,255,0.05); padding: 30px 20px; position: fixed; height: 100vh; overflow-y: auto; }
        .sidebar-header { display: flex; align-items: center; gap: 12px; padding-bottom: 30px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
        .sidebar-header img { width: 45px; height: 45px; border-radius: 12px; }
        .sidebar-header h2 { font-size: 1.2rem; background: linear-gradient(135deg, #fff, #4F46E5); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .sidebar .nav-item { padding: 12px 16px; margin: 4px 0; border-radius: 14px; cursor: pointer; display: flex; align-items: center; gap: 12px; color: #A1A1AA; transition: 0.3s; }
        .sidebar .nav-item:hover, .sidebar .nav-item.active { background: rgba(79,70,229,0.15); color: #4F46E5; }
        .main-content { flex: 1; margin-left: 280px; padding: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(16,185,129,0.05)); border-radius: 20px; padding: 20px; border: 1px solid rgba(79,70,229,0.2); }
        .stat-card h3 { font-size: 0.85rem; color: #A1A1AA; margin-bottom: 10px; }
        .stat-card .number { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #4F46E5, #10B981); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .card { background: rgba(255,255,255,0.03); border-radius: 20px; padding: 25px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.05); }
        .card h3 { margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
        input, textarea, select { width: 100%; padding: 12px 16px; margin: 8px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.5); color: white; }
        button { background: linear-gradient(135deg, #4F46E5, #6366F1); color: white; padding: 10px 24px; border: none; border-radius: 40px; cursor: pointer; font-weight: 600; margin-top: 10px; transition: 0.3s; }
        button:hover { transform: translateY(-2px); opacity: 0.9; }
        .success { background: #10B981; padding: 12px; border-radius: 12px; margin-bottom: 20px; }
        .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .bot-status { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-online { background: #10B981; }
        .status-offline { background: #EF4444; }
        .order-item { border-bottom: 1px solid rgba(255,255,255,0.1); padding: 15px 0; }
        .badge-pending { background: #F59E0B; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; }
        @media (max-width: 768px) { .sidebar { width: 80px; padding: 20px 10px; } .sidebar span { display: none; } .main-content { margin-left: 80px; } .stats-grid { grid-template-columns: repeat(2, 1fr); } .grid-2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<div class="admin-container">
    <div class="sidebar">
        <div class="sidebar-header"><img src="{{ settings.logo_url }}" alt="logo"><h2>Prime Web</h2></div>
        <div class="nav-item active" data-tab="dashboard"><i class="fas fa-tachometer-alt"></i> <span>Dashboard</span></div>
        <div class="nav-item" data-tab="bot"><i class="fab fa-discord"></i> <span>Bot Control</span></div>
        <div class="nav-item" data-tab="plans"><i class="fas fa-box"></i> <span>Plans</span></div>
        <div class="nav-item" data-tab="payment"><i class="fas fa-credit-card"></i> <span>Payment</span></div>
        <div class="nav-item" data-tab="orders"><i class="fas fa-shopping-cart"></i> <span>Orders</span></div>
        <div class="nav-item" data-tab="settings"><i class="fas fa-sliders-h"></i> <span>Settings</span></div>
        <div class="nav-item" data-tab="features"><i class="fas fa-star"></i> <span>Features</span></div>
        <div class="nav-item" data-tab="testimonials"><i class="fas fa-comment"></i> <span>Testimonials</span></div>
        <div class="nav-item" data-tab="password"><i class="fas fa-key"></i> <span>Security</span></div>
        <div class="nav-item" onclick="window.location.href='/admin/logout'"><i class="fas fa-sign-out-alt"></i> <span>Logout</span></div>
    </div>
    <div class="main-content">
        <div id="dashboard-tab">
            <div class="stats-grid">
                <div class="stat-card"><h3><i class="fas fa-shopping-cart"></i> Total Orders</h3><div class="number">{{ orders|length }}</div></div>
                <div class="stat-card"><h3><i class="fas fa-box"></i> Total Plans</h3><div class="number">{{ plans.VPS|length + plans.NITRO|length }}</div></div>
                <div class="stat-card"><h3><i class="fas fa-star"></i> Features</h3><div class="number">{{ features|length }}</div></div>
                <div class="stat-card"><h3><i class="fas fa-comment"></i> Testimonials</h3><div class="number">{{ testimonials|length }}</div></div>
            </div>
            <div class="card"><h3><i class="fab fa-discord"></i> Bot Status</h3><p><strong>Status:</strong> <span class="bot-status {% if bot_config.bot_status == 'online' %}status-online{% else %}status-offline{% endif %}">{{ bot_config.bot_status|upper }}</span></p><p><strong>Token:</strong> {% if bot_config.bot_token %}✅ Configured{% else %}❌ Not Set{% endif %}</p><div style="display:flex;gap:15px;margin-top:20px;"><button onclick="startBot()" style="background:#10B981;"><i class="fas fa-play"></i> Start Bot</button><button onclick="stopBot()" style="background:#EF4444;"><i class="fas fa-stop"></i> Stop Bot</button></div><div id="botMsg"></div></div>
            <div class="card"><h3><i class="fas fa-chart-line"></i> Recent Orders</h3>{% for order in orders[:5] %}<div class="order-item"><strong>{{ order.id[:8] }}</strong> - {{ order.customer_name }} - ${{ order.total }} - <span class="badge-pending">{{ order.status }}</span></div>{% else %}<p>No orders yet</p>{% endfor %}</div>
        </div>
        <div id="bot-tab" style="display:none;"><div class="card"><h3><i class="fab fa-discord"></i> Discord Bot Configuration</h3><form id="botForm"><div class="grid-2"><div><label>Bot Token</label><input type="password" name="bot_token" value="{{ bot_config.bot_token }}"></div><div><label>Bot Presence</label><select name="bot_presence"><option value="online" {% if bot_config.bot_presence == 'online' %}selected{% endif %}>🟢 Online</option><option value="idle" {% if bot_config.bot_presence == 'idle' %}selected{% endif %}>🟡 Idle</option><option value="dnd" {% if bot_config.bot_presence == 'dnd' %}selected{% endif %}>🔴 DND</option><option value="invisible" {% if bot_config.bot_presence == 'invisible' %}selected{% endif %}>👻 Invisible</option></select></div><div><label>Activity Type</label><select name="bot_activity_type"><option value="watching" {% if bot_config.bot_activity_type == 'watching' %}selected{% endif %}>Watching</option><option value="playing" {% if bot_config.bot_activity_type == 'playing' %}selected{% endif %}>Playing</option><option value="listening" {% if bot_config.bot_activity_type == 'listening' %}selected{% endif %}>Listening</option></select></div><div><label>Activity Name</label><input type="text" name="bot_activity" value="{{ bot_config.bot_activity }}"></div><div><label>Webhook URL</label><input type="text" name="webhook_url" value="{{ bot_config.webhook_url }}"></div><div><label>Main Admin ID</label><input type="text" name="main_admin_id" value="{{ admin.main_admin_id or '' }}"></div></div><button type="submit"><i class="fas fa-save"></i> Save Bot Settings</button></form><div id="botConfigMsg"></div></div><div class="card"><h3><i class="fas fa-terminal"></i> Bot Commands</h3><div class="grid-2"><div><code>/ping</code> - Check latency</div><div><code>/plans</code> - View plans</div><div><code>/website</code> - Website link</div><div><code>/support</code> - Support link</div><div><code>/status</code> - Change status</div><div><code>/activity</code> - Change activity</div><div><code>/ticket</code> - Create ticket</div><div><code>/close</code> - Close ticket</div><div><code>/userinfo</code> - User info</div><div><code>/server</code> - Server mgmt</div><div><code>/announce</code> - Announcement</div><div><code>/help</code> - Help menu</div></div></div></div>
        <div id="plans-tab" style="display:none;"><div class="card"><h3><i class="fas fa-server"></i> VPS Plans</h3>{% for plan in plans.VPS %}<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.1);"><strong>{{ plan.icon }} {{ plan.name }}</strong> - ${{ plan.price }}/mo <button onclick="editPlan('VPS',{{ loop.index0 }})" style="background:#F59E0B;padding:6px 16px;">Edit</button></div>{% endfor %}<button onclick="addPlan('VPS')"><i class="fas fa-plus"></i> Add VPS Plan</button></div><div class="card"><h3><i class="fab fa-discord"></i> Nitro Plans</h3>{% for plan in plans.NITRO %}<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.1);"><strong>{{ plan.icon }} {{ plan.name }}</strong> - ${{ plan.price }}/mo <button onclick="editPlan('NITRO',{{ loop.index0 }})" style="background:#F59E0B;padding:6px 16px;">Edit</button></div>{% endfor %}<button onclick="addPlan('NITRO')"><i class="fas fa-plus"></i> Add Nitro Plan</button></div></div>
        <div id="payment-tab" style="display:none;"><div class="card"><h3><i class="fas fa-credit-card"></i> Payment Configuration</h3><form id="paymentForm"><div class="grid-2"><div><label>UPI ID</label><input type="text" name="upi_id" value="{{ payment_config.upi_id }}"><label>Bank Name</label><input type="text" name="bank_name" value="{{ payment_config.bank_name }}"></div><div><label>Account Number</label><input type="text" name="account_number" value="{{ payment_config.account_number }}"><label>IFSC Code</label><input type="text" name="ifsc_code" value="{{ payment_config.ifsc_code }}"></div></div><label>Instructions</label><textarea name="payment_instructions" rows="3">{{ payment_config.payment_instructions }}</textarea><button type="submit"><i class="fas fa-save"></i> Save Payment Settings</button></form><div id="paymentMsg"></div></div></div>
        <div id="orders-tab" style="display:none;"><div class="card"><h3><i class="fas fa-clock"></i> Pending Orders</h3>{% for order in orders if order.status == 'pending' %}<div class="order-item"><strong>🆔 {{ order.id }}</strong> <span class="badge-pending">PENDING</span><p>👤 {{ order.customer_name }} | Discord: {{ order.discord_id }}</p><p>💰 ${{ order.total }}</p><div><button onclick="approveOrder('{{ order.id }}')" style="background:#10B981;">✅ Approve</button><button onclick="rejectOrder('{{ order.id }}')" style="background:#EF4444;margin-left:10px;">❌ Reject</button><button onclick="contactCustomer('{{ order.discord_id }}')" style="background:#5865F2;margin-left:10px;">💬 Contact</button></div></div>{% else %}<p>No pending orders</p>{% endfor %}</div></div>
        <div id="settings-tab" style="display:none;"><div class="card"><h3><i class="fas fa-palette"></i> Website Settings</h3><form id="settingsForm"><div class="grid-2"><div><label>Website Name</label><input type="text" name="website_name" value="{{ settings.website_name }}"><label>Logo URL</label><input type="text" name="logo_url" value="{{ settings.logo_url }}"><label>Primary Color</label><input type="color" name="primary_color" value="{{ settings.primary_color }}"></div><div><label>Hero Title</label><input type="text" name="hero_title" value="{{ settings.hero_title }}"><label>Hero Subtitle</label><input type="text" name="hero_subtitle" value="{{ settings.hero_subtitle }}"><label>Contact Email</label><input type="email" name="contact_email" value="{{ settings.contact_email }}"></div></div><button type="submit"><i class="fas fa-save"></i> Save Settings</button></form><div id="settingsMsg"></div></div></div>
        <div id="features-tab" style="display:none;"><div class="card"><h3><i class="fas fa-star"></i> Manage Features</h3>{% for f in features %}<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.1);"><strong>{{ f.icon }} {{ f.title }}</strong><p>{{ f.description }}</p><button onclick="editFeature({{ loop.index0 }})" style="background:#F59E0B;">Edit</button><button onclick="deleteFeature({{ loop.index0 }})" style="background:#EF4444;margin-left:10px;">Delete</button></div>{% endfor %}<button onclick="addFeature()"><i class="fas fa-plus"></i> Add Feature</button></div></div>
        <div id="testimonials-tab" style="display:none;"><div class="card"><h3><i class="fas fa-users"></i> Manage Testimonials</h3>{% for t in testimonials %}<div style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.1);"><strong>{{ t.name }}</strong><p>"{{ t.content }}"</p><button onclick="editTestimonial({{ loop.index0 }})" style="background:#F59E0B;">Edit</button><button onclick="deleteTestimonial({{ loop.index0 }})" style="background:#EF4444;margin-left:10px;">Delete</button></div>{% endfor %}<button onclick="addTestimonial()"><i class="fas fa-plus"></i> Add Testimonial</button></div></div>
        <div id="password-tab" style="display:none;"><div class="card"><h3><i class="fas fa-shield-alt"></i> Change Admin Password</h3><form id="passwordForm"><input type="password" name="current_password" placeholder="Current Password"><input type="password" name="new_password" placeholder="New Password"><input type="password" name="confirm_password" placeholder="Confirm Password"><button type="submit"><i class="fas fa-key"></i> Change Password</button></form><div id="passwordMsg"></div></div></div>
    </div>
</div>
<script>
    document.querySelectorAll('.nav-item').forEach(item=>{item.addEventListener('click',()=>{document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active'));item.classList.add('active');const tab=item.dataset.tab;document.querySelectorAll('[id$="-tab"]').forEach(t=>t.style.display='none');document.getElementById(`${tab}-tab`).style.display='block';});});
    async function postData(url,data,msgElement){await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(msgElement)msgElement.innerHTML='<div class="success">✅ Saved! Refreshing...</div>';setTimeout(()=>location.reload(),1000);}
    function startBot(){fetch('/admin/api/start-bot',{method:'POST'}).then(()=>{document.getElementById('botMsg').innerHTML='<div class="success">✅ Bot starting...</div>';setTimeout(()=>location.reload(),2000);});}
    function stopBot(){fetch('/admin/api/stop-bot',{method:'POST'}).then(()=>{document.getElementById('botMsg').innerHTML='<div class="success">⏹️ Bot stopping...</div>';setTimeout(()=>location.reload(),2000);});}
    document.getElementById('botForm')?.addEventListener('submit',(e)=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));data.main_admin_id=parseInt(data.main_admin_id)||null;postData('/admin/api/save-bot',data,document.getElementById('botConfigMsg'));});
    document.getElementById('paymentForm')?.addEventListener('submit',(e)=>{e.preventDefault();postData('/admin/api/save-payment',Object.fromEntries(new FormData(e.target)),document.getElementById('paymentMsg'));});
    document.getElementById('settingsForm')?.addEventListener('submit',(e)=>{e.preventDefault();postData('/admin/api/save-settings',Object.fromEntries(new FormData(e.target)),document.getElementById('settingsMsg'));});
    document.getElementById('passwordForm')?.addEventListener('submit',async(e)=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));if(data.new_password!==data.confirm_password){document.getElementById('passwordMsg').innerHTML='<div class="success" style="background:#EF4444;">❌ Passwords do not match</div>';return;}const res=await fetch('/admin/api/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await res.json();document.getElementById('passwordMsg').innerHTML=result.success?'<div class="success">✅ Password changed!</div>':'<div class="success" style="background:#EF4444;">❌ Current password incorrect</div>';});
    function editPlan(cat,idx){const name=prompt('New plan name:');const price=prompt('New price:');if(name&&price)fetch('/admin/api/edit-plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category:cat,index:idx,name,price:parseInt(price)})}).then(()=>location.reload());}
    function addPlan(cat){const name=prompt('Plan name:');const price=prompt('Price:');if(name&&price)fetch('/admin/api/add-plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category:cat,name,price:parseInt(price)})}).then(()=>location.reload());}
    function editFeature(idx){const title=prompt('Feature title:');const desc=prompt('Description:');if(title&&desc)fetch('/admin/api/edit-feature',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx,title,description:desc})}).then(()=>location.reload());}
    function deleteFeature(idx){if(confirm('Delete?'))fetch('/admin/api/delete-feature',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx})}).then(()=>location.reload());}
    function addFeature(){const title=prompt('Feature title:');const desc=prompt('Description:');if(title&&desc)fetch('/admin/api/add-feature',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,description:desc,icon:'✨'})}).then(()=>location.reload());}
    function editTestimonial(idx){const name=prompt('Name:');const content=prompt('Content:');if(name&&content)fetch('/admin/api/edit-testimonial',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx,name,content})}).then(()=>location.reload());}
    function deleteTestimonial(idx){if(confirm('Delete?'))fetch('/admin/api/delete-testimonial',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx})}).then(()=>location.reload());}
    function addTestimonial(){const name=prompt('Name:');const content=prompt('Content:');if(name&&content)fetch('/admin/api/add-testimonial',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,content,role:'Customer'})}).then(()=>location.reload());}
    function approveOrder(id){fetch('/admin/api/approve-order/'+id,{method:'POST'}).then(()=>location.reload());}
    function rejectOrder(id){fetch('/admin/api/reject-order/'+id,{method:'POST'}).then(()=>location.reload());}
    function contactCustomer(discordId){if(discordId&&discordId!=='N/A')window.open('https://discord.com/users/'+discordId,'_blank');else alert('No Discord ID provided');}
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
    order = {"id": order_id, "items": request.json.get('items', []), "total": request.json.get('total', 0), "customer_name": request.json.get('customer_name'), "discord_id": request.json.get('discord_id'), "email": request.json.get('email'), "transaction_id": request.json.get('transaction_id'), "status": "pending", "date": datetime.now().isoformat()}
    data['orders'].insert(0, order)
    save_db(data)
    webhook_url = data['bot_config'].get('webhook_url')
    if webhook_url:
        items_text = "\n".join([f"• {item['quantity']}x {item['name']} - ${item['price']}" for item in order['items']])
        send_discord_webhook(webhook_url, "🛒 New Order - Pending Approval", f"**Order ID:** `{order_id}`\n**Customer:** {order['customer_name']}\n**Total:** ${order['total']}\n\n**Items:**\n{items_text}", 0xF59E0B)
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
    data['admin']['main_admin_id'] = request.json.get('main_admin_id')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-payment', methods=['POST'])
def save_payment():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['payment_config']['upi_id'] = request.json.get('upi_id')
    data['payment_config']['bank_name'] = request.json.get('bank_name')
    data['payment_config']['account_number'] = request.json.get('account_number')
    data['payment_config']['ifsc_code'] = request.json.get('ifsc_code')
    data['payment_config']['payment_instructions'] = request.json.get('payment_instructions')
    save_db(data)
    return jsonify({"success": True})

@app.route('/admin/api/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = load_db()
    data['settings']['website_name'] = request.json.get('website_name')
    data['settings']['logo_url'] = request.json.get('logo_url')
    data['settings']['primary_color'] = request.json.get('primary_color')
    data['settings']['hero_title'] = request.json.get('hero_title')
    data['settings']['hero_subtitle'] = request.json.get('hero_subtitle')
    data['settings']['contact_email'] = request.json.get('contact_email')
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
    print("=" * 60)
    print("🚀 Prime Web Ultimate Platform Starting...")
    print("=" * 60)
    print("📱 Website: http://localhost:5000")
    print("🔐 Admin Login: admin@primeweb.com / admin123")
    print("🤖 Bot: Configure token in Admin Panel → Bot Control")
    print("💬 Bot Commands: /plans, /help, /ticket, /ping, /status, /activity, /userinfo, /server, /announce")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
