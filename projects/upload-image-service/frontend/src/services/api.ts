import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター（認証トークン追加）
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター（エラー処理）
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // トークン期限切れ - 再ログイン
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ファイルアップロード
export const uploadFiles = async (
  files: File[],
  onProgress?: (progress: { fileId: string; percent: number }) => void
) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await api.post('/api/v1/upload/multiple', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress({ fileId: files[0].name, percent });
      }
    },
  });

  return response.data;
};

// アップロード一覧取得
export const getUploads = async (params?: { status?: string; skip?: number; limit?: number }) => {
  const response = await api.get('/api/v1/upload/list', { params });
  return response.data;
};

// アップロードステータス更新
export const updateUploadStatus = async (uploadId: string, status: 'approved' | 'rejected') => {
  const response = await api.patch(`/api/v1/upload/${uploadId}/status`, { status });
  return response.data;
};

// ログイン
export const login = async (username: string, password: string) => {
  const response = await api.post('/api/v1/auth/token', {
    username,
    password,
  });

  const { access_token, token_type } = response.data;
  localStorage.setItem('access_token', access_token);

  return response.data;
};

// ログアウト
export const logout = () => {
  localStorage.removeItem('access_token');
  window.location.href = '/login';
};

// 現在のユーザー情報取得
export const getCurrentUser = async () => {
  const response = await api.get('/api/v1/auth/me');
  return response.data;
};

export default api;
