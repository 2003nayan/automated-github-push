"""
Core backup service for Code Backup Daemon
"""
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Set, Optional
from datetime import datetime, timedelta

from .git_service import GitService
from .github_service import GitHubService
from .folder_watcher import FolderWatcher

logger = logging.getLogger(__name__)

class BackupService:
    """Core service that orchestrates all backup operations"""

    def __init__(self, config):
        self.config = config
        self.git_service = GitService(config)
        self.github_service = GitHubService(config)

        # State management
        self.state_file = config.get_path('daemon.state_file')
        self.tracked_repos: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.backup_thread: Optional[threading.Thread] = None

        # Multi-path support: folder_watchers is now a list
        self.folder_watchers: list[FolderWatcher] = []

        # Configuration
        self.backup_interval = config.get('daemon.backup_interval', 86400)  # 24 hours
        self.watched_paths = config.get('watched_paths', [])

        # WebSocket handler for UI (set by web server)
        self.websocket_handler = None

        # Statistics
        self.stats = {
            'total_repos': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'repos_created': 0,
            'last_backup_time': None,
            'start_time': None
        }

        # Load existing state
        self.load_state()

    @property
    def repositories(self):
        """Alias for tracked_repos for API compatibility"""
        return self.tracked_repos

    @property
    def running(self):
        """Alias for is_running for API compatibility"""
        return self.is_running

    def start(self):
        """Start the backup service"""
        if self.is_running:
            logger.warning("Backup service is already running")
            return

        logger.info("Starting Code Backup Service...")

        # Validate configuration
        if not self.config.validate():
            logger.error("Configuration validation failed")
            return

        # Check GitHub authentication for all accounts
        if not self._verify_all_accounts():
            logger.error("GitHub authentication failed for one or more accounts")
            return

        self.is_running = True
        self.stats['start_time'] = datetime.now()

        # Initial scan of all watched paths
        self.initial_scan_all()

        # Start folder watchers for all paths
        self.start_all_folder_watchers()

        # Start backup loop
        self.start_backup_loop()

        logger.info("Code Backup Service started successfully")

    def stop(self):
        """Stop the backup service"""
        if not self.is_running:
            return

        logger.info("Stopping Code Backup Service...")

        self.is_running = False

        # Stop all folder watchers
        for watcher in self.folder_watchers:
            if watcher:
                watcher.stop()

        # Wait for backup thread to finish
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=10)

        # Save state
        self.save_state()

        logger.info("Code Backup Service stopped")

    def _verify_all_accounts(self) -> bool:
        """Verify GitHub authentication for all configured accounts"""
        all_authenticated = True

        for path_config in self.watched_paths:
            account_config = path_config.get('account', {})
            username = account_config.get('username')

            if not self.github_service.is_authenticated(account_config):
                logger.error(f"GitHub authentication failed for account: {username}")
                all_authenticated = False

        return all_authenticated

    def initial_scan_all(self):
        """Scan all watched paths and set up tracking"""
        logger.info("Performing initial scan of all watched paths...")

        if not self.watched_paths:
            logger.warning("No watched paths configured")
            return

        total_processed = 0

        for path_config in self.watched_paths:
            code_folder = Path(path_config['path']).expanduser()
            account_username = path_config.get('account', {}).get('username', 'unknown')

            logger.info(f"Scanning {code_folder} (account: {account_username})")

            if not code_folder.exists():
                logger.error(f"Code folder does not exist: {code_folder}")
                continue

            processed_count = 0

            for item in code_folder.iterdir():
                if item.is_dir() and not self._should_ignore_folder(item, path_config):
                    try:
                        if self.process_folder(item, path_config, is_initial_scan=True):
                            processed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing folder {item}: {e}")

            logger.info(f"Scanned {code_folder}: {processed_count} folders processed")
            total_processed += processed_count

        logger.info(f"Initial scan complete. Total processed: {total_processed} folders.")
        self.save_state()

    def initial_scan(self):
        """Deprecated: Use initial_scan_all() instead"""
        logger.warning("initial_scan() is deprecated. Use initial_scan_all() for multi-account support.")
        self.initial_scan_all()

    def process_folder(self, folder_path: Path, path_config: dict, is_initial_scan: bool = False) -> bool:
        """Process a folder (existing or new)"""
        folder_str = str(folder_path)
        folder_name = folder_path.name
        account_config = path_config.get('account', {})
        account_username = account_config.get('username', 'unknown')

        logger.debug(f"Processing folder: {folder_name} (account: {account_username})")

        # Skip if already tracked
        if folder_str in self.tracked_repos:
            logger.debug(f"Folder already tracked: {folder_name}")
            return True

        # Check if it's a git repository
        if self.git_service.is_git_repo(folder_path):
            return self._process_existing_git_repo(folder_path, path_config, is_initial_scan)
        else:
            return self._process_non_git_folder(folder_path, path_config, is_initial_scan)

    def _process_existing_git_repo(self, folder_path: Path, path_config: dict, is_initial_scan: bool) -> bool:
        """Process existing git repository"""
        folder_str = str(folder_path)
        folder_name = folder_path.name
        account_config = path_config.get('account', {})
        account_username = account_config.get('username', 'unknown')

        # Check if it has a remote
        if self.git_service.has_remote(folder_path):
            # Already has remote, just track it
            self.tracked_repos[folder_str] = {
                'name': folder_name,
                'path': folder_str,
                'created_at': datetime.now().isoformat(),
                'last_backup': None,
                'backup_count': 0,
                'status': 'tracked',
                'has_remote': True,
                'remote_url': self.git_service.get_remote_url(folder_path),
                'account_username': account_username
            }

            logger.info(f"Now tracking existing repository: {folder_name} (account: {account_username})")

            # Perform initial backup if needed
            if not is_initial_scan:
                self._backup_repository(folder_path)

            return True
        else:
            # Git repo without remote - create GitHub repo
            return self._add_remote_to_existing_repo(folder_path, path_config)

    def _process_non_git_folder(self, folder_path: Path, path_config: dict, is_initial_scan: bool) -> bool:
        """Process folder that is not a git repository"""
        # Check if it's a valid project
        if not self._is_valid_project(folder_path, path_config):
            logger.debug(f"Not a valid project: {folder_path.name}")
            return False

        return self._initialize_new_repository(folder_path, path_config)

    def _add_remote_to_existing_repo(self, folder_path: Path, path_config: dict) -> bool:
        """Add GitHub remote to existing git repository"""
        folder_name = folder_path.name
        account_config = path_config.get('account', {})
        account_username = account_config.get('username', 'unknown')

        logger.info(f"Adding GitHub remote to existing repository: {folder_name} (account: {account_username})")

        # Set git config for this repository (user.name and user.email)
        email = account_config.get('email', f"{account_username}@users.noreply.github.com")
        self.git_service.set_repo_git_config(folder_path, account_username, email)

        # Create GitHub repository
        description = self.github_service.generate_repo_description(folder_path)

        if self.github_service.create_repository(folder_name, folder_path, description, account_config):
            # Track the repository
            self.tracked_repos[str(folder_path)] = {
                'name': folder_name,
                'path': str(folder_path),
                'created_at': datetime.now().isoformat(),
                'last_backup': datetime.now().isoformat(),
                'backup_count': 1,
                'status': 'synced',
                'has_remote': True,
                'remote_url': self.git_service.get_remote_url(folder_path),
                'account_username': account_username
            }

            self.stats['repos_created'] += 1
            logger.info(f"Successfully added remote to repository: {folder_name}")
            return True
        else:
            logger.error(f"Failed to add remote to repository: {folder_name}")
            return False

    def _initialize_new_repository(self, folder_path: Path, path_config: dict) -> bool:
        """Initialize new git repository and create GitHub repo"""
        folder_name = folder_path.name
        account_config = path_config.get('account', {})
        account_username = account_config.get('username', 'unknown')

        logger.info(f"Initializing new repository: {folder_name} (account: {account_username})")

        # Get email for git config
        email = account_config.get('email', f"{account_username}@users.noreply.github.com")

        # Initialize git repository WITH user config before initial commit
        # This ensures the initial commit is attributed to the correct account
        if not self.git_service.init_repo(folder_path, account_username, email):
            logger.error(f"Failed to initialize git repository: {folder_name}")
            return False

        # Create GitHub repository
        description = self.github_service.generate_repo_description(folder_path)

        if self.github_service.create_repository(folder_name, folder_path, description, account_config):
            # Track the repository
            self.tracked_repos[str(folder_path)] = {
                'name': folder_name,
                'path': str(folder_path),
                'created_at': datetime.now().isoformat(),
                'last_backup': datetime.now().isoformat(),
                'backup_count': 1,
                'status': 'synced',
                'has_remote': True,
                'remote_url': self.git_service.get_remote_url(folder_path),
                'account_username': account_username
            }

            self.stats['repos_created'] += 1
            logger.info(f"Successfully initialized and created repository: {folder_name}")
            return True
        else:
            logger.error(f"Failed to create GitHub repository: {folder_name}")
            return False

    def start_all_folder_watchers(self):
        """Start monitoring all watched paths"""
        for path_config in self.watched_paths:
            try:
                code_folder = Path(path_config['path']).expanduser()
                account_username = path_config.get('account', {}).get('username', 'unknown')

                logger.info(f"Starting folder watcher for {code_folder} (account: {account_username})")

                # Create callback with path_config bound
                def make_callback(pc):
                    def callback(folder_path):
                        self.on_new_folder_detected(folder_path, pc)
                    return callback

                watcher = FolderWatcher(
                    self.config,
                    make_callback(path_config),
                    watched_path=code_folder
                )
                watcher.start()
                self.folder_watchers.append(watcher)

            except Exception as e:
                logger.error(f"Failed to start folder watcher for {code_folder}: {e}")

    def start_folder_watcher(self):
        """Deprecated: Use start_all_folder_watchers() instead"""
        logger.warning("start_folder_watcher() is deprecated. Use start_all_folder_watchers() for multi-account support.")
        self.start_all_folder_watchers()

    def on_new_folder_detected(self, folder_path: Path, path_config: dict):
        """Callback for when folder watcher detects a new folder"""
        account_username = path_config.get('account', {}).get('username', 'unknown')
        logger.info(f"New folder detected by watcher: {folder_path.name} (account: {account_username})")

        try:
            if self.process_folder(folder_path, path_config):
                self.save_state()
                self._send_notification(f"New repository created: {folder_path.name} (account: {account_username})")

                # Notify WebSocket clients of new project
                if self.websocket_handler:
                    self.websocket_handler.broadcast_project_detected(
                        folder_path.name, account_username
                    )
        except Exception as e:
            logger.error(f"Error processing new folder {folder_path}: {e}")

    def start_backup_loop(self):
        """Start the continuous backup loop"""
        def backup_loop():
            logger.info(f"Starting backup loop (interval: {self.backup_interval}s)")

            while self.is_running:
                try:
                    self.backup_all_repositories()
                    self.stats['last_backup_time'] = datetime.now()

                    # Sleep in chunks to allow for quick shutdown
                    sleep_time = self.backup_interval
                    while sleep_time > 0 and self.is_running:
                        chunk = min(10, sleep_time)  # Sleep in 10-second chunks
                        time.sleep(chunk)
                        sleep_time -= chunk

                except Exception as e:
                    logger.error(f"Error in backup loop: {e}")
                    time.sleep(60)  # Wait a minute before retrying

        self.backup_thread = threading.Thread(target=backup_loop, daemon=True)
        self.backup_thread.start()

    def backup_all_repositories(self):
        """Backup all tracked repositories"""
        if not self.tracked_repos:
            logger.debug("No repositories to backup")
            return

        logger.info(f"Starting backup of {len(self.tracked_repos)} repositories...")

        successful = 0
        failed = 0
        skipped = 0

        for repo_path, repo_info in self.tracked_repos.items():
            try:
                repo_name = repo_info.get('name', Path(repo_path).name)

                # SKIP DISABLED PROJECTS
                if not self.config.get_project_enabled(repo_name):
                    logger.debug(f"Skipping disabled project: {repo_name}")
                    skipped += 1
                    continue

                path = Path(repo_path)

                # Check if folder still exists
                if not path.exists():
                    logger.warning(f"Repository path no longer exists: {repo_path}")
                    repo_info['status'] = 'missing'
                    continue

                # Perform backup and get detailed result
                result = self._backup_repository(path)

                # Always update last_check timestamp (daemon checked this repo)
                repo_info['last_check'] = datetime.now().isoformat()

                # Handle result based on what actually happened
                if result['success'] and result['changes_pushed']:
                    # Changes were committed and pushed to GitHub
                    successful += 1
                    repo_info['last_backup'] = datetime.now().isoformat()
                    repo_info['backup_count'] = repo_info.get('backup_count', 0) + 1
                    repo_info['status'] = 'synced'
                elif result['success'] and not result['changes_pushed']:
                    # No changes to backup (success, but nothing to do)
                    skipped += 1
                    repo_info['status'] = 'no_changes'
                else:
                    # Backup failed
                    failed += 1
                    repo_info['status'] = 'failed'
                    repo_info['last_error'] = result['message']

            except Exception as e:
                logger.error(f"Error backing up {repo_path}: {e}")
                failed += 1
                if repo_path in self.tracked_repos:
                    self.tracked_repos[repo_path]['status'] = 'error'
                    self.tracked_repos[repo_path]['last_error'] = str(e)

        self.stats['successful_backups'] += successful
        self.stats['failed_backups'] += failed

        if successful > 0 or failed > 0 or skipped > 0:
            logger.info(f"Backup completed: {successful} successful, {failed} failed, {skipped} skipped")

            if failed > 0:
                self._send_notification(f"Backup completed with {failed} failures")

        # Save state periodically
        self.save_state()

    def _backup_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Backup a single repository (internal method)

        Returns:
            dict: {
                'success': bool,
                'changes_pushed': bool,
                'message': str
            }
        """
        try:
            repo_name = repo_path.name

            # Notify WebSocket clients that backup started
            if self.websocket_handler:
                self.websocket_handler.broadcast_backup_started(repo_name)

            # Check for changes
            if not self.git_service.has_uncommitted_changes(repo_path):
                logger.debug(f"No changes to backup in {repo_name}")
                # Notify success (no changes)
                if self.websocket_handler:
                    self.websocket_handler.broadcast_backup_completed(repo_name, True)
                return {
                    'success': True,
                    'changes_pushed': False,
                    'message': 'No changes to backup'
                }

            logger.info(f"Backing up {repo_name}...")

            # Sync repository (commit, pull, push)
            success = self.git_service.sync_repository(repo_path)

            # Notify WebSocket clients of completion
            if self.websocket_handler:
                if success:
                    self.websocket_handler.broadcast_backup_completed(repo_name, True)
                else:
                    self.websocket_handler.broadcast_backup_completed(
                        repo_name, False, "Sync failed"
                    )

            if success:
                logger.debug(f"Successfully backed up {repo_name}")
            else:
                logger.warning(f"Failed to backup {repo_name}")

            return {
                'success': success,
                'changes_pushed': success,
                'message': 'Pushed to GitHub' if success else 'Push failed'
            }

        except Exception as e:
            logger.error(f"Error backing up {repo_path}: {e}")
            # Notify WebSocket clients of error
            if self.websocket_handler:
                self.websocket_handler.broadcast_backup_completed(
                    repo_path.name, False, str(e)
                )
            return {
                'success': False,
                'changes_pushed': False,
                'message': str(e)
            }

    def backup_repository(self, repo_name: str) -> bool:
        """Public method to backup a specific repository by name"""
        try:
            # Find repository by name
            for repo_path, repo_info in self.tracked_repos.items():
                if repo_info.get('name') == repo_name or Path(repo_path).name == repo_name:
                    path = Path(repo_path)

                    if not path.exists():
                        logger.error(f"Repository path no longer exists: {repo_path}")
                        return False

                    logger.info(f"Manual backup triggered for {repo_name}")
                    result = self._backup_repository(path)

                    # Always update last_check
                    repo_info['last_check'] = datetime.now().isoformat()

                    # Update based on what actually happened
                    if result['success'] and result['changes_pushed']:
                        repo_info['last_backup'] = datetime.now().isoformat()
                        repo_info['backup_count'] = repo_info.get('backup_count', 0) + 1
                        repo_info['status'] = 'synced'
                        self.save_state()
                    elif result['success'] and not result['changes_pushed']:
                        repo_info['status'] = 'no_changes'
                        self.save_state()
                    else:
                        repo_info['status'] = 'failed'
                        repo_info['last_error'] = result['message']
                        self.save_state()

                    return result['success']

            logger.error(f"Repository not found: {repo_name}")
            return False

        except Exception as e:
            logger.error(f"Error in backup_repository for {repo_name}: {e}")
            return False

    def force_backup(self, repo_name: Optional[str] = None) -> bool:
        """Force backup of specific repository or all repositories"""
        if repo_name:
            # Backup specific repository
            for repo_path, repo_info in self.tracked_repos.items():
                if repo_info['name'] == repo_name:
                    path = Path(repo_path)
                    logger.info(f"Force backing up {repo_name}...")
                    return self._backup_repository(path)

            logger.error(f"Repository not found: {repo_name}")
            return False
        else:
            # Backup all repositories
            logger.info("Force backing up all repositories...")
            self.backup_all_repositories()
            return True

    def _is_valid_project(self, folder_path: Path, path_config: dict = None) -> bool:
        """Check if folder is a valid project (using folder watcher logic)"""
        # Always create a temporary watcher for validation (stateless check)
        watched_path = Path(path_config['path']).expanduser() if path_config else None
        temp_watcher = FolderWatcher(self.config, lambda x: None, watched_path=watched_path)
        return temp_watcher.is_valid_project(folder_path)

    def _should_ignore_folder(self, folder_path: Path, path_config: dict = None) -> bool:
        """Check if folder should be ignored"""
        # Always create a temporary watcher for validation (stateless check)
        watched_path = Path(path_config['path']).expanduser() if path_config else None
        temp_watcher = FolderWatcher(self.config, lambda x: None, watched_path=watched_path)
        return temp_watcher.should_ignore_folder(folder_path)

    def _send_notification(self, message: str):
        """Send notification (placeholder for future implementation)"""
        if self.config.get('notifications.enabled', True):
            logger.info(f"NOTIFICATION: {message}")
            # TODO: Implement desktop notifications, email, etc.

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        status = {
            'is_running': self.is_running,
            'stats': self.stats.copy(),
            'tracked_repos': len(self.tracked_repos),
            'config': {
                'watched_paths': [str(Path(pc['path']).expanduser()) for pc in self.watched_paths],
                'backup_interval': self.backup_interval
            }
        }

        # Add folder watchers status
        status['folder_watchers'] = []
        for watcher in self.folder_watchers:
            if watcher:
                status['folder_watchers'].append(watcher.get_status())

        # Add repository details
        status['repositories'] = []
        for repo_path, repo_info in self.tracked_repos.items():
            repo_status = repo_info.copy()
            try:
                path = Path(repo_path)
                if path.exists():
                    git_status = self.git_service.get_status(path)
                    repo_status['git_status'] = git_status
                else:
                    repo_status['exists'] = False
            except Exception as e:
                repo_status['error'] = str(e)

            status['repositories'].append(repo_status)

        return status

    def load_state(self):
        """Load service state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.tracked_repos = data.get('tracked_repos', {})
                    self.stats.update(data.get('stats', {}))

                # Migrate old repos: add account_username if missing
                self._migrate_repo_accounts()

                # Migrate corrupted timestamps from old code
                self._migrate_backup_timestamps()

                logger.info(f"Loaded state: {len(self.tracked_repos)} tracked repositories")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.tracked_repos = {}

    def _migrate_repo_accounts(self):
        """Migrate existing repos to include account_username based on path"""
        updated = False
        for repo_path, repo_info in self.tracked_repos.items():
            # Skip if already has account_username
            if 'account_username' in repo_info and repo_info['account_username'] != 'unknown':
                continue

            # Find matching watched path and extract account
            for path_config in self.config.get('watched_paths', []):
                watched_path = Path(path_config.get('path')).expanduser().resolve()
                repo_path_obj = Path(repo_path)

                # Check if repo is under this watched path
                try:
                    repo_path_obj.relative_to(watched_path)
                    # Found matching watched path
                    account_username = path_config.get('account', {}).get('username', 'unknown')
                    repo_info['account_username'] = account_username
                    logger.info(f"Migrated {repo_info.get('name')} to account: {account_username}")
                    updated = True
                    break
                except ValueError:
                    # Not under this watched path, continue
                    continue

        if updated:
            self.save_state()
            logger.info("Repository account migration completed")

    def _migrate_backup_timestamps(self):
        """Fix corrupted last_backup timestamps and counts from old code that counted no-change runs"""
        updated = False

        for repo_path, repo_info in self.tracked_repos.items():
            try:
                path = Path(repo_path)

                # Skip if repo doesn't exist
                if not path.exists():
                    continue

                # Get actual last commit time from git
                last_commit_info = self.git_service.get_last_commit_info(path)

                if last_commit_info:
                    actual_last_commit_time = last_commit_info['date']
                    actual_commit_count = self._get_commit_count(path)
                    stored_last_backup = repo_info.get('last_backup')
                    stored_backup_count = repo_info.get('backup_count', 0)

                    # Always check and fix backup_count if it doesn't match reality
                    if actual_commit_count is not None and stored_backup_count != actual_commit_count:
                        repo_info['backup_count'] = actual_commit_count
                        logger.info(f"Correcting backup count for {repo_info.get('name')}: {stored_backup_count} -> {actual_commit_count}")
                        updated = True

                    # Check timestamp corruption
                    if stored_last_backup:
                        try:
                            stored_time = datetime.fromisoformat(stored_last_backup)

                            # If stored time is NEWER than actual commit, it's corrupted
                            if stored_time > actual_last_commit_time:
                                logger.info(f"Fixing corrupted timestamp for {repo_info.get('name')}: {stored_time} -> {actual_last_commit_time}")
                                repo_info['last_backup'] = actual_last_commit_time.isoformat()
                                updated = True
                        except ValueError:
                            pass
                    else:
                        # No last_backup stored but we have commits, set it
                        repo_info['last_backup'] = actual_last_commit_time.isoformat()
                        updated = True
                        logger.info(f"Set initial last_backup for {repo_info.get('name')}: {actual_last_commit_time}")

            except Exception as e:
                logger.debug(f"Could not migrate timestamp for {repo_path}: {e}")
                continue

        if updated:
            self.save_state()
            logger.info("Backup timestamp migration completed")

    def _get_commit_count(self, path: Path) -> Optional[int]:
        """Get total number of commits in the repository"""
        try:
            from git import Repo
            repo = Repo(path)
            # Count commits on current branch
            commit_count = sum(1 for _ in repo.iter_commits())
            return commit_count
        except Exception as e:
            logger.debug(f"Could not get commit count for {path}: {e}")
            return None

    def save_state(self):
        """Save service state to file"""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert datetime objects to ISO format strings
            stats_copy = self.stats.copy()
            if stats_copy.get('start_time'):
                if isinstance(stats_copy['start_time'], datetime):
                    stats_copy['start_time'] = stats_copy['start_time'].isoformat()
            if stats_copy.get('last_backup_time'):
                if isinstance(stats_copy['last_backup_time'], datetime):
                    stats_copy['last_backup_time'] = stats_copy['last_backup_time'].isoformat()

            data = {
                'tracked_repos': self.tracked_repos,
                'stats': stats_copy,
                'last_saved': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def remove_repository(self, repo_name: str) -> bool:
        """Remove repository from tracking (does not delete files or GitHub repo)"""
        for repo_path, repo_info in list(self.tracked_repos.items()):
            if repo_info['name'] == repo_name:
                del self.tracked_repos[repo_path]
                self.save_state()
                logger.info(f"Removed repository from tracking: {repo_name}")
                return True

        logger.error(f"Repository not found: {repo_name}")
        return False

    def delete_repository_complete(self, repo_name: str, delete_github: bool = False, delete_local: bool = False) -> dict:
        """Complete repository deletion with options

        Args:
            repo_name: Name of the repository to delete
            delete_github: If True, delete the GitHub repository
            delete_local: If True, delete local files (DANGEROUS!)

        Returns:
            dict: Status of each deletion step
        """
        result = {
            'github_deleted': False,
            'local_deleted': False,
            'tracking_removed': False,
            'errors': []
        }

        # Find the repository
        repo_path = None
        repo_info = None
        for path, info in self.tracked_repos.items():
            if info.get('name') == repo_name:
                repo_path = path
                repo_info = info
                break

        if not repo_info:
            result['errors'].append(f"Repository not found: {repo_name}")
            return result

        account_username = repo_info.get('account_username', 'unknown')

        # Step 1: Delete from GitHub
        if delete_github:
            try:
                # Find account config
                account_config = None
                for path_config in self.watched_paths:
                    if path_config.get('account', {}).get('username') == account_username:
                        account_config = path_config.get('account', {})
                        break

                if account_config:
                    result['github_deleted'] = self.github_service.delete_repository(repo_name, account_config)
                    if not result['github_deleted']:
                        result['errors'].append(f"Failed to delete from GitHub: {repo_name}")
                else:
                    result['errors'].append(f"Account config not found for: {account_username}")
            except Exception as e:
                result['errors'].append(f"GitHub deletion error: {str(e)}")
                logger.error(f"Error deleting from GitHub: {e}")

        # Step 2: Delete local files
        if delete_local and repo_path:
            try:
                import shutil
                path = Path(repo_path)
                if path.exists():
                    shutil.rmtree(path)
                    result['local_deleted'] = True
                    logger.warning(f"DELETED LOCAL FILES: {repo_path}")
            except Exception as e:
                result['errors'].append(f"Local deletion error: {str(e)}")
                logger.error(f"Error deleting local files: {e}")

        # Step 3: Remove from tracking (always attempt this)
        try:
            result['tracking_removed'] = self.remove_repository(repo_name)
        except Exception as e:
            result['errors'].append(f"Tracking removal error: {str(e)}")
            logger.error(f"Error removing from tracking: {e}")

        return result

    def add_repository(self, folder_path: Path, account_username: Optional[str] = None) -> bool:
        """Manually add a repository to tracking with optional account selection"""
        if not folder_path.exists():
            logger.error(f"Folder does not exist: {folder_path}")
            return False

        # Find the appropriate path_config for this account
        path_config = None

        if account_username:
            # Find path_config for specified account
            for pc in self.watched_paths:
                if pc.get('account', {}).get('username') == account_username:
                    path_config = pc
                    break

            if not path_config:
                logger.error(f"Account not found: {account_username}")
                return False
        else:
            # Use first available path_config if no account specified
            if self.watched_paths:
                path_config = self.watched_paths[0]
            else:
                logger.error("No watched paths configured")
                return False

        logger.info(f"Adding repository {folder_path.name} to account {path_config.get('account', {}).get('username')}")
        return self.process_folder(folder_path, path_config, is_initial_scan=False)
