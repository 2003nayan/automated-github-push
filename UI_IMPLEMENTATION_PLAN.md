# Web UI Implementation Plan for Code Backup Daemon

## 📋 Overview

This document outlines the step-by-step implementation plan for adding a modern web-based user interface to the Code Backup Daemon. The UI will enable users to selectively control which projects are backed up to GitHub through an intuitive, visually appealing interface.

---

## 🎯 Project Goals

### Core Functionality
- ✅ Visual project selector with enable/disable toggles
- ✅ Real-time backup status monitoring
- ✅ Manual backup triggers per project
- ✅ Multi-account support visualization
- ✅ Beautiful, modern design

### Technical Stack
- **Backend:** Flask (Python web framework)
- **Frontend:** React.js with Vite
- **Styling:** Tailwind CSS
- **Icons:** Lucide React / Heroicons
- **State Management:** React Context API
- **API Communication:** Axios / Fetch API
- **WebSocket:** Flask-SocketIO (for real-time updates)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Web Browser                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │         React Frontend (Port 5173)              │   │
│  │  - Project Dashboard                            │   │
│  │  - Settings Panel                               │   │
│  │  - Status Indicators                            │   │
│  └──────────────────┬──────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────┘
                      │
                      │ HTTP/WebSocket
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Flask API Server (Port 5000)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  REST API Endpoints                             │   │
│  │  - GET  /api/projects                           │   │
│  │  - POST /api/projects/:id/toggle                │   │
│  │  - POST /api/projects/:id/backup                │   │
│  │  - GET  /api/status                             │   │
│  │  - WebSocket events (real-time updates)         │   │
│  └──────────────────┬──────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────┘
                      │
                      │ Python Integration
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Existing Daemon Components                      │
│  - BackupService                                        │
│  - GitService                                           │
│  - GitHubService                                        │
│  - FolderWatcher                                        │
│  - Config (with UI preferences)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 New Project Structure

```
automated-github-push/
├── code_backup_daemon/          # Existing daemon code
│   ├── backup_service.py
│   ├── cli.py
│   ├── config.py
│   ├── folder_watcher.py
│   ├── git_service.py
│   ├── github_service.py
│   ├── main.py
│   ├── utils.py
│   └── web/                     # NEW: Web UI components
│       ├── __init__.py
│       ├── api.py               # Flask API routes
│       ├── websocket.py         # WebSocket handlers
│       └── server.py            # Flask app setup
│
├── web-ui/                      # NEW: React frontend
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ProjectCard.jsx
│   │   │   ├── AccountSection.jsx
│   │   │   ├── StatusBar.jsx
│   │   │   ├── SettingsModal.jsx
│   │   │   └── BackupHistory.jsx
│   │   ├── hooks/
│   │   │   ├── useProjects.js
│   │   │   ├── useWebSocket.js
│   │   │   └── useBackupStatus.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── utils/
│   │   │   └── formatters.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── start_web_ui.sh              # NEW: Start web UI + daemon
├── requirements.txt             # Updated with Flask, SocketIO
└── UI_IMPLEMENTATION_PLAN.md    # This file
```

---

## 🔧 Implementation Steps

### **PHASE 1: Backend Infrastructure** (Days 1-2)

#### Step 1.1: Install Flask Dependencies
**File:** `requirements.txt`

**Action:** Add new dependencies
```txt
# Existing dependencies
gitpython==3.1.40
watchdog==3.0.0
click==8.1.7
pyyaml==6.0.1
requests==2.31.0

# NEW: Web UI dependencies
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
```

**Installation:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

#### Step 1.2: Update Config Schema
**File:** `code_backup_daemon/config.py`

**Action:** Add UI preferences to config structure

**Changes:**
1. Add `ui` section to `DEFAULT_CONFIG`:
```python
DEFAULT_CONFIG = {
    # ... existing config ...

    "ui": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 5000,
        "auto_open_browser": True,
        "theme": "dark",  # dark or light
    },

    "project_preferences": {},  # NEW: Store per-project settings
}
```

2. Add method to get/set project preferences:
```python
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
    self.save_config()
```

---

#### Step 1.3: Create Flask API Server
**File:** `code_backup_daemon/web/server.py`

**Action:** Setup Flask application with CORS and SocketIO

