# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Code Backup Daemon is a Python-based service that automatically monitors multiple code folders, detects new projects, and backs them up to GitHub with multi-account support. It runs as a unified systemd service with integrated web UI. Uses watchdog for filesystem monitoring, GitPython for git operations, GitHub API for repository management, and Flask + React for the web interface.

## Development Commands

### Installation & Setup
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Create .env file for GitHub tokens (NOT tracked in git)
cp .env.example .env
# Edit .env and add your tokens:
# GITHUB_TOKEN_NK=ghp_xxx
# GITHUB_TOKEN_AI4M=ghp_yyy
```

### Running the Service

**Production (Unified Service - Recommended):**
```bash
# Install and enable systemd service
cp code-backup.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable code-backup
systemctl --user start code-backup

# Check status
systemctl --user status code-backup
journalctl --user -u code-backup -f

# Access UI at http://localhost:8080
```

**Development Mode (Separate Processes):**
```bash
# Terminal 1: Start backend daemon
./start_backend.sh  # Runs on port 8080

# Terminal 2: Start React dev server
cd web-ui
npm install  # First time only
npm run dev  # Runs on port 5173, proxies API to 8080
```

### Web UI Development
```bash
# Production build
cd web-ui
npm run build  # Output: web-ui/dist/

# The daemon serves built files from web-ui/dist/ at http://localhost:8080
```

### CLI Commands
```bash
code-backup start              # Start daemon (foreground)
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

## Architecture

### Production Service Architecture

The service runs as a **single unified process** with three integrated components:

1. **Daemon Thread** - Background backup loop (every 6 hours default)
2. **Flask Backend** - REST API + WebSocket on port 8080
3. **Static Frontend** - React bundle served by Flask from `web-ui/dist/`

All three run in one systemd service for simplified deployment and automatic startup.

### Core Components

1. **BackupService** ([backup_service.py](code_backup_daemon/backup_service.py)) - Main orchestrator
   - Manages lifecycle: start, stop, state persistence
   - Coordinates git_service, github_service, folder_watchers (one per watched path)
   - Runs periodic backup loop in separate thread
   - Tracks repository state in `state.json` with account mapping
   - Maintains statistics (total_repos, successful_backups, etc.)
   - Integrates with WebSocket for real-time UI updates

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
   - **CRITICAL**: Validates push results for errors (ERROR, REJECTED, REMOTE_REJECTED, REMOTE_FAILURE flags)
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
   - Default UI port: **8080**

6. **CLI** ([cli.py](code_backup_daemon/cli.py)) - Command-line interface
   - Click-based commands for daemon management
   - Status reporting, repository listing
   - Configuration viewing/editing
   - Signal handling for graceful shutdown
   - Integrated web UI launcher (starts Flask server on port 8080)

7. **Web UI** ([web-ui/](web-ui/)) - React-based management interface
   - Real-time monitoring via WebSocket
   - Enable/disable individual projects
   - Manual backup triggers
   - Multi-account project grouping
   - Built with React + Vite + TailwindCSS
   - Production build served by Flask from `web-ui/dist/`

8. **Web Server** ([code_backup_daemon/web/](code_backup_daemon/web/)) - Flask backend
   - RESTful API for daemon control ([api.py](code_backup_daemon/web/api.py))
   - WebSocket support via Flask-SocketIO ([websocket.py](code_backup_daemon/web/websocket.py))
   - Serves static React build in production from `web-ui/dist/`
   - CORS enabled for development (ports 5173 and 8080)
   - Port: **8080**

### Multi-Account Architecture

**Key Concept**: Each watched path is associated with a specific GitHub account configuration.

```yaml
watched_paths:
  - name: Personal Projects
    path: /home/user/Desktop/Personal
    account:
      username: personal-username
      token_env_var: GITHUB_TOKEN_PERSONAL  # Loaded from .env
      email: personal@email.com
      ssh_host: github.com-personal  # SSH config alias
      default_visibility: private
  - name: Work Projects
    path: /home/user/Desktop/Work
    account:
      username: work-username
      token_env_var: GITHUB_TOKEN_WORK  # Loaded from .env
      email: work@email.com
      ssh_host: github.com-office
      default_visibility: private
```

**Account Routing Flow:**
1. Project detected in `/home/user/Desktop/Personal/my-app`
2. BackupService matches path to "Personal Projects" config
3. Reads account settings (username, token, email, ssh_host)
4. GitService initializes repo with personal email
5. GitHubService creates repo using personal token (from env var)
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
  - Validates push results (checks ERROR/REJECTED flags)
  - Returns False if push rejected by GitHub
  ↓
State persisted to state.json with account association
  ↓
