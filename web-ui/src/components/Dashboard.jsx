import React, { useState, useEffect } from 'react';
import { projectsApi, statusApi, accountsApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
// import { useTheme } from '../hooks/useTheme';
import { StatusBar } from './StatusBar';
import { AccountSection } from './AccountSection';
import { AddProjectModal } from './AddProjectModal';
import { SettingsModal } from './SettingsModal';
import { GitBranch, RefreshCw, Loader2, Sun, Moon, FolderPlus, Settings } from 'lucide-react';

export const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const { connected, events } = useWebSocket();
  // const { theme, toggleTheme } = useTheme();

  // Fetch initial data
  useEffect(() => {
    fetchData();
  }, []);

  // Set default selected account when accounts load or restore from URL
  useEffect(() => {
    if (accounts.length > 0 && !selectedAccount) {
      // Try to restore from URL query parameter
      const params = new URLSearchParams(window.location.search);
      const accountFromUrl = params.get('account');

      if (accountFromUrl && accounts.some(a => a.username === accountFromUrl)) {
        setSelectedAccount(accountFromUrl);
      } else {
        setSelectedAccount(accounts[0].username);
      }
    }
  }, [accounts, selectedAccount]);

  // Persist selected account to URL
  useEffect(() => {
    if (selectedAccount) {
      const params = new URLSearchParams(window.location.search);
      params.set('account', selectedAccount);
      const newUrl = `${window.location.pathname}?${params.toString()}`;
      window.history.replaceState({}, '', newUrl);
    }
  }, [selectedAccount]);

  // Handle WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];

      if (latestEvent.type === 'backup_completed' || latestEvent.type === 'project_detected') {
        // Refresh data when backup completes or new project detected
        fetchData();
      }
    }
  }, [events]);

  const fetchData = async () => {
    try {
      setError(null);
      const [projectsRes, statusRes, accountsRes] = await Promise.all([
        projectsApi.getAll(),
        statusApi.get(),
        accountsApi.getAll(),
      ]);

      setProjects(projectsRes.data.projects || []);
      setStatus(statusRes.data);
      setAccounts(accountsRes.data.accounts || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Make sure the daemon is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (projectId, enabled) => {
    try {
      await projectsApi.toggle(projectId, enabled);

      // Update local state immediately
      setProjects(prev =>
        prev.map(p => p.id === projectId ? { ...p, enabled } : p)
      );

      // Refresh status to update counts
      const statusRes = await statusApi.get();
      setStatus(statusRes.data);
    } catch (error) {
      console.error('Error toggling project:', error);
      alert('Failed to toggle project sync');
    }
  };

  const handleBackup = async (projectId) => {
    try {
      await projectsApi.backup(projectId);
      // Data will refresh via WebSocket event
      setTimeout(fetchData, 1000); // Fallback refresh
    } catch (error) {
      console.error('Error backing up project:', error);
      alert('Failed to backup project: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleAddProject = async (folderPath, accountUsername) => {
    try {
      await projectsApi.add(folderPath, accountUsername);
      // Refresh data to show new project
      await fetchData();
    } catch (error) {
      console.error('Error adding project:', error);
      throw error; // Re-throw to let modal handle the error
    }
  };

  const handleDelete = async (projectId, options) => {
    try {
      await projectsApi.delete(projectId, options);
      // Refresh data to remove deleted project
      await fetchData();
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('Failed to delete project: ' + (error.response?.data?.error || error.message));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-neutral-50 dark:bg-neutral-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-accent-500 mx-auto mb-4" />
          <p className="text-neutral-600 dark:text-neutral-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-neutral-50 dark:bg-neutral-900">
        <div className="text-center max-w-md p-6">
          <div className="text-error mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold mb-2 text-neutral-950 dark:text-neutral-50">Connection Error</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-accent-500 text-white rounded-lg hover:bg-accent-600 transition-all active:scale-95"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 shadow-minimal">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center shadow-sm">
                <GitBranch className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-neutral-950 dark:text-neutral-50 tracking-tight">
                  Code Backup
                </h1>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">Automated repository sync</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* WebSocket Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-neutral-100 dark:bg-neutral-700 border border-neutral-200 dark:border-neutral-600">
                <div className={`status-indicator ${connected ? 'bg-success' : 'bg-danger'}`} />
                <span className="text-xs font-medium text-neutral-700 dark:text-neutral-200">
                  {connected ? 'Live' : 'Offline'}
                </span>
              </div>

              {/* Add Project Button */}
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-500 text-white hover:bg-accent-600 active:scale-95 transition-all shadow-sm"
                title="Add new project"
              >
                <FolderPlus className="w-4 h-4" />
                <span className="text-sm font-medium">Add Folder</span>
              </button>

              {/* Settings Button */}
              <button
                onClick={() => setShowSettingsModal(true)}
                className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-600 bg-white dark:bg-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-600 active:scale-95 transition-all"
                title="Settings"
              >
                <Settings className="w-4 h-4 text-neutral-700 dark:text-neutral-200" />
              </button>

              {/* Theme Toggle */}
              {/* <button
                onClick={toggleTheme}
                className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-600 bg-white dark:bg-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-600 active:scale-95 transition-all"
                title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              >
                {theme === 'light' ? (
                  <Moon className="w-4 h-4 text-neutral-700 dark:text-neutral-200" />
                ) : (
                  <Sun className="w-4 h-4 text-neutral-700 dark:text-neutral-200" />
                )}
              </button> */}

              {/* Refresh Button */}
              <button
                onClick={fetchData}
                className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-600 bg-white dark:bg-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-600 active:scale-95 transition-all"
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4 text-neutral-700 dark:text-neutral-200" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        {/* Status Bar */}
        <StatusBar status={status} />

        {/* Account Tabs */}
        {accounts.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 border-b border-neutral-200 dark:border-neutral-700">
              {accounts.map(account => {
                const accountProjects = projects.filter(p => p.account === account.username);
                const isActive = selectedAccount === account.username;

                return (
                  <button
                    key={account.username}
                    onClick={() => setSelectedAccount(account.username)}
                    className={`px-6 py-3 text-sm font-medium transition-all relative ${
                      isActive
                        ? 'text-neutral-950 dark:text-neutral-50'
                        : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      {account.name || account.username}
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        isActive
                          ? 'bg-accent-500 text-white'
                          : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400'
                      }`}>
                        {accountProjects.length}
                      </span>
                    </span>
                    {isActive && (
                      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-500 rounded-t-full" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Selected Account Projects */}
        {selectedAccount && accounts.length > 0 && (() => {
          const account = accounts.find(a => a.username === selectedAccount);
          const accountProjects = projects.filter(p => p.account === selectedAccount);

          return account ? (
            <AccountSection
              key={account.username}
              account={account}
              projects={accountProjects}
              onToggle={handleToggle}
              onBackup={handleBackup}
              onDelete={handleDelete}
            />
          ) : null;
        })()}

        {/* Empty State */}
        {projects.length === 0 && !loading && (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-neutral-100 dark:bg-neutral-850 rounded-2xl mb-4">
              <GitBranch className="w-8 h-8 text-neutral-400 dark:text-neutral-500" />
            </div>
            <h3 className="text-xl font-semibold text-neutral-950 dark:text-neutral-50 mb-2">
              No projects yet
            </h3>
            <p className="text-neutral-500 dark:text-neutral-400 max-w-md mx-auto">
              Create a project in your watched folders to start automatic backup syncing
            </p>
          </div>
        )}
      </main>

      {/* Add Project Modal */}
      {showAddModal && (
        <AddProjectModal
          accounts={accounts}
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddProject}
        />
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <SettingsModal
          onClose={() => setShowSettingsModal(false)}
        />
      )}
    </div>
  );
};
