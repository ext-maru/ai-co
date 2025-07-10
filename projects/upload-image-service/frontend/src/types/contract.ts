// 契約タイプ
export enum ContractType {
  INDIVIDUAL = 'individual',
  CORPORATE = 'corporate'
}

// 書類タイプ
export enum DocumentType {
  // 共通
  APPLICATION_FORM = 'application_form',
  
  // 個人契約者用
  RESIDENT_CARD = 'resident_card',
  SEAL_CERTIFICATE = 'seal_certificate',
  TAX_RETURN = 'tax_return',
  DRIVERS_LICENSE = 'drivers_license',
  BANK_BOOK = 'bank_book',
  
  // 法人契約者用
  CORPORATE_REGISTRY = 'corporate_registry',
  CORPORATE_SEAL_CERT = 'corporate_seal_cert',
  FINANCIAL_STATEMENT = 'financial_statement',
  BALANCE_SHEET = 'balance_sheet',
  INCOME_STATEMENT = 'income_statement',
  EQUITY_STATEMENT = 'equity_statement',
  
  // 代表者用（法人の場合）
  REP_RESIDENT_CARD = 'rep_resident_card',
  REP_SEAL_CERTIFICATE = 'rep_seal_certificate',
  REP_TAX_RETURN = 'rep_tax_return',
  REP_DRIVERS_LICENSE = 'rep_drivers_license'
}

// アップロードステータス
export enum UploadStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired'
}

// 書類要件
export interface DocumentRequirement {
  document_type: string;
  display_name: string;
  description: string;
  required: boolean;
  max_files: number;
  allowed_formats: string[];
  max_size_mb: number;
  expiry_days: number;
}

// 書類カテゴリ
export interface DocumentCategory {
  name: string;
  documents: DocumentRequirement[];
}

// 契約要件レスポンス
export interface ContractRequirementsResponse {
  contract_type: ContractType;
  categories: DocumentCategory[];
}

// 書類アップロード状況
export interface DocumentUploadStatus {
  document_type: DocumentType;
  display_name: string;
  description: string;
  required: boolean;
  uploaded: boolean;
  file_count: number;
  max_files: number;
  files: UploadedFile[];
  status: UploadStatus;
  expiry_date?: string;
  allowed_formats: string[];
  max_size_mb: number;
}

// アップロード済みファイル
export interface UploadedFile {
  id: string;
  filename: string;
  size: number;
  uploaded_at: string;
  status: string;
  thumbnail_url?: string;
}

// 契約アップロード作成
export interface ContractUploadCreate {
  contract_type: ContractType;
  metadata?: Record<string, any>;
}

// 契約アップロードレスポンス
export interface ContractUploadResponse {
  id: string;
  user_id: string;
  contract_type: ContractType;
  status: UploadStatus;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_notes?: string;
  metadata: Record<string, any>;
}

// 契約アップロード詳細
export interface ContractUploadDetail extends ContractUploadResponse {
  document_statuses: DocumentUploadStatus[];
  completion_rate: number;
  missing_documents: string[];
  expired_documents: string[];
}

// ファイルアップロードレスポンス
export interface FileUploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  size: number;
  content_type: string;
  document_type: DocumentType;
  status: UploadStatus;
  created_at: string;
  thumbnail_url?: string;
}