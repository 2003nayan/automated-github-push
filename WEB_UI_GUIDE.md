# Web UI Guide - Code Backup Daemon

## 🎨 Overview

The Web UI provides a beautiful, modern interface to manage your code backup daemon. You can:

- ✅ **View all projects** across multiple GitHub accounts
- ✅ **Enable/Disable sync** for individual projects with a toggle
- ✅ **Manual backup** trigger for any project
- ✅ **Real-time updates** via WebSocket
- ✅ **Status monitoring** with live statistics
- ✅ **Direct GitHub links** to open repositories

---

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)

```bash
./start_web_ui.sh
```

This starts:
- Backend daemon on `http://localhost:5000`
- Web UI automatically (daemon handles it)

Then open another terminal and run:
```bash
./start_ui_dev.sh
```

This starts the React dev server on `http://localhost:5173`

**Access the UI:** Open browser to `http://localhost:5173`

---

### Option 2: Start Separately

**Terminal 1 - Start Daemon:**
```bash
source venv/bin/activate
export GITHUB_TOKEN_NK="your_token_here"
export GITHUB_TOKEN_AI4M="your_token_here"
python -m code_backup_daemon.cli start
```

**Terminal 2 - Start React Dev Server:**
```bash
cd web-ui
npm run dev
```

---

## 🎯 Features

### 1. Dashboard Overview

The main dashboard shows:
- **Status Bar** with daemon status and statistics
- **Account Sections** grouping projects by GitHub account
- **Project Cards** for each repository

### 2. Enable/Disable Projects

Click the **"Enabled"** or **"Disabled"** button on any project card to toggle sync.

**When disabled:**
- ❌ Project will NOT be backed up during automatic cycles
- ⏸️ Status shows as "Paused"
- 🚫 Manual backup button is disabled

**When enabled:**
- ✅ Project will be backed up every 6 hours (or configured interval)
- ✅ Manual backup is available
- ✅ Real-time status updates

### 3. Manual Backup

Click **"Backup Now"** to immediately backup a project.

**What happens:**
1. Button shows loading spinner
2. Backend commits and pushes changes
3. WebSocket sends real-time update
4. Dashboard refreshes automatically
5. "Last backup" time updates

### 4. Real-Time Updates

The UI uses WebSocket for live updates:

**Events:**
- 🟢 **backup_started** - Backup begins
- ✅ **backup_completed** - Backup succeeds
- ❌ **backup_error** - Backup fails
- 🆕 **project_detected** - New project added

**Connection Status:**
- 🟢 Green dot = Connected
- 🔴 Red dot = Disconnected

### 5. Project Information

Each project card shows:
- **Project name** and GitHub account
- **Enable/Disable toggle**
- **Last backup time**
- **Total backup count**
- **Error messages** (if any)
- **GitHub link** to open repo in browser

---

## 🎨 UI Components

### StatusBar
Displays overall statistics:
- Daemon running status
- Enabled/Disabled project counts
- Successful/Failed backup counts

### AccountSection
Groups projects by GitHub account:
- Account name and path
- Project count
- Grid of project cards

### ProjectCard
Individual project with:
- Project info and status
- Enable/Disable toggle
- Backup Now button
- GitHub link

---

## 🛠️ Development

### File Structure

```
web-ui/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx       # Main container
│   │   ├── StatusBar.jsx       # Statistics bar
│   │   ├── AccountSection.jsx  # Account grouping
│   │   └── ProjectCard.jsx     # Project card
│   ├── services/
│   │   └── api.js              # API calls
│   ├── hooks/
│   │   └── useWebSocket.js     # WebSocket hook
│   ├── App.jsx                 # Root component
│   ├── main.jsx                # Entry point
│   └── index.css               # Tailwind styles
├── package.json
├── vite.config.js              # Vite config with proxy
└── tailwind.config.js          # Tailwind theme
```

### API Endpoints

**Projects:**
- `GET /api/projects` - List all projects
- `POST /api/projects/:id/toggle` - Toggle enabled status
- `POST /api/projects/:id/backup` - Trigger manual backup

**Status:**
- `GET /api/status` - Get daemon status
- `GET /api/accounts` - List GitHub accounts
- `GET /api/config` - Get configuration

**WebSocket:**
- `ws://localhost:5000/socket.io` - Real-time events

### Running in Development

```bash
# Install dependencies
cd web-ui
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🎨 Customization

### Change Theme

Edit `web-ui/tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        500: '#0ea5e9',  // Change primary color
      },
      dark: {
        bg: '#0f172a',    // Change dark background
        card: '#1e293b',  // Change dark card color
      }
    }
  }
}
```

### Change Ports

**Backend (daemon):**
Edit `~/.config/code-backup/config.yaml`:
```yaml
ui:
  port: 5000  # Change backend port
```

**Frontend (React):**
Edit `web-ui/vite.config.js`:
```javascript
server: {
  port: 5173,  // Change frontend port
}
```

---

## 🐛 Troubleshooting

### UI Won't Load

**Check daemon is running:**
```bash
curl http://localhost:5000/api/health
```

Should return: `{"status":"healthy","timestamp":"..."}`

**Check React dev server:**
```bash
cd web-ui
npm run dev
```

Should start on `http://localhost:5173`

### WebSocket Not Connecting

**Check browser console for errors:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for WebSocket connection errors

**Common fixes:**
- Make sure daemon is running
- Check firewall isn't blocking port 5000
- Verify Flask-SocketIO is installed: `pip list | grep socketio`

### API Errors

**Enable/Disable not working:**
- Check browser console for API errors
- Verify config file has write permissions
- Check daemon logs: `tail -f ~/.local/share/code-backup/daemon.log`

**Backup fails:**
- Make sure project is enabled
- Check git authentication (SSH keys)
- View project error message on card

### Projects Not Showing

**Check daemon has detected projects:**
```bash
cat ~/.local/share/code-backup/state.json | jq
```

**Force initial scan:**
Restart daemon - it performs initial scan on startup

---

## 📊 Performance

### Production Build

For production, build the React app:

```bash
cd web-ui
npm run build
```

This creates optimized files in `web-ui/dist/`

Serve with Flask (modify `web/server.py` to serve static files) or use nginx.

### WebSocket Performance

- WebSocket connection is persistent
- Events are sent only when needed
- Dashboard auto-refreshes on events
- Manual refresh button available

---

## 🔒 Security

**Important Notes:**
- Web UI runs on localhost by default
- No authentication implemented (local use only)
- For remote access, use SSH tunnel:
  ```bash
  ssh -L 5173:localhost:5173 -L 5000:localhost:5000 user@remote-host
  ```

**Future Enhancements:**
- Add authentication (JWT tokens)
- Add HTTPS support
- Add user roles and permissions

---

## 🎓 Next Steps

1. **Customize the theme** to match your preferences
2. **Add more features** - see `UI_IMPLEMENTATION_PLAN.md` Phase 4
3. **Deploy to production** with nginx reverse proxy
4. **Add authentication** for remote access

---

## 📝 Summary

✅ Modern, responsive UI with Tailwind CSS
✅ Real-time updates with WebSocket
✅ Per-project enable/disable control
✅ Manual backup triggers
✅ Multi-account support
✅ Dark mode by default
✅ Mobile-friendly design

**Enjoy your new Web UI! 🎉**
