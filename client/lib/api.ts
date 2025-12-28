import axios from 'axios';

// Use Next.js API routes instead of calling backend directly
// This avoids CORS issues and keeps backend URL secure
const api = axios.create({
  baseURL: '', // Same origin - uses Next.js API routes
});

// Helper for file uploads (important for images!)
export const createIssue = async (formData: FormData) => {
  const response = await api.post('/api/issues', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getIssues = async () => {
  const response = await api.get('/api/issues');
  return response.data;
};

export const getIssue = async (id: number) => {
  const response = await api.get(`/api/issues/${id}`);
  return response.data;
};

export const searchSimilarIssues = async (id: number, limit: number = 5) => {
  const response = await api.get(`/api/issues/${id}/similar?limit=${limit}`);
  return response.data;
};

export const updateIssueStatus = async (id: number, status: string) => {
  const response = await api.patch(`/api/issues/${id}/status`, { status });
  return response.data;
};

// For image URLs, we still need to use the backend directly
// since images are served as static files
export const getImageUrl = (imagePath: string) => {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  return `${backendUrl}/${imagePath}`;
};

export default api;
