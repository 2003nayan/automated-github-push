import React, { useState, useEffect } from 'react';
import { projectsApi, statusApi, accountsApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { StatusBar } from './StatusBar';
import { AccountSection } from './AccountSection';
import { Github, RefreshCw, Loader2 } from 'lucide-react';

export const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-dark-bg">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-dark-bg">
        <div className="text-center max-w-md p-6">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">Connection Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            Retry
          </button>
        </div>
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
                title="Refresh"
              >
                <RefreshCw className="w-5 h-5" />
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
        {projects.length === 0 && !loading && (
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
