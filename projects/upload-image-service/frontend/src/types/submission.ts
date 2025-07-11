// 提出セッション関連の型定義

export enum SubmissionType {
  INDIVIDUAL = 'individual',
  CORPORATE = 'corporate',
  CUSTOM = 'custom'
}

export enum SessionStatus {
  CREATED = 'created',
  SENT = 'sent',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

export interface SubmissionSessionCreate {
  submitter_name: string;
  submitter_email?: string;
  submitter_phone?: string;
  submitter_organization?: string;
  
  submission_type: SubmissionType;
  title: string;
  description?: string;
  admin_notes?: string;
  
  due_date?: string;
  max_file_size_mb?: number;
  allowed_file_types?: string;
  
  access_password?: string;
  access_ip_whitelist?: string;
}

export interface SubmissionSessionResponse {
  id: string;
  session_url_key: string;
  submission_url: string;
  
  creator_admin_id: string;
  creator_admin_name: string;
  
  submitter_name: string;
  submitter_email?: string;
  submitter_phone?: string;
  submitter_organization?: string;
  
  submission_type: SubmissionType;
  title: string;
  description?: string;
  admin_notes?: string;
  
  due_date?: string;
  max_file_size_mb: string;
  allowed_file_types: string;
  
  status: SessionStatus;
  is_active: boolean;
  
  created_at: string;
  updated_at: string;
  sent_at?: string;
  first_access_at?: string;
  completed_at?: string;
  
  is_expired: boolean;
  days_until_due: number;
  upload_count: number;
}

export interface SubmissionUploadResponse {
  id: string;
  session_id: string;
  
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: string;
  thumbnail_path?: string;
  
  document_category?: string;
  submitter_comment?: string;
  
  admin_status: string;
  admin_comment?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  
  uploaded_at: string;
}
export interface SubmissionSessionDetail extends SubmissionSessionResponse {
  uploads: SubmissionUploadResponse[];
  
  total_file_size: string;
  completion_percentage: number;
}

export interface SubmissionStatistics {
  total_sessions: number;
  active_sessions: number;
  completed_sessions: number;
  expired_sessions: number;
  
  total_uploads: number;
  pending_reviews: number;
  approved_files: number;
  rejected_files: number;
  
  avg_completion_time_hours: number;
  total_file_size_gb: number;
  
  monthly_stats: Array<{[key: string]: any}>;
  type_stats: {[key: string]: number};
}

export interface SessionStatusUpdate {
  status: SessionStatus;
  admin_notes?: string;
}

export interface FileReviewUpdate {
  admin_status: string;
  admin_comment?: string;
}

export interface SessionMessageCreate {
  message_content: string;
  attachment_file_id?: string;
}