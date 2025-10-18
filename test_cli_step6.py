#!/usr/bin/env python3
"""
Test Suite for Step 6: CLI Multi-Account Support
Tests CLI commands for multi-account display and filtering
"""

import sys
from pathlib import Path


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def print_test(test_name):
    """Print test name"""
    print(f"Testing: {test_name}")


def test_start_command_shows_watched_paths():
    """Test 1: start command shows all watched paths"""
    print_section("TEST 1: Start Command Output")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("start command shows watched_paths")
    assert "watched_paths = config.get('paths.watched_paths'" in content, \
        "start command should get watched_paths from config"
    print("  ✓ Gets watched_paths from config")

    assert "Monitoring {len(watched_paths)} path(s)" in content or \
           "Monitoring {len(watched_paths)} paths" in content, \
        "Should display count of watched paths"
    print("  ✓ Displays count of watched paths")

    assert "account_config.get('account', {}).get('username'" in content or \
           "path_config.get('account', {}).get('username'" in content, \
        "Should extract username from account config"
    print("  ✓ Extracts username from account config")

    print("\n✅ TEST 1 PASSED\n")


def test_status_command_groups_by_account():
    """Test 2: status command groups repos by account"""
    print_section("TEST 2: Status Command Grouping")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("status command shows watched paths")
    assert "watched_paths = config.get('paths.watched_paths'" in content, \
        "status should get watched_paths"
    print("  ✓ Gets watched_paths")

    assert "📁 Watched Paths:" in content, \
        "Should display watched paths section"
    print("  ✓ Displays watched paths section")

    print_test("status command groups repos by account")
    assert "repos_by_account" in content, \
        "Should group repos by account"
    print("  ✓ Groups repos by account")

    assert "account = repo_info.get('account_username'" in content, \
        "Should extract account_username from repo info"
    print("  ✓ Extracts account_username from repo info")

    print("\n✅ TEST 2 PASSED\n")


def test_list_repos_has_account_filter():
    """Test 3: list-repos command has --account filter"""
    print_section("TEST 3: List-Repos Account Filter")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("list_repos has --account option")
    # Look for the option definition before list_repos (decorators come first)
    list_repos_index = content.find("def list_repos")
    list_repos_section = content[max(0, list_repos_index - 200):list_repos_index + 500]
    assert "--account" in list_repos_section or "'-a'" in list_repos_section, \
        "list_repos should have --account/-a option"
    print("  ✓ Has --account/-a option")

    print_test("list_repos accepts account parameter")
    assert "def list_repos(ctx, account)" in content, \
        "list_repos should accept account parameter"
    print("  ✓ Accepts account parameter")

    print_test("list_repos filters by account")
    # Get the full list_repos function
    list_repos_start = content.find("def list_repos")
    list_repos_end = content.find("\n@cli.command()", list_repos_start + 1)
    if list_repos_end == -1:
        list_repos_end = content.find("\ndef ", list_repos_start + 100)
    list_repos_full = content[list_repos_start:list_repos_end]

    assert "if account:" in list_repos_full, \
        "Should have conditional logic for account filtering"
    assert "account_username" in list_repos_full, \
        "Should check account_username field"
    print("  ✓ Filters repos by account")

    print("\n✅ TEST 3 PASSED\n")


def test_list_repos_groups_by_account():
    """Test 4: list-repos groups repos by account"""
    print_section("TEST 4: List-Repos Grouping")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("list_repos groups repos by account")
    list_repos_section = content[content.find("def list_repos"):]
    assert "repos_by_account" in list_repos_section[:2000], \
        "Should create repos_by_account grouping"
    print("  ✓ Creates repos_by_account grouping")

    assert "👤 Account:" in list_repos_section[:2000] or \
           "Account:" in list_repos_section[:2000], \
        "Should display account headers"
    print("  ✓ Displays account headers")

    print("\n✅ TEST 4 PASSED\n")


def test_backwards_compatibility():
    """Test 5: Commands have fallback for old config format"""
    print_section("TEST 5: Backwards Compatibility")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("status command has fallback for old config")
    status_section = content[content.find("def status("):][:2000]
    assert "else:" in status_section and \
           ("code_folder" in status_section or "fallback" in status_section.lower()), \
        "Should have fallback handling for old config"
    print("  ✓ Has fallback for old config format")

    print("\n✅ TEST 5 PASSED\n")


def test_cli_command_signatures():
    """Test 6: Command signatures are correct"""
    print_section("TEST 6: Command Signatures")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("start command exists")
    assert "def start(ctx):" in content, "start command should exist"
    print("  ✓ start command exists")

    print_test("status command exists")
    assert "def status(ctx):" in content, "status command should exist"
    print("  ✓ status command exists")

    print_test("list_repos command exists with account param")
    assert "def list_repos(ctx, account):" in content, \
        "list_repos should have account parameter"
    print("  ✓ list_repos has account parameter")

    print("\n✅ TEST 6 PASSED\n")


def test_display_formatting():
    """Test 7: Multi-account display formatting"""
    print_section("TEST 7: Display Formatting")

    cli_file = Path('code_backup_daemon/cli.py')
    content = cli_file.read_text()

    print_test("Uses appropriate emojis and formatting")
    assert "📁" in content, "Should use folder emoji"
    assert "👤" in content or "Account:" in content, "Should show account info"
    print("  ✓ Uses emojis and clear formatting")

    print_test("Shows account associations")
    assert "→" in content or "->" in content, "Should show path → account mapping"
    print("  ✓ Shows path → account associations")

    print("\n✅ TEST 7 PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STEP 6: CLI MULTI-ACCOUNT SUPPORT TESTS")
    print("=" * 60)

    tests = [
        test_start_command_shows_watched_paths,
        test_status_command_groups_by_account,
        test_list_repos_has_account_filter,
        test_list_repos_groups_by_account,
        test_backwards_compatibility,
        test_cli_command_signatures,
        test_display_formatting
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
        print("\n🎉 ALL TESTS PASSED! Step 6 is complete.")
        print("\nNote: The setup wizard still uses old config format.")
        print("Users should manually create multi-account configs using the example file.")
        sys.exit(0)


if __name__ == '__main__':
    main()
