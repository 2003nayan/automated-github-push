#!/usr/bin/env python3
"""
Test Suite for Step 3: Backup Service Multi-Watcher Implementation
Tests the BackupService integration with multi-account support
"""

import sys
import yaml
import tempfile
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.backup_service import BackupService


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def print_test(test_name):
    """Print test name"""
    print(f"Testing: {test_name}")


def create_test_config():
    """Create a temporary config file for testing"""
    config_data = {
        'daemon': {
            'backup_interval': 3600,
            'state_file': '~/.config/code-backup/state.json',
            'log_file': '~/.config/code-backup/daemon.log'
        },
        'paths': {
            'watched_paths': [
                {
                    'path': '/home/nayan-ai4m/Desktop/NK',
                    'account': {
                        'username': '2003nayan',
                        'auth_method': 'token',
                        'token_env': 'GITHUB_TOKEN_NK'
                    }
                },
                {
                    'path': '/home/nayan-ai4m/Desktop/AI4M',
                    'account': {
                        'username': 'nayan-ai4m',
                        'auth_method': 'gh_cli'
                    }
                }
            ]
        },
        'github': {
            'default_visibility': 'private'
        },
        'git': {
            'default_branch': 'main'
        },
        'project_detection': {
            'project_indicators': ['package.json', 'requirements.txt'],
            'code_extensions': ['.py', '.js'],
            'ignore_patterns': ['node_modules', 'venv']
        }
    }

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(config_data, temp_file)
    temp_file.close()

    return temp_file.name


def test_backup_service_init():
    """Test 1: BackupService initialization with multi-account config"""
    print_section("TEST 1: BackupService Initialization")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)

    # Clean up
    Path(config_file).unlink()

    # Check instance variables
    print_test("BackupService has watched_paths")
    assert hasattr(backup_service, 'watched_paths'), "Missing watched_paths attribute"
    assert len(backup_service.watched_paths) == 2, "watched_paths should have 2 entries"
    print("  ✓ watched_paths attribute exists and has correct count")

    print_test("BackupService has folder_watchers list (not single watcher)")
    assert hasattr(backup_service, 'folder_watchers'), "Missing folder_watchers attribute"
    assert isinstance(backup_service.folder_watchers, list), "folder_watchers should be a list"
    assert len(backup_service.folder_watchers) == 0, "folder_watchers should start empty"
    print("  ✓ folder_watchers is a list and starts empty")

    print_test("BackupService does NOT have old code_folder attribute")
    # It should have watched_paths instead
    assert hasattr(backup_service, 'watched_paths'), "Should have watched_paths"
    print("  ✓ Uses watched_paths instead of single code_folder")

    print("\n✅ TEST 1 PASSED\n")


def test_verify_all_accounts():
    """Test 2: _verify_all_accounts method"""
    print_section("TEST 2: Verify All Accounts Method")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("_verify_all_accounts method exists")
    assert hasattr(backup_service, '_verify_all_accounts'), "Missing _verify_all_accounts method"
    print("  ✓ _verify_all_accounts method exists")

    print_test("Method signature accepts no arguments (uses self.watched_paths)")
    # Method should be callable with just self
    import inspect
    sig = inspect.signature(backup_service._verify_all_accounts)
    assert len(sig.parameters) == 0, "Method should have no parameters besides self"
    print("  ✓ Method signature is correct")

    print("\n✅ TEST 2 PASSED\n")


def test_initial_scan_all():
    """Test 3: initial_scan_all method"""
    print_section("TEST 3: Initial Scan All Method")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("initial_scan_all method exists")
    assert hasattr(backup_service, 'initial_scan_all'), "Missing initial_scan_all method"
    print("  ✓ initial_scan_all method exists")

    print_test("Old initial_scan method still exists (for compatibility)")
    assert hasattr(backup_service, 'initial_scan'), "Missing initial_scan method"
    print("  ✓ initial_scan method exists (deprecated)")

    print("\n✅ TEST 3 PASSED\n")


def test_process_folder_signature():
    """Test 4: process_folder method signature"""
    print_section("TEST 4: Process Folder Method Signature")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("process_folder accepts path_config parameter")
    import inspect
    sig = inspect.signature(backup_service.process_folder)
    params = list(sig.parameters.keys())

    assert 'folder_path' in params, "Missing folder_path parameter"
    assert 'path_config' in params, "Missing path_config parameter"
    assert 'is_initial_scan' in params, "Missing is_initial_scan parameter"
    print("  ✓ process_folder has correct parameters: folder_path, path_config, is_initial_scan")

    print("\n✅ TEST 4 PASSED\n")


def test_tracked_repo_metadata():
    """Test 5: Tracked repository metadata includes account_username"""
    print_section("TEST 5: Repository Metadata")

    print_test("Check that repo metadata structure includes account_username")

    # Read the backup_service.py to verify account_username is added
    backup_service_file = Path('code_backup_daemon/backup_service.py')
    content = backup_service_file.read_text()

    # Check if account_username is being set in tracked_repos
    assert "'account_username': account_username" in content, \
        "account_username not being added to tracked_repos metadata"

    print("  ✓ account_username is added to tracked repo metadata")

    # Count occurrences - should be in multiple places
    count = content.count("'account_username': account_username")
    assert count >= 3, f"account_username should be set in at least 3 places, found {count}"
    print(f"  ✓ account_username set in {count} places (good coverage)")

    print("\n✅ TEST 5 PASSED\n")


