#!/usr/bin/env python3
"""
Test script for Step 2: GitHub Service Refactoring
Tests the multi-account GitHub service implementation
"""

import sys
import os
from pathlib import Path

# Add code_backup_daemon to path
sys.path.insert(0, str(Path(__file__).parent))

from code_backup_daemon.github_service import GitHubService
from code_backup_daemon.config import Config
import tempfile


def test_account_config_extraction():
    """Test account config extraction and normalization"""
    print("=" * 60)
    print("TEST 1: Account Config Extraction")
    print("=" * 60)

    config = Config()
    gh_service = GitHubService(config)

    # Test account config
    account_config = {
        'username': '2003nayan',
        'token_env_var': 'GITHUB_TOKEN_NK',
        'default_visibility': 'private',
        'use_gh_cli': False
    }

    extracted = gh_service._get_account_config(account_config)

    print(f"\n✓ Extracted account config:")
    print(f"  Username: {extracted['username']}")
    print(f"  Token Env Var: {extracted['token_env_var']}")
    print(f"  Visibility: {extracted['default_visibility']}")
    print(f"  Use gh CLI: {extracted['use_gh_cli']}")

    # Test with minimal config (should use defaults)
    minimal_config = {'username': 'testuser'}
    extracted_minimal = gh_service._get_account_config(minimal_config)

    print(f"\n✓ Extracted minimal config with defaults:")
    print(f"  Username: {extracted_minimal['username']}")
    print(f"  Visibility: {extracted_minimal['default_visibility']}")
    print(f"  Use gh CLI: {extracted_minimal['use_gh_cli']}")

    print("\n✅ TEST 1 PASSED\n")
    return True


def test_token_retrieval():
    """Test token retrieval from environment"""
    print("=" * 60)
    print("TEST 2: Token Retrieval")
    print("=" * 60)

    config = Config()
    gh_service = GitHubService(config)

    # Set test tokens in environment
    os.environ['GITHUB_TOKEN_TEST1'] = 'test_token_123'
    os.environ['GITHUB_TOKEN_TEST2'] = 'test_token_456'

    # Test 1: Token from env var
    account_config_1 = {
        'username': 'test1',
        'token_env_var': 'GITHUB_TOKEN_TEST1',
        'use_gh_cli': False
    }

    token1 = gh_service._get_github_token(account_config_1)
    if token1 == 'test_token_123':
        print("✓ Retrieved token from GITHUB_TOKEN_TEST1")
    else:
        print(f"✗ Expected 'test_token_123', got '{token1}'")
        return False

    # Test 2: Different token for different account
    account_config_2 = {
        'username': 'test2',
        'token_env_var': 'GITHUB_TOKEN_TEST2',
        'use_gh_cli': False
    }

    token2 = gh_service._get_github_token(account_config_2)
    if token2 == 'test_token_456':
        print("✓ Retrieved token from GITHUB_TOKEN_TEST2")
    else:
        print(f"✗ Expected 'test_token_456', got '{token2}'")
        return False

    # Test 3: Token caching
    token1_cached = gh_service._get_github_token(account_config_1)
    if token1_cached == token1:
        print("✓ Token caching works correctly")
    else:
        print("✗ Token caching failed")
        return False

    # Cleanup
    del os.environ['GITHUB_TOKEN_TEST1']
    del os.environ['GITHUB_TOKEN_TEST2']

    print("\n✅ TEST 2 PASSED\n")
    return True


def test_authentication_check():
    """Test authentication checking"""
    print("=" * 60)
    print("TEST 3: Authentication Check")
    print("=" * 60)

    config = Config()
    gh_service = GitHubService(config)

    # Test with token available
    os.environ['GITHUB_TOKEN_AUTH_TEST'] = 'auth_test_token'

    account_config = {
        'username': 'testuser',
        'token_env_var': 'GITHUB_TOKEN_AUTH_TEST',
        'use_gh_cli': False
    }

    is_auth = gh_service.is_authenticated(account_config)
    if is_auth:
        print("✓ Authentication check passed with token")
    else:
        print("✗ Authentication check failed when token available")
        del os.environ['GITHUB_TOKEN_AUTH_TEST']
        return False

    # Test without token
    del os.environ['GITHUB_TOKEN_AUTH_TEST']

    account_config_no_token = {
        'username': 'testuser2',
        'token_env_var': 'NONEXISTENT_TOKEN',
        'use_gh_cli': False
    }

    is_auth_no_token = gh_service.is_authenticated(account_config_no_token)
    if not is_auth_no_token:
        print("✓ Authentication check correctly failed without token")
    else:
        print("✗ Authentication check incorrectly passed without token")
        return False

    print("\n✅ TEST 3 PASSED\n")
    return True


def test_method_signatures():
    """Test that all methods accept account_config parameter"""
    print("=" * 60)
    print("TEST 4: Method Signatures")
    print("=" * 60)

    config = Config()
    gh_service = GitHubService(config)

    # Check method signatures
    import inspect

    methods_to_check = [
        'is_authenticated',
        'repo_exists',
        'create_repository',
        'get_repository_info',
        'delete_repository',
        'list_repositories'
    ]

    print("\n✓ Checking method signatures:")
    for method_name in methods_to_check:
        method = getattr(gh_service, method_name)
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        if 'account_config' in params:
            print(f"  ✓ {method_name} accepts account_config")
        else:
            print(f"  ✗ {method_name} missing account_config parameter")
            print(f"    Parameters: {params}")
            return False

    print("\n✅ TEST 4 PASSED\n")
    return True


def test_instance_variables():
    """Test that instance-level account data is removed"""
    print("=" * 60)
    print("TEST 5: Instance Variables")
    print("=" * 60)

    config = Config()
    gh_service = GitHubService(config)

    # Check that old instance variables are NOT present
    removed_attrs = ['username', 'default_visibility', 'create_org_repos', 'organization', 'use_gh_cli', 'github_token']

    print("\n✓ Checking removed instance variables:")
    all_removed = True
    for attr in removed_attrs:
        if hasattr(gh_service, attr):
            print(f"  ✗ {attr} still exists (should be removed)")
            all_removed = False
        else:
            print(f"  ✓ {attr} removed")

    if not all_removed:
        return False

    # Check that new instance variables ARE present
    required_attrs = ['config', 'api_base', '_token_cache']

    print("\n✓ Checking new instance variables:")
    for attr in required_attrs:
        if hasattr(gh_service, attr):
            print(f"  ✓ {attr} exists")
        else:
            print(f"  ✗ {attr} missing")
            return False

    print("\n✅ TEST 5 PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STEP 2 GITHUB SERVICE TESTS")
    print("=" * 60 + "\n")

    tests = [
        test_account_config_extraction,
        test_token_retrieval,
        test_authentication_check,
        test_method_signatures,
        test_instance_variables
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
        print("\n🎉 ALL TESTS PASSED! Step 2 is complete.\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
