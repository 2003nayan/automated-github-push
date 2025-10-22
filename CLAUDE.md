# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Code Backup Daemon is a Python-based service that automatically monitors multiple code folders, detects new projects, and backs them up to GitHub with multi-account support. It runs as a daemon/systemd service and includes a web UI for management. Uses watchdog for filesystem monitoring, GitPython for git operations, and GitHub API for repository management.

## Development Commands

### Installation & Setup
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Set environment variables for GitHub tokens
export GITHUB_TOKEN_PERSONAL="ghp_xxx"
export GITHUB_TOKEN_WORK="ghp_yyy"
```

### Testing
```bash
# Run all tests
pytest test_*.py -v

# Run specific test file
pytest test_backup_service.py -v

# Format code
black .

# Lint code
flake8 .
```

### Running the Daemon
```bash
# Start daemon (foreground)
./start_daemon.sh
# Or: python -m code_backup_daemon.cli start

# Start daemon in background
./start_daemon_background.sh

# Check status
./check_daemon_status.sh
# Or: code-backup status

# Stop daemon
./stop_daemon.sh
# Or: code-backup stop

# As systemd service
systemctl --user start code-backup
systemctl --user status code-backup
journalctl --user -u code-backup -f
```

### Web UI Development
```bash
# Start backend (daemon with web server)
./start_backend.sh

# Start React dev server (separate terminal)
cd web-ui
npm install  # First time only
npm run dev  # Runs on http://localhost:5173

# Production build
cd web-ui
npm run build
```

### CLI Commands
```bash
code-backup start              # Start daemon
code-backup stop               # Stop daemon
code-backup status             # Show daemon status and stats
code-backup list-repos         # List tracked repositories
code-backup list-repos --account username  # Filter by account
code-backup backup [repo]      # Force backup (all or specific)
code-backup add <path>         # Manually add project
code-backup remove <name>      # Remove from tracking
code-backup config-show        # Display configuration
code-backup config-set <key> <value>  # Update configuration
```

## Architecture

### Core Components

1. **BackupService** ([backup_service.py](code_backup_daemon/backup_service.py)) - Main orchestrator
   - Manages lifecycle: start, stop, state persistence
   - Coordinates git_service, github_service, folder_watchers (plural - one per watched path)
   - Runs periodic backup loop in separate thread
   - Tracks repository state in JSON file with account mapping
   - Maintains statistics (total_repos, successful_backups, etc.)
   - Provides WebSocket integration for real-time UI updates

2. **FolderWatcher** ([folder_watcher.py](code_backup_daemon/folder_watcher.py)) - Filesystem monitoring
   - Uses watchdog Observer to detect new folders
   - Filters based on ignore_patterns from config
   - Delays processing (30s) to let users set up folders
   - Callbacks to BackupService when valid projects detected
   - Multi-instance: one watcher per watched path

3. **GitService** ([git_service.py](code_backup_daemon/git_service.py)) - Local git operations
   - Initialize repos with account-specific user/email configuration
   - Create initial commits with .gitignore
   - Stage, commit, push changes
   - Handle merge conflicts (skip/notify/force strategies)
   - Support SSH URL generation with account-specific hostnames
   - Manage branches (default: main)

4. **GitHubService** ([github_service.py](code_backup_daemon/github_service.py)) - Remote GitHub operations
   - Create repositories via GitHub API (multi-account support)
   - Check repository existence
   - Handle org vs personal repos
   - Set visibility (private/public)
   - Token-based authentication per account (from environment variables)

5. **Config** ([config.py](code_backup_daemon/config.py)) - Configuration management
   - Loads from YAML (default: `~/.config/code-backup/config.yaml`)
   - Deep merges user config with defaults
   - Validates required fields and paths
   - Supports dot notation access (e.g., `config.get('daemon.backup_interval')`)
   - **Multi-account structure**: `watched_paths` is a list of path configs, each with `account` settings

6. **CLI** ([cli.py](code_backup_daemon/cli.py)) - Command-line interface
   - Click-based commands for daemon management
   - Status reporting, repository listing
   - Configuration viewing/editing
   - Signal handling for graceful shutdown
   - Integrated web UI launcher

7. **Web UI** ([web-ui/](web-ui/)) - React-based management interface
   - Real-time monitoring via WebSocket
   - Enable/disable individual projects
   - Manual backup triggers
   - Multi-account project grouping
   - Built with React + Vite + TailwindCSS

8. **Web Server** ([code_backup_daemon/web/](code_backup_daemon/web/)) - Flask backend
   - RESTful API for daemon control
   - WebSocket support via Flask-SocketIO
   - Serves static React build in production
   - CORS enabled for development

### Multi-Account Architecture

**Key Concept**: Each watched path is associated with a specific GitHub account configuration.

```yaml
watched_paths:
  - name: Personal Projects
    path: /home/user/Desktop/Personal
    account:
      username: personal-username
      token_env_var: GITHUB_TOKEN_PERSONAL
      email: personal@email.com
      ssh_host: github.com-personal  # SSH config alias
      default_visibility: private
  - name: Work Projects
    path: /home/user/Desktop/Work
    account:
      username: work-username
      token_env_var: GITHUB_TOKEN_WORK
      email: work@email.com
      ssh_host: github.com-office
      default_visibility: private
