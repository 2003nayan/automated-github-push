import React from 'react';
import { Activity, CheckCircle, XCircle, Pause } from 'lucide-react';

export const StatusBar = ({ status }) => {
  if (!status) return null;

  const stats = [
    {
      icon: Activity,
      label: 'Service Status',
      value: status.daemon_running ? 'Running' : 'Stopped',
      count: null,
      color: status.daemon_running ? 'success' : 'danger',
    },
    {
      icon: CheckCircle,
      label: 'Active',
      value: status.enabled_projects,
      count: status.enabled_projects,
      color: 'neutral',
    },
    {
      icon: Pause,
      label: 'Paused',
      value: status.disabled_projects,
      count: status.disabled_projects,
      color: 'neutral',
    },
    {
      icon: CheckCircle,
      label: 'Total Backups',
      value: status.total_backups,
      count: status.total_backups,
      color: 'neutral',
    },
    {
      icon: XCircle,
      label: 'Failed',
      value: status.failed_backups,
      count: status.failed_backups,
      color: status.failed_backups > 0 ? 'danger' : 'neutral',
    },
  ];

  return (
    <div className="mb-8">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="minimal-card p-5 hover:border-neutral-300 group"
            >
              <div className="flex flex-col">
                {/* Icon and Label */}
                <div className="flex items-center gap-2 mb-3">
                  <div className={`p-1.5 rounded ${
                    stat.color === 'success' ? 'bg-success-light dark:bg-success-dark/20' :
                    stat.color === 'danger' ? 'bg-error-light dark:bg-error-dark/20' :
                    'bg-neutral-100 dark:bg-neutral-700'
                  }`}>
                    <Icon className={`w-4 h-4 ${
                      stat.color === 'success' ? 'text-success dark:text-success' :
                      stat.color === 'danger' ? 'text-error dark:text-error' :
                      'text-neutral-700 dark:text-neutral-300'
                    }`} />
                  </div>
                </div>

                {/* Label */}
                <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-1">
                  {stat.label}
                </p>

                {/* Value */}
                <p className="text-2xl font-semibold text-neutral-950 dark:text-neutral-50 tracking-tight">
                  {stat.value}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
