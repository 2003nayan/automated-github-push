#!/usr/bin/env bash
#
# Update Test Repository Remotes to Use SSH URLs
# This fixes the authentication issue by using SSH with account-specific keys
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo "Update Test Repository Remotes to SSH URLs"
echo "============================================================"
echo ""

# Update NK repository
echo -e "${BLUE}1. Updating NK repository remote...${NC}"
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk

echo "   Current remote:"
git remote -v

echo "   Updating to SSH URL with github.com-personal..."
git remote set-url origin git@github.com-personal:2003nayan/test-backup-nk.git

echo "   New remote:"
git remote -v

echo -e "${GREEN}   ✓ NK repository updated${NC}"
echo ""

# Update AI4M repository
echo -e "${BLUE}2. Updating AI4M repository remote...${NC}"
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m

echo "   Current remote:"
git remote -v

echo "   Updating to SSH URL with github.com-office..."
git remote set-url origin git@github.com-office:nayan-ai4m/test-backup-ai4m.git

echo "   New remote:"
git remote -v

echo -e "${GREEN}   ✓ AI4M repository updated${NC}"
echo ""

cd /home/nayan-ai4m/Desktop/NK/automated-github-push

echo "============================================================"
echo "✓ Repository remotes updated successfully"
echo "============================================================"
echo ""
echo "Now testing push to both repositories..."
echo ""

# Test NK push
echo -e "${BLUE}Testing NK push...${NC}"
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
if git push -u origin main 2>&1; then
    echo -e "${GREEN}✓ NK push successful${NC}"
else
    echo "⚠ NK push failed (may already be up-to-date)"
fi
echo ""

# Test AI4M push
echo -e "${BLUE}Testing AI4M push...${NC}"
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m
if git push -u origin main 2>&1; then
    echo -e "${GREEN}✓ AI4M push successful${NC}"
else
    echo "⚠ AI4M push failed - check error above"
fi
echo ""

cd /home/nayan-ai4m/Desktop/NK/automated-github-push

echo "============================================================"
echo "✓ COMPLETE"
echo "============================================================"
echo ""
echo "Verify on GitHub:"
echo "  • NK:   https://github.com/2003nayan/test-backup-nk"
echo "  • AI4M: https://github.com/nayan-ai4m/test-backup-ai4m"
echo ""
