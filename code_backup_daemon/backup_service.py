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
        self.folder_watcher: Optional[FolderWatcher] = None

        # Configuration
        self.backup_interval = config.get('daemon.backup_interval', 86400)  # 24 hours
        self.code_folder = config.get_path('paths.code_folder')

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

        # Check GitHub authentication
        if not self.github_service.is_authenticated():
            logger.error("GitHub authentication failed. Please run 'gh auth login' or set GITHUB_TOKEN")
            return

        self.is_running = True
        self.stats['start_time'] = datetime.now()

        # Initial scan of existing folders
        self.initial_scan()

        # Start folder watcher
        self.start_folder_watcher()

        # Start backup loop
        self.start_backup_loop()

        logger.info("Code Backup Service started successfully")

    def stop(self):
        """Stop the backup service"""
        if not self.is_running:
            return

        logger.info("Stopping Code Backup Service...")

        self.is_running = False

        # Stop folder watcher
        if self.folder_watcher:
            self.folder_watcher.stop()

        # Wait for backup thread to finish
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=10)

        # Save state
        self.save_state()

        logger.info("Code Backup Service stopped")

    def initial_scan(self):
        """Scan existing folders and set up tracking"""
        logger.info("Performing initial scan of code folder...")

        if not self.code_folder.exists():
            logger.error(f"Code folder does not exist: {self.code_folder}")
            return

        processed_count = 0

        for item in self.code_folder.iterdir():
            if item.is_dir() and not self._should_ignore_folder(item):
                try:
                    if self.process_folder(item, is_initial_scan=True):
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing folder {item}: {e}")

        logger.info(f"Initial scan complete. Processed {processed_count} folders.")
        self.save_state()

    def process_folder(self, folder_path: Path, is_initial_scan: bool = False) -> bool:
        """Process a folder (existing or new)"""
        folder_str = str(folder_path)
        folder_name = folder_path.name

        logger.debug(f"Processing folder: {folder_name}")

        # Skip if already tracked
        if folder_str in self.tracked_repos:
            logger.debug(f"Folder already tracked: {folder_name}")
            return True

        # Check if it's a git repository
        if self.git_service.is_git_repo(folder_path):
            return self._process_existing_git_repo(folder_path, is_initial_scan)
        else:
            return self._process_non_git_folder(folder_path, is_initial_scan)

    def _process_existing_git_repo(self, folder_path: Path, is_initial_scan: bool) -> bool:
        """Process existing git repository"""
        folder_str = str(folder_path)
        folder_name = folder_path.name

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
                'remote_url': self.git_service.get_remote_url(folder_path)
            }

            logger.info(f"Now tracking existing repository: {folder_name}")

            # Perform initial backup if needed
            if not is_initial_scan:
                self._backup_repository(folder_path)

            return True
        else:
            # Git repo without remote - create GitHub repo
            return self._add_remote_to_existing_repo(folder_path)

    def _process_non_git_folder(self, folder_path: Path, is_initial_scan: bool) -> bool:
        """Process folder that is not a git repository"""
        # Check if it's a valid project
        if not self._is_valid_project(folder_path):
            logger.debug(f"Not a valid project: {folder_path.name}")
            return False

        return self._initialize_new_repository(folder_path)

    def _add_remote_to_existing_repo(self, folder_path: Path) -> bool:
        """Add GitHub remote to existing git repository"""
        folder_name = folder_path.name

        logger.info(f"Adding GitHub remote to existing repository: {folder_name}")

        # Create GitHub repository
        description = self.github_service.generate_repo_description(folder_path)

        if self.github_service.create_repository(folder_name, folder_path, description):
            # Track the repository
            self.tracked_repos[str(folder_path)] = {
                'name': folder_name,
                'path': str(folder_path),
                'created_at': datetime.now().isoformat(),
                'last_backup': datetime.now().isoformat(),
                'backup_count': 1,
                'status': 'synced',
                'has_remote': True,
                'remote_url': self.git_service.get_remote_url(folder_path)
            }

            self.stats['repos_created'] += 1
            logger.info(f"Successfully added remote to repository: {folder_name}")
            return True
        else:
            logger.error(f"Failed to add remote to repository: {folder_name}")
            return False

    def _initialize_new_repository(self, folder_path: Path) -> bool:
        """Initialize new git repository and create GitHub repo"""
        folder_name = folder_path.name

        logger.info(f"Initializing new repository: {folder_name}")

        # Initialize git repository
        if not self.git_service.init_repo(folder_path):
            logger.error(f"Failed to initialize git repository: {folder_name}")
            return False

        # Create GitHub repository
        description = self.github_service.generate_repo_description(folder_path)

        if self.github_service.create_repository(folder_name, folder_path, description):
            # Track the repository
            self.tracked_repos[str(folder_path)] = {
                'name': folder_name,
                'path': str(folder_path),
                'created_at': datetime.now().isoformat(),
                'last_backup': datetime.now().isoformat(),
                'backup_count': 1,
                'status': 'synced',
                'has_remote': True,
                'remote_url': self.git_service.get_remote_url(folder_path)
            }

            self.stats['repos_created'] += 1
            logger.info(f"Successfully initialized and created repository: {folder_name}")
            return True
        else:
            logger.error(f"Failed to create GitHub repository: {folder_name}")
            return False

    def start_folder_watcher(self):
        """Start monitoring for new folders"""
        try:
            self.folder_watcher = FolderWatcher(
                self.config,
                self.on_new_folder_detected
            )
            self.folder_watcher.start()
        except Exception as e:
            logger.error(f"Failed to start folder watcher: {e}")

    def on_new_folder_detected(self, folder_path: Path):
        """Callback for when folder watcher detects a new folder"""
        logger.info(f"New folder detected by watcher: {folder_path.name}")

        try:
            if self.process_folder(folder_path):
                self.save_state()
                self._send_notification(f"New repository created: {folder_path.name}")
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

        for repo_path, repo_info in self.tracked_repos.items():
            try:
                path = Path(repo_path)

                # Check if folder still exists
                if not path.exists():
                    logger.warning(f"Repository path no longer exists: {repo_path}")
                    repo_info['status'] = 'missing'
                    continue

                if self._backup_repository(path):
                    successful += 1
                    repo_info['last_backup'] = datetime.now().isoformat()
                    repo_info['backup_count'] = repo_info.get('backup_count', 0) + 1
                    repo_info['status'] = 'synced'
                else:
                    failed += 1
                    repo_info['status'] = 'failed'

            except Exception as e:
                logger.error(f"Error backing up {repo_path}: {e}")
                failed += 1
                if repo_path in self.tracked_repos:
                    self.tracked_repos[repo_path]['status'] = 'error'

        self.stats['successful_backups'] += successful
        self.stats['failed_backups'] += failed

        if successful > 0 or failed > 0:
            logger.info(f"Backup completed: {successful} successful, {failed} failed")

            if failed > 0:
                self._send_notification(f"Backup completed with {failed} failures")

        # Save state periodically
        self.save_state()

    def _backup_repository(self, repo_path: Path) -> bool:
        """Backup a single repository"""
        try:
            # Check for changes
            if not self.git_service.has_uncommitted_changes(repo_path):
                logger.debug(f"No changes to backup in {repo_path.name}")
                return True

            logger.info(f"Backing up {repo_path.name}...")

            # Sync repository (commit, pull, push)
            if self.git_service.sync_repository(repo_path):
                logger.debug(f"Successfully backed up {repo_path.name}")
                return True
            else:
                logger.warning(f"Failed to backup {repo_path.name}")
                return False

        except Exception as e:
            logger.error(f"Error backing up {repo_path}: {e}")
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

    def _is_valid_project(self, folder_path: Path) -> bool:
        """Check if folder is a valid project (using folder watcher logic)"""
        if not self.folder_watcher:
            # Create a temporary watcher for validation
            temp_watcher = FolderWatcher(self.config, lambda x: None)
            return temp_watcher.is_valid_project(folder_path)
        else:
            return self.folder_watcher.is_valid_project(folder_path)

    def _should_ignore_folder(self, folder_path: Path) -> bool:
        """Check if folder should be ignored"""
        if not self.folder_watcher:
            # Create a temporary watcher for validation
            temp_watcher = FolderWatcher(self.config, lambda x: None)
            return temp_watcher.should_ignore_folder(folder_path)
        else:
            return self.folder_watcher.should_ignore_folder(folder_path)

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
                'code_folder': str(self.code_folder),
                'backup_interval': self.backup_interval,
                'github_username': self.config.get('github.username')
            }
        }

        # Add folder watcher status
        if self.folder_watcher:
            status['folder_watcher'] = self.folder_watcher.get_status()

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

                logger.info(f"Loaded state: {len(self.tracked_repos)} tracked repositories")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.tracked_repos = {}

    def save_state(self):
        """Save service state to file"""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert datetime objects to ISO format strings
            stats_copy = self.stats.copy()
            if stats_copy.get('start_time'):
                stats_copy['start_time'] = stats_copy['start_time'].isoformat()
            if stats_copy.get('last_backup_time'):
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

    def add_repository(self, folder_path: Path) -> bool:
        """Manually add a repository to tracking"""
        if not folder_path.exists():
            logger.error(f"Folder does not exist: {folder_path}")
            return False

        return self.process_folder(folder_path)
