"""
REST API endpoints for Code Backup Daemon UI
"""
from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime
from pathlib import Path

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all tracked projects with their status"""
    try:
        service = current_app.backup_service
        config = service.config

        projects = []
        for repo_path, repo_info in service.repositories.items():
            repo_name = repo_info.get('name', Path(repo_path).name)
            account = repo_info.get('account_username', 'unknown')
            enabled = config.get_project_enabled(repo_name)

            # Convert SSH URL to HTTPS for display
            remote_url = repo_info.get('remote_url', '')
            github_url = ''
            if remote_url:
                # Convert git@github.com-personal:user/repo.git -> https://github.com/user/repo
                if remote_url.startswith('git@'):
                    parts = remote_url.split(':')
                    if len(parts) == 2:
                        repo_path = parts[1].replace('.git', '')
                        github_url = f'https://github.com/{repo_path}'
                elif remote_url.startswith('https://'):
                    github_url = remote_url.replace('.git', '')

            projects.append({
                'id': repo_name,
                'name': repo_name,
                'path': repo_info.get('path', repo_path),
                'account': account,
                'enabled': enabled,
                'last_backup': repo_info.get('last_backup'),
                'backup_count': repo_info.get('backup_count', 0),
                'github_url': github_url,
                'status': repo_info.get('status', 'active'),
                'error_count': repo_info.get('error_count', 0),
                'last_error': repo_info.get('last_error')
            })

        return jsonify({'projects': projects})

    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/projects/<project_id>/toggle', methods=['POST'])
def toggle_project(project_id):
    """Enable/disable project sync"""
    try:
        data = request.json
        enabled = data.get('enabled', True)

        service = current_app.backup_service
        service.config.set_project_enabled(project_id, enabled)

        logger.info(f"Project '{project_id}' sync {'enabled' if enabled else 'disabled'}")

        return jsonify({
            'success': True,
            'project_id': project_id,
            'enabled': enabled
        })

    except Exception as e:
        logger.error(f"Error toggling project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/projects/<project_id>/backup', methods=['POST'])
def backup_project(project_id):
    """Trigger manual backup for specific project"""
    try:
        service = current_app.backup_service

        # Check if project is enabled
        if not service.config.get_project_enabled(project_id):
            return jsonify({
                'success': False,
                'error': 'Project sync is disabled'
            }), 400

        # Trigger backup (backup_repository will check if project exists)
        success = service.backup_repository(project_id)

        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully backed up {project_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Project not found or backup failed - check logs for details'
            }), 404

    except Exception as e:
        logger.error(f"Error backing up {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get daemon status and statistics"""
    try:
        service = current_app.backup_service

        enabled_projects = sum(
            1 for repo_info in service.repositories.values()
            if service.config.get_project_enabled(repo_info.get('name'))
        )

        return jsonify({
            'daemon_running': service.running,
            'total_projects': len(service.repositories),
            'enabled_projects': enabled_projects,
            'disabled_projects': len(service.repositories) - enabled_projects,
            'total_backups': service.stats.get('successful_backups', 0),
            'failed_backups': service.stats.get('failed_backups', 0),
            'last_backup_time': service.stats.get('last_backup_time'),
            'uptime': service.stats.get('uptime', 0)
        })

    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/projects/add', methods=['POST'])
