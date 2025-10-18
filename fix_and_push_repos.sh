#!/usr/bin/env bash
#
# Fix GitHub Repositories Creation and Push
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
echo "Fix and Push Test Repositories to GitHub"
echo "============================================================"
echo ""

# Set your tokens (already exported in environment)
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

# Change to project directory
cd /home/nayan-ai4m/Desktop/NK/automated-github-push

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "============================================================"
echo "Step 1: Create GitHub Repositories via API"
echo "============================================================"
echo ""

# Create AI4M repository (NK already exists)
echo "Creating AI4M repository: test-backup-ai4m..."
curl -X POST \
    -H "Authorization: token $GITHUB_TOKEN_AI4M" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user/repos \
    -d '{
        "name": "test-backup-ai4m",
        "description": "Test backup project for AI4M account - Multi-account daemon testing",
        "private": true,
        "auto_init": false
    }' 2>&1 | grep -q '"full_name"' && echo -e "${GREEN}✓ Created: nayan-ai4m/test-backup-ai4m${NC}" || echo -e "${YELLOW}ℹ Repository may already exist${NC}"

echo ""

# Also check NK repository exists
echo "Checking NK repository: test-backup-nk..."
curl -s \
    -H "Authorization: token $GITHUB_TOKEN_NK" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/2003nayan/test-backup-nk | grep -q '"full_name"' && echo -e "${GREEN}✓ Exists: 2003nayan/test-backup-nk${NC}" || echo -e "${RED}✗ Does not exist${NC}"

echo ""
echo "============================================================"
echo "Step 2: Push Local Repositories"
echo "============================================================"
echo ""

# Push NK repository
echo "Pushing NK repository..."
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
if git push -u origin main 2>&1; then
    echo -e "${GREEN}✓ Successfully pushed test-backup-nk${NC}"
else
    echo -e "${YELLOW}⚠ Push may have failed or already up-to-date${NC}"
fi

echo ""

# Push AI4M repository
echo "Pushing AI4M repository..."
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m

# Ensure remote is configured correctly
if ! git remote get-url origin &>/dev/null; then
    echo "Adding remote origin..."
    git remote add origin https://github.com/nayan-ai4m/test-backup-ai4m.git
fi

# Push with upstream
if git push -u origin main 2>&1; then
    echo -e "${GREEN}✓ Successfully pushed test-backup-ai4m${NC}"
else
    echo -e "${RED}✗ Failed to push test-backup-ai4m${NC}"
    echo "Error details above"
fi

cd /home/nayan-ai4m/Desktop/NK/automated-github-push

echo ""
echo "============================================================"
echo "Step 3: Verify Commit Attribution"
echo "============================================================"
echo ""

echo "NK Project:"
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
echo "  Configured: $(git config user.name) <$(git config user.email)>"
echo "  Last commit: $(git log --format='%an <%ae>' -1 2>/dev/null || echo 'No commits')"

echo ""
echo "AI4M Project:"
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m
echo "  Configured: $(git config user.name) <$(git config user.email)>"
echo "  Last commit: $(git log --format='%an <%ae>' -1 2>/dev/null || echo 'No commits')"

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
