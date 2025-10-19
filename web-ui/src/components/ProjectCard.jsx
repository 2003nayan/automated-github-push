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
    try {
      await onBackup(project.id);
    } finally {
      setTimeout(() => setIsBackingUp(false), 1000);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return 'Invalid date';
    }
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
      {project.error_count > 0 && project.last_error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-300">
            {project.last_error}
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
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-center"
            title="Open on GitHub"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  );
};
