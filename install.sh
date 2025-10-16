#!/bin/bash

# Code Backup Daemon Installation Script
# This script installs the Code Backup Daemon on Linux/macOS systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

print_info "Code Backup Daemon Installation"
echo "=================================="

# Check system requirements
print_info "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    exit 1
fi
print_success "pip3 found"

# Check git
if ! command -v git &> /dev/null; then
    print_error "Git is required but not installed"
    exit 1
fi
print_success "Git found"

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI (gh) is not installed"
    print_info "Installing GitHub CLI..."

    # Detect OS and install gh
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install gh
        else
            print_error "Homebrew is required to install GitHub CLI on macOS"
            print_info "Install Homebrew first: https://brew.sh/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt &> /dev/null; then
            # Debian/Ubuntu
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS/Fedora
            sudo yum install -y gh
        elif command -v dnf &> /dev/null; then
            # Fedora (newer)
            sudo dnf install -y gh
        else
            print_error "Unsupported Linux distribution"
            print_info "Please install GitHub CLI manually: https://github.com/cli/cli#installation"
            exit 1
        fi
    else
        print_error "Unsupported operating system"
        exit 1
    fi
fi

if command -v gh &> /dev/null; then
    print_success "GitHub CLI found"
else
    print_error "Failed to install GitHub CLI"
    exit 1
fi

# Install Python package
print_info "Installing Code Backup Daemon..."

# Create virtual environment (optional but recommended)
if [[ "$1" != "--system" ]]; then
    print_info "Creating virtual environment..."
    VENV_DIR="$HOME/.local/share/code-backup/venv"
    mkdir -p "$(dirname "$VENV_DIR")"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment created at $VENV_DIR"
fi

# Install package
pip3 install -e .
print_success "Python package installed"

# Create directories
print_info "Creating directories..."
mkdir -p "$HOME/.config/code-backup"
mkdir -p "$HOME/.local/share/code-backup"
mkdir -p "$HOME/CODE"
print_success "Directories created"

# Copy configuration file
if [[ ! -f "$HOME/.config/code-backup/config.yaml" ]]; then
    cp default_config.yaml "$HOME/.config/code-backup/config.yaml"
    print_success "Configuration file created"
else
    print_info "Configuration file already exists"
fi

# Install systemd service (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_info "Installing systemd service..."

    # Create user systemd directory
    mkdir -p "$HOME/.config/systemd/user"

    # Copy service file
    cp code-backup.service "$HOME/.config/systemd/user/"

    # Reload systemd
    systemctl --user daemon-reload

    print_success "Systemd service installed"
    print_info "To enable auto-start: systemctl --user enable code-backup"
    print_info "To start service: systemctl --user start code-backup"
fi

# Setup GitHub authentication
print_info "Setting up GitHub authentication..."
if ! gh auth status &> /dev/null; then
    print_warning "GitHub CLI is not authenticated"
    print_info "Please run: gh auth login"
    print_info "After authentication, run: code-backup setup"
else
    print_success "GitHub CLI is already authenticated"
fi

# Create symlink for easy access (if not using venv)
if [[ "$1" == "--system" ]]; then
    if [[ -w "/usr/local/bin" ]]; then
        ln -sf "$(which code-backup)" /usr/local/bin/code-backup 2>/dev/null || true
        print_success "Created symlink in /usr/local/bin"
    fi
fi

print_success "Installation completed!"
echo
echo "Next steps:"
echo "1. Authenticate with GitHub: gh auth login"
echo "2. Run setup wizard: code-backup setup"  
echo "3. Start the daemon: code-backup start"
echo
echo "For more help: code-backup --help"