def add_project():
    """Manually add a new project/folder to tracking"""
    try:
        data = request.json
        folder_path = data.get('folder_path')
        account_username = data.get('account_username')

        if not folder_path:
            return jsonify({
                'success': False,
                'error': 'folder_path is required'
            }), 400

        if not account_username:
            return jsonify({
                'success': False,
                'error': 'account_username is required'
            }), 400

        service = current_app.backup_service
        from pathlib import Path
        path = Path(folder_path).expanduser()

        # Validate path exists
        if not path.exists():
            return jsonify({
                'success': False,
                'error': f'Folder does not exist: {folder_path}'
            }), 404

        # Validate it's a directory
        if not path.is_dir():
            return jsonify({
                'success': False,
                'error': f'Path is not a directory: {folder_path}'
            }), 400

        # Add repository
        success = service.add_repository(path, account_username)

        if success:
            service.save_state()

            # Notify WebSocket clients
            if service.websocket_handler:
                service.websocket_handler.broadcast_project_detected(
                    path.name, account_username
                )

            return jsonify({
                'success': True,
                'message': f'Successfully added {path.name} to {account_username}',
                'project_name': path.name
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add project - check logs for details'
            }), 500

    except Exception as e:
        logger.error(f"Error adding project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get list of configured accounts"""
    try:
        service = current_app.backup_service
        config = service.config

        accounts = []
        for path_config in config.get('watched_paths', []):
            account_info = path_config.get('account', {})
            username = account_info.get('username')

            # Count projects for this account
            project_count = sum(
                1 for repo in service.repositories.values()
                if repo.get('account_username') == username
            )

            accounts.append({
                'username': username,
                'name': path_config.get('name'),
                'path': path_config.get('path'),
                'project_count': project_count
            })

        return jsonify({'accounts': accounts})

    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get UI-relevant configuration"""
    try:
        service = current_app.backup_service
        config = service.config

        return jsonify({
            'backup_interval': config.get('daemon.backup_interval', 21600),
            'theme': config.get('ui.theme', 'dark'),
            'watched_paths': [
                {
                    'name': p.get('name'),
                    'path': p.get('path'),
                    'account': p.get('account', {}).get('username')
                }
                for p in config.get('watched_paths', [])
            ]
        })

    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/projects/<project_id>/delete', methods=['DELETE'])
def delete_project(project_id):
    """Delete project from tracking and optionally from GitHub"""
    try:
        data = request.json or {}
        delete_github = data.get('delete_github', False)
        delete_local = data.get('delete_local', False)

        service = current_app.backup_service

        # Find the project
        project_info = None
        project_path = None
        for repo_path, repo_info in service.repositories.items():
            if repo_info.get('name') == project_id or Path(repo_path).name == project_id:
                project_info = repo_info
                project_path = repo_path
                break

        if not project_info:
            return jsonify({
                'success': False,
                'error': f'Project not found: {project_id}'
            }), 404

        account_username = project_info.get('account_username', 'unknown')

        # Step 1: Delete from GitHub if requested
        github_deleted = False
        if delete_github:
            # Find account config
            account_config = None
            for path_config in service.config.get('watched_paths', []):
                if path_config.get('account', {}).get('username') == account_username:
                    account_config = path_config.get('account', {})
                    break

            if account_config:
                github_deleted = service.github_service.delete_repository(project_id, account_config)
                if not github_deleted:
                    logger.warning(f"Failed to delete {project_id} from GitHub")
            else:
                logger.error(f"Could not find account config for {account_username}")

        # Step 2: Delete local files if requested (DANGEROUS!)
        local_deleted = False
        if delete_local and project_path:
            try:
                import shutil
                path = Path(project_path)
                if path.exists():
                    shutil.rmtree(path)
                    local_deleted = True
                    logger.warning(f"DELETED LOCAL FILES: {project_path}")
            except Exception as e:
                logger.error(f"Failed to delete local files for {project_id}: {e}")

        # Step 3: Remove from tracking (always do this)
        tracking_removed = service.remove_repository(project_id)

        return jsonify({
            'success': True,
            'message': f'Project {project_id} deleted successfully',
            'details': {
                'github_deleted': github_deleted,
                'local_deleted': local_deleted,
                'tracking_removed': tracking_removed
            }
        })

    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/browse-folders', methods=['GET'])
def browse_folders():
    """Browse filesystem folders for folder selection"""
    try:
        # Get the path to browse from query parameter, default to user's home
        path_param = request.args.get('path', str(Path.home()))
        current_path = Path(path_param).expanduser().resolve()

        # Security check - don't allow browsing system directories
        forbidden_paths = ['/etc', '/sys', '/proc', '/dev', '/boot', '/root']
        if any(str(current_path).startswith(fp) for fp in forbidden_paths):
            return jsonify({
                'error': 'Access to system directories is not allowed'
            }), 403

        # Validate path exists and is a directory
        if not current_path.exists():
            return jsonify({
                'error': f'Path does not exist: {path_param}'
            }), 404

        if not current_path.is_dir():
            return jsonify({
                'error': f'Path is not a directory: {path_param}'
            }), 400

        # Get parent directory (for "up" navigation)
        parent = str(current_path.parent) if current_path.parent != current_path else None

        # List subdirectories
        folders = []
        try:
            for item in sorted(current_path.iterdir()):
                # Skip hidden files/folders and common ignore patterns
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    try:
                        # Check if we can access the folder
                        list(item.iterdir())
                        folders.append({
                            'name': item.name,
                            'path': str(item),
                            'is_accessible': True
                        })
                    except PermissionError:
                        folders.append({
                            'name': item.name,
                            'path': str(item),
                            'is_accessible': False
                        })
        except PermissionError:
            return jsonify({
                'error': 'Permission denied to access this directory'
            }), 403

        return jsonify({
            'current_path': str(current_path),
            'parent_path': parent,
            'folders': folders
        })

    except Exception as e:
        logger.error(f"Error browsing folders: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/settings/backup-schedule', methods=['GET'])
def get_backup_schedule():
    """Get backup schedule settings"""
    try:
        service = current_app.backup_service
        config = service.config

        # Get backup interval in seconds
        interval_seconds = config.get('daemon.backup_interval', 21600)

        # Calculate next backup time
        last_backup_time = service.stats.get('last_backup_time')
        next_backup_time = None

        if last_backup_time:
            try:
                if isinstance(last_backup_time, str):
                    last_backup_dt = datetime.fromisoformat(last_backup_time)
                else:
                    last_backup_dt = last_backup_time

                from datetime import timedelta
                next_backup_dt = last_backup_dt + timedelta(seconds=interval_seconds)
                next_backup_time = next_backup_dt.isoformat()
            except Exception as e:
                logger.error(f"Error calculating next backup time: {e}")

        return jsonify({
            'interval_seconds': interval_seconds,
            'interval_hours': interval_seconds / 3600,
            'last_backup_time': last_backup_time,
            'next_backup_time': next_backup_time,
            'auto_backup_enabled': service.running
        })

    except Exception as e:
        logger.error(f"Error fetching backup schedule: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/settings/backup-schedule', methods=['POST'])
def update_backup_schedule():
    """Update backup schedule settings"""
    try:
        data = request.json
        interval_hours = data.get('interval_hours')

        if interval_hours is None:
            return jsonify({
                'success': False,
                'error': 'interval_hours is required'
            }), 400

        # Validate interval (minimum 1 hour, maximum 7 days)
        if interval_hours < 1 or interval_hours > 168:
            return jsonify({
                'success': False,
                'error': 'Interval must be between 1 and 168 hours (7 days)'
            }), 400

        service = current_app.backup_service
        config = service.config

        # Update config
        interval_seconds = int(interval_hours * 3600)
        config.set('daemon.backup_interval', interval_seconds)

        # Save config to file
        config.save()

        logger.info(f"Backup interval updated to {interval_hours} hours ({interval_seconds} seconds)")

        return jsonify({
            'success': True,
            'message': f'Backup interval updated to {interval_hours} hours',
            'interval_seconds': interval_seconds,
            'interval_hours': interval_hours
        })

    except Exception as e:
        logger.error(f"Error updating backup schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
