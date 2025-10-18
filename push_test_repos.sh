#!/usr/bin/env bash
#
# Push Test Repositories to GitHub
# This script pushes the test repositories with proper authentication
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo "Pushing Test Repositories to GitHub"
echo "============================================================"
echo ""

# Set your tokens here (replace with actual full tokens)
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

# Check tokens
if [ -z "$GITHUB_TOKEN_NK" ]; then
    echo -e "${RED}ERROR: GITHUB_TOKEN_NK not set${NC}"
    exit 1
fi

if [ -z "$GITHUB_TOKEN_AI4M" ]; then
    echo -e "${RED}ERROR: GITHUB_TOKEN_AI4M not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tokens are set${NC}"
echo ""

# Activate venv and use Python to push
source venv/bin/activate

python << 'PYTHON_SCRIPT'
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.git_service import GitService
from code_backup_daemon.github_service import GitHubService

config = Config()
git_service = GitService(config)
github_service = GitHubService(config)

watched_paths = config.get('watched_paths', [])

# Process NK project
print("Processing NK project...")
nk_path = Path('/home/nayan-ai4m/Desktop/NK/test-backup-nk')
nk_account = watched_paths[0].get('account', {})

# Ensure remote is set
remote_url = f"https://github.com/{nk_account['username']}/test-backup-nk.git"
if not git_service.has_remote(nk_path):
    git_service.add_remote(nk_path, remote_url)

# Push
if git_service.push_changes(nk_path):
    print(f"✓ Successfully pushed test-backup-nk")
else:
    print(f"✗ Failed to push test-backup-nk")

print()

# Process AI4M project
print("Processing AI4M project...")
ai4m_path = Path('/home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m')
ai4m_account = watched_paths[1].get('account', {})

# Ensure remote is set
remote_url = f"https://github.com/{ai4m_account['username']}/test-backup-ai4m.git"
if not git_service.has_remote(ai4m_path):
    git_service.add_remote(ai4m_path, remote_url)

# Push
if git_service.push_changes(ai4m_path):
    print(f"✓ Successfully pushed test-backup-ai4m")
else:
    print(f"✗ Failed to push test-backup-ai4m")

print()
print("Done!")
PYTHON_SCRIPT

echo ""
echo "============================================================"
echo "Verification"
echo "============================================================"
echo ""
echo "Please verify on GitHub:"
echo "  1. https://github.com/2003nayan/test-backup-nk"
echo "  2. https://github.com/nayan-ai4m/test-backup-ai4m"
echo ""