```python
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

def create_app(backup_service):
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    # Enable CORS for React dev server
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Setup WebSocket
    socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

    # Attach backup service to app
    app.backup_service = backup_service

    # Register blueprints
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app, socketio
```

---

#### Step 1.4: Create REST API Endpoints
**File:** `code_backup_daemon/web/api.py`

**Action:** Implement API routes for project management

```python
from flask import Blueprint, jsonify, request, current_app
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all tracked projects with their status"""
    service = current_app.backup_service
    config = service.config

    projects = []
    for repo_name, repo_info in service.repositories.items():
        account = repo_info.get('account', 'unknown')
        enabled = config.get_project_enabled(repo_name)

        projects.append({
            'id': repo_name,
            'name': repo_name,
            'path': repo_info.get('local_path', ''),
            'account': account,
            'enabled': enabled,
            'last_backup': repo_info.get('last_backup_time', None),
            'backup_count': repo_info.get('backup_count', 0),
            'github_url': repo_info.get('remote_url', '').replace('git@github.com:', 'https://github.com/').replace('.git', ''),
            'status': 'active' if repo_info.get('is_active') else 'inactive',
            'error_count': repo_info.get('error_count', 0),
            'last_error': repo_info.get('last_error', None)
        })

    return jsonify({'projects': projects})

@api_bp.route('/projects/<project_id>/toggle', methods=['POST'])
def toggle_project(project_id):
    """Enable/disable project sync"""
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

@api_bp.route('/projects/<project_id>/backup', methods=['POST'])
def backup_project(project_id):
    """Trigger manual backup for specific project"""
    service = current_app.backup_service

    # Check if project is enabled
    if not service.config.get_project_enabled(project_id):
        return jsonify({
            'success': False,
            'error': 'Project sync is disabled'
        }), 400

    try:
        # Trigger backup
        success = service.backup_repository(project_id)

        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully backed up {project_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Backup failed'
            }), 500

    except Exception as e:
        logger.error(f"Error backing up {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get daemon status and statistics"""
    service = current_app.backup_service

    enabled_projects = sum(
        1 for repo_name in service.repositories.keys()
        if service.config.get_project_enabled(repo_name)
    )

    return jsonify({
        'daemon_running': service.running,
        'total_projects': len(service.repositories),
        'enabled_projects': enabled_projects,
        'disabled_projects': len(service.repositories) - enabled_projects,
        'total_backups': service.stats.get('successful_backups', 0),
        'failed_backups': service.stats.get('failed_backups', 0),
        'last_backup_time': service.stats.get('last_backup_time', None),
        'uptime': service.stats.get('uptime', 0)
    })

@api_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get list of configured accounts"""
    service = current_app.backup_service
    config = service.config

    accounts = []
    for path_config in config.get('watched_paths', []):
        account_info = path_config.get('account', {})
        accounts.append({
            'username': account_info.get('username'),
            'name': path_config.get('name'),
            'path': path_config.get('path'),
            'project_count': sum(
                1 for repo in service.repositories.values()
                if repo.get('account') == account_info.get('username')
            )
        })

    return jsonify({'accounts': accounts})

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get UI-relevant configuration"""
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
```

---

#### Step 1.5: Create WebSocket Handler
**File:** `code_backup_daemon/web/websocket.py`

**Action:** Implement real-time event broadcasting

```python
from flask_socketio import emit
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
            emit('connected', {'status': 'ok'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from WebSocket')

    def broadcast_backup_started(self, project_name):
        """Notify clients that backup started"""
        self.socketio.emit('backup_started', {
            'project': project_name,
            'timestamp': datetime.now().isoformat()
        })

    def broadcast_backup_completed(self, project_name, success, error=None):
        """Notify clients that backup completed"""
        self.socketio.emit('backup_completed', {
            'project': project_name,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })

    def broadcast_project_detected(self, project_name):
        """Notify clients of new project detection"""
        self.socketio.emit('project_detected', {
            'project': project_name,
            'timestamp': datetime.now().isoformat()
        })

    def broadcast_status_update(self, status_data):
        """Broadcast general status update"""
        self.socketio.emit('status_update', status_data)
```

---

#### Step 1.6: Integrate Web Server with BackupService
**File:** `code_backup_daemon/backup_service.py`

