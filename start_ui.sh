#!/bin/bash

# Start React Dev Server (for development)
# Use this when daemon is already running

PROJECT_DIR="/home/nayan-ai4m/Desktop/NK/automated-github-push"
cd "$PROJECT_DIR/web-ui"

echo "🎨 Starting React Dev Server..."
echo ""
echo "Web UI will be available at: http://localhost:5173"
echo "Make sure the daemon is running on port 8080"
echo ""

npm run dev
