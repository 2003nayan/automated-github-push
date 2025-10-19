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

# Set environment variables
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

echo "📡 Starting daemon with web UI..."
echo ""

# Start daemon (it will start web UI automatically)
python -m code_backup_daemon.cli start

# Note: The daemon's CLI now starts the web UI automatically
# The daemon runs in foreground, web UI runs in a background thread
