"""
Flask web server for Code Backup Daemon UI
"""
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import logging

logger = logging.getLogger(__name__)


def create_app(backup_service):
    """Create and configure Flask application

    Args:
        backup_service: BackupService instance to integrate with

    Returns:
        tuple: (Flask app, SocketIO instance)
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    # Enable CORS for React dev server
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"]
        }
    })

    # Setup WebSocket with eventlet
    socketio = SocketIO(
        app,
        cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        async_mode='eventlet'
    )

    # Attach backup service to app
    app.backup_service = backup_service

    # Register API blueprint
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    logger.info("Flask application created successfully")

    return app, socketio
