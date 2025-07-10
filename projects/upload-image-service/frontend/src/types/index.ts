// アップロード関連の型定義
export interface Upload {
  id: string;
  filename: string;
  size: number;
  contentType: string;
  status: UploadStatus;
  uploadedAt: string;
  userId: string;
  thumbnailUrl?: string;
  cloudUrl?: string;
  approvalNotes?: string;
  approvedBy?: string;
  approvedAt?: string;
}

export type UploadStatus = 'pending' | 'approved' | 'rejected';

export interface UploadResponse {
  fileId: string;
  filename: string;
  size: number;
  status: string;
  thumbnailUrl?: string;
}

// ユーザー関連の型定義
export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  createdAt: string;
}

export type UserRole = 'admin' | 'user' | 'guest';

// 認証関連の型定義
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// API共通の型定義
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// エラー型定義
export interface ApiError {
  message: string;
  detail?: string;
  status: number;
}
