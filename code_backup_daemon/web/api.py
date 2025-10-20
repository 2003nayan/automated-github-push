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


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
