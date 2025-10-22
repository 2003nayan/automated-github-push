#!/bin/bash

# Stop all Code Backup Daemon services

echo "============================================================"
echo "🛑 Stopping Code Backup Daemon Services"
echo "============================================================"
echo ""

# Stop Python daemon
echo "📡 Stopping Backend Daemon..."
pkill -f "code_backup_daemon.cli" && echo "✅ Backend stopped" || echo "⚠️  Backend not running"

# Stop React dev server
echo "⚛️  Stopping Frontend Dev Server..."
pkill -f "vite" && echo "✅ Frontend stopped" || echo "⚠️  Frontend not running"

# Stop any remaining node processes for this project
pkill -f "node.*web-ui" 2>/dev/null

echo ""
echo "✅ All services stopped"
