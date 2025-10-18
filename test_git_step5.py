#!/usr/bin/env python3
"""
Test Suite for Step 5: Git Service Per-Repo Config
Tests the set_repo_git_config method for multi-account commit attribution
"""

import sys
import tempfile
import yaml
from pathlib import Path
from code_backup_daemon.config import Config
from code_backup_daemon.git_service import GitService
from git import Repo


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
                        'email': '2003nayan@users.noreply.github.com',
                        'auth_method': 'token',
                        'token_env': 'GITHUB_TOKEN_NK'
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


def test_set_repo_git_config_method_exists():
    """Test 1: set_repo_git_config method exists"""
    print_section("TEST 1: Method Existence")

    config_file = create_test_config()
    config = Config(config_file)
    git_service = GitService(config)
    Path(config_file).unlink()

    print_test("GitService has set_repo_git_config method")
    assert hasattr(git_service, 'set_repo_git_config'), "Missing set_repo_git_config method"
    print("  ✓ set_repo_git_config method exists")

    print_test("Method signature")
    import inspect
    sig = inspect.signature(git_service.set_repo_git_config)
    params = list(sig.parameters.keys())

    assert 'path' in params, "Missing path parameter"
    assert 'username' in params, "Missing username parameter"
    assert 'email' in params, "Missing email parameter"
    print("  ✓ Method has correct parameters: path, username, email")

    print("\n✅ TEST 1 PASSED\n")


def test_set_repo_git_config_functionality():
    """Test 2: set_repo_git_config actually sets git config"""
    print_section("TEST 2: Functionality")

    config_file = create_test_config()
    config = Config(config_file)
    git_service = GitService(config)
    Path(config_file).unlink()

    # Create a temporary git repository
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test_repo"
        repo_path.mkdir()

        # Initialize git repo
        repo = Repo.init(repo_path)

        print_test("Set git config for repository")
        test_username = "testuser"
        test_email = "testuser@example.com"

        result = git_service.set_repo_git_config(repo_path, test_username, test_email)
        assert result is True, "set_repo_git_config should return True"
        print("  ✓ set_repo_git_config returned True")

        print_test("Verify git config was actually set")
        # Read config back
        with repo.config_reader() as config_reader:
            actual_username = config_reader.get_value("user", "name")
            actual_email = config_reader.get_value("user", "email")

        assert actual_username == test_username, f"Expected username '{test_username}', got '{actual_username}'"
        assert actual_email == test_email, f"Expected email '{test_email}', got '{actual_email}'"
        print(f"  ✓ user.name set to: {actual_username}")
        print(f"  ✓ user.email set to: {actual_email}")

    print("\n✅ TEST 2 PASSED\n")


def test_set_repo_git_config_error_handling():
    """Test 3: set_repo_git_config handles errors gracefully"""
    print_section("TEST 3: Error Handling")

    config_file = create_test_config()
    config = Config(config_file)
    git_service = GitService(config)
    Path(config_file).unlink()

    print_test("Handle non-existent repository")
    fake_path = Path("/tmp/nonexistent_repo_12345")
    result = git_service.set_repo_git_config(fake_path, "user", "user@example.com")

    assert result is False, "Should return False for non-existent repo"
    print("  ✓ Returns False for non-existent repository")

    print("\n✅ TEST 3 PASSED\n")


def test_backup_service_calls_set_repo_git_config():
    """Test 4: BackupService calls set_repo_git_config"""
    print_section("TEST 4: Integration with BackupService")

    backup_service_file = Path('code_backup_daemon/backup_service.py')
    content = backup_service_file.read_text()

    print_test("Verify _initialize_new_repository calls set_repo_git_config")
    assert 'set_repo_git_config(' in content, "set_repo_git_config not called in backup_service.py"
    print("  ✓ set_repo_git_config is called")

    # Count occurrences - should be in both methods
    count = content.count('set_repo_git_config(')
    assert count >= 2, f"set_repo_git_config should be called at least 2 times, found {count}"
    print(f"  ✓ set_repo_git_config called {count} times (good coverage)")

    print_test("Verify email parameter uses account_config.get('email')")
    assert "account_config.get('email'" in content, "Email not extracted from account_config"
    print("  ✓ Email extracted from account_config")

    print_test("Verify fallback to GitHub noreply email")
    assert "@users.noreply.github.com" in content, "Missing fallback to GitHub noreply email"
    print("  ✓ Fallback to GitHub noreply email present")

    print("\n✅ TEST 4 PASSED\n")


def test_git_config_documentation():
    """Test 5: Method has proper documentation"""
    print_section("TEST 5: Documentation")

    config_file = create_test_config()
    config = Config(config_file)
    git_service = GitService(config)
    Path(config_file).unlink()

    print_test("Method has docstring")
    assert git_service.set_repo_git_config.__doc__ is not None, "Missing docstring"
    docstring = git_service.set_repo_git_config.__doc__
    print("  ✓ Method has docstring")

    print_test("Docstring mentions multi-account purpose")
    assert any(keyword in docstring.lower() for keyword in ['account', 'attributed', 'commit']), \
        "Docstring should explain multi-account purpose"
    print("  ✓ Docstring explains multi-account purpose")

    print("\n✅ TEST 5 PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STEP 5: GIT SERVICE PER-REPO CONFIG TESTS")
    print("=" * 60)

    tests = [
        test_set_repo_git_config_method_exists,
        test_set_repo_git_config_functionality,
        test_set_repo_git_config_error_handling,
        test_backup_service_calls_set_repo_git_config,
        test_git_config_documentation
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
        print("\n🎉 ALL TESTS PASSED! Step 5 is complete.")
        sys.exit(0)


if __name__ == '__main__':
    main()
