import React, { useState, useEffect } from 'react';
import { browseApi } from '../services/api';
import { Folder, FolderOpen, ChevronRight, Home, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';

export const FolderBrowser = ({ onSelect, initialPath }) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '~');
  const [folders, setFolders] = useState([]);
  const [parentPath, setParentPath] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFolder, setSelectedFolder] = useState(null);

  useEffect(() => {
    loadFolders(currentPath);
  }, [currentPath]);

  const loadFolders = async (path) => {
    setLoading(true);
    setError('');

    try {
      const response = await browseApi.getFolders(path);
      const data = response.data;

      setCurrentPath(data.current_path);
      setParentPath(data.parent_path);
      setFolders(data.folders || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load folders');
      console.error('Error loading folders:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = (folder) => {
    if (folder.is_accessible) {
      setCurrentPath(folder.path);
      setSelectedFolder(null);
    }
  };

  const handleFolderSelect = (folder) => {
    setSelectedFolder(folder.path);
  };

  const handleGoUp = () => {
    if (parentPath) {
      setCurrentPath(parentPath);
      setSelectedFolder(null);
    }
  };

  const handleGoHome = () => {
    setCurrentPath('~');
    setSelectedFolder(null);
  };

  const handleConfirmSelect = () => {
    if (selectedFolder) {
      onSelect(selectedFolder);
    } else {
      onSelect(currentPath);
    }
  };

  return (
    <div className="flex flex-col h-[500px] bg-white dark:bg-neutral-900 rounded-lg border border-neutral-300 dark:border-neutral-600">
      {/* Navigation Header */}
      <div className="flex items-center gap-2 p-3 border-b border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800">
        <button
          onClick={handleGoHome}
          className="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
          title="Go to home directory"
        >
          <Home className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
        </button>
        <button
          onClick={handleGoUp}
          disabled={!parentPath}
          className="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Go up one level"
        >
          <ArrowLeft className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
        </button>
        <div className="flex-1 px-3 py-1.5 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-600 rounded text-sm text-neutral-700 dark:text-neutral-300 font-mono truncate">
          {currentPath}
        </div>
      </div>

      {/* Folder List */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-accent-500" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-4">
              <AlertCircle className="w-8 h-8 text-error mx-auto mb-2" />
              <p className="text-sm text-error">{error}</p>
            </div>
          </div>
        ) : folders.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-neutral-500 dark:text-neutral-400">No folders in this directory</p>
          </div>
        ) : (
          <div className="space-y-1">
            {folders.map((folder) => (
              <div
                key={folder.path}
                className={`flex items-center gap-2 p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer transition-colors ${
                  selectedFolder === folder.path
                    ? 'bg-accent-100 dark:bg-accent-900/30 border border-accent-500'
                    : 'border border-transparent'
                } ${
                  !folder.is_accessible ? 'opacity-50' : ''
                }`}
                onClick={() => handleFolderSelect(folder)}
                onDoubleClick={() => handleFolderClick(folder)}
              >
                {folder.is_accessible ? (
                  <Folder className="w-4 h-4 text-accent-500 flex-shrink-0" />
                ) : (
                  <FolderOpen className="w-4 h-4 text-neutral-400 flex-shrink-0" />
                )}
                <span className="flex-1 text-sm text-neutral-700 dark:text-neutral-300 truncate">
                  {folder.name}
                </span>
                {folder.is_accessible && (
                  <ChevronRight className="w-4 h-4 text-neutral-400 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with current selection */}
      <div className="p-3 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Selected:</p>
            <p className="text-sm text-neutral-700 dark:text-neutral-300 font-mono truncate">
              {selectedFolder || currentPath}
            </p>
          </div>
          <button
            onClick={handleConfirmSelect}
            className="ml-3 px-4 py-2 bg-accent-500 text-white rounded-lg hover:bg-accent-600 transition-all active:scale-95 text-sm font-medium"
          >
            Select
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="px-3 pb-2">
        <p className="text-xs text-neutral-500 dark:text-neutral-400 text-center">
          Single click to select • Double click to open
        </p>
      </div>
    </div>
  );
};
