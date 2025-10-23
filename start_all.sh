#!/bin/bash

# Code Backup Daemon - Complete Launcher
# Starts both Backend (Python daemon) and Frontend (React dev server)

set -e

PROJECT_DIR="/home/nayan-ai4m/Desktop/NK/automated-github-push"
cd "$PROJECT_DIR"

echo "============================================================"
echo "🚀 Code Backup Daemon - Complete Setup"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "   Installing Python dependencies..."
    pip install -r requirements.txt
    pip install -e .
else
    echo "✅ Virtual environment found"
fi

# Check if node_modules exists
if [ ! -d "web-ui/node_modules" ]; then
    echo "❌ Node modules not found!"
    echo "   Installing Node dependencies..."
    cd web-ui
    npm install
    cd ..
else
    echo "✅ Node modules found"
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
    echo "  cp .env.example .env"
    echo "  nano .env  # Add your tokens"
    exit 1
fi

# Verify tokens are set
if [ -z "$GITHUB_TOKEN_NK" ] || [ -z "$GITHUB_TOKEN_AI4M" ]; then
    echo "❌ ERROR: GitHub tokens not set in .env file!"
    echo "   Please edit .env and add your tokens"
    exit 1
fi

echo "✅ GitHub tokens loaded"
echo ""
echo "============================================================"
echo "Starting Services..."
echo "============================================================"
echo ""

# Create log directory if it doesn't exist
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "============================================================"
    echo "🛑 Shutting down services..."
    echo "============================================================"

    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    echo "✅ All services stopped"
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Backend (Python daemon with Flask server)
echo "📡 Starting Backend Daemon..."
python -m code_backup_daemon.cli start > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Backend logs: logs/backend.log"
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start! Check logs/backend.log"
    exit 1
fi

echo "✅ Backend started on http://127.0.0.1:8080"
echo ""

# Start Frontend (React dev server)
echo "⚛️  Starting Frontend Dev Server..."
cd web-ui
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"
echo "   Frontend logs: logs/frontend.log"
sleep 3

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Frontend failed to start! Check logs/frontend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Frontend started on http://localhost:5173"
echo ""

# Display status
echo "============================================================"
echo "✅ ALL SERVICES RUNNING!"
echo "============================================================"
echo ""
echo "📊 Access Points:"
echo "   • Web UI:        http://localhost:5173"
echo "   • Backend API:   http://127.0.0.1:8080"
echo ""
echo "📝 Logs:"
echo "   • Backend:  tail -f logs/backend.log"
echo "   • Frontend: tail -f logs/frontend.log"
echo ""
echo "📁 Watching Folders:"
echo "   • /home/nayan-ai4m/Desktop/NK (Account: 2003nayan)"
echo "   • /home/nayan-ai4m/Desktop/AI4M (Account: nayan-ai4m)"
echo ""
echo "⏰ Auto-backup interval: Every 6 hours"
echo ""
echo "============================================================"
echo "Press Ctrl+C to stop all services"
echo "============================================================"

# Keep script running and wait for processes
wait $BACKEND_PID $FRONTEND_PID
