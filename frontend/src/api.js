import axios from 'axios';

const API_URL = 'http://localhost:8000/api/filesharing';
const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2MDU4ODIwLCJpYXQiOjE3NDc0MTg4MjAsImp0aSI6Ijc2NWFmZTRlYWZlODQ4ZDRhMWQzZjMxNmJlZjc2ZmU2IiwidXNlcl9pZCI6MTJ9.m6HY5Ihcj1iClZB_dl8q5lq8Jq-Q8fPz0KlkX8C40L0';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Accept-Charset': 'utf-8',
    'Authorization': `Bearer ${TOKEN}`,
  },
});

export const getCollection = async (id) => {
  const response = await api.get(`/collections/${id}/client/`);
  return response.data;
};

export const updateCollection = async (id, name) => {
  const response = await api.patch(`/collections/${id}/`, { name });
  return response.data;
};

export const uploadPhoto = async (id, file) => {
  const formData = new FormData();
  formData.append('files', file);
  const response = await api.post(`/collections/${id}/photos/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const deletePhoto = async (collectionId, photoId) => {
  const response = await api.delete(`/collections/${collectionId}/photos/${photoId}/`);
  return response.data;
};

export default api;