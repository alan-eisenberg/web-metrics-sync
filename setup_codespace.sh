#!/bin/bash
set -e

echo "========================================================"
echo "  Setting up Z.ai Farm Environment (Codespace / xRDP)   "
echo "========================================================"

# 1. Fix TUN device for OpenVPN in Docker/Codespaces
echo "[1/5] Configuring OpenVPN TUN device for containers..."
sudo mkdir -p /dev/net
# Create the tun device if it doesn't exist (ignore error if it does)
sudo mknod /dev/net/tun c 10 200 2>/dev/null || true
sudo chmod 600 /dev/net/tun

# 2. Install System Dependencies
echo "[2/5] Updating packages and installing core tools..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip openvpn curl wget unzip git xvfb x11-xserver-utils

# 3. Install Google Chrome (Crucial for Docker)
# We install official Google Chrome instead of Chromium because Ubuntu's Chromium 
# is a "snap" package, which notoriously crashes inside Docker/Codespaces.
echo "[3/5] Installing Google Chrome (Stable)..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 2>/dev/null || true
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Note: Selenium 4+ automatically downloads the correct ChromeDriver via "Selenium Manager", 
# so we don't need to manually install chromedriver if your requirements.txt has a recent selenium version!

# 4. Setup Python Environment
echo "[4/5] Setting up Python virtual environment..."
# Ensure we are in the project root
if [ -d "automation" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "Warning: requirements.txt not found. Please install python packages manually."
    fi
else
    echo "Warning: Not inside the zai-automation folder. Skipping Python venv creation."
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

echo "========================================================"
echo "  Setup Complete!                                       "
echo "========================================================"
echo ""
echo "To run your farm with the UI visible on Chrome Remote Desktop / xRDP:"
echo "1. Activate your environment: source .venv/bin/activate"
echo "2. Export the display:        export DISPLAY=:1  (or :0 depending on your remote desktop)"
echo "3. Run the bot:               python -m automation.main --stage full --monos"
