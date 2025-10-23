"""
Flask web server for Code Backup Daemon UI
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_app(backup_service):
    """Create and configure Flask application

    Args:
        backup_service: BackupService instance to integrate with

    Returns:
        tuple: (Flask app, SocketIO instance)
    """
    # Determine static folder path (built React app)
    project_root = Path(__file__).parent.parent.parent
    static_folder = project_root / 'web-ui' / 'dist'

    app = Flask(__name__, static_folder=str(static_folder))
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    # Enable CORS for development (still allow dev server)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173",
                       "http://localhost:8080", "http://127.0.0.1:8080"]
        }
    })

    # Setup WebSocket with eventlet
    socketio = SocketIO(
        app,
        cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                            "http://localhost:8080", "http://127.0.0.1:8080"],
        async_mode='eventlet'
    )

    # Attach backup service to app
    app.backup_service = backup_service

    # Register API blueprint
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Serve React static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        """Serve React app (catch-all route for client-side routing)"""
        if path and (static_folder / path).exists():
            return send_from_directory(str(static_folder), path)
        else:
            # For client-side routing, always return index.html
            return send_from_directory(str(static_folder), 'index.html')

    logger.info(f"Flask application created successfully (static: {static_folder})")

    return app, socketio
