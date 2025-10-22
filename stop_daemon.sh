#!/usr/bin/env bash
#
# Stop Code Backup Daemon
#

set -e

# Load environment variables from .env file (if exists)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Stopping Code Backup Daemon..."

# Activate virtual environment
source venv/bin/activate

# Stop daemon
python -m code_backup_daemon.cli stop

echo "Daemon stopped."