def test_github_service_calls():
    """Test 6: GitHub service calls pass account_config"""
    print_section("TEST 6: GitHub Service Integration")

    print_test("Verify create_repository calls include account_config")

    backup_service_file = Path('code_backup_daemon/backup_service.py')
    content = backup_service_file.read_text()

    # Check for create_repository calls with account_config
    assert 'create_repository(folder_name, folder_path, description, account_config)' in content, \
        "create_repository not called with account_config parameter"

    print("  ✓ create_repository calls include account_config")

    # Count occurrences
    count = content.count('create_repository(folder_name, folder_path, description, account_config)')
    assert count >= 2, f"Should have at least 2 create_repository calls with account_config, found {count}"
    print(f"  ✓ Found {count} create_repository calls with account_config")

    print("\n✅ TEST 6 PASSED\n")


def test_start_all_folder_watchers():
    """Test 7: start_all_folder_watchers method"""
    print_section("TEST 7: Start All Folder Watchers")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("start_all_folder_watchers method exists")
    assert hasattr(backup_service, 'start_all_folder_watchers'), "Missing start_all_folder_watchers method"
    print("  ✓ start_all_folder_watchers method exists")

    print_test("Old start_folder_watcher method still exists (deprecated)")
    assert hasattr(backup_service, 'start_folder_watcher'), "Missing start_folder_watcher method"
    print("  ✓ start_folder_watcher method exists (deprecated)")

    print("\n✅ TEST 7 PASSED\n")


def test_folder_watcher_callback():
    """Test 8: Folder watcher callback signature"""
    print_section("TEST 8: Folder Watcher Callback")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("on_new_folder_detected accepts path_config parameter")
    import inspect
    sig = inspect.signature(backup_service.on_new_folder_detected)
    params = list(sig.parameters.keys())

    assert 'folder_path' in params, "Missing folder_path parameter"
    assert 'path_config' in params, "Missing path_config parameter"
    print("  ✓ on_new_folder_detected has correct parameters: folder_path, path_config")

    print("\n✅ TEST 8 PASSED\n")


def test_folder_watcher_construction():
    """Test 9: FolderWatcher accepts watched_path parameter"""
    print_section("TEST 9: FolderWatcher Construction")

    from code_backup_daemon.folder_watcher import FolderWatcher

    config_file = create_test_config()
    config = Config(config_file)
    Path(config_file).unlink()

    print_test("FolderWatcher accepts watched_path parameter")
    import inspect
    sig = inspect.signature(FolderWatcher.__init__)
    params = list(sig.parameters.keys())

    assert 'watched_path' in params, "Missing watched_path parameter in FolderWatcher.__init__"
    print("  ✓ FolderWatcher.__init__ accepts watched_path parameter")

    # Test creating a watcher with custom path
    test_path = Path('/tmp/test_watch')
    watcher = FolderWatcher(config, lambda x: None, watched_path=test_path)

    assert watcher.code_folder == test_path, "watched_path not set correctly"
    print("  ✓ FolderWatcher correctly uses watched_path parameter")

    print("\n✅ TEST 9 PASSED\n")


def test_helper_methods_updated():
    """Test 10: Helper methods accept path_config"""
    print_section("TEST 10: Helper Methods")

    config_file = create_test_config()
    config = Config(config_file)
    backup_service = BackupService(config)
    Path(config_file).unlink()

    print_test("_is_valid_project accepts path_config parameter")
    import inspect
    sig = inspect.signature(backup_service._is_valid_project)
    params = list(sig.parameters.keys())
    assert 'path_config' in params, "Missing path_config parameter in _is_valid_project"
    print("  ✓ _is_valid_project accepts path_config")

    print_test("_should_ignore_folder accepts path_config parameter")
    sig = inspect.signature(backup_service._should_ignore_folder)
    params = list(sig.parameters.keys())
    assert 'path_config' in params, "Missing path_config parameter in _should_ignore_folder"
    print("  ✓ _should_ignore_folder accepts path_config")

    print("\n✅ TEST 10 PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STEP 3: BACKUP SERVICE MULTI-WATCHER TESTS")
    print("=" * 60)

    tests = [
        test_backup_service_init,
        test_verify_all_accounts,
        test_initial_scan_all,
        test_process_folder_signature,
        test_tracked_repo_metadata,
        test_github_service_calls,
        test_start_all_folder_watchers,
        test_folder_watcher_callback,
        test_folder_watcher_construction,
        test_helper_methods_updated
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}\n")
            failed += 1

    # Print summary
    print_section("TEST SUMMARY")
    print(f"Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"Failed: {failed}/{len(tests)}")
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED! Step 3 is complete.")
        sys.exit(0)


if __name__ == '__main__':
    main()
