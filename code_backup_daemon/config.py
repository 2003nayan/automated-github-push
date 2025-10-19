"""
Configuration management for Code Backup Daemon
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the code backup daemon"""

    DEFAULT_CONFIG = {
        'daemon': {
            'backup_interval': 86400,  # 24 hours
            'log_level': 'INFO',
            'pid_file': '~/.local/share/code-backup/daemon.pid',
            'log_file': '~/.local/share/code-backup/daemon.log',
            'state_file': '~/.local/share/code-backup/state.json'
        },
        'paths': {
            'config_dir': '~/.config/code-backup',
            'data_dir': '~/.local/share/code-backup'
        },
        # NEW: Multi-account support - list of watched paths with account configs
        'watched_paths': [
            # Example structure (will be populated by setup wizard):
            # {
            #     'name': 'NK Projects',
            #     'path': '/home/user/Desktop/NK',
            #     'github': {
            #         'username': '2003nayan',
            #         'token_env_var': 'GITHUB_TOKEN_NK',  # Optional: env var for token
            #         'default_visibility': 'private',
            #         'create_org_repos': False,
            #         'organization': '',
            #         'use_gh_cli': False  # Use API with token for multi-account
            #     },
            #     'git': {
            #         'default_branch': 'main',
            #         'auto_commit_message': 'Auto-backup: {timestamp}',
            #         'pull_before_push': True,
            #         'handle_conflicts': 'skip'
            #     }
            # }
        ],
        'project_detection': {
            'min_size_bytes': 1024,  # Minimum 1KB
            'project_indicators': [
                'package.json', 'requirements.txt', 'Cargo.toml',
                'go.mod', 'pom.xml', 'Gemfile', 'composer.json',
                'setup.py', 'pyproject.toml', 'README.md', 'Makefile'
            ],
            'code_extensions': [
                '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp',
                '.c', '.h', '.go', '.rs', '.php', '.rb', '.swift',
                '.kt', '.cs', '.scala', '.clj', '.hs', '.elm'
            ],
            'ignore_patterns': [
                'node_modules', 'venv', '.venv', 'env', '__pycache__',
                '.cache', 'dist', 'build', 'target', '.git', '.svn',
                '.idea', '.vscode', 'tmp', 'temp', '.DS_Store'
            ]
        },
        'notifications': {
            'enabled': True,
            'on_error': True,
            'on_new_repo': True,
            'on_backup_complete': False
        },
        'ui': {
            'enabled': True,
            'host': '127.0.0.1',
            'port': 5000,
            'auto_open_browser': True,
            'theme': 'dark'
        },
        'project_preferences': {}  # Stores per-project settings (enabled/disabled)
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()
        self._ensure_directories()

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve configuration file path"""
        if config_path:
            return Path(config_path).expanduser()

        # Check standard locations
        locations = [
            Path.home() / '.config' / 'code-backup' / 'config.yaml',
            Path('/etc/code-backup/config.yaml'),
            Path.cwd() / 'config.yaml'
        ]

        for path in locations:
            if path.exists():
                return path

        # Return default location
        return locations[0]

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}

                # Check if old format and migrate
                if self._is_old_format(user_config):
                    logger.info("Detected old configuration format, migrating to new format...")
                    user_config = self._migrate_old_config(user_config)

                # Merge with defaults
                config = self._deep_merge(self.DEFAULT_CONFIG.copy(), user_config)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config

            except Exception as e:
                logger.error(f"Error loading config from {self.config_path}: {e}")
                logger.info("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info("No config file found, creating default configuration")
            self._create_default_config()
            return self.DEFAULT_CONFIG.copy()

    def _create_default_config(self):
        """Create default configuration file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)

        logger.info(f"Created default config at {self.config_path}")

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _ensure_directories(self):
        """Ensure required directories exist"""
        dirs_to_create = [
            self.get_path('paths.data_dir'),
            self.get_path('paths.config_dir'),
            Path(self.get_path('daemon.log_file')).parent,
            Path(self.get_path('daemon.pid_file')).parent
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_path(self, key: str) -> Path:
        """Get path configuration value, expanded and resolved"""
        path_str = self.get(key)
        if path_str is None:
            raise ValueError(f"Path configuration '{key}' not found")

        return Path(path_str).expanduser().resolve()

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def validate(self) -> bool:
        """Validate configuration"""
        watched_paths = self.get('watched_paths', [])

        if not watched_paths:
            logger.error("No watched paths configured. Run 'code-backup setup' to configure.")
            return False

        # Validate each watched path
        for idx, path_config in enumerate(watched_paths):
            path_name = path_config.get('name', f'Path #{idx + 1}')

            # Check required fields
            if 'path' not in path_config:
                logger.error(f"{path_name}: Missing 'path' field")
                return False

            if 'account' not in path_config:
                logger.error(f"{path_name}: Missing 'account' configuration")
                return False

            if 'username' not in path_config['account']:
                logger.error(f"{path_name}: Missing 'account.username' field")
                return False

            # Validate path exists
            try:
                folder_path = Path(path_config['path']).expanduser().resolve()
                if not folder_path.exists():
                    logger.error(f"{path_name}: Path does not exist: {folder_path}")
                    return False
                if not folder_path.is_dir():
                    logger.error(f"{path_name}: Path is not a directory: {folder_path}")
                    return False
            except Exception as e:
                logger.error(f"{path_name}: Invalid path: {e}")
                return False

        return True

    def get_all_watched_paths(self) -> list:
        """Get all watched path configurations"""
        return self.get('watched_paths', [])

    def get_path_config(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific repository path"""
        repo_path_str = str(repo_path.resolve())

        for path_config in self.get('watched_paths', []):
            watched_path = Path(path_config['path']).expanduser().resolve()
            watched_path_str = str(watched_path)

            # Check if repo is under this watched path
            if repo_path_str.startswith(watched_path_str):
                return path_config

        return None

    def get_github_config_for_path(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Get GitHub configuration for a specific repository path"""
        path_config = self.get_path_config(repo_path)
        if path_config:
            return path_config.get('github')
        return None

    def get_git_config_for_path(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Get Git configuration for a specific repository path"""
        path_config = self.get_path_config(repo_path)
        if path_config:
            return path_config.get('git', {
                'default_branch': 'main',
                'auto_commit_message': 'Auto-backup: {timestamp}',
                'pull_before_push': True,
                'handle_conflicts': 'skip'
            })
        return None

    def _is_old_format(self, config: Dict[str, Any]) -> bool:
        """Check if configuration is in old single-account format"""
        # Old format has 'paths.code_folder' and 'github.username' at root level
        return ('paths' in config and 'code_folder' in config['paths']) or \
               ('github' in config and 'username' in config.get('github', {}))

    def _migrate_old_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old single-account config to new multi-account format"""
        logger.info("Migrating configuration from old format to new format")

        # Extract old values
        code_folder = old_config.get('paths', {}).get('code_folder', '')
        github_config = old_config.get('github', {})
        git_config = old_config.get('git', {})

        # Create new watched_paths entry
        watched_path_entry = {
            'name': 'Default Projects',
            'path': code_folder,
            'github': {
                'username': github_config.get('username', ''),
                'token_env_var': None,
                'default_visibility': github_config.get('default_visibility', 'private'),
                'create_org_repos': github_config.get('create_org_repos', False),
                'organization': github_config.get('organization', ''),
                'use_gh_cli': github_config.get('use_gh_cli', True)
            },
            'git': {
                'default_branch': git_config.get('default_branch', 'main'),
                'auto_commit_message': git_config.get('auto_commit_message', 'Auto-backup: {timestamp}'),
                'pull_before_push': git_config.get('pull_before_push', True),
                'handle_conflicts': git_config.get('handle_conflicts', 'skip')
            }
        }

        # Create new config structure
        new_config = old_config.copy()

        # Remove old structure
        if 'paths' in new_config and 'code_folder' in new_config['paths']:
            del new_config['paths']['code_folder']
        if 'github' in new_config:
            del new_config['github']
        if 'git' in new_config:
            del new_config['git']

        # Add new structure
        new_config['watched_paths'] = [watched_path_entry]

        # Save migrated config
        try:
            backup_path = self.config_path.parent / f"{self.config_path.name}.old"
            import shutil
            shutil.copy(self.config_path, backup_path)
            logger.info(f"Backed up old config to: {backup_path}")

            with open(self.config_path, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False, indent=2)
            logger.info("Saved migrated configuration")
        except Exception as e:
            logger.error(f"Could not save migrated config: {e}")

        return new_config

    def get_project_enabled(self, repo_name: str) -> bool:
        """Check if project sync is enabled (default: True)"""
        return self.config.get('project_preferences', {}).get(repo_name, {}).get('enabled', True)

    def set_project_enabled(self, repo_name: str, enabled: bool):
        """Enable/disable project sync"""
        if 'project_preferences' not in self.config:
            self.config['project_preferences'] = {}
        if repo_name not in self.config['project_preferences']:
            self.config['project_preferences'][repo_name] = {}
        self.config['project_preferences'][repo_name]['enabled'] = enabled
        self.save()
        logger.info(f"Project '{repo_name}' sync {'enabled' if enabled else 'disabled'}")

    def __str__(self) -> str:
        """String representation of config"""
        return yaml.dump(self.config, default_flow_style=False, indent=2)
