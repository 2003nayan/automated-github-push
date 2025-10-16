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
            'code_folder': '/home/nayan-ai4m/Desktop/NK',
            'config_dir': '~/.config/code-backup',
            'data_dir': '~/.local/share/code-backup'
        },
        'github': {
            'username': '',
            'default_visibility': 'private',  # private or public
            'create_org_repos': False,
            'organization': '',
            'use_gh_cli': True  # Use gh CLI vs PyGithub
        },
        'git': {
            'default_branch': 'main',
            'auto_commit_message': 'Auto-backup: {timestamp}',
            'pull_before_push': True,
            'handle_conflicts': 'skip'  # skip, notify, or force
        },
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
        }
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
        required_fields = [
            'paths.code_folder',
            'github.username'
        ]

        for field in required_fields:
            if not self.get(field):
                logger.error(f"Required configuration field missing: {field}")
                return False

        # Validate paths exist
        try:
            code_folder = self.get_path('paths.code_folder')
            if not code_folder.exists():
                logger.error(f"Code folder does not exist: {code_folder}")
                return False
        except Exception as e:
            logger.error(f"Invalid code folder path: {e}")
            return False

        return True

    def __str__(self) -> str:
        """String representation of config"""
        return yaml.dump(self.config, default_flow_style=False, indent=2)
