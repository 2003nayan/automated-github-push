# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Code Backup Daemon is a Python-based service that automatically monitors a code folder, detects new projects, and backs them up to GitHub. It runs as a daemon/systemd service and uses watchdog for filesystem monitoring, GitPython for git operations, and GitHub CLI for repository management.

## Development Commands

### Installation & Setup
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Run installation script
./install.sh

# Setup wizard (creates config)
code-backup setup
```

### Testing & Code Quality
```bash
# Run tests
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

### Running the Daemon
```bash
# Start daemon (foreground)
python main.py

# Or via CLI
code-backup start

# As systemd service
systemctl --user start code-backup
systemctl --user status code-backup
journalctl --user -u code-backup -f
```

### CLI Commands
```bash
code-backup start              # Start daemon
code-backup stop               # Stop daemon
code-backup status             # Show daemon status and stats
code-backup list-repos         # List tracked repositories
code-backup backup [repo]      # Force backup (all or specific)
code-backup add <path>         # Manually add project
code-backup remove <name>      # Remove from tracking
code-backup config-show        # Display configuration
code-backup config-set <key> <value>  # Update configuration
```

## Architecture

### Core Components

1. **BackupService** ([backup_service.py](backup_service.py)) - Main orchestrator
   - Manages lifecycle: start, stop, state persistence
   - Coordinates git_service, github_service, folder_watcher
   - Runs periodic backup loop in separate thread
   - Tracks repository state in JSON file
   - Maintains statistics (total_repos, successful_backups, etc.)

2. **FolderWatcher** ([folder_watcher.py](folder_watcher.py)) - Filesystem monitoring
   - Uses watchdog Observer to detect new folders
   - Filters based on ignore_patterns from config
   - Delays processing (30s) to let users set up folders
   - Callbacks to BackupService when valid projects detected

3. **GitService** ([git_service.py](git_service.py)) - Local git operations
   - Initialize repos, create initial commits with .gitignore
   - Stage, commit, push changes
   - Handle merge conflicts (skip/notify/force strategies)
   - Manage branches (default: main)

4. **GitHubService** ([github_service.py](github_service.py)) - Remote GitHub operations
   - Create repositories (via gh CLI or API)
   - Check repository existence
   - Handle org vs personal repos
   - Set visibility (private/public)

5. **Config** ([config.py](config.py)) - Configuration management
   - Loads from YAML (default: `~/.config/code-backup/config.yaml`)
   - Deep merges user config with defaults
   - Validates required fields and paths
   - Supports dot notation access (e.g., `config.get('daemon.backup_interval')`)

6. **CLI** ([cli.py](cli.py)) - Command-line interface
   - Click-based commands for daemon management
   - Status reporting, repository listing
   - Configuration viewing/editing
   - Signal handling for graceful shutdown

### Key Data Flow

```
New folder created → FolderWatcher detects
  ↓
Checks project indicators (package.json, requirements.txt, etc.)
  ↓
BackupService.add_repository()
  ↓
GitService.init_repo() (if needed)
  ↓
GitHubService.create_repository()
  ↓
GitService.add_remote() and push
  ↓
State persisted to state.json
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
  - github_exists, last_backup_time, backup_count
  - is_active, error_count, last_error
- **daemon.pid** - Process ID for daemon management
- **daemon.log** - Application logs

### Configuration Structure

Key config sections:
- `daemon.*` - Backup interval, log level, file paths
- `paths.*` - code_folder (monitored), config_dir, data_dir
- `github.*` - username, default_visibility, org settings
- `git.*` - default_branch, commit message template, conflict handling
- `project_detection.*` - indicators, extensions, ignore_patterns
- `notifications.*` - Error/success notification settings

## Important Implementation Notes

- The daemon uses threading for the backup loop - be careful with thread safety when modifying shared state
- The backup service saves state after every significant operation (add, remove, backup)
- Git operations use GitPython library, not subprocess calls (except for specialized commands)
- GitHub operations prefer gh CLI over API when `use_gh_cli: true` (default)
- The folder watcher only monitors immediate subdirectories (recursive=False) to avoid deep nesting
- Initial commits automatically create a comprehensive .gitignore based on config patterns
- Conflict handling strategies: 'skip' (default), 'notify' (log only), 'force' (force push)

## File Dependencies

- GitPython for git operations
- watchdog for filesystem monitoring
- click for CLI interface
- PyYAML for configuration
- requests for direct GitHub API access (when not using gh CLI)
- GitHub CLI (`gh`) must be installed and authenticated

## SystemD Integration

The service file ([code-backup.service](code-backup.service)) should be copied to `~/.config/systemd/user/` for user-level service management.
