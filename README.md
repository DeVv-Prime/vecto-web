# vecto-nodes-dash
# Vectro Nodes - Premium Hosting Solution

## 🚀 Features

- **VPS Hosting** - Deploy virtual private servers
- **Minecraft Hosting** - Game server hosting
- **RDP Servers** - Remote desktop access
- **Discord Nitro** - Premium nitro plans
- **Discord Bot** - 30+ commands for management
- **Admin Panel** - Full control over everything

## 📦 Deployment on Render

### Steps to Deploy:

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on Render.com

3. **Connect your GitHub repository**

4. **Use these settings:**
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. **Add environment variables:**
   - `SECRET_KEY`: (Render will generate automatically)
   - `DISCORD_BOT_TOKEN`: (Optional - for Discord bot)

6. **Deploy!**

### Local Development

```bash
# Clone repository
git clone https://github.com/DeVv-Prime/vecto-web.git

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
