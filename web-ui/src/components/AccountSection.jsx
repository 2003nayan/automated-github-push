import React from 'react';
import { User, Folder } from 'lucide-react';
import { ProjectCard } from './ProjectCard';

export const AccountSection = ({ account, projects, onToggle, onBackup }) => {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <div className="mb-8">
      {/* Account Header */}
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200 dark:border-dark-border">
        <User className="w-6 h-6 text-primary-500" />
        <div>
          <h2 className="text-xl font-bold">{account.name || account.username}</h2>
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Folder className="w-4 h-4" />
            <span>{account.path}</span>
            <span className="mx-2">•</span>
            <span>{projects.length} projects</span>
          </div>
        </div>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map(project => (
          <ProjectCard
            key={project.id}
            project={project}
            onToggle={onToggle}
            onBackup={onBackup}
          />
        ))}
      </div>
    </div>
  );
};
