#!/usr/bin/env bash
#
# Check Code Backup Daemon Status
#

set -e

# Set environment variables
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

# Activate virtual environment
source venv/bin/activate

# Show status
python -m code_backup_daemon.cli status

echo ""
echo "============================================================"
echo "Tracked Repositories:"
echo "============================================================"
python -m code_backup_daemon.cli list-repos
