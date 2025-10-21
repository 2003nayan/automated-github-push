import axios from 'axios';

const API_BASE_URL = '/api';  // Using proxy

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const projectsApi = {
  getAll: () => api.get('/projects'),
  toggle: (projectId, enabled) =>
    api.post(`/projects/${projectId}/toggle`, { enabled }),
  backup: (projectId) =>
    api.post(`/projects/${projectId}/backup`),
  add: (folderPath, accountUsername) =>
    api.post('/projects/add', { folder_path: folderPath, account_username: accountUsername }),
  delete: (projectId, options) =>
    api.delete(`/projects/${projectId}/delete`, { data: options }),
};

export const statusApi = {
  get: () => api.get('/status'),
};

export const accountsApi = {
  getAll: () => api.get('/accounts'),
};

export const configApi = {
  get: () => api.get('/config'),
};

export const browseApi = {
  getFolders: (path) => api.get('/browse-folders', { params: { path } }),
};

export const settingsApi = {
  getBackupSchedule: () => api.get('/settings/backup-schedule'),
  updateBackupSchedule: (intervalHours) =>
    api.post('/settings/backup-schedule', { interval_hours: intervalHours }),
};

export default api;
