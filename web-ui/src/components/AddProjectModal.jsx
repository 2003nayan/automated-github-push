import React, { useState, useRef } from 'react';
import { X, FolderPlus, Loader2, FolderOpen } from 'lucide-react';

export const AddProjectModal = ({ accounts, onClose, onAdd }) => {
  const [folderPath, setFolderPath] = useState('');
  const [selectedAccount, setSelectedAccount] = useState(accounts[0]?.username || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const folderInputRef = useRef(null);

  const handleFolderSelect = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      // Get the full path from the first file
      const firstFile = files[0];
      const fullPath = firstFile.webkitRelativePath || firstFile.path || '';

      // Extract the folder path (remove the filename from the path)
      if (fullPath) {
        const pathParts = fullPath.split('/');
        const folderName = pathParts[0];

        // Since we can't get absolute paths in browser, we'll use the folder name
        // and let the user edit it to add the full path
        setFolderPath(folderName);
      }
    }
  };

  const handleBrowseClick = () => {
    folderInputRef.current?.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!folderPath.trim()) {
      setError('Please enter a folder path');
      return;
    }

    if (!selectedAccount) {
      setError('Please select an account');
      return;
    }

    setIsSubmitting(true);

    try {
      await onAdd(folderPath.trim(), selectedAccount);
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to add project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-neutral-950 dark:text-neutral-50">
              Add New Project
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
          >
            <X className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Folder Path Input */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Folder Path
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="/home/user/my-project"
                className="flex-1 px-4 py-2.5 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent transition-all"
                disabled={isSubmitting}
              />
              <button
                type="button"
                onClick={handleBrowseClick}
                className="px-4 py-2.5 bg-neutral-100 dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-all active:scale-95 flex items-center gap-2"
                disabled={isSubmitting}
                title="Browse for folder"
              >
                <FolderOpen className="w-4 h-4" />
                Browse
              </button>
            </div>
            {/* Hidden file input for folder selection */}
            <input
              ref={folderInputRef}
              type="file"
              webkitdirectory=""
              directory=""
              multiple
              onChange={handleFolderSelect}
              className="hidden"
            />
            <p className="mt-1.5 text-xs text-neutral-500 dark:text-neutral-400">
              Enter the absolute path or click Browse to select a folder
            </p>
          </div>

          {/* Account Selection */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              GitHub Account
            </label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full px-4 py-2.5 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent transition-all cursor-pointer"
              disabled={isSubmitting}
            >
              {accounts.map((account) => (
                <option key={account.username} value={account.username}>
                  {account.username} ({account.name})
                </option>
              ))}
            </select>
            <p className="mt-1.5 text-xs text-neutral-500 dark:text-neutral-400">
              Choose which GitHub account to sync this project to
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-error-light dark:bg-error-dark/20 border border-error/20 dark:border-error/30 rounded-lg">
              <p className="text-sm text-error-dark dark:text-error">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 font-medium transition-all active:scale-95"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 bg-accent-500 text-white rounded-lg hover:bg-accent-600 font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
