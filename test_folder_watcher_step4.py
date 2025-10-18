#!/usr/bin/env python3
"""
Test Suite for Step 4: Folder Watcher Multi-Path Support

This test verifies that FolderWatcher correctly supports:
1. Optional watched_path parameter in __init__
2. Backward compatibility with old config format
3. Multiple watcher instances can coexist
4. Each watcher monitors its assigned path
"""

import sys
import os
import tempfile
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_backup_daemon.config import Config
from code_backup_daemon.folder_watcher import FolderWatcher


def create_test_config(code_folder_path=None):
    """Create a temporary config file for testing"""
    config_data = {
        'daemon': {
            'log_level': 'INFO',
            'backup_interval': 86400,
            'state_file': '/tmp/test_state.json',
            'pid_file': '/tmp/test_daemon.pid',
            'log_file': '/tmp/test_daemon.log'
        },
        'paths': {
            'code_folder': code_folder_path or '/tmp/test_code',
            'watched_paths': [
                {
                    'name': 'NK Projects',
                    'path': '/home/nayan-ai4m/Desktop/NK',
                    'account': {
                        'username': '2003nayan',
                        'token_env_var': 'GITHUB_TOKEN_NK',
                        'email': '2003nayan@users.noreply.github.com'
                    }
                },
                {
                    'name': 'AI4M Projects',
                    'path': '/home/nayan-ai4m/Desktop/AI4M',
                    'account': {
                        'username': 'nayan-ai4m',
                        'token_env_var': 'GITHUB_TOKEN_AI4M',
                        'email': 'nayan-ai4m@users.noreply.github.com'
                    }
                }
            ]
        },
        'github': {
            'username': 'default_user',
            'default_visibility': 'private',
            'use_gh_cli': True
        },
        'git': {
            'default_branch': 'main',
            'commit_message_template': 'Auto-backup: {date}',
            'conflict_handling': 'skip'
        },
        'project_detection': {
            'min_size_bytes': 1024,
            'ignore_patterns': ['node_modules', 'venv', '__pycache__'],
            'project_indicators': ['package.json', 'requirements.txt', 'Cargo.toml'],
            'code_extensions': ['.py', '.js', '.java', '.go', '.rs']
        }
    }

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(config_data, temp_file)
    temp_file.close()
    return temp_file.name


def test_1_init_accepts_watched_path_parameter():
    """Test 1: FolderWatcher.__init__ accepts watched_path parameter"""
    print("=" * 60)
    print("TEST 1: FolderWatcher.__init__ accepts watched_path parameter")
    print("=" * 60)

    try:
        # Create temporary directories
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()

        config_file = create_test_config(temp_dir1)
        config = Config(config_file)

        # Test 1a: Create watcher with watched_path parameter
        watcher1 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir2)
        )

        assert watcher1.code_folder == Path(temp_dir2), \
            f"Expected code_folder to be {temp_dir2}, got {watcher1.code_folder}"
        print(f"✓ Watcher created with custom watched_path: {watcher1.code_folder}")

        # Test 1b: Verify watcher uses provided path, not config path
        assert watcher1.code_folder != Path(temp_dir1), \
            "Watcher should use watched_path parameter, not config path"
        print(f"✓ Watcher correctly overrides config path with watched_path parameter")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir1)
        os.rmdir(temp_dir2)

        print("✅ TEST 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}\n")
        return False


def test_2_backward_compatibility():
    """Test 2: Backward compatibility - falls back to config when no watched_path"""
    print("=" * 60)
    print("TEST 2: Backward Compatibility")
    print("=" * 60)

    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()

        # Create config WITH code_folder for backward compatibility test
        config_file = create_test_config(temp_dir)
        config = Config(config_file)

        # Manually add code_folder to config (simulating old format that was migrated)
        config.set('paths.code_folder', temp_dir)

        # Create watcher WITHOUT watched_path parameter
        watcher = FolderWatcher(config, lambda x: None)

        assert watcher.code_folder == Path(temp_dir), \
            f"Expected code_folder to be {temp_dir}, got {watcher.code_folder}"
        print(f"✓ Watcher falls back to config.code_folder: {watcher.code_folder}")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir)

        print("✅ TEST 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}\n")
        return False


def test_3_multiple_watcher_instances():
    """Test 3: Multiple FolderWatcher instances can coexist"""
    print("=" * 60)
    print("TEST 3: Multiple Watcher Instances")
    print("=" * 60)

    try:
        # Create temporary directories for two different paths
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()

        config_file = create_test_config()
        config = Config(config_file)

        # Create two watchers with different paths
        watcher1 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir1)
        )

        watcher2 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir2)
        )

        # Verify they have different paths
        assert watcher1.code_folder != watcher2.code_folder, \
            "Watchers should have different code_folder paths"
        print(f"✓ Watcher 1 monitors: {watcher1.code_folder}")
        print(f"✓ Watcher 2 monitors: {watcher2.code_folder}")

        # Verify they are independent instances
        assert watcher1 is not watcher2, "Watchers should be independent instances"
        print(f"✓ Watchers are independent instances")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir1)
        os.rmdir(temp_dir2)

        print("✅ TEST 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}\n")
        return False


