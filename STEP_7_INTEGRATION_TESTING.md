# Step 7: Integration Testing Guide

## Overview

This guide will help you complete the final step of the multi-account implementation: integration testing with real GitHub tokens.

## ✅ Pre-Requisites (Already Complete)

- [x] All unit tests passing (36/36)
- [x] Multi-account config file created
- [x] Test projects created in both directories
- [x] Integration test scripts created

## 🚀 Running Integration Tests

### Option 1: Quick Test (Recommended)

1. **Edit the run script with your actual tokens:**
   ```bash
   nano run_integration_test.sh
   ```

   Replace the placeholder tokens with your actual tokens:
   ```bash
   export GITHUB_TOKEN_NK="ghp_sje..." # Your actual NK token
   export GITHUB_TOKEN_AI4M="ghp_Whp..." # Your actual AI4M token
   ```

2. **Run the integration test:**
   ```bash
   ./run_integration_test.sh
   ```

### Option 2: Manual Test

1. **Set tokens in your current shell:**
   ```bash
   export GITHUB_TOKEN_NK="ghp_sje*****************"
   export GITHUB_TOKEN_AI4M="ghp_Whp***************"
   ```

2. **Run the integration test script:**
   ```bash
   ./integration_test_step7.sh
   ```

## 📋 What the Integration Test Does

The integration test script will:

1. ✅ **Verify all unit tests still pass** (36/36 tests)
2. ✅ **Verify configuration loads correctly**
   - Checks that both watched paths are configured
   - Verifies account associations

3. ✅ **Test GitHub authentication**
   - Tests authentication for 2003nayan account
   - Tests authentication for nayan-ai4m account

4. ✅ **Process test projects** (asks for confirmation)
   - Initializes git repositories
   - Sets per-repo git config
   - Creates initial commits
   - Creates GitHub repositories
   - Pushes to remote

5. ✅ **Verify state file**
   - Checks that repositories are tracked
   - Verifies account_username is set
   - Shows repository grouping by account

6. ✅ **Test CLI commands**
   - `code-backup status` - Shows multi-account status
   - `code-backup list-repos` - Lists all repositories
   - `code-backup list-repos --account 2003nayan` - Filters by account
   - `code-backup list-repos --account nayan-ai4m` - Filters by account

## 🔍 Manual Verification Steps

After running the integration test, manually verify on GitHub:

### 1. Check 2003nayan Account

Visit: https://github.com/2003nayan

**Expected:**
- Repository `test-backup-nk` should exist
- Repository should be private
- Commits should be authored by 2003nayan
- Commit email should be `2003nayan@users.noreply.github.com`

**Check:**
```bash
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
git log --format="%an <%ae>" -1
```

Expected output: `2003nayan <2003nayan@users.noreply.github.com>`

### 2. Check nayan-ai4m Account

Visit: https://github.com/nayan-ai4m

**Expected:**
- Repository `test-backup-ai4m` should exist
- Repository should be private
- Commits should be authored by nayan-ai4m
- Commit email should be `nayan-ai4m@users.noreply.github.com`

**Check:**
```bash
cd /home/nayan-ai4m/Desktop/AI4M/test-backup-ai4m
git log --format="%an <%ae>" -1
```

Expected output: `nayan-ai4m <nayan-ai4m@users.noreply.github.com>`

### 3. Verify No Cross-Account Contamination

**Important:** Verify that:
- NK project (`test-backup-nk`) is ONLY under 2003nayan account
- AI4M project (`test-backup-ai4m`) is ONLY under nayan-ai4m account
- No repositories appear under the wrong account

## 🎯 Success Criteria

Mark these as complete once verified:

- [ ] Both accounts authenticate successfully
- [ ] test-backup-nk repository created under 2003nayan
- [ ] test-backup-ai4m repository created under nayan-ai4m
- [ ] Commits attributed to correct users
- [ ] State file contains account_username for all repos
- [ ] CLI commands show account grouping
- [ ] No cross-account contamination
- [ ] Daemon can start successfully

## 🔧 Testing Daemon Operations

Once integration tests pass, test the daemon:

### 1. Start the Daemon

```bash
# Make sure tokens are set first!
export GITHUB_TOKEN_NK="ghp_sje*****************"
export GITHUB_TOKEN_AI4M="ghp_Whp***************"

# Start daemon
source venv/bin/activate
code-backup start
```

### 2. Monitor Daemon

```bash
# Check status
code-backup status

# View logs
tail -f ~/.local/share/code-backup/daemon.log
```

### 3. Test Automatic Detection

Create a new project in the NK directory:
```bash
mkdir -p /home/nayan-ai4m/Desktop/NK/auto-detect-test
cd /home/nayan-ai4m/Desktop/NK/auto-detect-test
echo "# Auto Detect Test" > README.md
echo "print('Hello')" > test.py
```

