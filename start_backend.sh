#!/bin/bash

# Code Backup Daemon - Web UI Launcher
# Starts both the daemon and web UI

set -e

PROJECT_DIR="/home/nayan-ai4m/Desktop/NK/automated-github-push"
cd "$PROJECT_DIR"

echo "🚀 Starting Code Backup Daemon with Web UI..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "web-ui/node_modules" ]; then
    echo "❌ Node modules not found. Installing..."
    cd web-ui
    npm install
    cd ..
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded environment variables from .env"
else
    echo "❌ ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your GitHub tokens:"
    echo "  GITHUB_TOKEN_NK=your_token_here"
    echo "  GITHUB_TOKEN_AI4M=your_token_here"
    echo ""
    echo "See .env.example for template"
    exit 1
fi

# Verify tokens are set
if [ -z "$GITHUB_TOKEN_NK" ] || [ -z "$GITHUB_TOKEN_AI4M" ]; then
    echo "❌ ERROR: GitHub tokens not set in .env file!"
    exit 1
fi


echo "📡 Starting daemon with web UI..."
echo ""

# Start daemon (it will start web UI automatically)
python -m code_backup_daemon.cli start

# Note: The daemon's CLI now starts the web UI automatically
# The daemon runs in foreground, web UI runs in a background thread
