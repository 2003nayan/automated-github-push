import React, { useState } from 'react';
import { X, Trash2, AlertTriangle, Github, Folder, Database } from 'lucide-react';

export const DeleteConfirmModal = ({ project, onClose, onConfirm }) => {
  const [deleteGithub, setDeleteGithub] = useState(false);
  const [deleteLocal, setDeleteLocal] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const isConfirmValid = confirmText === project.name;

  const handleDelete = async () => {
    if (!isConfirmValid) return;

    setIsDeleting(true);
    try {
      await onConfirm({
        delete_github: deleteGithub,
        delete_local: deleteLocal
      });
      onClose();
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl max-w-lg w-full border border-neutral-200 dark:border-neutral-700 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-error/10 dark:bg-error/20 rounded-lg flex items-center justify-center">
              <Trash2 className="w-5 h-5 text-error" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-neutral-950 dark:text-neutral-50">
                Delete Project
              </h2>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                This action cannot be undone
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
            disabled={isDeleting}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Warning */}
          <div className="flex items-start gap-3 p-4 bg-warning-light dark:bg-warning-dark/20 rounded-lg border border-warning/20 dark:border-warning/30">
            <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-warning-dark dark:text-warning mb-1">
                Warning: Permanent Deletion
              </p>
              <p className="text-xs text-warning-dark/80 dark:text-warning/80 leading-relaxed">
                You are about to delete <span className="font-semibold">{project.name}</span> from account <span className="font-mono font-semibold">{project.account}</span>.
              </p>
            </div>
          </div>

          {/* Delete Options */}
          <div className="space-y-3">
            <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              What would you like to delete?
            </p>

            {/* Remove from Tracking (Always) */}
            <div className="flex items-start gap-3 p-4 bg-neutral-50 dark:bg-neutral-850 rounded-lg border border-neutral-200 dark:border-neutral-700">
              <div className="flex items-center justify-center w-5 h-5 bg-neutral-900 dark:bg-neutral-100 rounded flex-shrink-0 mt-0.5">
                <Database className="w-3 h-3 text-white dark:text-neutral-900" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  Remove from tracking
                </p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                  Stop monitoring this project (always enabled)
                </p>
              </div>
            </div>

            {/* Delete from GitHub */}
            <label className="flex items-start gap-3 p-4 bg-white dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700 cursor-pointer hover:border-error/50 dark:hover:border-error/50 transition-colors">
              <input
                type="checkbox"
                checked={deleteGithub}
                onChange={(e) => setDeleteGithub(e.target.checked)}
                disabled={isDeleting}
                className="mt-1 w-4 h-4 text-error border-neutral-300 dark:border-neutral-600 rounded focus:ring-error focus:ring-offset-0"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Github className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    Delete from GitHub
                  </p>
                </div>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">
                  Permanently delete the repository from GitHub
                </p>
              </div>
            </label>

            {/* Delete Local Files */}
            <label className="flex items-start gap-3 p-4 bg-error-light/30 dark:bg-error-dark/10 rounded-lg border-2 border-error/50 dark:border-error/30 cursor-pointer hover:border-error dark:hover:border-error transition-colors">
              <input
                type="checkbox"
                checked={deleteLocal}
                onChange={(e) => setDeleteLocal(e.target.checked)}
                disabled={isDeleting}
                className="mt-1 w-4 h-4 text-error border-error rounded focus:ring-error focus:ring-offset-0"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Folder className="w-4 h-4 text-error" />
                  <p className="text-sm font-medium text-error">
                    Delete local files
                  </p>
                </div>
                <p className="text-xs text-error/80 dark:text-error/70">
                  ⚠️ DANGER: This will permanently delete all local files at:<br />
                  <span className="font-mono mt-1 inline-block">{project.path}</span>
                </p>
              </div>
            </label>
          </div>

          {/* Confirmation Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Type <span className="font-mono font-semibold text-error">{project.name}</span> to confirm:
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              disabled={isDeleting}
              placeholder={project.name}
              className="w-full px-4 py-3 bg-white dark:bg-neutral-850 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-error focus:border-transparent transition-all text-sm font-mono"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-neutral-200 dark:border-neutral-700">
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={!isConfirmValid || isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-error hover:bg-error-dark rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isDeleting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                Delete Project
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
