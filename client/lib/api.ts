import axios from 'axios';

// Use Next.js API routes instead of calling backend directly
// This avoids CORS issues and keeps backend URL secure
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '', // Same origin - uses Next.js API routes
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

// For image URLs - now supports both Cloudinary (full URL) and legacy local paths
export const getImageUrl = (imagePath: string) => {
  // If it's already a full URL (Cloudinary), return as-is
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  // Legacy support for local uploads
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  return `${backendUrl}/${imagePath}`;
};

export default api;
