import React from 'react';
import { User, Folder } from 'lucide-react';
import { ProjectCard } from './ProjectCard';

export const AccountSection = ({ account, projects, onToggle, onBackup, onDelete }) => {
  return (
    <div className="animate-fade-in">
      {/* Account Info */}
      <div className="mb-6 flex items-center gap-3 text-sm text-neutral-600 dark:text-neutral-400">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4" />
          <span className="font-medium">{account.username}</span>
        </div>
        {/* <span className="text-neutral-300 dark:text-neutral-600">•</span>
        <div className="flex items-center gap-2">
          <Folder className="w-4 h-4" />
          <span className="font-mono">{account.path}</span>
        </div> */}
        <span className="text-neutral-300 dark:text-neutral-600">•</span>
        <span>{projects.length} {projects.length === 1 ? 'project' : 'projects'}</span>
      </div>

      {/* Project Grid or Empty State */}
      {projects.length > 0 ? (
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
      ) : (
        <div className="text-center py-20 bg-neutral-50 dark:bg-neutral-850 rounded-2xl border border-neutral-200 dark:border-neutral-700">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-neutral-100 dark:bg-neutral-800 rounded-xl mb-3">
            <Folder className="w-6 h-6 text-neutral-400 dark:text-neutral-500" />
          </div>
          <h3 className="text-base font-semibold text-neutral-950 dark:text-neutral-50 mb-1">
            No projects yet
          </h3>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            Create a project in <span className="font-mono text-xs">{account.path}</span> to start syncing
          </p>
        </div>
      )}
    </div>
  );
};