Wait ~30 seconds, then check:
```bash
code-backup list-repos --account 2003nayan
```

Expected: `auto-detect-test` should appear

Create a new project in the AI4M directory:
```bash
mkdir -p /home/nayan-ai4m/Desktop/AI4M/auto-detect-test-ai4m
cd /home/nayan-ai4m/Desktop/AI4M/auto-detect-test-ai4m
echo "# Auto Detect Test AI4M" > README.md
echo "console.log('Hello')" > test.js
```

Wait ~30 seconds, then check:
```bash
code-backup list-repos --account nayan-ai4m
```

Expected: `auto-detect-test-ai4m` should appear

## 🐛 Troubleshooting

### Authentication Fails

**Problem:** "No authentication found for 2003nayan" or similar

**Solution:**
1. Verify tokens are set: `echo $GITHUB_TOKEN_NK`
2. Verify token is correct (not expired)
3. Verify token has `repo` scope

### Repository Creation Fails

**Problem:** "Failed to create repository"

**Possible causes:**
1. Repository already exists - check GitHub
2. Token doesn't have `repo` permission
3. Network issue - check internet connection

**Solution:**
```bash
# Delete existing test repos from GitHub first
gh repo delete 2003nayan/test-backup-nk --yes
gh repo delete nayan-ai4m/test-backup-ai4m --yes

# Then re-run integration test
```

### Wrong Account Attribution

**Problem:** Commits show wrong author

**Check:**
```bash
cd /path/to/repo
git config user.name
git config user.email
```

**Fix:**
The `set_repo_git_config()` should have been called. If not:
```bash
# Manually set for testing
cd /home/nayan-ai4m/Desktop/NK/test-backup-nk
git config user.name "2003nayan"
git config user.email "2003nayan@users.noreply.github.com"
```

### Daemon Won't Start

**Problem:** Daemon fails to start

**Check logs:**
```bash
tail -50 ~/.local/share/code-backup/daemon.log
```

**Common issues:**
1. Tokens not exported in daemon's environment
2. Config file syntax error
3. Watched paths don't exist

## 📊 Expected Test Results

When you run the integration test, you should see:

```
============================================================
STEP 7: MULTI-ACCOUNT INTEGRATION TESTING
============================================================

✓ Both GitHub tokens are set

============================================================
TEST 1: Verify All Unit Tests Still Pass
============================================================

✓ Step 1: 3/3 tests passed
✓ Step 2: 5/5 tests passed
✓ Step 3: 10/10 tests passed
✓ Step 4: 6/6 tests passed
✓ Step 5: 5/5 tests passed
✓ Step 6: 7/7 tests passed

✓ All unit tests passed (36/36)

============================================================
TEST 2: Verify Configuration
============================================================

Watched Paths: 2
  • NK Projects: /home/nayan-ai4m/Desktop/NK → 2003nayan
  • AI4M Projects: /home/nayan-ai4m/Desktop/AI4M → nayan-ai4m

============================================================
TEST 3: Verify GitHub Authentication
============================================================

✓ 2003nayan authentication: SUCCESS
✓ nayan-ai4m authentication: SUCCESS

✓ Both accounts authenticated successfully

============================================================
[... rest of tests ...]
============================================================
```

## 📝 Reporting Results

After completing all tests, update the following files:

1. **MULTI_ACCOUNT_IMPLEMENTATION_PLAN.md**
   - Mark Step 7 as complete
   - Add integration test results
   - Update progress to 100%

2. **SESSION_PROGRESS.md**
   - Add Step 7 completion details
   - Document any issues encountered
   - Add final statistics

## 🎉 Next Steps After Success

Once all tests pass:

1. **Clean up test repositories** (optional):
   ```bash
   gh repo delete 2003nayan/test-backup-nk --yes
   gh repo delete nayan-ai4m/test-backup-ai4m --yes
   ```

2. **Set tokens permanently** in `~/.bashrc` or `~/.zshrc`:
   ```bash
   echo 'export GITHUB_TOKEN_NK="ghp_your_token"' >> ~/.bashrc
   echo 'export GITHUB_TOKEN_AI4M="ghp_your_token"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Set up systemd service** for automatic startup:
   ```bash
   ./install.sh
   systemctl --user enable code-backup
   systemctl --user start code-backup
   ```

4. **Start using the daemon** for real projects!

## ✅ Completion Checklist

Step 7 is complete when:

- [ ] Integration test script runs without errors
- [ ] Both accounts authenticate successfully
- [ ] Test repositories created under correct accounts
- [ ] Commits have correct attribution
- [ ] CLI commands work and show account grouping
- [ ] State file tracks account_username correctly
- [ ] No cross-account contamination verified
- [ ] Daemon starts and runs successfully
- [ ] Automatic project detection works for both paths
- [ ] Documentation updated with results

---

**Ready to test? Run: `./run_integration_test.sh`**

(After updating the tokens in that file with your actual values)
