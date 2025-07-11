import axios from 'axios';
import {
  ContractType,
  DocumentType,
  ContractRequirementsResponse,
  ContractUploadCreate,
  ContractUploadResponse,
  ContractUploadDetail,
  FileUploadResponse,
  UploadStatus
} from '../types/contract';

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

// 契約タイプ別の必要書類取得
export const getContractRequirements = async (
  contractType: ContractType
): Promise<ContractRequirementsResponse> => {
  const response = await api.get(`/api/v1/contract/requirements/${contractType}`);
  return response.data;
};

// 契約アップロードセッション作成
export const createContractUpload = async (
  data: ContractUploadCreate
): Promise<ContractUploadResponse> => {
  const response = await api.post('/api/v1/contract/', data);
  return response.data;
};

// 契約アップロード詳細取得
export const getContractUploadDetail = async (
  contractUploadId: string
): Promise<ContractUploadDetail> => {
  const response = await api.get(`/api/v1/contract/${contractUploadId}`);
  return response.data;
};

// 書類ファイルアップロード
export const uploadContractDocument = async (
  contractUploadId: string,
  documentType: DocumentType,
  file: File,
  onProgress?: (percent: number) => void
): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const response = await api.post(
    `/api/v1/contract/${contractUploadId}/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    }
  );

  return response.data;
};

// 契約書類提出
export const submitContractUpload = async (
  contractUploadId: string
): Promise<ContractUploadResponse> => {
  const response = await api.post(`/api/v1/contract/${contractUploadId}/submit`);
  return response.data;
};

// 契約アップロード一覧取得
export const listContractUploads = async (params?: {
  status?: UploadStatus;
  skip?: number;
  limit?: number;
}) => {
  const response = await api.get('/api/v1/contract/', { params });
  return response.data;
};

// 管理者用：全契約アップロード一覧取得
export const listAllContractUploads = async (params?: {
  status?: UploadStatus;
  skip?: number;
  limit?: number;
}) => {
  const response = await api.get('/api/v1/contract/admin/list', { params });
  return response.data;
};

// 管理者用：契約アップロード詳細取得
export const getContractUploadDetailAdmin = async (
  contractUploadId: string
): Promise<ContractUploadDetail> => {
  const response = await api.get(`/api/v1/contract/admin/${contractUploadId}`);
  return response.data;
};

// 管理者用：契約書類レビュー
export const reviewContractUpload = async (
  contractUploadId: string,
  action: 'approve' | 'reject',
  notes?: string,
  documentNotes?: Record<string, string>
) => {
  const response = await api.post(`/api/v1/contract/admin/${contractUploadId}/review`, {
    action,
    notes,
    document_notes: documentNotes
  });
  return response.data;
};

// 作業中案件一括取得（管理者用）
export const getPendingContracts = async (params?: {
  skip?: number;
  limit?: number;
}) => {
  const response = await api.get('/api/v1/contract/admin/pending', { params });
  return response.data;
};

// 契約ステータス更新（簡易版）
export const updateContractStatus = async (
  contractUploadId: string,
  status: UploadStatus,
  adminNotes?: string
) => {
  const response = await api.patch(`/api/v1/contract/admin/${contractUploadId}/status`, {
    status,
    admin_notes: adminNotes
  });
  return response.data;
};

export default {
  getContractRequirements,
  createContractUpload,
  getContractUploadDetail,
  uploadContractDocument,
  submitContractUpload,
  listContractUploads,
  listAllContractUploads,
  getContractUploadDetailAdmin,
  reviewContractUpload,
  getPendingContracts,
  updateContractStatus
};
