import React, { useState, useEffect } from 'react';
import { X, Settings, Clock, Loader2, CheckCircle } from 'lucide-react';
import { settingsApi } from '../services/api';

export const SettingsModal = ({ onClose }) => {
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [intervalHours, setIntervalHours] = useState(6);
  const [timeUntilNext, setTimeUntilNext] = useState('');
  const [nextBackupTime, setNextBackupTime] = useState('');
  const [lastBackupFormatted, setLastBackupFormatted] = useState('');

  useEffect(() => {
    fetchSchedule();
  }, []);

  // Update countdown and last backup time every second
  useEffect(() => {
    if (!schedule) return;

    const updateTimes = () => {
      const now = new Date();

      // Update next backup countdown
      if (schedule.next_backup_time) {
        const nextBackup = new Date(schedule.next_backup_time);
        const diff = nextBackup - now;

        if (diff <= 0) {
          setTimeUntilNext('Backup running or overdue');
        } else {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);

          if (hours > 0) {
            setTimeUntilNext(`${hours}h ${minutes}m`);
          } else if (minutes > 0) {
            setTimeUntilNext(`${minutes}m ${seconds}s`);
          } else {
            setTimeUntilNext(`${seconds}s`);
          }
        }

        // Format absolute time
        const timeStr = nextBackup.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
        setNextBackupTime(timeStr);
      }

      // Update last backup time (real-time)
      if (schedule.last_backup_time) {
        const lastBackup = new Date(schedule.last_backup_time);
        const diffMs = now - lastBackup;

        const minutes = Math.floor(diffMs / (1000 * 60));
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        const timeStr = lastBackup.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });

        let agoStr = '';
        if (days > 0) {
          agoStr = `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (hours > 0) {
          agoStr = `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (minutes > 0) {
          agoStr = `${minutes} min${minutes > 1 ? 's' : ''} ago`;
        } else {
          agoStr = 'just now';
        }

        setLastBackupFormatted(`${timeStr} (${agoStr})`);
      } else {
        setLastBackupFormatted('Never');
      }
    };

    updateTimes();
    const interval = setInterval(updateTimes, 1000);

    return () => clearInterval(interval);
  }, [schedule]);

  const fetchSchedule = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await settingsApi.getBackupSchedule();
      setSchedule(response.data);
      setIntervalHours(response.data.interval_hours);
    } catch (err) {
      setError('Failed to load backup schedule');
      console.error('Error fetching schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      await settingsApi.updateBackupSchedule(intervalHours);

      setSuccess('Backup schedule updated successfully!');

      // Refresh schedule data
      await fetchSchedule();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update backup schedule');
      console.error('Error updating schedule:', err);
    } finally {
      setSaving(false);
    }
  };

  const commonIntervals = [
    { label: 'Every hour', value: 1 },
    { label: 'Every 2 hours', value: 2 },
    { label: 'Every 3 hours', value: 3 },
    { label: 'Every 6 hours', value: 6 },
    { label: 'Every 12 hours', value: 12 },
    { label: 'Every 24 hours', value: 24 },
    { label: 'Custom', value: 'custom' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-2xl w-full animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-neutral-950 dark:text-neutral-50">
              Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
          >
            <X className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Backup Schedule Section */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="w-5 h-5 text-accent-500" />
                  <h3 className="text-lg font-semibold text-neutral-950 dark:text-neutral-50">
                    Backup Schedule
                  </h3>
                </div>

                <div className="bg-neutral-50 dark:bg-neutral-900 rounded-lg p-5 space-y-4 border border-neutral-200 dark:border-neutral-700">
                  {/* Interval Selection */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      Backup Interval
                    </label>
                    <select
                      value={
                        commonIntervals.find(i => i.value === intervalHours)
                          ? intervalHours
                          : 'custom'
                      }
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value !== 'custom') {
                          setIntervalHours(Number(value));
                        }
                      }}
                      className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent transition-all cursor-pointer"
                    >
                      {commonIntervals.map((interval) => (
                        <option key={interval.value} value={interval.value}>
                          {interval.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Custom Interval Input */}
                  {!commonIntervals.find(i => i.value === intervalHours && i.value !== 'custom') && (
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                        Custom Interval (hours)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="168"
                        value={intervalHours}
                        onChange={(e) => setIntervalHours(Number(e.target.value))}
                        className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded-lg text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent transition-all"
                      />
                      <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
                        Between 1 and 168 hours (7 days)
                      </p>
                    </div>
                  )}

                  {/* Next Backup Info */}
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 border border-neutral-200 dark:border-neutral-700">
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Next Backup</p>
                      {schedule?.next_backup_time ? (
                        <>
                          <p className="text-lg font-semibold text-accent-600 dark:text-accent-400">
                            {timeUntilNext}
                          </p>
                          <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                            at {nextBackupTime}
                          </p>
                        </>
                      ) : (
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                          Not scheduled
                        </p>
                      )}
                    </div>

                    <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 border border-neutral-200 dark:border-neutral-700">
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Last Push to GitHub</p>
                      <p className="text-sm text-neutral-700 dark:text-neutral-300 font-medium">
                        {lastBackupFormatted || 'Never'}
                      </p>
                    </div>
                  </div>

                  {/* Auto Backup Status */}
                  <div className="flex items-center gap-2 pt-2">
                    <div className={`w-2 h-2 rounded-full ${schedule?.auto_backup_enabled ? 'bg-success' : 'bg-danger'}`} />
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">
                      Automatic backups {schedule?.auto_backup_enabled ? 'enabled' : 'disabled'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Error/Success Messages */}
              {error && (
                <div className="p-3 bg-error-light dark:bg-error-dark/20 border border-error/20 dark:border-error/30 rounded-lg">
                  <p className="text-sm text-error-dark dark:text-error">{error}</p>
                </div>
              )}

              {success && (
                <div className="p-3 bg-success-light dark:bg-success-dark/20 border border-success/20 dark:border-success/30 rounded-lg flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-success-dark dark:text-success" />
                  <p className="text-sm text-success-dark dark:text-success">{success}</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-600 font-medium transition-all active:scale-95"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving || intervalHours === schedule?.interval_hours}
                  className="flex-1 px-4 py-2.5 bg-accent-500 text-white rounded-lg hover:bg-accent-600 font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
