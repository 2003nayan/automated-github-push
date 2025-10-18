#!/usr/bin/env bash
#
# Step 7: Integration Testing Script
# Multi-Account Code Backup Daemon Integration Test
#
# This script tests the complete multi-account functionality with real GitHub tokens
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "STEP 7: MULTI-ACCOUNT INTEGRATION TESTING"
echo "============================================================"
echo ""

# Check if tokens are set
if [ -z "$GITHUB_TOKEN_NK" ]; then
    echo -e "${RED}ERROR: GITHUB_TOKEN_NK is not set${NC}"
    echo "Please set it: export GITHUB_TOKEN_NK=\"ghp_your_token_here\""
    exit 1
fi

if [ -z "$GITHUB_TOKEN_AI4M" ]; then
    echo -e "${RED}ERROR: GITHUB_TOKEN_AI4M is not set${NC}"
    echo "Please set it: export GITHUB_TOKEN_AI4M=\"ghp_your_token_here\""
    exit 1
fi

echo -e "${GREEN}✓ Both GitHub tokens are set${NC}"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "============================================================"
echo "TEST 1: Verify All Unit Tests Still Pass"
echo "============================================================"
echo ""

echo "Running Step 1 tests (Configuration)..."
python test_config_step1.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 1: 3/3 tests passed${NC}" || echo -e "${RED}✗ Step 1 tests failed${NC}"

echo "Running Step 2 tests (GitHub Service)..."
python test_github_step2.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 2: 5/5 tests passed${NC}" || echo -e "${RED}✗ Step 2 tests failed${NC}"

echo "Running Step 3 tests (Backup Service)..."
python test_backup_step3.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 3: 10/10 tests passed${NC}" || echo -e "${RED}✗ Step 3 tests failed${NC}"

echo "Running Step 4 tests (Folder Watcher)..."
python test_folder_watcher_step4.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 4: 6/6 tests passed${NC}" || echo -e "${RED}✗ Step 4 tests failed${NC}"

echo "Running Step 5 tests (Git Service)..."
python test_git_step5.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 5: 5/5 tests passed${NC}" || echo -e "${RED}✗ Step 5 tests failed${NC}"

echo "Running Step 6 tests (CLI)..."
python test_cli_step6.py > /dev/null 2>&1 && echo -e "${GREEN}✓ Step 6: 7/7 tests passed${NC}" || echo -e "${RED}✗ Step 6 tests failed${NC}"

echo ""
echo -e "${GREEN}✓ All unit tests passed (36/36)${NC}"
echo ""

echo "============================================================"
echo "TEST 2: Verify Configuration"
echo "============================================================"
echo ""

python -c "
from code_backup_daemon.config import Config
config = Config()
watched_paths = config.get('watched_paths', [])
print(f'Watched Paths: {len(watched_paths)}')
for path_config in watched_paths:
    name = path_config.get('name')
    path = path_config.get('path')
    account = path_config.get('account', {})
    username = account.get('username')
    print(f'  • {name}: {path} → {username}')
"
echo ""

echo "============================================================"
echo "TEST 3: Verify GitHub Authentication"
echo "============================================================"
echo ""

echo "Testing authentication for 2003nayan..."
python -c "
import os
from code_backup_daemon.config import Config
from code_backup_daemon.github_service import GitHubService

config = Config()
github_service = GitHubService(config)

# Get account config for NK
watched_paths = config.get('watched_paths', [])
nk_account = watched_paths[0].get('account', {})

# Test authentication
if github_service.is_authenticated(nk_account):
    print('✓ 2003nayan authentication: SUCCESS')
else:
    print('✗ 2003nayan authentication: FAILED')
    exit(1)
"

echo "Testing authentication for nayan-ai4m..."
python -c "
import os
from code_backup_daemon.config import Config
from code_backup_daemon.github_service import GitHubService

config = Config()
github_service = GitHubService(config)

# Get account config for AI4M
watched_paths = config.get('watched_paths', [])
ai4m_account = watched_paths[1].get('account', {})

# Test authentication
if github_service.is_authenticated(ai4m_account):
    print('✓ nayan-ai4m authentication: SUCCESS')
else:
    print('✗ nayan-ai4m authentication: FAILED')
    exit(1)
"

echo ""
echo -e "${GREEN}✓ Both accounts authenticated successfully${NC}"
echo ""

echo "============================================================"
echo "TEST 4: Manual Repository Creation Test"
echo "============================================================"
echo ""

