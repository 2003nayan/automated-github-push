import React from 'react';
import { User, Folder } from 'lucide-react';
import { ProjectCard } from './ProjectCard';

export const AccountSection = ({ account, projects, onToggle, onBackup, onDelete }) => {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <div className="mb-12">
      {/* Account Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 bg-gradient-to-br from-accent-100 to-accent-200 dark:from-accent-900/30 dark:to-accent-800/30 rounded-lg flex items-center justify-center">
            <User className="w-4 h-4 text-accent-700 dark:text-accent-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-neutral-950 dark:text-neutral-50">
              {account.name || account.username}
            </h2>
            <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
              <Folder className="w-3 h-3" />
              <span className="font-mono">{account.path}</span>
              <span className="text-neutral-300 dark:text-neutral-600">•</span>
              <span>{projects.length} {projects.length === 1 ? 'project' : 'projects'}</span>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="divider" />
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map(project => (
          <ProjectCard
            key={project.id}
            project={project}
            onToggle={onToggle}
            onBackup={onBackup}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  );
};
