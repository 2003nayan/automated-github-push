import React, { useState, useEffect } from 'react';
import {
  FolderGit2,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ExternalLink,
  GitCommit,
  Circle,
  Trash2
} from 'lucide-react';
import { DeleteConfirmModal } from './DeleteConfirmModal';

export const ProjectCard = ({ project, onToggle, onBackup, onDelete }) => {
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every minute to refresh relative timestamps
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const handleBackup = async () => {
    setIsBackingUp(true);
    try {
      await onBackup(project.id);
    } finally {
      setTimeout(() => setIsBackingUp(false), 1000);
    }
  };

  const handleDelete = async (options) => {
    await onDelete(project.id, options);
    setShowDeleteModal(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    try {
      const date = new Date(dateStr);
      const diffMs = currentTime - date;
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="minimal-card p-6 hover:border-neutral-300 dark:hover:border-neutral-600 group animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 bg-gradient-to-br from-neutral-900 to-neutral-950 dark:from-neutral-100 dark:to-neutral-200 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
            <FolderGit2 className="w-5 h-5 text-white dark:text-neutral-900" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-neutral-950 dark:text-neutral-50 mb-1 truncate">
              {project.name}
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
              {project.account}
            </p>
          </div>
        </div>

        {/* Status Toggle */}
        <button
          onClick={() => onToggle(project.id, !project.enabled)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all active:scale-95 flex-shrink-0 ml-2 ${
            project.enabled
              ? 'bg-success-light dark:bg-success-dark/20 text-success-dark dark:text-success border border-success/20 dark:border-success/30'
              : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-600 hover:bg-neutral-200 dark:hover:bg-neutral-600'
          }`}
        >
          <Circle className={`w-2 h-2 ${project.enabled ? 'fill-success' : 'fill-neutral-400 dark:fill-neutral-500'}`} />
          {project.enabled ? 'Active' : 'Paused'}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        {/* Status */}
        <div className="flex items-center gap-2 px-3 py-2 bg-neutral-50 dark:bg-neutral-850 rounded-lg border border-neutral-100 dark:border-neutral-700">
          {project.enabled ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-success flex-shrink-0" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-neutral-400 dark:text-neutral-500 flex-shrink-0" />
          )}
          <span className="text-xs text-neutral-600 dark:text-neutral-300 truncate">
            {project.enabled ? 'Syncing' : 'Paused'}
          </span>
        </div>

        {/* Backup Count */}
        <div className="flex items-center gap-2 px-3 py-2 bg-neutral-50 dark:bg-neutral-850 rounded-lg border border-neutral-100 dark:border-neutral-700">
          <GitCommit className="w-3.5 h-3.5 text-neutral-600 dark:text-neutral-400 flex-shrink-0" />
          <span className="text-xs text-neutral-600 dark:text-neutral-300 truncate">
            {project.backup_count} {project.backup_count === 1 ? 'backup' : 'backups'}
          </span>
        </div>
      </div>

      {/* Last Backup */}
      <div className="flex items-center gap-2 px-3 py-2 bg-neutral-50 dark:bg-neutral-850 rounded-lg border border-neutral-100 dark:border-neutral-700 mb-5">
        <Calendar className="w-3.5 h-3.5 text-neutral-500 dark:text-neutral-400 flex-shrink-0" />
        <span className="text-xs text-neutral-600 dark:text-neutral-300">
          Last backup: {formatDate(project.last_backup)}
        </span>
      </div>

      {/* Error Display */}
      {project.error_count > 0 && project.last_error && (
        <div className="mb-5 p-3 bg-error-light dark:bg-error-dark/20 rounded-lg border border-error/20 dark:border-error/30">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3.5 h-3.5 text-error mt-0.5 flex-shrink-0" />
            <p className="text-xs text-error-dark dark:text-error leading-relaxed">
              {project.last_error}
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleBackup}
          disabled={!project.enabled || isBackingUp}
          className="minimal-button-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isBackingUp ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Syncing...</span>
            </>
          ) : (
            <span className="text-sm">Backup Now</span>
          )}
        </button>

        {project.github_url && (
          <a
            href={project.github_url}
            target="_blank"
            rel="noopener noreferrer"
            className="minimal-button-secondary flex items-center justify-center w-12 h-12"
            title="View on GitHub"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        )}

        <button
          onClick={() => setShowDeleteModal(true)}
          className="minimal-button-secondary flex items-center justify-center w-12 h-12 hover:bg-error-light hover:text-error hover:border-error/30 dark:hover:bg-error-dark/20 dark:hover:text-error dark:hover:border-error/30 transition-all"
          title="Delete Project"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <DeleteConfirmModal
          project={project}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
};
