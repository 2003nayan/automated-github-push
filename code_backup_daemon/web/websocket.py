"""
WebSocket handler for real-time updates
"""
from flask_socketio import emit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handle WebSocket events for real-time updates"""

    def __init__(self, socketio):
        self.socketio = socketio
        self.setup_events()

    def setup_events(self):
        """Register WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to WebSocket')
            emit('connected', {'status': 'ok', 'timestamp': datetime.now().isoformat()})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from WebSocket')

        @self.socketio.on('ping')
        def handle_ping():
            emit('pong', {'timestamp': datetime.now().isoformat()})

    def broadcast_backup_started(self, project_name):
        """Notify clients that backup started"""
        try:
            self.socketio.emit('backup_started', {
                'project': project_name,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Broadcasted backup_started for {project_name}")
        except Exception as e:
            logger.error(f"Error broadcasting backup_started: {e}")

    def broadcast_backup_completed(self, project_name, success, error=None):
        """Notify clients that backup completed"""
        try:
            self.socketio.emit('backup_completed', {
                'project': project_name,
                'success': success,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Broadcasted backup_completed for {project_name} (success={success})")
        except Exception as e:
            logger.error(f"Error broadcasting backup_completed: {e}")

    def broadcast_project_detected(self, project_name, account):
        """Notify clients of new project detection"""
        try:
            self.socketio.emit('project_detected', {
                'project': project_name,
                'account': account,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Broadcasted project_detected for {project_name}")
        except Exception as e:
            logger.error(f"Error broadcasting project_detected: {e}")

    def broadcast_status_update(self, status_data):
        """Broadcast general status update"""
        try:
            self.socketio.emit('status_update', {
                **status_data,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug("Broadcasted status_update")
        except Exception as e:
            logger.error(f"Error broadcasting status_update: {e}")

    def broadcast_error(self, project_name, error_message):
        """Broadcast error notification"""
        try:
            self.socketio.emit('backup_error', {
                'project': project_name,
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Broadcasted error for {project_name}")
        except Exception as e:
            logger.error(f"Error broadcasting error: {e}")