def test_4_watcher_path_independence():
    """Test 4: Each watcher maintains independent watched_folders set"""
    print("=" * 60)
    print("TEST 4: Watcher Path Independence")
    print("=" * 60)

    try:
        # Create temporary directories
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()

        config_file = create_test_config()
        config = Config(config_file)

        # Create two watchers
        watcher1 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir1)
        )

        watcher2 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir2)
        )

        # Add folder to watcher1's tracked set
        test_folder = "/test/folder/1"
        watcher1.watched_folders.add(test_folder)

        # Verify watcher2's set is independent
        assert test_folder in watcher1.watched_folders, \
            "Watcher1 should have the test folder"
        assert test_folder not in watcher2.watched_folders, \
            "Watcher2 should not have watcher1's folders"
        print(f"✓ Watcher1 tracked folders: {watcher1.watched_folders}")
        print(f"✓ Watcher2 tracked folders: {watcher2.watched_folders}")
        print(f"✓ Watchers maintain independent watched_folders sets")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir1)
        os.rmdir(temp_dir2)

        print("✅ TEST 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}\n")
        return False


def test_5_watcher_callback_independence():
    """Test 5: Each watcher can have independent callbacks"""
    print("=" * 60)
    print("TEST 5: Watcher Callback Independence")
    print("=" * 60)

    try:
        # Create temporary directories
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()

        config_file = create_test_config()
        config = Config(config_file)

        # Track callback invocations
        callback1_called = []
        callback2_called = []

        def callback1(path):
            callback1_called.append(path)

        def callback2(path):
            callback2_called.append(path)

        # Create two watchers with different callbacks
        watcher1 = FolderWatcher(
            config,
            callback1,
            watched_path=Path(temp_dir1)
        )

        watcher2 = FolderWatcher(
            config,
            callback2,
            watched_path=Path(temp_dir2)
        )

        # Verify callbacks are different
        assert watcher1.on_new_folder_callback is not watcher2.on_new_folder_callback, \
            "Watchers should have independent callbacks"
        print(f"✓ Watcher1 callback: {watcher1.on_new_folder_callback}")
        print(f"✓ Watcher2 callback: {watcher2.on_new_folder_callback}")

        # Test callback invocation
        test_path1 = Path("/test/path1")
        test_path2 = Path("/test/path2")

        watcher1.on_new_folder_callback(test_path1)
        watcher2.on_new_folder_callback(test_path2)

        assert callback1_called == [test_path1], \
            f"Callback1 should have been called with {test_path1}"
        assert callback2_called == [test_path2], \
            f"Callback2 should have been called with {test_path2}"
        print(f"✓ Callback1 received: {callback1_called}")
        print(f"✓ Callback2 received: {callback2_called}")
        print(f"✓ Callbacks are independent and work correctly")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir1)
        os.rmdir(temp_dir2)

        print("✅ TEST 5 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}\n")
        return False


def test_6_get_status_includes_correct_path():
    """Test 6: get_status() returns correct code_folder for each watcher"""
    print("=" * 60)
    print("TEST 6: get_status() Returns Correct Path")
    print("=" * 60)

    try:
        # Create temporary directories
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()

        config_file = create_test_config()
        config = Config(config_file)

        # Create two watchers
        watcher1 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir1)
        )

        watcher2 = FolderWatcher(
            config,
            lambda x: None,
            watched_path=Path(temp_dir2)
        )

        # Get status for each watcher
        status1 = watcher1.get_status()
        status2 = watcher2.get_status()

        # Verify code_folder in status
        assert status1['code_folder'] == str(Path(temp_dir1)), \
            f"Watcher1 status should show {temp_dir1}"
        assert status2['code_folder'] == str(Path(temp_dir2)), \
            f"Watcher2 status should show {temp_dir2}"

        print(f"✓ Watcher1 status: {status1['code_folder']}")
        print(f"✓ Watcher2 status: {status2['code_folder']}")
        print(f"✓ Each watcher reports correct code_folder in status")

        # Cleanup
        os.unlink(config_file)
        os.rmdir(temp_dir1)
        os.rmdir(temp_dir2)

        print("✅ TEST 6 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ TEST 6 FAILED: {e}\n")
        return False


def main():
    print("\n" + "=" * 60)
    print("STEP 4 TEST SUITE: Folder Watcher Multi-Path Support")
    print("=" * 60 + "\n")

    tests = [
        test_1_init_accepts_watched_path_parameter,
        test_2_backward_compatibility,
        test_3_multiple_watcher_instances,
        test_4_watcher_path_independence,
        test_5_watcher_callback_independence,
        test_6_get_status_includes_correct_path
    ]

    results = []
    for test in tests:
        results.append(test())

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 60)
    print(f"SUMMARY: Passed {passed}/{total} tests")
    print("=" * 60)

    if passed == total:
        print("✅ ALL TESTS PASSED - Step 4 Implementation Complete!")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