**Action:** Add WebSocket notifications to backup operations

**Changes:**
1. Add websocket handler attribute:
```python
class BackupService:
    def __init__(self, config):
        # ... existing init ...
        self.websocket_handler = None  # Set by web server
```

2. Add notifications to `backup_repository()`:
```python
def backup_repository(self, repo_name: str) -> bool:
    """Backup a specific repository (existing method)"""

    # Notify WebSocket clients
    if self.websocket_handler:
        self.websocket_handler.broadcast_backup_started(repo_name)

    # ... existing backup logic ...

    # Notify completion
    if self.websocket_handler:
        self.websocket_handler.broadcast_backup_completed(
            repo_name,
            success=success,
            error=error if not success else None
        )

    return success
```

3. Add notification when new projects are detected:
```python
def add_repository(self, path: str, repo_name: str = None, account_config: dict = None):
    """Add repository to tracking (existing method)"""

    # ... existing logic ...

    # Notify WebSocket clients
    if self.websocket_handler:
        self.websocket_handler.broadcast_project_detected(repo_name)
```

---

#### Step 1.7: Update CLI to Start Web Server
**File:** `code_backup_daemon/cli.py`

**Action:** Add web UI option to start command

**Changes:**
```python
@click.command()
@click.option('--foreground', is_flag=True, help='Run in foreground')
@click.option('--no-ui', is_flag=True, help='Start without web UI')
def start(foreground, no_ui):
    """Start the backup daemon"""

    # ... existing daemon start logic ...

    # Start web UI if enabled
    if not no_ui and config.get('ui.enabled', True):
        from code_backup_daemon.web.server import create_app
        from code_backup_daemon.web.websocket import WebSocketHandler

        app, socketio = create_app(service)
        service.websocket_handler = WebSocketHandler(socketio)

        # Start in separate thread
        import threading

        def run_web_server():
            host = config.get('ui.host', '127.0.0.1')
            port = config.get('ui.port', 5000)
            socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)

        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()

        click.echo(f"Web UI started at http://{host}:{port}")

        # Open browser if configured
        if config.get('ui.auto_open_browser', True):
            import webbrowser
            webbrowser.open(f"http://{host}:{port}")
```

---

### **PHASE 2: Frontend Development** (Days 3-5)

#### Step 2.1: Initialize React Project
**Location:** `web-ui/`

**Action:** Create Vite + React + Tailwind project

```bash
cd /home/nayan-ai4m/Desktop/NK/automated-github-push
npm create vite@latest web-ui -- --template react
cd web-ui
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios lucide-react socket.io-client
npm install react-router-dom recharts
```

---

#### Step 2.2: Configure Tailwind CSS
**File:** `web-ui/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        dark: {
          bg: '#0f172a',
          card: '#1e293b',
          border: '#334155',
        }
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}
```

**File:** `web-ui/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-gray-100;
  }
}
```

---

#### Step 2.3: Create API Service
**File:** `web-ui/src/services/api.js`

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const projectsApi = {
  getAll: () => api.get('/projects'),
  toggle: (projectId, enabled) =>
    api.post(`/projects/${projectId}/toggle`, { enabled }),
  backup: (projectId) =>
    api.post(`/projects/${projectId}/backup`),
};

export const statusApi = {
  get: () => api.get('/status'),
};

export const accountsApi = {
  getAll: () => api.get('/accounts'),
};

export const configApi = {
  get: () => api.get('/config'),
};

export default api;
```

---

#### Step 2.4: Create WebSocket Hook
**File:** `web-ui/src/hooks/useWebSocket.js`

```javascript
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

export const useWebSocket = (url = 'http://localhost:5000') => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const newSocket = io(url);

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on('backup_started', (data) => {
      setEvents(prev => [...prev, { type: 'backup_started', ...data }]);
    });

    newSocket.on('backup_completed', (data) => {
      setEvents(prev => [...prev, { type: 'backup_completed', ...data }]);
    });

    newSocket.on('project_detected', (data) => {
      setEvents(prev => [...prev, { type: 'project_detected', ...data }]);
    });

    setSocket(newSocket);

    return () => newSocket.close();
  }, [url]);

  return { socket, connected, events };
};
```

---

#### Step 2.5: Create ProjectCard Component
**File:** `web-ui/src/components/ProjectCard.jsx`

```jsx
import React, { useState } from 'react';
import {
  FolderGit2,
  Github,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ExternalLink
} from 'lucide-react';