WebSocket notification to UI (if connected)
```

### State Management

**Two-level timestamp tracking:**

1. **Per-Repository** (`state.json`):
   - `last_backup` - When this specific repo was last pushed
   - `last_check` - When daemon last checked this repo
   - `backup_count` - Number of successful pushes (NOT cycles)
   - Only increments on actual successful pushes

2. **Global Stats** (`stats` in BackupService):
   - `last_backup_time` - When last backup cycle completed (internal use)
   - API returns most recent `last_backup` across all repos (not cycle time)

**Repository Metadata** (`state.json`):
- repo_name, local_path, remote_url
- account_username, account_path (identifies which account)
- github_exists, last_backup, backup_count
- is_active, error_count, last_error
- enabled (for UI toggle feature)

**Other State Files:**
- **daemon.pid** - Process ID for daemon management
- **daemon.log** - Application logs
- **project_preferences** in config - Stores per-project enabled/disabled state

## Important Implementation Notes

### Security & Token Management

**CRITICAL**: Never commit tokens to git!

- Tokens are stored in `.env` file (in `.gitignore`)
- SystemD service uses `EnvironmentFile=/path/to/.env`
- Each account specifies `token_env_var` pointing to env var name
- Tokens resolved at runtime via `os.environ.get(token_env_var)`
- Validation occurs at startup to ensure all tokens are available

**File Format:**
```bash
# .env file (no quotes for systemd compatibility)
GITHUB_TOKEN_NK=ghp_xxx
GITHUB_TOKEN_AI4M=ghp_yyy
```

### Push Error Detection

**CRITICAL FIX** (commit 61351dd): GitPython's `push()` doesn't raise exceptions when GitHub rejects pushes (e.g., secret scanning). Always check push results:

```python
push_info = origin.push(...)
for info in push_info:
    if info.flags & (info.ERROR | info.REJECTED | info.REMOTE_REJECTED | info.REMOTE_FAILURE):
        return False  # Push failed!
```

Without this check, backup_count increments even when pushes fail, causing drift between local state and GitHub.

### Multi-Account SSH Setup

**Required for multi-account support:**

SSH config at `~/.ssh/config`:
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

- Each account's `ssh_host` maps to a specific SSH key
- Git remotes use SSH URLs, not HTTPS, for proper multi-account auth
- Repo-specific git config sets user.name/user.email per repository

Test connections:
```bash
ssh -T git@github.com-personal  # Should show: Hi username!
ssh -T git@github.com-office    # Should show: Hi username!
```

### Threading and Concurrency

- Backup loop runs in separate thread - use locks when accessing shared state
- Web server (Flask-SocketIO) runs in daemon thread
- FolderWatcher observers run in their own threads (one per watched path)
- State saves are atomic to prevent corruption

### WebSocket Integration

- BackupService has optional `websocket_handler` attribute
- UI updates sent via `service.websocket_handler.emit_event()` if handler exists
- Events: repository_added, backup_started, backup_completed, status_update
- WebSocket connects to same origin (production) or proxies to port 8080 (dev)

### Port Configuration

**Production**: Single port **8080** for everything
- Flask API: http://localhost:8080/api/*
- WebSocket: ws://localhost:8080/socket.io
- Static UI: http://localhost:8080/

**Development**: Two ports
- React dev server: http://localhost:5173 (proxies API/WS to 8080)
- Flask backend: http://localhost:8080

Update ports in:
- `config.yaml`: `ui.port: 8080`
- `web-ui/vite.config.js`: proxy target `http://localhost:8080`
- Default in `config.py`: `DEFAULT_CONFIG['ui']['port'] = 8080`

## Common Development Patterns

### Adding a New API Endpoint

1. Add route to `code_backup_daemon/web/api.py`
2. Access service via `current_app.backup_service`
3. Return JSON with proper error handling
4. Update frontend to call new endpoint

### Adding a New WebSocket Event

1. Define event in `code_backup_daemon/web/websocket.py`
2. Emit via `service.websocket_handler.emit_event(event_name, data)`
3. Listen in React: `socket.on('event_name', handler)`

### Modifying Backup Logic

1. Edit `code_backup_daemon/backup_service.py`
2. Remember: `backup_count` only increments on successful pushes
3. Always check `result['changes_pushed']` before incrementing
4. Use `repo_info['last_backup']` for actual push time
5. Use `repo_info['last_check']` for when daemon checked

### Testing Multi-Account

1. Set up two SSH keys and add to `~/.ssh/config`
2. Create two watched paths in `config.yaml` with different accounts
3. Drop test projects in each folder
4. Verify commits use correct email: `git log --format='%an <%ae>'`
5. Verify pushes go to correct account

## File Dependencies

- GitPython for git operations
- watchdog for filesystem monitoring
- click for CLI interface
- PyYAML for configuration
- requests for GitHub API access
- Flask + Flask-SocketIO for web server
- Flask-CORS for development CORS support
- eventlet for async WebSocket support
- React + Vite + TailwindCSS for web UI

## Migration Notes

The codebase evolved from single-account to multi-account support:
- Old config: `github.*` at top level
- New config: `watched_paths[].account.*`
- Migration script: [migrate_accounts.py](migrate_accounts.py)

Recent consolidation (commit 61351dd):
- Merged daemon + backend + frontend into single service
- Changed from port 5000 → 8080
- Added push error detection
- Moved tokens from service file to .env file
