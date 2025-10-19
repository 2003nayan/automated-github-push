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

export default api;
