# Generate comprehensive README.md
readme_content = '''# Code Backup Daemon

🚀 **Automatically backup your code to GitHub without lifting a finger!**

A smart Python daemon that monitors your code folder, detects new projects, and automatically creates GitHub repositories and keeps them synced. Never lose your work again!

## ✨ Features

- 🔍 **Smart Project Detection** - Automatically identifies valid code projects
- 📁 **New Folder Monitoring** - Watches for new projects in real-time  
- 🐙 **GitHub Integration** - Creates private/public repositories automatically
- 🔄 **Continuous Backup** - Commits and pushes changes on schedule
- ⚙️ **Configurable** - Customize backup intervals, ignore patterns, and more
- 🖥️ **CLI Interface** - Easy command-line management
- 🛠️ **Systemd Support** - Run as system service on Linux
- 📊 **Status Monitoring** - Track backup statistics and repository health

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- [GitHub CLI](https://cli.github.com/) (`gh`)
- GitHub account

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/code-backup-daemon.git
   cd code-backup-daemon
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Authenticate with GitHub:**
   ```bash
   gh auth login
   ```

4. **Run the setup wizard:**
   ```bash
   code-backup setup
   ```

5. **Start the daemon:**
   ```bash
   code-backup start
   ```

That's it! Your code is now being automatically backed up to GitHub! 🎉

## 📚 Usage

### Basic Commands

```bash
# Start the daemon
code-backup start

# Stop the daemon  
code-backup stop

# Check status
code-backup status

# List tracked repositories
code-backup list-repos

# Force backup all repos
code-backup backup

# Force backup specific repo
code-backup backup my-project

# Add a folder manually
code-backup add /path/to/project

# Remove from tracking
code-backup remove project-name

# Show configuration
code-backup config-show

# Set configuration value
code-backup config-set github.default_visibility public
```

### Run as System Service (Linux)

```bash
# Enable auto-start
systemctl --user enable code-backup

# Start service
systemctl --user start code-backup

# Check service status
systemctl --user status code-backup

# View logs
journalctl --user -u code-backup -f
```

## ⚙️ Configuration

The daemon uses a YAML configuration file located at `~/.config/code-backup/config.yaml`.

### Key Configuration Options

```yaml
# Daemon settings
daemon:
  backup_interval: 1800  # 30 minutes
  log_level: INFO

# Paths
paths:
  code_folder: ~/CODE  # Folder to monitor

# GitHub settings  
github:
  username: your-username
  default_visibility: private  # or public
  use_gh_cli: true

# Project detection
project_detection:
  min_size_bytes: 1024
  project_indicators:
    - package.json
    - requirements.txt
    - README.md
  ignore_patterns:
    - node_modules
    - venv
    - __pycache__
```

## 🔍 How It Works

### Project Detection

The daemon identifies valid code projects by looking for:

- **Project files**: `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, etc.
- **Source code**: Files with extensions like `.py`, `.js`, `.java`, `.go`, etc.
- **Documentation**: `README.md`, `LICENSE`, etc.
- **Minimum size**: Projects must be larger than 1KB by default

### Backup Process

1. **Scan existing folders** on startup
2. **Monitor for new folders** in real-time
3. **Initialize git** if not already a repository
4. **Create GitHub repository** with appropriate visibility
5. **Commit changes** automatically with timestamps
6. **Push to GitHub** on configured intervals
7. **Handle conflicts** gracefully (skip, notify, or force)

### File System Structure

```
~/.config/code-backup/
├── config.yaml          # Main configuration
└── ...

~/.local/share/code-backup/
├── daemon.log           # Application logs
├── daemon.pid           # Process ID file
├── state.json           # Repository tracking state
└── venv/               # Virtual environment (if used)

~/CODE/                  # Your code folder (configurable)
├── my-python-project/
├── my-web-app/
└── ...
```

## 🛡️ Security & Privacy

- **Private by default** - New repositories are created as private
- **Token security** - Uses GitHub CLI authentication (no hardcoded tokens)
- **Local processing** - All code analysis happens locally
- **Configurable visibility** - Choose public/private per repository or globally
- **Sensitive file detection** - Built-in `.gitignore` patterns
- **No code scanning** - Only backs up, never reads your code content

## 📊 Monitoring & Troubleshooting

### Check Status

```bash
code-backup status
```

```
📊 Code Backup Daemon Status
========================================
🟢 Status: Running
🆔 PID: 12345
📁 Code Folder: /home/user/CODE
👤 GitHub User: your-username
⏰ Backup Interval: 1800s
📚 Tracked Repositories: 15
✅ Successful Backups: 142
❌ Failed Backups: 3
🕐 Last Backup: 2025-10-16 22:30:15
```

### View Logs

```bash
# Real-time logs
tail -f ~/.local/share/code-backup/daemon.log

# System service logs (Linux)
journalctl --user -u code-backup -f
```

### Common Issues

**Daemon won't start:**
- Check GitHub CLI authentication: `gh auth status`
- Verify configuration: `code-backup config-show`
- Check logs for specific errors

**Repository not being tracked:**
- Ensure it meets project detection criteria
- Check ignore patterns in configuration
- Manually add: `code-backup add /path/to/project`

**Push failures:**
- Check internet connection
- Verify GitHub repository exists and is accessible
- Check for merge conflicts in logs

## 🔧 Advanced Usage

### Custom Project Detection

```yaml
project_detection:
  # Custom project indicators
  project_indicators:
    - package.json
    - requirements.txt
    - your-custom-file.txt
  
  # Custom code extensions
  code_extensions:
    - .py
    - .js
    - .your-ext
  
  # Additional ignore patterns
  ignore_patterns:
    - temp
    - cache
    - your-folder-pattern
```

### Organization Repositories

```yaml
github:
  create_org_repos: true
  organization: your-org-name
```

### Custom Git Settings

```yaml
git:
  default_branch: main
  auto_commit_message: "Backup: {timestamp}"
  handle_conflicts: skip  # or notify, force
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/code-backup-daemon.git
cd code-backup-daemon

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GitHub CLI](https://cli.github.com/) for seamless GitHub integration
- [Watchdog](https://github.com/gorakhargosh/watchdog) for file system monitoring
- [GitPython](https://github.com/gitpython-developers/GitPython) for Git operations
- [Click](https://click.palletsprojects.com/) for the CLI interface

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/code-backup-daemon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/code-backup-daemon/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/code-backup-daemon/wiki)

---

**Happy coding! 🚀** Your code is now safe and backed up automatically!
'''