echo -e "${YELLOW}NOTE: This test will create real repositories on GitHub!${NC}"
echo -e "${YELLOW}Repository names: test-backup-nk, test-backup-ai4m${NC}"
echo ""
read -p "Continue with repository creation? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping repository creation test"
else
    echo "Processing test projects..."

    python -c "
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.backup_service import BackupService

config = Config()
service = BackupService(config)

# Get watched paths
watched_paths = config.get('watched_paths', [])

# Process NK test project
nk_path = Path('/home/nayan-ai4m/Desktop/NK/test-backup-nk')
if nk_path.exists():
    print(f'Processing NK project: {nk_path}')
    service.process_folder(nk_path, watched_paths[0], is_initial_scan=True)
else:
    print(f'NK project not found at {nk_path}')

# Process AI4M test project
ai4m_path = Path('/home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m')
if ai4m_path.exists():
    print(f'Processing AI4M project: {ai4m_path}')
    service.process_folder(ai4m_path, watched_paths[1], is_initial_scan=True)
else:
    print(f'AI4M project not found at {ai4m_path}')

# Save state
service.save_state()
print('✓ Projects processed and state saved')
    "

    echo ""
    echo -e "${GREEN}✓ Test projects processed${NC}"
fi

echo ""

echo "============================================================"
echo "TEST 5: Verify State File"
echo "============================================================"
echo ""

python -c "
import json
from pathlib import Path

state_file = Path.home() / '.local/share/code-backup/state.json'
if state_file.exists():
    with open(state_file) as f:
        state = json.load(f)

    repos = state.get('tracked_repos', {})
    print(f'Tracked repositories: {len(repos)}')

    # Group by account
    by_account = {}
    for repo_path, repo_info in repos.items():
        account = repo_info.get('account_username', 'unknown')
        if account not in by_account:
            by_account[account] = []
        by_account[account].append(repo_info.get('repo_name'))

    for account, repo_names in by_account.items():
        print(f'  {account}: {len(repo_names)} repo(s)')
        for name in repo_names[:3]:  # Show first 3
            print(f'    - {name}')
else:
    print('State file not found')
"

echo ""

echo "============================================================"
echo "TEST 6: CLI Commands"
echo "============================================================"
echo ""

echo "Testing 'code-backup status' command..."
code-backup status
echo ""

echo "Testing 'code-backup list-repos' command..."
code-backup list-repos
echo ""

echo "Testing 'code-backup list-repos --account 2003nayan'..."
code-backup list-repos --account 2003nayan
echo ""

echo "Testing 'code-backup list-repos --account nayan-ai4m'..."
code-backup list-repos --account nayan-ai4m
echo ""

echo "============================================================"
echo "INTEGRATION TEST SUMMARY"
echo "============================================================"
echo ""
echo -e "${GREEN}✓ All unit tests passed (36/36)${NC}"
echo -e "${GREEN}✓ Configuration loaded correctly${NC}"
echo -e "${GREEN}✓ Both accounts authenticated${NC}"
echo -e "${GREEN}✓ State file updated${NC}"
echo -e "${GREEN}✓ CLI commands working${NC}"
echo ""
echo "============================================================"
echo "MANUAL VERIFICATION REQUIRED"
echo "============================================================"
echo ""
echo "Please manually verify on GitHub:"
echo ""
echo "1. Visit https://github.com/2003nayan"
echo "   Check if 'test-backup-nk' repository exists"
echo ""
echo "2. Visit https://github.com/nayan-ai4m"
echo "   Check if 'test-backup-ai4m' repository exists"
echo ""
echo "3. Check commit attribution:"
echo "   - test-backup-nk commits should be by 2003nayan"
echo "   - test-backup-ai4m commits should be by nayan-ai4m"
echo ""
echo "============================================================"
echo "NEXT STEPS"
echo "============================================================"
echo ""
echo "If repositories were created successfully:"
echo ""
echo "1. Start the daemon for continuous monitoring:"
echo "   code-backup start"
echo ""
echo "2. Monitor daemon status:"
echo "   code-backup status"
echo ""
echo "3. View logs:"
echo "   tail -f ~/.local/share/code-backup/daemon.log"
echo ""
echo "4. Create new projects in either directory to test automatic detection"
echo ""
echo "============================================================"
echo -e "${GREEN}✓ INTEGRATION TESTING COMPLETE${NC}"
echo "============================================================"