```

**Account Routing Flow:**
1. Project detected in `/home/user/Desktop/Personal/my-app`
2. BackupService matches path to "Personal Projects" config
3. Reads account settings (username, token, email, ssh_host)
4. GitService initializes repo with personal email
5. GitHubService creates repo using personal token
6. GitService adds SSH remote: `git@github.com-personal:personal-username/my-app.git`
7. SSH config routes to correct key via ssh_host alias
8. All commits/pushes use personal account credentials

### Key Data Flow

```
New folder created → FolderWatcher detects (path-specific instance)
  ↓
Checks project indicators (package.json, requirements.txt, etc.)
  ↓
BackupService.add_repository(path, account_config)
  ↓
GitService.init_repo(account_config) - Sets user.name/user.email per repo
  ↓
GitHubService.create_repository(account_config) - Uses account-specific token
  ↓
GitService.add_remote(ssh_host) - Uses SSH URL with account hostname
  ↓
GitService.push() - Authenticated via SSH key
  ↓
State persisted to state.json with account association
  ↓
WebSocket notification to UI (if connected)
```

### Project Detection Logic

A folder is considered a valid project if it contains:
- Project indicator files (package.json, requirements.txt, Cargo.toml, go.mod, etc.)
- OR source code files with specific extensions (.py, .js, .java, .go, etc.)
- AND meets minimum size threshold (default: 1KB)
- AND not in ignore_patterns (node_modules, venv, __pycache__, etc.)

### State Management

- **state.json** - Tracks all repositories with metadata:
  - repo_name, local_path, remote_url
  - account_username, account_path (identifies which account)
  - github_exists, last_backup_time, backup_count
  - is_active, error_count, last_error
  - enabled (for UI toggle feature)
- **daemon.pid** - Process ID for daemon management
- **daemon.log** - Application logs
- **project_preferences** in config - Stores per-project enabled/disabled state

### Configuration Structure

Key config sections:
- `daemon.*` - Backup interval, log level, file paths
- `watched_paths[]` - **List of path configurations**, each with:
  - `name` - Display name for the path
  - `path` - Filesystem path to monitor
  - `account.*` - GitHub account settings (username, token_env_var, email, ssh_host)
  - `git.*` - Git settings (default_branch, commit message, conflict handling)
- `project_detection.*` - Indicators, extensions, ignore_patterns
- `notifications.*` - Error/success notification settings
- `ui.*` - Web UI settings (enabled, host, port, theme)
- `project_preferences.*` - Per-project enabled/disabled toggles

## Important Implementation Notes

### Multi-Account SSH Setup
- Requires SSH config with per-account host aliases (e.g., `github.com-personal`, `github.com-office`)
- Each account's `ssh_host` maps to a specific SSH key via `~/.ssh/config`
- Git remotes use SSH URLs, not HTTPS, for proper multi-account auth
- Repo-specific git config sets user.name/user.email per repository

### Threading and Concurrency
- Backup loop runs in separate thread - use locks when accessing shared state
- Web server (Flask-SocketIO) runs in separate daemon thread
- FolderWatcher observers run in their own threads (one per watched path)
- State saves are atomic to prevent corruption

### Token Management
- Tokens loaded from environment variables (not stored in config)
- Each account specifies `token_env_var` pointing to env var name
- Tokens resolved at runtime via `os.environ.get(token_env_var)`
- Validation occurs at startup to ensure all tokens are available

### WebSocket Integration
- BackupService has optional `websocket_handler` attribute
- UI updates sent via `service.websocket_handler.emit_event()` if handler exists
- Events: repository_added, backup_started, backup_completed, status_update

### Key Differences from Single-Account
- `watched_paths` is now a **list** (not single `code_folder`)
- Account config moved from top-level `github.*` to per-path `account.*`
- Multiple FolderWatcher instances (one per watched path)
- State tracks `account_username` and `account_path` for each repo
- Git operations receive account config parameter

## File Dependencies

- GitPython for git operations
- watchdog for filesystem monitoring
- click for CLI interface
- PyYAML for configuration
- requests for GitHub API access
- Flask + Flask-SocketIO for web server
- Flask-CORS for development CORS support
- eventlet for async WebSocket support
- React + Vite + TailwindCSS for web UI (in web-ui/)

## SSH Configuration Requirements

Multi-account support requires SSH config file at `~/.ssh/config`:

```
Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_personal

Host github.com-office
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_office
```

Test SSH connections:
```bash
ssh -T git@github.com-personal  # Should show: Hi username!
ssh -T git@github.com-office    # Should show: Hi username!
```

## SystemD Integration

The service file ([code-backup.service](code-backup.service)) should be copied to `~/.config/systemd/user/` for user-level service management. Ensure environment variables for tokens are set in the service file or via systemd environment.

## Migration Notes

The codebase evolved from single-account to multi-account support. Key files for migration:
- [migrate_accounts.py](migrate_accounts.py) - Script to migrate old state.json to new format
- Old config used `github.*` at top level, new uses `watched_paths[].account.*`
