#!/usr/bin/env python3
"""
Test SSH URL Fix for Multi-Account Support
This script tests that the SSH URLs are generated correctly
"""
import os
import sys
from pathlib import Path

# Set environment variables
os.environ['GITHUB_TOKEN_NK'] = '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'
os.environ['GITHUB_TOKEN_AI4M'] = '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'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from code_backup_daemon.config import Config
from code_backup_daemon.github_service import GitHubService

def test_ssh_url_generation():
    """Test that SSH URLs are generated correctly for both accounts"""
    config = Config()
    github_service = GitHubService(config)

    watched_paths = config.get('watched_paths', [])

    print("=" * 60)
    print("Testing SSH URL Generation")
    print("=" * 60)
    print()

    # Test NK account
    print("1. NK Account (2003nayan)")
    print("-" * 60)
    nk_config = watched_paths[0]
    nk_account = nk_config.get('account', {})

    nk_ssh_url = github_service._get_ssh_url('test-backup-nk', nk_account)
    print(f"   Repository: test-backup-nk")
    print(f"   Username: {nk_account.get('username')}")
    print(f"   SSH Host: {nk_account.get('ssh_host', 'github.com')}")
    print(f"   Generated SSH URL: {nk_ssh_url}")
    print(f"   Expected: git@github.com-personal:2003nayan/test-backup-nk.git")
    print(f"   ✓ Match: {nk_ssh_url == 'git@github.com-personal:2003nayan/test-backup-nk.git'}")
    print()

    # Test AI4M account
    print("2. AI4M Account (nayan-ai4m)")
    print("-" * 60)
    ai4m_config = watched_paths[1]
    ai4m_account = ai4m_config.get('account', {})

    ai4m_ssh_url = github_service._get_ssh_url('test-backup-ai4m', ai4m_account)
    print(f"   Repository: test-backup-ai4m")
    print(f"   Username: {ai4m_account.get('username')}")
    print(f"   SSH Host: {ai4m_account.get('ssh_host', 'github.com')}")
    print(f"   Generated SSH URL: {ai4m_ssh_url}")
    print(f"   Expected: git@github.com-office:nayan-ai4m/test-backup-ai4m.git")
    print(f"   ✓ Match: {ai4m_ssh_url == 'git@github.com-office:nayan-ai4m/test-backup-ai4m.git'}")
    print()

    print("=" * 60)
    print("✓ SSH URL Generation Test Complete")
    print("=" * 60)
    print()

    return True

if __name__ == '__main__':
    try:
        test_ssh_url_generation()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
