#!/usr/bin/env bash
#
# Start Code Backup Daemon as Background Service
# Runs continuously, auto-backs up every 6 hours
#

set -e

# Set environment variables for GitHub tokens
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

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
