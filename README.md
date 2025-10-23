# Code Backup Daemon - Multi-Account Edition

🚀 **Automatically backup your code to multiple GitHub accounts without lifting a finger!**

A smart Python daemon that monitors multiple code folders, detects new projects, and automatically creates GitHub repositories with proper account routing and SSH authentication. Never lose your work again, with full multi-account support!

## ✨ Key Features

- 👥 **Multi-Account Support** - Manage multiple GitHub accounts seamlessly
- 🔐 **SSH Authentication** - Secure SSH key-based authentication per account
- 🔍 **Smart Project Detection** - Automatically identifies valid code projects
- 📁 **Real-Time Monitoring** - Watches for new projects across multiple folders
- 🐙 **GitHub Integration** - Creates private/public repositories automatically
- 🔄 **Continuous Backup** - Commits and pushes changes on schedule (every 6 hours)
- ✍️ **Correct Attribution** - Each commit uses the right name/email per account
- ⚙️ **Configurable** - Customize backup intervals, ignore patterns, and more
- 🖥️ **CLI Interface** - Easy command-line management
- 🌐 **Web UI** - React-based dashboard with real-time monitoring
- 🛠️ **Systemd Support** - Run as system service on Linux
- 📊 **Status Monitoring** - Track backup statistics and repository health
- 🔌 **WebSocket Integration** - Real-time updates in the web interface

## 🎯 Perfect For

