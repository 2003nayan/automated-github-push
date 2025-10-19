"""
Command Line Interface for Code Backup Daemon
"""
import click
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
import subprocess

from .config import Config
from .backup_service import BackupService


def setup_logging(log_level):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def start_web_ui(service, config):
    """Start web UI in a separate thread

    Args:
        service: BackupService instance
        config: Config instance

    Returns:
        Thread object running the web server
    """
    import threading

    try:
        from .web.server import create_app
        from .web.websocket import WebSocketHandler

        click.echo("🌐 Starting Web UI...")

        app, socketio = create_app(service)
        service.websocket_handler = WebSocketHandler(socketio)

        host = config.get('ui.host', '127.0.0.1')
        port = config.get('ui.port', 5000)

        def run_web_server():
            # Use eventlet for production-ready async support
            socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True, log_output=False)

        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()

        click.echo(f"✅ Web UI started at http://{host}:{port}")

        # Open browser if configured
        if config.get('ui.auto_open_browser', False):
            try:
                import webbrowser
                webbrowser.open(f"http://{host}:{port}")
                click.echo(f"🌐 Opened browser at http://{host}:{port}")
            except Exception as e:
                click.echo(f"⚠️  Could not auto-open browser: {e}")

        return web_thread

    except Exception as e:
        click.echo(f"⚠️  Failed to start web UI: {e}")
        click.echo("   Daemon will continue running without UI")
        return None


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.pass_context
def cli(ctx, config, log_level):
    """Code Backup Daemon - Automatically backup your code to GitHub"""
    ctx.ensure_object(dict)

    # Setup logging
    setup_logging(log_level)

    # Load configuration
    try:
        ctx.obj['config'] = Config(config)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--no-ui', is_flag=True, help='Start without web UI')