with open("README.md", "w") as f:
    f.write(readme_content)

print("✅ Generated README.md")

# Create a simple test file to verify the structure
test_content = '''"""
Simple test to verify the code structure works
"""
import unittest
import tempfile
import shutil
from pathlib import Path

# Test imports work
try:
    from config import Config
    from backup_service import BackupService
    from git_service import GitService
    from github_service import GitHubService
    from folder_watcher import FolderWatcher
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")

class TestStructure(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_creation(self):
        """Test configuration creation"""
        config = Config()
        self.assertIsNotNone(config)
        self.assertTrue(hasattr(config, 'get'))
        self.assertTrue(hasattr(config, 'validate'))
    
    def test_services_creation(self):
        """Test that services can be created"""
        config = Config()
        
        # These might fail due to missing dependencies, but should be importable
        git_service = GitService(config)
        github_service = GitHubService(config)
        
        self.assertIsNotNone(git_service)
        self.assertIsNotNone(github_service)

if __name__ == '__main__':
    # Just run the import test
    print("🧪 Running basic structure test...")
    unittest.main(verbosity=2)
'''

with open("test_structure.py", "w") as f:
    f.write(test_content)

print("✅ Generated test_structure.py")

print("\\n🎉 Production-ready Code Backup Daemon generated successfully!")
print("\\n📁 Files created:")
files_created = [
    "requirements.txt", "config.py", "git_service.py", "github_service.py",
    "folder_watcher.py", "backup_service.py", "cli.py", "main.py", 
    "utils.py", "__init__.py", "default_config.yaml", "code-backup.service",
    "setup.py", "install.sh", ".gitignore", "README.md", "test_structure.py"
]

for file in files_created:
    print(f"  ✅ {file}")

print("\\n🚀 To get started:")
print("1. Run: chmod +x install.sh && ./install.sh")
print("2. Authenticate: gh auth login") 
print("3. Setup: code-backup setup")
print("4. Start: code-backup start")