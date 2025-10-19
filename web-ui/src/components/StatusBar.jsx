import React from 'react';
import { Activity, CheckCircle, XCircle, Pause } from 'lucide-react';

export const StatusBar = ({ status }) => {
  if (!status) return null;

  return (
    <div className="bg-white dark:bg-dark-card rounded-lg shadow-md p-6 mb-6 border border-gray-200 dark:border-dark-border">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Daemon Status */}
        <div className="flex items-center gap-3">
          <Activity className={`w-8 h-8 ${status.daemon_running ? 'text-green-500' : 'text-red-500'}`} />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Daemon</p>
            <p className="text-lg font-semibold">
              {status.daemon_running ? 'Running' : 'Stopped'}
            </p>
          </div>
        </div>

        {/* Enabled Projects */}
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-green-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Enabled</p>
            <p className="text-lg font-semibold">{status.enabled_projects}</p>
          </div>
        </div>

        {/* Disabled Projects */}
        <div className="flex items-center gap-3">
          <Pause className="w-8 h-8 text-gray-400" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Disabled</p>
            <p className="text-lg font-semibold">{status.disabled_projects}</p>
          </div>
        </div>

        {/* Successful Backups */}
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-blue-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Successful</p>
            <p className="text-lg font-semibold">{status.total_backups}</p>
          </div>
        </div>

        {/* Failed Backups */}
        <div className="flex items-center gap-3">
          <XCircle className="w-8 h-8 text-red-500" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
            <p className="text-lg font-semibold">{status.failed_backups}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