export const ProjectCard = ({ project, onToggle, onBackup }) => {
  const [isBackingUp, setIsBackingUp] = useState(false);

  const handleBackup = async () => {
    setIsBackingUp(true);
    await onBackup(project.id);
    setIsBackingUp(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="bg-white dark:bg-dark-card rounded-lg shadow-md p-6 border border-gray-200 dark:border-dark-border hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <FolderGit2 className="w-8 h-8 text-primary-500" />
          <div>
            <h3 className="text-lg font-semibold">{project.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {project.account}
            </p>
          </div>
        </div>

        {/* Enable/Disable Toggle */}
        <button
          onClick={() => onToggle(project.id, !project.enabled)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            project.enabled
              ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
          }`}
        >
          {project.enabled ? 'Enabled' : 'Disabled'}
        </button>
      </div>

      {/* Status */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm">
          {project.enabled ? (
            <CheckCircle2 className="w-4 h-4 text-green-500" />
          ) : (
            <AlertCircle className="w-4 h-4 text-gray-400" />
          )}
          <span className="text-gray-600 dark:text-gray-300">
            Status: {project.enabled ? 'Syncing' : 'Paused'}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-gray-600 dark:text-gray-300">
            Last backup: {formatDate(project.last_backup)}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <Github className="w-4 h-4 text-gray-400" />
          <span className="text-gray-600 dark:text-gray-300">
            {project.backup_count} backups
          </span>
        </div>
      </div>

      {/* Error Display */}
      {project.error_count > 0 && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-300">
            {project.last_error || 'Recent backup failed'}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleBackup}
          disabled={!project.enabled || isBackingUp}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isBackingUp ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Backing up...
            </>
          ) : (
            'Backup Now'
          )}
        </button>

        {project.github_url && (
          <a
            href={project.github_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  );
};
```

---

#### Step 2.6: Create AccountSection Component
**File:** `web-ui/src/components/AccountSection.jsx`

```jsx
import React from 'react';
import { User, Folder } from 'lucide-react';
import { ProjectCard } from './ProjectCard';

export const AccountSection = ({ account, projects, onToggle, onBackup }) => {
  return (
    <div className="mb-8">
      {/* Account Header */}
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200 dark:border-dark-border">
        <User className="w-6 h-6 text-primary-500" />
        <div>
          <h2 className="text-xl font-bold">{account.name}</h2>
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Folder className="w-4 h-4" />
            <span>{account.path}</span>
            <span className="mx-2">•</span>
            <span>{projects.length} projects</span>
          </div>
        </div>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map(project => (
          <ProjectCard
            key={project.id}
            project={project}
            onToggle={onToggle}
            onBackup={onBackup}
          />
        ))}
      </div>
    </div>
  );
};
```

---

#### Step 2.7: Create StatusBar Component
**File:** `web-ui/src/components/StatusBar.jsx`

```jsx
import React from 'react';
import { Activity, CheckCircle, XCircle, Pause, Clock } from 'lucide-react';

export const StatusBar = ({ status }) => {
  if (!status) return null;

  return (
    <div className="bg-white dark:bg-dark-card rounded-lg shadow-md p-6 mb-6 border border-gray-200 dark:border-dark-border">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Daemon Status */}
        <div className="flex items-center gap-3">
          <Activity className={`w-8 h-8 ${status.daemon_running ? 'text-green-500' : 'text-red-500'}`} />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Daemon</p>
            <p className="text-lg font-semibold">
              {status.daemon_running ? 'Running' : 'Stopped'}
            </p>
          </div>
        </div>

        {/* Enabled Projects */}
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-green-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Enabled</p>
            <p className="text-lg font-semibold">{status.enabled_projects}</p>
          </div>
        </div>

        {/* Disabled Projects */}
        <div className="flex items-center gap-3">
          <Pause className="w-8 h-8 text-gray-400" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Disabled</p>
            <p className="text-lg font-semibold">{status.disabled_projects}</p>
          </div>
        </div>

        {/* Successful Backups */}
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-blue-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Successful</p>
            <p className="text-lg font-semibold">{status.total_backups}</p>
          </div>
        </div>

        {/* Failed Backups */}
        <div className="flex items-center gap-3">
          <XCircle className="w-8 h-8 text-red-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
            <p className="text-lg font-semibold">{status.failed_backups}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

#### Step 2.8: Create Main Dashboard
**File:** `web-ui/src/components/Dashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { projectsApi, statusApi, accountsApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { StatusBar } from './StatusBar';
import { AccountSection } from './AccountSection';
import { Github, RefreshCw, Settings } from 'lucide-react';

export const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const { connected, events } = useWebSocket();

  // Fetch initial data
  useEffect(() => {
    fetchData();
  }, []);

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];

      if (latestEvent.type === 'backup_completed' || latestEvent.type === 'project_detected') {
        fetchData(); // Refresh data
      }
    }
  }, [events]);

  const fetchData = async () => {
    try {
      const [projectsRes, statusRes, accountsRes] = await Promise.all([
        projectsApi.getAll(),
        statusApi.get(),
        accountsApi.getAll(),
      ]);

      setProjects(projectsRes.data.projects);
      setStatus(statusRes.data);
      setAccounts(accountsRes.data.accounts);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (projectId, enabled) => {
    try {
      await projectsApi.toggle(projectId, enabled);

      // Update local state
      setProjects(prev =>
        prev.map(p => p.id === projectId ? { ...p, enabled } : p)
      );
    } catch (error) {
      console.error('Error toggling project:', error);
    }
  };

  const handleBackup = async (projectId) => {
    try {
      await projectsApi.backup(projectId);
      await fetchData(); // Refresh to get updated backup time
    } catch (error) {
      console.error('Error backing up project:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      {/* Header */}
      <header className="bg-white dark:bg-dark-card shadow-md border-b border-gray-200 dark:border-dark-border">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Github className="w-8 h-8 text-primary-500" />
              <h1 className="text-2xl font-bold">Code Backup Dashboard</h1>
            </div>

            <div className="flex items-center gap-4">
              {/* WebSocket Status */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Refresh Button */}
              <button
                onClick={fetchData}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
              </button>

              {/* Settings Button */}
              <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Status Bar */}
        <StatusBar status={status} />

        {/* Projects by Account */}
        {accounts.map(account => {
          const accountProjects = projects.filter(
            p => p.account === account.username
          );

          return (
            <AccountSection
              key={account.username}
              account={account}
              projects={accountProjects}
              onToggle={handleToggle}
              onBackup={handleBackup}
            />
          );
        })}

        {/* Empty State */}
        {projects.length === 0 && (
          <div className="text-center py-12">
            <Github className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 dark:text-gray-400 mb-2">
              No projects found
            </h3>
            <p className="text-gray-500 dark:text-gray-500">
              Create a project in one of your watched folders to get started
            </p>
          </div>
        )}
      </main>
    </div>
  );
};
```

---

#### Step 2.9: Create Main App Component
**File:** `web-ui/src/App.jsx`

```jsx
import React from 'react';
import { Dashboard } from './components/Dashboard';

function App() {
  return (
    <div className="dark">
      <Dashboard />
    </div>
  );
}

export default App;
```

---

#### Step 2.10: Update Vite Config for Proxy
**File:** `web-ui/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
    },
  },
})
```

---

### **PHASE 3: Integration & Testing** (Days 6-7)

#### Step 3.1: Create Startup Script
**File:** `start_web_ui.sh`

```bash
#!/bin/bash

