#!/bin/bash

# Test UI Setup - Verify all components are ready

echo "🧪 Testing Web UI Setup..."
echo ""

PROJECT_DIR="/home/nayan-ai4m/Desktop/NK/automated-github-push"
cd "$PROJECT_DIR"

ERRORS=0

# Test 1: Check Python dependencies
echo "1. Checking Python dependencies..."
source venv/bin/activate
if python -c "import flask, flask_cors, flask_socketio" 2>/dev/null; then
    echo "   ✅ Flask dependencies installed"
else
    echo "   ❌ Flask dependencies missing"
    ERRORS=$((ERRORS + 1))
fi

# Test 2: Check web module structure
echo "2. Checking web module structure..."
if [ -f "code_backup_daemon/web/server.py" ] && \
   [ -f "code_backup_daemon/web/api.py" ] && \
   [ -f "code_backup_daemon/web/websocket.py" ]; then
    echo "   ✅ Backend web modules exist"
else
    echo "   ❌ Backend web modules missing"
    ERRORS=$((ERRORS + 1))
fi

# Test 3: Check React dependencies
echo "3. Checking React dependencies..."
if [ -d "web-ui/node_modules" ]; then
    echo "   ✅ Node modules installed"
else
    echo "   ❌ Node modules missing - run: cd web-ui && npm install"
    ERRORS=$((ERRORS + 1))
fi

# Test 4: Check React components
echo "4. Checking React components..."
if [ -f "web-ui/src/components/Dashboard.jsx" ] && \
   [ -f "web-ui/src/components/ProjectCard.jsx" ] && \
   [ -f "web-ui/src/services/api.js" ] && \
   [ -f "web-ui/src/hooks/useWebSocket.js" ]; then
    echo "   ✅ React components exist"
else
    echo "   ❌ React components missing"
    ERRORS=$((ERRORS + 1))
fi

# Test 5: Check configuration
echo "5. Checking configuration..."
if python -c "from code_backup_daemon.config import Config; c = Config(); assert 'ui' in c.config" 2>/dev/null; then
    echo "   ✅ Config has UI section"
else
    echo "   ❌ Config missing UI section"
    ERRORS=$((ERRORS + 1))
fi

# Test 6: Check startup scripts
echo "6. Checking startup scripts..."
if [ -x "start_web_ui.sh" ] && [ -x "start_ui_dev.sh" ]; then
    echo "   ✅ Startup scripts exist and are executable"
else
    echo "   ❌ Startup scripts missing or not executable"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests passed! UI setup is complete."
    echo ""
    echo "To start the application:"
    echo "  Terminal 1: ./start_web_ui.sh"
    echo "  Terminal 2: ./start_ui_dev.sh"
    echo ""
    echo "Then open: http://localhost:5173"
else
    echo "❌ $ERRORS test(s) failed. Please fix the issues above."
    exit 1
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
