# Running the Multi-Account Code Backup Daemon

## Quick Start

### 1. Start the Daemon (Foreground - Recommended for First Run)

```bash
./start_daemon.sh
```

This runs the daemon in the foreground so you can see live logs. Good for testing!

**What happens:**
- Daemon performs initial scan of `/Desktop/NK` and `/Desktop/AI4M`
- Detects all existing projects
- Creates GitHub repos for any projects without remotes
- Starts watching for new folders
- Auto-backs up every 6 hours

Press `Ctrl+C` to stop.

---

### 2. Start the Daemon (Background - For Continuous Operation)

```bash
./start_daemon_background.sh
```

This runs the daemon in the background. It will:
- Keep running even after you close the terminal
- Auto-backup every 6 hours
- Watch for new projects continuously

---

### 3. Check Daemon Status

```bash
./check_daemon_status.sh
```

Shows:
- ✅ Daemon running status
- 📊 Statistics (total repos, backups, errors)
- 📁 List of all tracked repositories
- 👤 Account grouping

---

### 4. Stop the Daemon

```bash
./stop_daemon.sh
```

Gracefully stops the background daemon.

---

## How the Multi-Account System Works

### Automatic Account Detection

The daemon automatically determines which GitHub account to use based on **folder location**:

```
📁 /home/nayan-ai4m/Desktop/NK/
   └── my-project/          → Pushed to 2003nayan account
   └── another-project/     → Pushed to 2003nayan account

📁 /home/nayan-ai4m/Desktop/AI4M/
   └── ai4m-dashboard/      → Pushed to nayan-ai4m account
   └── client-project/      → Pushed to nayan-ai4m account
```

**You don't need to do anything!** Just put your project in the right folder.

### What Gets Backed Up

A folder is backed up if it contains:

**Project Indicators:**
- `package.json` (Node.js)
- `requirements.txt` (Python)
- `Cargo.toml` (Rust)
- `go.mod` (Go)
- `pom.xml` (Java)
- etc.

**OR has code files:**
- `.js`, `.ts`, `.py`, `.java`, `.cpp`, `.go`, etc.

**AND is at least 1KB in size**

### What's Ignored

These folders are automatically skipped:
- `node_modules`
- `venv`, `.venv`
- `__pycache__`
- `.git`
- `dist`, `build`
- `tmp`, `temp`
- etc.

---

## Testing the Multi-Account Setup

### Step 1: Create Test Projects

**For NK Account (2003nayan):**
```bash
mkdir -p ~/Desktop/NK/test-webapp
cd ~/Desktop/NK/test-webapp

cat > README.md << 'EOF'
# Test Web App
A test project for NK account backup testing.
EOF

cat > package.json << 'EOF'
{
  "name": "test-webapp",
  "version": "1.0.0",
  "description": "Test project for multi-account daemon"
}
EOF

cat > index.js << 'EOF'
console.log("Hello from NK account!");
EOF
```

**For AI4M Account (nayan-ai4m):**
```bash
mkdir -p ~/Desktop/AI4M/test-api
cd ~/Desktop/AI4M/test-api

cat > README.md << 'EOF'
# Test API
A test project for AI4M account backup testing.
EOF

cat > requirements.txt << 'EOF'
flask==2.0.1
requests==2.26.0
EOF

cat > app.py << 'EOF'
print("Hello from AI4M account!")
EOF
```

### Step 2: Start Daemon & Watch

```bash
./start_daemon.sh
```

You should see:
```
INFO - Performing initial scan of /home/nayan-ai4m/Desktop/NK...
INFO - Found potential project: test-webapp
INFO - Initializing new repository: test-webapp (account: 2003nayan)
INFO - Created GitHub repository: test-webapp for 2003nayan
INFO - Successfully initialized and created repository: test-webapp

INFO - Performing initial scan of /home/nayan-ai4m/Desktop/AI4M...
INFO - Found potential project: test-api
INFO - Initializing new repository: test-api (account: nayan-ai4m)
INFO - Created GitHub repository: test-api for nayan-ai4m
INFO - Successfully initialized and created repository: test-api
```

### Step 3: Verify on GitHub

Check that repos were created:
- NK: https://github.com/2003nayan/test-webapp
- AI4M: https://github.com/nayan-ai4m/test-api

