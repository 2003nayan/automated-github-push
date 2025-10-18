#!/usr/bin/env bash
#
# Create and Push Test Repositories to GitHub
# This script creates the GitHub repositories first, then pushes
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================================"
echo "Create and Push Test Repositories to GitHub"
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

# Activate venv
source venv/bin/activate

echo "============================================================"
echo "Step 1: Create GitHub Repositories"
echo "============================================================"
echo ""

python << 'PYTHON_SCRIPT'
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.git_service import GitService
from code_backup_daemon.github_service import GitHubService

config = Config()
git_service = GitService(config)
github_service = GitHubService(config)

watched_paths = config.get('watched_paths', [])

# Create NK repository
print("Creating repository: test-backup-nk...")
nk_account = watched_paths[0].get('account', {})
nk_username = nk_account.get('username')

if github_service.repo_exists('test-backup-nk', nk_account):
    print(f"  ℹ Repository already exists: {nk_username}/test-backup-nk")
else:
    if github_service.create_repository('test-backup-nk', nk_account):
        print(f"  ✓ Created: {nk_username}/test-backup-nk")
    else:
        print(f"  ✗ Failed to create: {nk_username}/test-backup-nk")

print()

# Create AI4M repository
print("Creating repository: test-backup-ai4m...")
ai4m_account = watched_paths[1].get('account', {})
ai4m_username = ai4m_account.get('username')

if github_service.repo_exists('test-backup-ai4m', ai4m_account):
    print(f"  ℹ Repository already exists: {ai4m_username}/test-backup-ai4m")
else:
    if github_service.create_repository('test-backup-ai4m', ai4m_account):
        print(f"  ✓ Created: {ai4m_username}/test-backup-ai4m")
    else:
        print(f"  ✗ Failed to create: {ai4m_username}/test-backup-ai4m")

PYTHON_SCRIPT

echo ""
echo "============================================================"
echo "Step 2: Push Local Repositories"
echo "============================================================"
echo ""

python << 'PYTHON_SCRIPT'
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.git_service import GitService

config = Config()
git_service = GitService(config)

watched_paths = config.get('watched_paths', [])

# Push NK project
print("Pushing NK project...")
nk_path = Path('/home/nayan-ai4m/Desktop/NK/test-backup-nk')
nk_account = watched_paths[0].get('account', {})

# Ensure remote is set
remote_url = f"https://github.com/{nk_account['username']}/test-backup-nk.git"
if not git_service.has_remote(nk_path):
    git_service.add_remote(nk_path, remote_url)

# Push
if git_service.push_changes(nk_path):
    print(f"  ✓ Successfully pushed test-backup-nk")
else:
    print(f"  ✗ Failed to push test-backup-nk")

print()

# Push AI4M project
print("Pushing AI4M project...")
ai4m_path = Path('/home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m')
ai4m_account = watched_paths[1].get('account', {})

# Ensure remote is set
remote_url = f"https://github.com/{ai4m_account['username']}/test-backup-ai4m.git"
if not git_service.has_remote(ai4m_path):
    git_service.add_remote(ai4m_path, remote_url)

# Push
if git_service.push_changes(ai4m_path):
    print(f"  ✓ Successfully pushed test-backup-ai4m")
else:
    print(f"  ✗ Failed to push test-backup-ai4m")

PYTHON_SCRIPT

echo ""
echo "============================================================"
echo "Step 3: Verify Commit Attribution"
echo "============================================================"
echo ""

echo "NK Project:"
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
echo "  Configured: $(git config user.name) <$(git config user.email)>"
echo "  Last commit: $(git log --format='%an <%ae>' -1)"

echo ""
echo "AI4M Project:"
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m
echo "  Configured: $(git config user.name) <$(git config user.email)>"
echo "  Last commit: $(git log --format='%an <%ae>' -1)"

cd /home/nayan-ai4m/Desktop/NK/automated-github-push

echo ""
echo "============================================================"
echo "✓ COMPLETE - Verification Required"
echo "============================================================"
echo ""
echo "Please verify on GitHub:"
echo ""
echo -e "${BLUE}1. NK Account (2003nayan):${NC}"
echo "   https://github.com/2003nayan/test-backup-nk"
echo ""
echo -e "${BLUE}2. AI4M Account (nayan-ai4m):${NC}"
echo "   https://github.com/nayan-ai4m/test-backup-ai4m"
echo ""
echo -e "${YELLOW}Note:${NC} The first commits may show your personal email."
echo "Future commits will use the correct account-specific emails."
echo ""
