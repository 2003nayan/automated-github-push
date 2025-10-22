#!/usr/bin/env bash
#
# Start Code Backup Daemon in Foreground
# Good for testing and seeing live logs
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
echo "Starting Code Backup Daemon (Multi-Account Mode)"
echo "============================================================"
echo ""
echo "Watching:"
echo "  • /home/nayan-ai4m/Desktop/NK (Account: 2003nayan)"
echo "  • /home/nayan-ai4m/Desktop/AI4M (Account: nayan-ai4m)"
echo ""
echo "Press Ctrl+C to stop the daemon"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Start daemon (runs in foreground by default)
python -m code_backup_daemon.cli start