# Code Backup Daemon - Web UI Launcher
# Starts both the daemon and web UI

set -e

PROJECT_DIR="/home/nayan-ai4m/Desktop/NK/automated-github-push"
cd "$PROJECT_DIR"

echo "🚀 Starting Code Backup Daemon with Web UI..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export GITHUB_TOKEN_NK="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"
export GITHUB_TOKEN_AI4M="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"

# Start daemon with web UI in background
echo "📡 Starting daemon..."
python -m code_backup_daemon.cli start --foreground &
DAEMON_PID=$!

# Wait for daemon to start
sleep 3

# Start React dev server
echo "🎨 Starting web UI..."
cd web-ui
npm run dev &
UI_PID=$!

echo ""
echo "✅ Code Backup Daemon with Web UI is running!"
echo ""
echo "📊 Dashboard: http://localhost:5173"
echo "🔌 API Server: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for interrupt
trap "kill $DAEMON_PID $UI_PID 2>/dev/null; exit" INT
wait
```

---

#### Step 3.2: Update Backup Logic to Respect Enabled Status
**File:** `code_backup_daemon/backup_service.py`

**Action:** Modify `_backup_loop()` to skip disabled projects

```python
def _backup_loop(self):
    """Periodic backup loop (existing method with modifications)"""

    while self.running:
        try:
            logger.info("Starting backup cycle...")

            for repo_name, repo_info in self.repositories.items():
                if not self.running:
                    break

                # SKIP DISABLED PROJECTS
                if not self.config.get_project_enabled(repo_name):
                    logger.debug(f"Skipping disabled project: {repo_name}")
                    continue

                # Only backup if active
                if repo_info.get('is_active', True):
                    self.backup_repository(repo_name)

            # ... rest of existing logic ...