Verify commit attribution:
- NK commits should show: `2003nayan <2003nayan@users.noreply.github.com>`
- AI4M commits should show: `nayan-ai4m <nayan-ai4m@users.noreply.github.com>`

### Step 4: Test Auto-Backup

Make a change to a project:
```bash
cd ~/Desktop/NK/test-webapp
echo "// Added new feature" >> index.js
```

Wait for next backup cycle (6 hours) or trigger manually:
```bash
source venv/bin/activate
export GITHUB_TOKEN_NK="your_personal_token_here"
export GITHUB_TOKEN_AI4M="your_work_token_here"

python -m code_backup_daemon.cli backup test-webapp
```

---

## Monitoring & Logs

### View Live Logs

```bash
tail -f ~/.local/share/code-backup/daemon.log
```

### Check State File

```bash
cat ~/.local/share/code-backup/state.json | jq
```

Shows all tracked repositories with metadata.

---

## Configuration

The daemon uses: `~/.config/code-backup/config.yaml`

**Key Settings:**

```yaml
daemon:
  backup_interval: 21600  # 6 hours (in seconds)

watched_paths:
  - name: NK Projects
    path: /home/nayan-ai4m/Desktop/NK
    account:
      username: 2003nayan
      ssh_host: github.com-personal  # Uses ~/.ssh/id_personal

  - name: AI4M Projects
    path: /home/nayan-ai4m/Desktop/AI4M
    account:
      username: nayan-ai4m
      ssh_host: github.com-office     # Uses ~/.ssh/id_office
```

---

## CLI Commands Reference

```bash
# Start daemon (foreground)
code-backup start --foreground

# Start daemon (background)
code-backup start

# Stop daemon
code-backup stop

# Check status
code-backup status

# List all tracked repos
code-backup list-repos

# List repos for specific account
code-backup list-repos --account 2003nayan

# Force backup all repos
code-backup backup

# Force backup specific repo
code-backup backup my-project

# Show configuration
code-backup config-show

# Update configuration
code-backup config-set daemon.backup_interval 3600
```

---

## Troubleshooting

### Daemon Won't Start

**Check if already running:**
```bash
cat ~/.local/share/code-backup/daemon.pid
ps aux | grep code-backup
```

**Kill stale process:**
```bash
./stop_daemon.sh
# or manually:
kill $(cat ~/.local/share/code-backup/daemon.pid)
rm ~/.local/share/code-backup/daemon.pid
```

### Repository Not Detected

**Check project indicators:**
```bash
cd ~/Desktop/NK/my-project
ls -la
```

Make sure it has a `package.json`, `requirements.txt`, or code files.

**Check size:**
```bash
du -sh ~/Desktop/NK/my-project
```

Must be > 1KB.

**Check logs:**
```bash
grep "my-project" ~/.local/share/code-backup/daemon.log
```

### Push Fails

**Verify SSH setup:**
```bash
ssh -T git@github.com-personal
ssh -T git@github.com-office
```

Should both respond with "Hi username!"

**Check remote URL:**
```bash
cd ~/Desktop/NK/my-project
git remote -v
```

Should show SSH URL: `git@github.com-personal:2003nayan/my-project.git`

---

## Production Deployment

### Option 1: systemd User Service (Recommended)

```bash
# Copy service file
cp code-backup.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable (start on login)
systemctl --user enable code-backup

# Start now
systemctl --user start code-backup

# Check status
systemctl --user status code-backup

# View logs
journalctl --user -u code-backup -f
```

### Option 2: Cron Job

```bash
# Edit crontab
crontab -e

# Add this line to run every 6 hours:
0 */6 * * * cd /home/nayan-ai4m/Desktop/NK/automated-github-push && ./start_daemon_background.sh
```

---

## Summary

✅ **Multi-account support** - Automatic account routing based on folder location
✅ **SSH authentication** - Uses account-specific SSH keys automatically
✅ **Auto-detection** - Finds projects automatically based on indicators
✅ **Auto-backup** - Periodic backups every 6 hours
✅ **Correct attribution** - Commits use proper name/email per account
✅ **Live monitoring** - Watch for new projects in real-time

**Just create your projects in the right folder and the daemon handles the rest!**
