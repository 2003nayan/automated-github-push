#!/usr/bin/env bash
#
# Check Code Backup Daemon Status
#

set -e

# Load environment variables from .env file (if exists)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Show status
python -m code_backup_daemon.cli status

echo ""
echo "============================================================"
echo "Tracked Repositories:"
echo "============================================================"
python -m code_backup_daemon.cli list-repos
