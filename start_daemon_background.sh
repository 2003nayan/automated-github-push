#!/usr/bin/env bash
#
# Start Code Backup Daemon as Background Service
# Runs continuously, auto-backs up every 6 hours
#

set -e

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

echo "============================================================"
echo "Starting Code Backup Daemon (Background Mode)"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Start daemon in background
python -m code_backup_daemon.cli start

echo ""
echo "Daemon started! Check status with:"
echo "  ./check_daemon_status.sh"
echo ""
echo "View logs with:"
echo "  tail -f ~/.local/share/code-backup/daemon.log"
echo ""
echo "Stop with:"
echo "  ./stop_daemon.sh"
echo ""
