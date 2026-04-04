# install.sh - VPS Deployment Script
#!/bin/bash
echo "🚀 Installing VectoNodes Platform..."
echo "======================================"

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python3 and pip
sudo apt install python3 python3-pip nginx -y

# Install Gunicorn
pip3 install gunicorn

# Clone repository (replace with your repo URL)
# git clone https://github.com/yourusername/vectonodes-dashboard.git
# cd vectonodes-dashboard

# Install dependencies
pip3 install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/vectonodes.service > /dev/null << 'EOF'
[Unit]
Description=VectoNodes Dashboard
After=network.target

[Service]
User=$USER
WorkingDirectory=$PWD
Environment="PATH=/usr/local/bin:$PATH"
ExecStart=/usr/local/bin/gunicorn app:app --bind 127.0.0.1:5000 --workers=3 --threads=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable vectonodes
sudo systemctl start vectonodes

# Configure Nginx
sudo tee /etc/nginx/sites-available/vectonodes > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/vectonodes /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "======================================"
echo "✅ Installation Complete!"
echo "🌐 Visit: http://$(curl -s ifconfig.me)"
echo "📧 Admin: vecto@dash.co"
echo "🔑 Password: prime123"
echo "⚠️  Change password on first login!"
echo "======================================"