```

---

#### Step 3.3: Create Testing Checklist
**File:** `TESTING_CHECKLIST.md`

```markdown
# Web UI Testing Checklist

## Backend Tests

### API Endpoints
- [ ] GET /api/projects returns all projects
- [ ] POST /api/projects/:id/toggle enables project
- [ ] POST /api/projects/:id/toggle disables project
- [ ] POST /api/projects/:id/backup triggers backup
- [ ] GET /api/status returns correct statistics
- [ ] GET /api/accounts returns all accounts
- [ ] GET /api/config returns configuration

### WebSocket Events
- [ ] Client connects successfully
- [ ] `backup_started` event fires when backup begins
- [ ] `backup_completed` event fires when backup ends
- [ ] `project_detected` event fires for new projects

### Integration
- [ ] Disabled projects are skipped in backup loop
- [ ] Manual backup respects enabled status
- [ ] Config persists project preferences

## Frontend Tests

### UI Components
- [ ] Dashboard loads without errors
- [ ] StatusBar shows correct statistics
- [ ] ProjectCard displays project info correctly
- [ ] Toggle button enables/disables project
- [ ] Backup button triggers backup
- [ ] GitHub link opens correct repository

### Real-time Updates
- [ ] WebSocket connection indicator works
- [ ] Live updates when backup completes
- [ ] New projects appear automatically

### User Interactions
- [ ] Clicking toggle updates state immediately
- [ ] Backup button shows loading state
- [ ] Disabled projects show correct status
- [ ] Refresh button updates all data

## End-to-End Tests

### Workflow 1: Disable Project
1. [ ] Open dashboard
2. [ ] Click toggle to disable project
3. [ ] Verify project shows "Disabled" status
4. [ ] Wait for backup cycle
5. [ ] Verify project was NOT backed up

### Workflow 2: Manual Backup
1. [ ] Click "Backup Now" on enabled project
2. [ ] Verify backup starts (loading indicator)
3. [ ] Verify WebSocket event received
4. [ ] Verify backup completes successfully
5. [ ] Verify last backup time updated

