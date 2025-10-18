#!/usr/bin/env bash
#
# Stop Code Backup Daemon
#

set -e

# Set environment variables
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

echo "Stopping Code Backup Daemon..."

# Activate virtual environment
source venv/bin/activate

# Stop daemon
python -m code_backup_daemon.cli stop

echo "Daemon stopped."