- Developers with personal + work GitHub accounts
- Freelancers managing multiple client accounts
- Organizations with separate GitHub orgs
- Anyone needing automatic, account-specific backups

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Multi-Account Setup](#multi-account-setup)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [Web UI](#web-ui)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Testing](#testing)
- [File Cleanup](#file-cleanup)

---

## 🔧 Prerequisites

- Python 3.8+
- Git
- Multiple GitHub accounts (optional, works with single account too)
- SSH keys configured for each GitHub account
- Node.js 16+ and npm (optional, only for Web UI)

### SSH Setup for Multi-Account

If using multiple GitHub accounts, configure SSH aliases in `~/.ssh/config`:

```ssh-config
# Personal GitHub Account
Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_personal

# Work/Office GitHub Account
Host github.com-office
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_office
```

Generate SSH keys if needed:
```bash
ssh-keygen -t ed25519 -C "your-personal@email.com" -f ~/.ssh/id_personal
ssh-keygen -t ed25519 -C "your-work@email.com" -f ~/.ssh/id_office
```

Add keys to respective GitHub accounts:
```bash
cat ~/.ssh/id_personal.pub  # Add to personal GitHub account
cat ~/.ssh/id_office.pub    # Add to work GitHub account
```

Test connections:
```bash
ssh -T git@github.com-personal   # Should say "Hi personal-username!"
ssh -T git@github.com-office     # Should say "Hi work-username!"
```

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd automated-github-push
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

**Backend (Python):**
```bash
pip install -r requirements.txt
pip install -e .
```

**Frontend (Node.js) - Optional, for Web UI:**
```bash
cd web-ui
npm install
cd ..
```

### 4. Set Environment Variables

Create environment variables for your GitHub tokens:

```bash
export GITHUB_TOKEN_PERSONAL="ghp_your_personal_token_here"
export GITHUB_TOKEN_WORK="ghp_your_work_token_here"
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:
```bash
echo 'export GITHUB_TOKEN_PERSONAL="ghp_your_personal_token_here"' >> ~/.bashrc
echo 'export GITHUB_TOKEN_WORK="ghp_your_work_token_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 👥 Multi-Account Setup

### Configuration File

Edit `~/.config/code-backup/config.yaml`:

```yaml
daemon:
  backup_interval: 21600  # 6 hours in seconds
  log_file: ~/.local/share/code-backup/daemon.log
  log_level: INFO

watched_paths:
  # Personal Account
  - name: Personal Projects
    path: /home/username/Desktop/Personal
    account:
      username: your-personal-username
      token_env_var: GITHUB_TOKEN_PERSONAL
      email: your-personal@email.com
      default_visibility: private
      ssh_host: github.com-personal  # SSH alias from ~/.ssh/config
    git:
      default_branch: main
      auto_commit_message: 'Auto-backup: {timestamp}'

  # Work Account
  - name: Work Projects
    path: /home/username/Desktop/Work
    account:
      username: your-work-username
      token_env_var: GITHUB_TOKEN_WORK
      email: your-work@email.com
      default_visibility: private
      ssh_host: github.com-office  # SSH alias from ~/.ssh/config
    git:
      default_branch: main
      auto_commit_message: 'Auto-backup: {timestamp}'

project_detection:
  min_size_bytes: 1024
  project_indicators:
    - package.json
    - requirements.txt
    - Cargo.toml
    - go.mod
    - pom.xml
    - README.md
  code_extensions:
    - .py
    - .js
    - .ts
    - .java
    - .go
    - .cpp
  ignore_patterns:
    - node_modules
    - venv
    - __pycache__
    - .git
    - dist
    - build
```

---

## 🚀 Quick Start

### Option 1: Start Everything (Recommended - One Command!)

**Start both Backend + Frontend:**
```bash
./start_all.sh
```

This single script starts:
- ✅ Backend daemon (Python + Flask API on http://localhost:8080)
- ✅ Frontend dev server (React on http://localhost:5173, proxies to backend)
- ✅ Automatically loads tokens from .env
- ✅ Creates logs/ directory for debugging

**Production Mode (Single Service):**
```bash
systemctl --user start code-backup
# Access UI at http://localhost:8080
```

**Stop everything:**
```bash
./stop_all.sh
```

Or press `Ctrl+C` in the terminal where you ran `./start_all.sh`

---

### Option 2: Using Separate Scripts

**Start daemon only (no UI):**
```bash
./start_daemon.sh
```

**Start daemon in background:**
```bash
./start_daemon_background.sh
```

**Check daemon status:**
```bash
./check_daemon_status.sh
```

**Stop daemon:**
```bash
./stop_daemon.sh
```

### Manual Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Set tokens
export GITHUB_TOKEN_PERSONAL="ghp_xxx"
export GITHUB_TOKEN_WORK="ghp_yyy"

# Start daemon
python -m code_backup_daemon.cli start
```

---

## 📚 Usage

### How Multi-Account Routing Works

The daemon automatically routes projects to the correct GitHub account based on **folder location**:

```
📁 /home/username/Desktop/Personal/
   ├── my-blog/                 → github.com/personal-username/my-blog
   ├── python-scripts/          → github.com/personal-username/python-scripts

📁 /home/username/Desktop/Work/
   ├── client-dashboard/        → github.com/work-username/client-dashboard
   ├── api-service/             → github.com/work-username/api-service
```

**No manual intervention needed!** Just create your project in the right folder.

### Basic Workflow

1. **Create a project** in one of your watched folders:
   ```bash
   mkdir ~/Desktop/Personal/my-new-app
   cd ~/Desktop/Personal/my-new-app
   echo "# My App" > README.md
   echo "print('hello')" > app.py
   ```

2. **Wait 30 seconds** - The daemon detects the new project

3. **Automatic magic happens:**
   - Initializes git repository
   - Sets correct git user/email for the account
   - Creates GitHub repository with SSH remote
   - Makes initial commit
   - Pushes to GitHub with correct authentication

4. **Continuous backups** - Every 6 hours, changes are auto-committed and pushed

### CLI Commands

```bash
# Daemon management
code-backup start              # Start daemon
code-backup stop               # Stop daemon
code-backup status             # Show status and statistics

# Repository management
code-backup list-repos         # List all tracked repositories
code-backup list-repos --account personal-username  # Filter by account
code-backup backup             # Force backup all repos now
code-backup backup my-project  # Force backup specific repo

# Manual operations
code-backup add /path/to/project    # Manually add project
code-backup remove project-name     # Remove from tracking

# Configuration
code-backup config-show        # Display current configuration
code-backup config-set daemon.backup_interval 3600  # Change settings
```

### 🌐 Web UI

The project includes a modern React-based web interface for managing your backups visually.

**Start the Web UI:**

```bash
# Option 1: Using the helper script
./start_ui.sh

# Option 2: Manual startup

# Terminal 1 - Start backend (daemon with web server)
./start_backend.sh

# Terminal 2 - Start React dev server
cd web-ui
npm install  # First time only
npm run dev  # Opens at http://localhost:5173
```

**Web UI Features:**
- 📊 Real-time dashboard with backup statistics
- 📁 View all tracked repositories grouped by account
- ▶️ Enable/disable individual projects
- 🔄 Manual backup triggers for specific repos
- 📡 Live updates via WebSocket (no refresh needed)
- 🎨 Modern interface built with React + Vite + TailwindCSS

**Production Build:**
```bash
cd web-ui
npm run build
# Static files served by Flask backend at http://localhost:8080

# Production service runs as single unified service
systemctl --user start code-backup
```

**Configuration:**

Enable/configure the web UI in `config.yaml`:
```yaml
ui:
  enabled: true
  host: localhost
  port: 8080
  theme: dark  # or 'light'

# Project preferences (managed via Web UI)
project_preferences:
  my-project-name:
    enabled: true  # Toggle backup on/off per project
```

---

## ⚙️ Configuration

### Configuration File Location

`~/.config/code-backup/config.yaml`

### Key Configuration Sections

#### Daemon Settings
```yaml
daemon:
  backup_interval: 21600     # Backup frequency in seconds (6 hours)
  log_level: INFO            # DEBUG, INFO, WARNING, ERROR
  pid_file: ~/.local/share/code-backup/daemon.pid
  state_file: ~/.local/share/code-backup/state.json
```

#### Watched Paths (Multi-Account)
```yaml
watched_paths:
  - name: Account Name
    path: /path/to/folder
    account:
      username: github-username
      token_env_var: GITHUB_TOKEN_VAR  # Environment variable name
      email: email@example.com
      ssh_host: github.com-personal    # SSH config alias
      default_visibility: private
      create_org_repos: false
      organization: ''                 # For org repos
      use_gh_cli: false
    git:
      default_branch: main
      auto_commit_message: 'Auto-backup: {timestamp}'
      pull_before_push: true
      handle_conflicts: skip           # skip, notify, force
```

#### Project Detection
```yaml
project_detection:
  min_size_bytes: 1024        # Minimum project size
  project_indicators:         # Files indicating a valid project
    - package.json
    - requirements.txt
    - Cargo.toml
    - go.mod
  code_extensions:            # Valid code file extensions
    - .py
    - .js
    - .ts
  ignore_patterns:            # Folders to ignore
    - node_modules
    - venv
    - __pycache__
```

---

## 🔍 How It Works

### Multi-Account Authentication Flow

```
1. New project detected in /Desktop/Personal/my-app
   ↓
2. Daemon matches path to "Personal Projects" config
   ↓
3. Reads account settings:
   - username: personal-username
   - ssh_host: github.com-personal
   - email: personal@email.com
   ↓
4. Initializes git with personal email
   ↓
5. Creates GitHub repo via API (using personal token)
   ↓
6. Adds SSH remote: git@github.com-personal:personal-username/my-app.git
   ↓
7. SSH config routes to ~/.ssh/id_personal key
   ↓
8. Push succeeds with correct account authentication
   ↓
9. Commit attribution shows: personal-username <personal@email.com>
```

### Project Detection Logic

A folder becomes a tracked project if:

1. **Has project indicators** (package.json, requirements.txt, etc.)
   OR **Contains code files** (.py, .js, .java, etc.)

2. **Meets minimum size** (default: 1KB)

3. **Not in ignore patterns** (node_modules, venv, etc.)

4. **Located in a watched path**

### Backup Cycle

Every 6 hours (configurable):

1. Check all tracked repositories for changes
2. Stage all changes (`git add .`)
3. Commit with timestamp message
4. Pull with rebase (if configured)
5. Push to GitHub with SSH authentication
6. Update statistics and state file

---

## 🛠️ Troubleshooting

### Daemon Won't Start

**Error: "No watched paths configured"**

✅ **Fix:** The config path was incorrect. This is now fixed. Restart the daemon.

**Error: "Missing 'account' configuration"**

✅ **Fix:** Updated config validation. Make sure config uses `account:` not `github:`.

### Repository Push Fails

**Error: "repository not found"**

**Cause:** Using HTTPS URL instead of SSH, can't authenticate.

✅ **Fix:** The daemon now uses SSH URLs automatically. Make sure:
1. `ssh_host` is set in account config
2. SSH key is added to GitHub account
3. SSH config has the correct alias

**Test SSH:**
```bash
ssh -T git@github.com-personal
# Should show: Hi your-username! You've successfully authenticated
```

**Check remote URL:**
```bash
cd ~/Desktop/Personal/my-project
git remote -v
# Should show: git@github.com-personal:username/my-project.git
```

### Wrong Account Attribution

**Problem:** Commits show wrong username/email

**Cause:** Git config not set correctly for the repository

✅ **Fix:** The daemon now sets repo-specific git config. Check with:
```bash
cd ~/Desktop/Personal/my-project
git config user.name
git config user.email
```

Should match the account settings in config.yaml.

### Project Not Detected

**Check if project meets criteria:**
```bash
# Has project indicator?
ls package.json requirements.txt README.md

# Has code files?
ls *.py *.js *.java

# Meets size requirement?
du -sh .  # Should be > 1KB
```

**Check logs:**
```bash
tail -f ~/.local/share/code-backup/daemon.log | grep "my-project"
```

### View Detailed Logs

```bash
# Real-time logs
tail -f ~/.local/share/code-backup/daemon.log

# Full daemon output (if running in foreground)
./start_daemon.sh

# Check tracked repositories
cat ~/.local/share/code-backup/state.json | jq
```

---

## 🎓 Advanced Usage

### Run as Systemd Service

For production use, run the daemon as a systemd service:

```bash
# Copy service file
cp code-backup.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable (start on login)
systemctl --user enable code-backup

# Start service
systemctl --user start code-backup

# Check status
systemctl --user status code-backup

# View logs
journalctl --user -u code-backup -f
```

### Custom Backup Intervals

Change backup frequency:

```bash
# Every hour
code-backup config-set daemon.backup_interval 3600

# Every 12 hours
code-backup config-set daemon.backup_interval 43200

# Every day
code-backup config-set daemon.backup_interval 86400
```

### Organization Repositories

To create repos in an organization:

```yaml
watched_paths:
  - name: Company Projects
    path: /home/user/Desktop/Company
    account:
      username: your-username
      create_org_repos: true
      organization: company-org-name
```

### Conflict Handling Strategies

```yaml
git:
  handle_conflicts: skip    # Skip backup if conflicts (default, safe)
  # handle_conflicts: notify # Log error but don't stop
  # handle_conflicts: force  # Force push (dangerous!)
```

---

## 🗑️ File Cleanup

The repository contains some development/test files that can be safely deleted:

### Safe to Delete

**Old development scripts (13 files):**
```bash
rm script.py script_{1..12}.py
```

**One-time test/fix scripts (7 files):**
```bash
rm create_and_push_repos.sh fix_and_push_repos.sh push_test_repos.sh \
   update_test_repo_remotes.sh integration_test_step7.sh run_integration_test.sh \
   test_ssh_url_fix.py
```

**Planning/completed documentation (4-5 files):**
```bash
rm STEP_7_READY.md config-multi-account-example.yaml \
   MULTI_ACCOUNT_IMPLEMENTATION_PLAN.md SESSION_PROGRESS.md \
   STEP_7_INTEGRATION_TESTING.md CLEANUP_ANALYSIS.md
```

**Cache directories:**
```bash
rm -rf __pycache__ .pytest_cache
```

**Optional - Unit tests (if not modifying code):**
```bash
rm test_*.py
```

### Keep These Files

**Essential:**
- `code_backup_daemon/` - Main application
- `setup.py`, `requirements.txt` - Installation
- `README.md`, `RUNNING_GUIDE.md` - Documentation
- `start_daemon.sh`, `stop_daemon.sh`, etc. - Helper scripts
- `code-backup.service` - Systemd service
- `.gitignore`, `.git/`, `venv/` - Development

---

## 📊 Project Structure

```
automated-github-push/
├── code_backup_daemon/          # Main application package
│   ├── __init__.py
│   ├── backup_service.py        # Backup orchestration
│   ├── cli.py                   # Command-line interface
│   ├── config.py                # Configuration management
│   ├── folder_watcher.py        # Filesystem monitoring
│   ├── git_service.py           # Git operations
│   ├── github_service.py        # GitHub API integration
│   └── web/                     # Web server components
│       ├── __init__.py
│       ├── api.py               # RESTful API endpoints
│       └── websocket.py         # WebSocket handlers
│
├── web-ui/                      # React frontend
│   ├── src/                     # React components
│   ├── public/                  # Static assets
│   ├── package.json             # NPM dependencies
│   └── vite.config.js           # Vite build config
│
├── setup.py                     # Package setup
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── RUNNING_GUIDE.md            # Detailed usage guide
├── FIX_SUMMARY.md              # SSH authentication fix docs
├── CLAUDE.md                   # Claude Code instructions
│
├── start_daemon.sh             # Start daemon (foreground)
├── start_daemon_background.sh  # Start daemon (background)
├── start_backend.sh            # Start backend with web server
├── start_ui.sh                 # Start complete UI stack
├── check_daemon_status.sh      # Check status
├── stop_daemon.sh              # Stop daemon
│
├── code-backup.service         # Systemd service file
├── .gitignore                  # Git ignore rules
└── venv/                       # Virtual environment
```

---

## 🔒 Security & Privacy

- **SSH Key Authentication** - More secure than HTTPS tokens
- **Private by Default** - New repositories are created as private
- **Token Security** - Tokens stored in environment variables (not in code)
- **Local Processing** - All code analysis happens locally
- **Account Isolation** - Each account uses its own SSH key
- **No Code Reading** - Only backs up, never reads your code content
- **Configurable .gitignore** - Automatically excludes sensitive files

---

## 📝 Documentation

- **[README.md](README.md)** - Main documentation (this file)
- **[RUNNING_GUIDE.md](RUNNING_GUIDE.md)** - Detailed usage and testing guide
- **[FIX_SUMMARY.md](FIX_SUMMARY.md)** - SSH authentication fix details
- **[CLAUDE.md](CLAUDE.md)** - Claude Code integration guide

---

## 🐛 Known Issues & Solutions

### ✅ RESOLVED: Multi-Account SSH Authentication

**Issue:** Daemon used HTTPS URLs which don't support multi-account SSH keys.

**Solution:** Implemented SSH URL generation with account-specific host aliases. See [FIX_SUMMARY.md](FIX_SUMMARY.md) for details.

### ✅ RESOLVED: Config Validation Errors

**Issue:** Config validation was checking for `github` instead of `account`.

**Solution:** Updated validation to use correct `account` field name.

---

## 🧪 Testing

### Backend Tests

Run the test suite:

```bash
source venv/bin/activate
pytest test_*.py -v
```

All tests should pass:
- ✅ Config tests (3/3)
- ✅ GitHub service tests (5/5)
- ✅ Backup service tests (10/10)
- ✅ Folder watcher tests (6/6)
- ✅ Git service tests (5/5)
- ✅ CLI tests (7/7)

**Total: 36/36 tests passing**

### Web UI Tests

```bash
cd web-ui
npm install
npm run test   # Run unit tests
npm run lint   # Check code style
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

### Backend
- **[GitPython](https://github.com/gitpython-developers/GitPython)** - Git operations
- **[Watchdog](https://github.com/gorakhargosh/watchdog)** - File system monitoring
- **[Click](https://click.palletsprojects.com/)** - CLI framework
- **[PyYAML](https://pyyaml.org/)** - Configuration parsing
- **[Requests](https://requests.readthedocs.io/)** - HTTP library for GitHub API
- **[Flask](https://flask.palletsprojects.com/)** - Web framework
- **[Flask-SocketIO](https://flask-socketio.readthedocs.io/)** - WebSocket support
- **[Flask-CORS](https://flask-cors.readthedocs.io/)** - CORS handling

### Frontend
- **[React](https://react.dev/)** - UI framework
- **[Vite](https://vitejs.dev/)** - Build tool and dev server
- **[TailwindCSS](https://tailwindcss.com/)** - CSS framework
- **[Socket.IO Client](https://socket.io/)** - WebSocket client

---

## 📞 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check existing documentation
- Review logs in `~/.local/share/code-backup/daemon.log`

---

**Happy coding! 🚀**

Your code is now automatically backed up to the right GitHub account, with proper authentication and attribution!