@click.pass_context
def start(ctx, no_ui):
    """Start the backup daemon"""
    config = ctx.obj['config']

    click.echo("🚀 Starting Code Backup Daemon...")

    # Check if already running
    pid_file = config.get_path('daemon.pid_file')
    if is_daemon_running(pid_file):
        click.echo("❌ Daemon is already running", err=True)
        sys.exit(1)

    # Start the service
    service = BackupService(config)

    # Start web UI if enabled
    web_thread = None
    if not no_ui and config.get('ui.enabled', True):
        web_thread = start_web_ui(service, config)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        click.echo("\n🛑 Received shutdown signal, stopping daemon...")
        service.stop()
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Write PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

        # Start service
        service.start()

        if service.is_running:
            click.echo("✅ Code Backup Daemon started successfully")

            # Show all watched paths with their associated accounts
            watched_paths = config.get('watched_paths', [])
            if watched_paths:
                click.echo(f"\n📁 Monitoring {len(watched_paths)} path(s):")
                for path_config in watched_paths:
                    path = path_config['path']
                    account = path_config.get('account', {}).get('username', 'unknown')
                    click.echo(f"   • {path} → {account}")

            click.echo(f"\n⏰ Backup interval: {config.get('daemon.backup_interval')}s")
            click.echo("\nPress Ctrl+C to stop")

            # Keep the main thread alive
            try:
                while service.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            click.echo("❌ Failed to start daemon", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error starting daemon: {e}", err=True)
        sys.exit(1)
    finally:
        # Cleanup
        service.stop()
        if pid_file.exists():
            pid_file.unlink()


@cli.command()
@click.pass_context
def stop(ctx):
    """Stop the backup daemon"""
    config = ctx.obj['config']
    pid_file = config.get_path('daemon.pid_file')

    if not is_daemon_running(pid_file):
        click.echo("❌ Daemon is not running")
        return

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Send SIGTERM signal
        import os
        os.kill(pid, signal.SIGTERM)

        # Wait for process to stop
        for _ in range(10):
            if not is_daemon_running(pid_file):
                break
            time.sleep(1)

        if is_daemon_running(pid_file):
            click.echo("⚠️  Daemon did not stop gracefully, forcing...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)

        if pid_file.exists():
            pid_file.unlink()

        click.echo("✅ Daemon stopped")

    except Exception as e:
        click.echo(f"❌ Error stopping daemon: {e}", err=True)


@cli.command()
@click.pass_context
def status(ctx):
    """Show daemon status"""
    config = ctx.obj['config']
    pid_file = config.get_path('daemon.pid_file')

    click.echo("📊 Code Backup Daemon Status")
    click.echo("=" * 40)

    # Check if daemon is running
    if is_daemon_running(pid_file):
        click.echo("🟢 Status: Running")
        try:
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            click.echo(f"🆔 PID: {pid}")
        except:
            pass
    else:
        click.echo("🔴 Status: Stopped")

    # Show configuration - multi-account support
    watched_paths = config.get('paths.watched_paths', [])
    if watched_paths:
        click.echo(f"\n📁 Watched Paths: {len(watched_paths)}")
        for idx, path_config in enumerate(watched_paths, 1):
            path = path_config['path']
            account = path_config.get('account', {}).get('username', 'unknown')
            click.echo(f"   {idx}. {path}")
            click.echo(f"      GitHub Account: {account}")
    else:
        # Fallback for old config format
        code_folder = config.get('paths.code_folder', 'Not configured')
        github_user = config.get('github.username', 'Not configured')
        click.echo(f"📁 Code Folder: {code_folder}")
        click.echo(f"👤 GitHub User: {github_user}")

    click.echo(f"\n⏰ Backup Interval: {config.get('daemon.backup_interval')}s")

    # Show state information
    state_file = config.get_path('daemon.state_file')
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            tracked_repos = state.get('tracked_repos', {})
            stats = state.get('stats', {})

            # Group repos by account
            repos_by_account = {}
            for repo_path, repo_info in tracked_repos.items():
                account = repo_info.get('account_username', 'unknown')
                if account not in repos_by_account:
                    repos_by_account[account] = []
                repos_by_account[account].append(repo_info)

            click.echo(f"\n📚 Tracked Repositories: {len(tracked_repos)}")
            if repos_by_account:
                for account, repos in sorted(repos_by_account.items()):
                    click.echo(f"   {account}: {len(repos)} repo(s)")

            click.echo(f"\n✅ Successful Backups: {stats.get('successful_backups', 0)}")
            click.echo(f"❌ Failed Backups: {stats.get('failed_backups', 0)}")

            last_backup = stats.get('last_backup_time')
            if last_backup:
                click.echo(f"🕐 Last Backup: {last_backup}")

        except Exception as e:
            click.echo(f"⚠️  Could not read state file: {e}")


@cli.command()
@click.option('--account', '-a', help='Filter by GitHub account')
@click.pass_context
def list_repos(ctx, account):
    """List tracked repositories"""
    config = ctx.obj['config']
    state_file = config.get_path('daemon.state_file')

    if not state_file.exists():
        click.echo("📝 No repositories are currently tracked")
        return

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        tracked_repos = state.get('tracked_repos', {})

        if not tracked_repos:
            click.echo("📝 No repositories are currently tracked")
            return

        # Filter by account if specified
        if account:
            tracked_repos = {
                path: info for path, info in tracked_repos.items()
                if info.get('account_username') == account
            }
            if not tracked_repos:
                click.echo(f"📝 No repositories found for account '{account}'")
                return
            click.echo(f"📚 Repositories for account '{account}' ({len(tracked_repos)})")
        else:
            click.echo(f"📚 All Tracked Repositories ({len(tracked_repos)})")

        click.echo("=" * 50)

        # Group by account for better organization
        repos_by_account = {}
        for repo_path, repo_info in tracked_repos.items():
            acc = repo_info.get('account_username', 'unknown')
            if acc not in repos_by_account:
                repos_by_account[acc] = []
            repos_by_account[acc].append((repo_path, repo_info))

        for acc, repos in sorted(repos_by_account.items()):
            if not account:  # Only show account headers when not filtering
                click.echo(f"\n👤 Account: {acc} ({len(repos)} repo(s))")
                click.echo("-" * 50)

            for repo_path, repo_info in repos:
                name = repo_info.get('name', 'Unknown')
                status = repo_info.get('status', 'unknown')
                last_backup = repo_info.get('last_backup', 'Never')
                backup_count = repo_info.get('backup_count', 0)

                # Status emoji
                status_emoji = {
                    'synced': '✅',
                    'failed': '❌',
                    'missing': '⚠️',
                    'error': '🔴',
                    'tracked': '📝'
                }.get(status, '❓')

                click.echo(f"\n{status_emoji} {name}")
                click.echo(f"   Path: {repo_path}")
                if account:  # Show account when filtering (redundant otherwise)
                    click.echo(f"   Account: {acc}")
                click.echo(f"   Status: {status}")
                click.echo(f"   Backups: {backup_count}")
                if last_backup != 'Never':
                    try:
                        backup_time = datetime.fromisoformat(last_backup)
                        click.echo(f"   Last Backup: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        click.echo(f"   Last Backup: {last_backup}")

    except Exception as e:
        click.echo(f"❌ Error reading repositories: {e}", err=True)


@cli.command()
@click.argument('repo_name', required=False)
@click.pass_context
def backup(ctx, repo_name):
    """Force backup of repositories"""
    config = ctx.obj['config']

    if not is_daemon_running(config.get_path('daemon.pid_file')):
        click.echo("⚠️  Daemon is not running. Starting one-time backup...")

        service = BackupService(config)

        if repo_name:
            click.echo(f"🔄 Backing up repository: {repo_name}")
            success = service.force_backup(repo_name)
        else:
            click.echo("🔄 Backing up all repositories...")
            success = service.force_backup()

        if success:
            click.echo("✅ Backup completed successfully")
        else:
            click.echo("❌ Backup failed", err=True)
            sys.exit(1)
    else:
        click.echo("⚠️  Cannot force backup while daemon is running")
        click.echo("Stop the daemon first with: code-backup stop")


@cli.command()
@click.argument('folder_path')
@click.pass_context
def add(ctx, folder_path):
    """Manually add a folder to tracking"""
    config = ctx.obj['config']
    path = Path(folder_path).expanduser().resolve()

    if not path.exists():
        click.echo(f"❌ Folder does not exist: {path}", err=True)
        sys.exit(1)

    if not path.is_dir():
        click.echo(f"❌ Path is not a directory: {path}", err=True)
        sys.exit(1)

    click.echo(f"📁 Adding folder to tracking: {path.name}")

    service = BackupService(config)

    if service.add_repository(path):
        click.echo("✅ Repository added successfully")
        service.save_state()
    else:
        click.echo("❌ Failed to add repository", err=True)
        sys.exit(1)


@cli.command()
@click.argument('repo_name')
@click.pass_context
def remove(ctx, repo_name):
    """Remove a repository from tracking"""
    config = ctx.obj['config']

    click.echo(f"🗑️  Removing repository from tracking: {repo_name}")
    click.echo("⚠️  This will not delete files or the GitHub repository")

    if not click.confirm("Are you sure?"):
        click.echo("❌ Cancelled")
        return

    service = BackupService(config)

    if service.remove_repository(repo_name):
        click.echo("✅ Repository removed from tracking")
    else:
        click.echo("❌ Repository not found", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration"""
    config = ctx.obj['config']

    click.echo("⚙️  Current Configuration")
    click.echo("=" * 40)
    click.echo(str(config))


@cli.command()
@click.argument('key')
@click.argument('value') 
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value"""
    config = ctx.obj['config']

    try:
        # Try to parse as JSON for complex values
        if value.startswith('{') or value.startswith('[') or value in ['true', 'false']:
            value = json.loads(value)

        config.set(key, value)
        config.save()

        click.echo(f"✅ Set {key} = {value}")

    except Exception as e:
        click.echo(f"❌ Error setting configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Initial setup wizard"""
    config = ctx.obj['config']

    click.echo("🛠️  Code Backup Daemon Setup")
    click.echo("=" * 40)

    # Check GitHub CLI
    if not check_gh_cli():
        click.echo("❌ GitHub CLI (gh) is not installed or authenticated")
        click.echo("Please install GitHub CLI and run: gh auth login")
        sys.exit(1)

    # Get GitHub username
    try:
        result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
        if result.returncode == 0:
            user_data = json.loads(result.stdout)
            username = user_data.get('login', '')
            click.echo(f"✅ GitHub user: {username}")
            config.set('github.username', username)
    except:
        username = click.prompt("GitHub username")
        config.set('github.username', username)

    # Get code folder
    default_code_folder = Path.home() / 'CODE'
    code_folder = click.prompt(
        "Code folder path", 
        default=str(default_code_folder)
    )

    code_path = Path(code_folder).expanduser()
    if not code_path.exists():
        if click.confirm(f"Create folder {code_path}?"):
            code_path.mkdir(parents=True, exist_ok=True)
        else:
            click.echo("❌ Setup cancelled")
            sys.exit(1)

    config.set('paths.code_folder', str(code_path))

    # Backup interval
    interval = click.prompt("Backup interval (seconds)", default=1800, type=int)
    config.set('daemon.backup_interval', interval)

    # Repository visibility
    visibility = click.prompt(
        "Default repository visibility", 
        default='private', 
        type=click.Choice(['private', 'public'])
    )
    config.set('github.default_visibility', visibility)

    # Save configuration
    config.save()

    click.echo("✅ Configuration saved!")
    click.echo("\n🚀 You can now start the daemon with: code-backup start")


def is_daemon_running(pid_file: Path) -> bool:
    """Check if daemon is running"""
    if not pid_file.exists():
        return False

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Check if process exists
        import os
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        return True

    except (ValueError, OSError, ProcessLookupError):
        # PID file is invalid or process doesn't exist
        if pid_file.exists():
            pid_file.unlink()
        return False


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated"""
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == '__main__':
    import os
    cli()