### Workflow 3: New Project Detection
1. [ ] Create new project in watched folder
2. [ ] Wait 30 seconds
3. [ ] Verify project appears in dashboard
4. [ ] Verify WebSocket notification received
```

---

### **PHASE 4: Polish & Documentation** (Day 8)

#### Step 4.1: Add Dark Mode Toggle
**Component Enhancement:** Add theme switcher to header

#### Step 4.2: Add Notifications/Toasts
**Library:** Install `react-hot-toast` for user feedback

#### Step 4.3: Add Loading Skeletons
**Enhancement:** Better UX while data loads

#### Step 4.4: Create User Documentation
**File:** `WEB_UI_GUIDE.md`

---

## 📊 Feature Comparison

| Feature | Current CLI | New Web UI |
|---------|------------|-----------|
| View projects | `code-backup list-repos` | Visual dashboard with cards |
| Enable/disable sync | ❌ Not available | ✅ Toggle button per project |
| Manual backup | `code-backup backup <name>` | ✅ "Backup Now" button |
| View status | `code-backup status` | ✅ Real-time status bar |
| Multi-account view | Text output | ✅ Grouped by account |
| Real-time updates | ❌ Must refresh | ✅ WebSocket live updates |
| GitHub links | ❌ Copy manually | ✅ Click to open |
| Backup history | ❌ Check logs | ✅ Visual timeline |

---

## 🎨 UI Design Mockup

```
┌────────────────────────────────────────────────────────────────┐
│  🐙 Code Backup Dashboard                   🟢 Connected  ⚙️  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐     │
│  │ Daemon   │ Enabled  │ Disabled │ Success  │ Failed   │     │
│  │ Running  │    5     │    2     │   147    │    3     │     │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘     │
│                                                                 │
│  NK Projects (2003nayan)                                        │
│  📁 /home/nayan-ai4m/Desktop/NK • 3 projects                   │
│  ─────────────────────────────────────────────────────────────│
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ 📂 my-webapp│  │ 📂 portfolio│  │ 📂 test-app │           │
│  │ 2003nayan   │  │ 2003nayan   │  │ 2003nayan   │           │
│  │             │  │             │  │             │           │
│  │ ✅ Syncing  │  │ ✅ Syncing  │  │ ⏸️  Paused  │           │
│  │ 🕒 2h ago   │  │ 🕒 5h ago   │  │ 🕒 Never    │           │
│  │ 🐙 47 backs │  │ 🐙 23 backs │  │ 🐙 0 backs  │           │
│  │             │  │             │  │             │           │
│  │[Backup Now] │  │[Backup Now] │  │[Backup Now] │           │
│  │   [Enabled] │  │   [Enabled] │  │  [Disabled] │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                 │
│  AI4M Projects (nayan-ai4m)                                     │
│  📁 /home/nayan-ai4m/Desktop/AI4M • 2 projects                 │
│  ─────────────────────────────────────────────────────────────│
│  ┌─────────────┐  ┌─────────────┐                             │
│  │ 📂 dashboard│  │ �� api-svc  │                             │
│  │ nayan-ai4m  │  │ nayan-ai4m  │                             │
│  │             │  │             │                             │
│  │ ✅ Syncing  │  │ ✅ Syncing  │                             │
│  │ 🕒 1h ago   │  │ 🕒 3h ago   │                             │
│  │ 🐙 89 backs │  │ 🐙 56 backs │                             │
│  │             │  │             │                             │
│  │[Backup Now] │  │[Backup Now] │                             │
│  │   [Enabled] │  │   [Enabled] │                             │
│  └─────────────┘  └─────────────┘                             │
└────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment & Production

### Production Checklist

- [ ] Change Flask secret key
- [ ] Use production WSGI server (Gunicorn)
- [ ] Build React for production (`npm run build`)
- [ ] Serve React build from Flask
- [ ] Add authentication (optional)
- [ ] Configure reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Set up systemd service

### Production Startup Script
**File:** `start_web_ui_production.sh`

```bash
#!/bin/bash

# Build React app
cd web-ui
npm run build

# Serve with Gunicorn
cd ..
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:5000 'code_backup_daemon.web.server:create_app()'
```

---

## 📝 Summary

This implementation plan provides:

1. ✅ **Project-level control** - Enable/disable sync per repository
2. ✅ **Beautiful web UI** - Modern React dashboard with Tailwind CSS
3. ✅ **Real-time updates** - WebSocket integration for live feedback
4. ✅ **Multi-account support** - Visual grouping by GitHub account
5. ✅ **Manual backup triggers** - On-demand backups via UI
6. ✅ **Status monitoring** - Live statistics and health indicators
7. ✅ **GitHub integration** - Direct links to repositories
8. ✅ **Persistent preferences** - Config-based project settings

### Estimated Timeline
- **Phase 1 (Backend):** 2 days
- **Phase 2 (Frontend):** 3 days
- **Phase 3 (Integration):** 2 days
- **Phase 4 (Polish):** 1 day

**Total: ~8 days** for full implementation

---

## 🎓 Next Steps

After reviewing this plan:
1. Approve the architecture and design
2. Begin Phase 1: Backend Infrastructure
3. Test each component incrementally
4. Deploy and gather user feedback
5. Iterate based on usage patterns

Ready to start implementation! 🚀
