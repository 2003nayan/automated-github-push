#!/usr/bin/env python3
"""
Test script for Step 1: Configuration System Refactoring
Tests the new multi-account configuration structure
"""

import sys
from pathlib import Path

# Add code_backup_daemon to path
sys.path.insert(0, str(Path(__file__).parent))

from code_backup_daemon.config import Config
import tempfile
import yaml

def test_new_config_structure():
    """Test new multi-account configuration structure"""
    print("=" * 60)
    print("TEST 1: New Configuration Structure")
    print("=" * 60)

    # Create a temporary config file with new structure
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'daemon': {
                'backup_interval': 86400,
                'log_level': 'INFO',
                'pid_file': '~/.local/share/code-backup/daemon.pid',
                'log_file': '~/.local/share/code-backup/daemon.log',
                'state_file': '~/.local/share/code-backup/state.json'
            },
            'paths': {
                'config_dir': '~/.config/code-backup',
                'data_dir': '~/.local/share/code-backup'
            },
            'watched_paths': [
                {
                    'name': 'NK Projects',
                    'path': '/home/nayan-ai4m/Desktop/NK',
                    'github': {
                        'username': '2003nayan',
                        'token_env_var': 'GITHUB_TOKEN_NK',
                        'default_visibility': 'private',
                        'use_gh_cli': False
                    },
                    'git': {
                        'default_branch': 'main'
                    }
                },
                {
                    'name': 'AI4M Projects',
                    'path': '/home/nayan-ai4m/Desktop/AI4M',
                    'github': {
                        'username': 'nayan-ai4m',
                        'token_env_var': 'GITHUB_TOKEN_AI4M',
                        'default_visibility': 'private',
                        'use_gh_cli': False
                    },
                    'git': {
                        'default_branch': 'main'
                    }
                }
            ]
        }
        yaml.dump(config_data, f)
        temp_config_path = f.name

    try:
        # Load config
        config = Config(temp_config_path)

        # Test get_all_watched_paths
        watched_paths = config.get_all_watched_paths()
        print(f"\n✓ Loaded {len(watched_paths)} watched paths")
        for idx, path_config in enumerate(watched_paths, 1):
            print(f"  {idx}. {path_config['name']}: {path_config['path']} → {path_config['github']['username']}")

        # Test get_path_config
        test_path = Path('/home/nayan-ai4m/Desktop/NK/test-project')
        path_config = config.get_path_config(test_path)
        if path_config:
            print(f"\n✓ Found config for {test_path}")
            print(f"  Account: {path_config['github']['username']}")
        else:
            print(f"\n✗ Could not find config for {test_path}")

        # Test get_github_config_for_path
        github_config = config.get_github_config_for_path(test_path)
        if github_config:
            print(f"\n✓ GitHub config for path:")
            print(f"  Username: {github_config['username']}")
            print(f"  Token Env Var: {github_config['token_env_var']}")
            print(f"  Use gh CLI: {github_config['use_gh_cli']}")

        print("\n✅ TEST 1 PASSED\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        Path(temp_config_path).unlink(missing_ok=True)


def test_old_config_migration():
    """Test migration from old single-account format"""
    print("=" * 60)
    print("TEST 2: Old Configuration Migration")
    print("=" * 60)

    # Create a temporary config file with OLD structure
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        old_config_data = {
            'daemon': {
                'backup_interval': 86400,
                'log_level': 'INFO',
                'pid_file': '~/.local/share/code-backup/daemon.pid',
                'log_file': '~/.local/share/code-backup/daemon.log',
                'state_file': '~/.local/share/code-backup/state.json'
            },
            'paths': {
                'code_folder': '/home/nayan-ai4m/Desktop/NK',  # OLD FORMAT
                'config_dir': '~/.config/code-backup',
                'data_dir': '~/.local/share/code-backup'
            },
            'github': {  # OLD FORMAT
                'username': '2003nayan',
                'default_visibility': 'private',
                'use_gh_cli': True
            },
            'git': {  # OLD FORMAT
                'default_branch': 'main',
                'auto_commit_message': 'Auto-backup: {timestamp}'
            }
        }
        yaml.dump(old_config_data, f)
        temp_config_path = f.name

    try:
        # Load config (should auto-migrate)
        config = Config(temp_config_path)

        # Check if migrated to new format
        watched_paths = config.get_all_watched_paths()

        if not watched_paths:
            print("\n✗ Migration failed: No watched_paths found")
            return False

        print(f"\n✓ Successfully migrated old config")
        print(f"  Created {len(watched_paths)} watched path(s)")

        path_config = watched_paths[0]
        print(f"\n  Name: {path_config['name']}")
        print(f"  Path: {path_config['path']}")
        print(f"  GitHub Username: {path_config['github']['username']}")
        print(f"  Default Branch: {path_config['git']['default_branch']}")

        # Verify backup was created
        backup_path = Path(temp_config_path).parent / f"{Path(temp_config_path).name}.old"
        if backup_path.exists():
            print(f"\n✓ Backup created at: {backup_path}")
            backup_path.unlink()
        else:
            print(f"\n⚠ No backup file created (might be in temp directory)")

        print("\n✅ TEST 2 PASSED\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        Path(temp_config_path).unlink(missing_ok=True)


def test_validation():
    """Test configuration validation"""
    print("=" * 60)
    print("TEST 3: Configuration Validation")
    print("=" * 60)

    # Test 3a: Valid configuration
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        valid_config = {
            'daemon': {'backup_interval': 86400},
            'paths': {'config_dir': '~/.config', 'data_dir': '~/.local/share'},
            'watched_paths': [
                {
                    'name': 'Test',
                    'path': str(Path.home()),  # Use home dir (guaranteed to exist)
                    'github': {'username': 'testuser'}
                }
            ]
        }
        yaml.dump(valid_config, f)
        temp_path = f.name

    try:
        config = Config(temp_path)
        if config.validate():
            print("\n✓ Valid configuration passed validation")
        else:
            print("\n✗ Valid configuration failed validation")
            return False
    finally:
        Path(temp_path).unlink(missing_ok=True)

    # Test 3b: Invalid configuration (missing username)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        invalid_config = {
            'daemon': {'backup_interval': 86400},
            'watched_paths': [
                {
                    'name': 'Test',
                    'path': str(Path.home()),
                    'github': {}  # Missing username
                }
            ]
        }
        yaml.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = Config(temp_path)
        if not config.validate():
            print("✓ Invalid configuration correctly rejected")
        else:
            print("✗ Invalid configuration incorrectly accepted")
            return False
    finally:
        Path(temp_path).unlink(missing_ok=True)

    # Test 3c: Empty watched_paths
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        empty_config = {
            'daemon': {'backup_interval': 86400},
            'watched_paths': []
        }
        yaml.dump(empty_config, f)
        temp_path = f.name

    try:
        config = Config(temp_path)
        if not config.validate():
            print("✓ Empty watched_paths correctly rejected")
        else:
            print("✗ Empty watched_paths incorrectly accepted")
            return False
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("\n✅ TEST 3 PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STEP 1 CONFIGURATION TESTS")
    print("=" * 60 + "\n")

    tests = [
        test_new_config_structure,
        test_old_config_migration,
        test_validation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! Step 1 is complete.\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
