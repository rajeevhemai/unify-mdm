import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Dashboard ---
export const getDashboardStats = () => api.get('/dashboard/stats');

// --- Data Sources ---
export const uploadFile = (file, name) => {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  return api.post('/sources/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const listSources = () => api.get('/sources/');
export const getSource = (id) => api.get(`/sources/${id}`);
export const deleteSource = (id) => api.delete(`/sources/${id}`);
export const previewFile = (id) => api.get(`/sources/${id}/preview`);
export const getAutoMapping = (id) => api.get(`/sources/${id}/auto-map`);
export const importRecords = (sourceId, mapping) =>
  api.post(`/sources/${sourceId}/import`, { source_id: sourceId, mapping });
export const getSourceRecords = (id, skip = 0, limit = 50) =>
  api.get(`/sources/${id}/records?skip=${skip}&limit=${limit}`);

// --- Matching ---
export const runMatching = (sourceId, threshold = 0.75) =>
  api.post(`/matches/run?source_id=${sourceId || ''}`, { threshold });
export const listMatches = (status, skip = 0, limit = 50) => {
  let url = `/matches/?skip=${skip}&limit=${limit}`;
  if (status) url += `&status=${status}`;
  return api.get(url);
};
export const getMatch = (id) => api.get(`/matches/${id}`);
export const reviewMatch = (id, status, notes) =>
  api.put(`/matches/${id}/review`, { status, notes });
export const getMatchStats = () => api.get('/matches/stats');

// --- Golden Records ---
export const listGoldenRecords = (skip = 0, limit = 50, search = '') => {
  let url = `/golden-records/?skip=${skip}&limit=${limit}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  return api.get(url);
};
export const getGoldenRecord = (id) => api.get(`/golden-records/${id}`);
export const mergeRecords = (matchId, survivingValues) =>
  api.post('/golden-records/merge', { match_id: matchId, surviving_values: survivingValues });
export const exportGoldenRecords = () =>
  api.get('/golden-records/export', { responseType: 'blob' });
export const promoteUnmatched = () => api.post('/golden-records/promote-unmatched');
export const getGoldenRecordCount = () => api.get('/golden-records/count');

export default api;
