"""
GitHub service for Code Backup Daemon
"""
import subprocess
import logging
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class GitHubService:
    """Handles GitHub operations (multi-account support)"""

    def __init__(self, config):
        self.config = config
        self.api_base = "https://api.github.com"

        # Cache for tokens to avoid repeated environment lookups
        self._token_cache = {}

    def _get_account_config(self, account_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize account configuration with defaults"""
        return {
            'username': account_config.get('username', ''),
            'token_env_var': account_config.get('token_env_var', None),
            'default_visibility': account_config.get('default_visibility', 'private'),
            'create_org_repos': account_config.get('create_org_repos', False),
            'organization': account_config.get('organization', ''),
            'use_gh_cli': account_config.get('use_gh_cli', True)
        }

    def _get_github_token(self, account_config: Dict[str, Any]) -> Optional[str]:
        """Get GitHub token for specific account"""
        import os

        config = self._get_account_config(account_config)
        username = config['username']

        # Check cache first
        if username in self._token_cache:
            return self._token_cache[username]

        token = None

        # Option 1: Use environment variable (preferred for multi-account)
        token_env = config.get('token_env_var')
        if token_env:
            token = os.environ.get(token_env)
            if token:
                logger.debug(f"Using token from {token_env} for {username}")
                self._token_cache[username] = token
                return token

        # Option 2: Try gh CLI (works for single account)
        if config['use_gh_cli']:
            try:
                result = subprocess.run(
                    ['gh', 'auth', 'token'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                token = result.stdout.strip()
                logger.debug(f"Using token from gh CLI for {username}")
                self._token_cache[username] = token
                return token
            except Exception as e:
                logger.debug(f"Could not get token from gh CLI for {username}: {e}")

        # Option 3: Fallback to generic GITHUB_TOKEN
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            logger.debug(f"Using GITHUB_TOKEN for {username}")
            self._token_cache[username] = token
            return token

        logger.error(f"No GitHub token found for {username}")
        return None

    def is_authenticated(self, account_config: Dict[str, Any]) -> bool:
        """Check if we can authenticate with GitHub for specific account"""
        config = self._get_account_config(account_config)
        username = config['username']

        if config['use_gh_cli']:
            try:
                result = subprocess.run(
                    ['gh', 'auth', 'status'],
                    capture_output=True,
                    text=True
                )
                # TODO: Could parse output to verify correct account
                return result.returncode == 0
            except Exception:
                return False
        else:
            token = self._get_github_token(account_config)
            if token:
                logger.debug(f"Authentication available for {username}")
                return True
            else:
                logger.error(f"No authentication found for {username}")
                return False

    def repo_exists(self, repo_name: str, account_config: Dict[str, Any]) -> bool:
        """Check if repository exists on GitHub"""
        config = self._get_account_config(account_config)

        if config['use_gh_cli']:
            return self._repo_exists_cli(repo_name, config)
        else:
            return self._repo_exists_api(repo_name, config, account_config)

    def _repo_exists_cli(self, repo_name: str, config: Dict[str, Any]) -> bool:
        """Check if repo exists using gh CLI"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            result = subprocess.run(
                ['gh', 'repo', 'view', f"{owner}/{repo_name}"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _repo_exists_api(self, repo_name: str, config: Dict[str, Any], account_config: Dict[str, Any]) -> bool:
        """Check if repo exists using GitHub API"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            url = f"{self.api_base}/repos/{owner}/{repo_name}"

            token = self._get_github_token(account_config)
            if not token:
                logger.error(f"No token available to check repo existence for {owner}/{repo_name}")
                return False

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get(url, headers=headers, timeout=30)
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Error checking if repo exists: {e}")
            return False

    def create_repository(self, repo_name: str, repo_path: Path, description: str, account_config: Dict[str, Any]) -> bool:
        """Create a new GitHub repository"""
        config = self._get_account_config(account_config)
        username = config['username']

        if self.repo_exists(repo_name, account_config):
            logger.warning(f"Repository {repo_name} already exists for {username}")
            return True

        if config['use_gh_cli']:
            return self._create_repository_cli(repo_name, repo_path, description, config)
        else:
            return self._create_repository_api(repo_name, repo_path, description, config, account_config)

    def _create_repository_cli(self, repo_name: str, repo_path: Path, description: str, config: Dict[str, Any]) -> bool:
        """Create repository using gh CLI"""
        try:
            username = config['username']
            cmd = [
                'gh', 'repo', 'create', repo_name,
                f'--{config["default_visibility"]}',
                '--source=.',
                '--remote=origin',
                '--push'
            ]

            if description:
                cmd.extend(['--description', description])

            if config['create_org_repos'] and config['organization']:
                # For organization repos
                cmd[3] = f"{config['organization']}/{repo_name}"

            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"Created GitHub repository: {repo_name} for {username}")
                return True
            else:
                logger.error(f"Failed to create repository {repo_name} for {username}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout creating repository {repo_name}")
            return False
        except Exception as e:
            logger.error(f"Error creating repository {repo_name}: {e}")
            return False

    def _create_repository_api(self, repo_name: str, repo_path: Path, description: str, config: Dict[str, Any], account_config: Dict[str, Any]) -> bool:
        """Create repository using GitHub API"""
        try:
            username = config['username']

            if config['create_org_repos'] and config['organization']:
                url = f"{self.api_base}/orgs/{config['organization']}/repos"
            else:
                url = f"{self.api_base}/user/repos"

            token = self._get_github_token(account_config)
            if not token:
                logger.error(f"No token available to create repository for {username}")
                return False

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }

            data = {
                'name': repo_name,
                'description': description,
                'private': config['default_visibility'] == 'private',
                'auto_init': False  # We'll push our existing content
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 201:
                repo_data = response.json()
                clone_url = repo_data['clone_url']

                # Add remote to local repo
                from .git_service import GitService
                git_service = GitService(self.config)

                if git_service.add_remote(repo_path, clone_url):
                    # Push initial content
                    if git_service.push_changes(repo_path):
                        logger.info(f"Created and pushed to GitHub repository: {repo_name} for {username}")
                        return True

                logger.error(f"Created repo but failed to push: {repo_name}")
                return False
            else:
                logger.error(f"Failed to create repository {repo_name} for {username}: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"Network error creating repository {repo_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating repository {repo_name}: {e}")
            return False

    def get_repository_info(self, repo_name: str, account_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get repository information"""
        config = self._get_account_config(account_config)

        if config['use_gh_cli']:
            return self._get_repository_info_cli(repo_name, config)
        else:
            return self._get_repository_info_api(repo_name, config, account_config)

    def _get_repository_info_cli(self, repo_name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get repository info using gh CLI"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            result = subprocess.run(
                ['gh', 'repo', 'view', f"{owner}/{repo_name}", '--json',
                 'name,description,isPrivate,url,sshUrl,updatedAt,pushedAt'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return None

        except Exception as e:
            logger.debug(f"Error getting repository info: {e}")
            return None

    def _get_repository_info_api(self, repo_name: str, config: Dict[str, Any], account_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get repository info using GitHub API"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            url = f"{self.api_base}/repos/{owner}/{repo_name}"

            token = self._get_github_token(account_config)
            if not token:
                return None

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            logger.debug(f"Error getting repository info: {e}")
            return None

    def generate_repo_description(self, repo_path: Path) -> str:
        """Generate a description for the repository based on its contents"""
        try:
            # Look for README files
            readme_files = list(repo_path.glob("README*"))
            if readme_files:
                with open(readme_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Extract first line or first paragraph
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return line[:100] + ('...' if len(line) > 100 else '')
                        elif line.startswith('# '):
                            return line[2:].strip()

            # Look for package.json
            package_json = repo_path / 'package.json'
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        data = json.load(f)
                        if 'description' in data:
                            return data['description']
                except Exception:
                    pass

            # Look for setup.py or pyproject.toml
            setup_py = repo_path / 'setup.py'
            if setup_py.exists():
                try:
                    with open(setup_py, 'r') as f:
                        content = f.read()
                        # Simple regex to find description
                        import re
                        match = re.search(r'description=[\"\']([^\"\']+)[\"\']', content)
                        if match:
                            return match.group(1)
                except Exception:
                    pass

            # Default description based on folder name
            folder_name = repo_path.name
            return f"Auto-backed up project: {folder_name}"

        except Exception as e:
            logger.debug(f"Error generating description for {repo_path}: {e}")
            return f"Auto-backed up project: {repo_path.name}"

    def delete_repository(self, repo_name: str, account_config: Dict[str, Any]) -> bool:
        """Delete a GitHub repository (use with caution!)"""
        config = self._get_account_config(account_config)
        username = config['username']

        logger.warning(f"Attempting to delete repository: {repo_name} for {username}")

        if config['use_gh_cli']:
            return self._delete_repository_cli(repo_name, config)
        else:
            return self._delete_repository_api(repo_name, config, account_config)

    def _delete_repository_cli(self, repo_name: str, config: Dict[str, Any]) -> bool:
        """Delete repository using gh CLI"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            result = subprocess.run(
                ['gh', 'repo', 'delete', f"{owner}/{repo_name}", '--confirm'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.warning(f"Deleted GitHub repository: {repo_name} for {owner}")
                return True
            else:
                logger.error(f"Failed to delete repository {repo_name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error deleting repository {repo_name}: {e}")
            return False

    def _delete_repository_api(self, repo_name: str, config: Dict[str, Any], account_config: Dict[str, Any]) -> bool:
        """Delete repository using GitHub API"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            url = f"{self.api_base}/repos/{owner}/{repo_name}"

            token = self._get_github_token(account_config)
            if not token:
                logger.error(f"No token available to delete repository for {owner}")
                return False

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.delete(url, headers=headers, timeout=30)

            if response.status_code == 204:
                logger.warning(f"Deleted GitHub repository: {repo_name} for {owner}")
                return True
            else:
                logger.error(f"Failed to delete repository {repo_name}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error deleting repository {repo_name}: {e}")
            return False

    def list_repositories(self, account_config: Dict[str, Any]) -> list:
        """List all repositories for the user/organization"""
        config = self._get_account_config(account_config)

        if config['use_gh_cli']:
            return self._list_repositories_cli(config)
        else:
            return self._list_repositories_api(config, account_config)

    def _list_repositories_cli(self, config: Dict[str, Any]) -> list:
        """List repositories using gh CLI"""
        try:
            owner = config['organization'] if config['create_org_repos'] else config['username']
            result = subprocess.run(
                ['gh', 'repo', 'list', owner, '--json', 'name,description,isPrivate,url'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return []

        except Exception as e:
            logger.error(f"Error listing repositories for {owner}: {e}")
            return []

    def _list_repositories_api(self, config: Dict[str, Any], account_config: Dict[str, Any]) -> list:
        """List repositories using GitHub API"""
        try:
            if config['create_org_repos'] and config['organization']:
                url = f"{self.api_base}/orgs/{config['organization']}/repos"
            else:
                url = f"{self.api_base}/user/repos"

            token = self._get_github_token(account_config)
            if not token:
                logger.error(f"No token available to list repositories for {config['username']}")
                return []

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            repos = []
            page = 1
            per_page = 100

            while True:
                params = {'page': page, 'per_page': per_page}
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code != 200:
                    break

                page_repos = response.json()
                if not page_repos:
                    break

                repos.extend(page_repos)
                page += 1

                # Rate limiting
                time.sleep(0.1)

            return repos

        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            return []
