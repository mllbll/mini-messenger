import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth API
export const authAPI = {
  register: (userData) => apiClient.post('/api/users/register', userData),
  login: (userData) => apiClient.post('/api/users/login', userData),
};

// Chats API
export const chatsAPI = {
  getChats: () => apiClient.get('/api/chats/'),
  createChat: (name) => apiClient.post('/api/chats/', null, { params: { name } }),
};

// Messages API
export const messagesAPI = {
  getMessages: (chatId) => apiClient.get(`/api/messages/${chatId}`),
  sendMessage: (messageData) => apiClient.post('/api/messages/', messageData),
};

// WebSocket connection
export const createWebSocketConnection = (chatId) => {
  const wsUrl = `ws://localhost:8000/ws/chat/${chatId}`;
  return new WebSocket(wsUrl);
};

export default apiClient;
