#!/usr/bin/env bash
#
# Start Code Backup Daemon in Foreground
# Good for testing and seeing live logs
#

set -e

# Set environment variables for GitHub tokens
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

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
