import React, { useState, useRef, useCallback } from 'react';
import { ContractType, ContractRequirementsResponse, ContractUploadDetail, DocumentStatus, DocumentRequirement } from '../../types/contract';
import { uploadDocument, getContractUploadDetail } from '../../services/contractApi';
import './DocumentUploadPanel.css';

interface DocumentUploadPanelProps {
  contractType: ContractType;
  requirements: ContractRequirementsResponse;
  contractUploadId: string;
  onUploadComplete: () => void;
  contractDetail: ContractUploadDetail | null;
}

interface UploadProgress {
  [documentType: string]: {
    progress: number;
    uploading: boolean;
    error?: string;
  };
}

export const DocumentUploadPanel: React.FC<DocumentUploadPanelProps> = ({
  contractType,
  requirements,
  contractUploadId,
  onUploadComplete,
  contractDetail
}) => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [dragOverDocument, setDragOverDocument] = useState<string | null>(null);
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({});

  // ドキュメントステータス取得
  const getDocumentStatus = (documentType: string): DocumentStatus | null => {
    if (!contractDetail) return null;
    return contractDetail.document_statuses.find(d => d.document_type === documentType) || null;
  };

  // ファイル検証
  const validateFile = (file: File, requirement: DocumentRequirement): string | null => {
    // ファイルサイズチェック
    const maxSizeBytes = requirement.max_size_mb * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return `ファイルサイズが上限（${requirement.max_size_mb}MB）を超えています`;
    }

    // ファイル形式チェック
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!requirement.allowed_formats.includes(fileExtension)) {
      return `対応していないファイル形式です（対応形式: ${requirement.allowed_formats.join(', ')}）`;
    }

    return null;
  };

  // ファイルアップロード処理
  const handleFileUpload = async (file: File, documentType: string, requirement: DocumentRequirement) => {
    // バリデーション
    const validationError = validateFile(file, requirement);
    if (validationError) {
      setUploadProgress(prev => ({
        ...prev,
        [documentType]: {
          progress: 0,
          uploading: false,
          error: validationError
        }
      }));
      return;
    }

    // アップロード開始
    setUploadProgress(prev => ({
      ...prev,
      [documentType]: {
        progress: 0,
        uploading: true,
        error: undefined
      }
    }));

    try {
      // ファイル読み込み
      const fileBuffer = await file.arrayBuffer();
      const fileData = new Uint8Array(fileBuffer);

      // プログレス更新（シミュレーション）
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const current = prev[documentType]?.progress || 0;
          if (current < 90) {
            return {
              ...prev,
              [documentType]: {
                ...prev[documentType],
                progress: current + 10
              }
            };
          }
          return prev;
        });
      }, 200);

      // API呼び出し
      const response = await uploadDocument(
        contractUploadId,
        documentType,
        fileData,
        file.name,
        file.type
      );

      clearInterval(progressInterval);

      // 完了状態に更新
      setUploadProgress(prev => ({
        ...prev,
        [documentType]: {
          progress: 100,
          uploading: false,
          error: undefined
        }
      }));

      // 親コンポーネントに通知
      onUploadComplete();

    } catch (error) {
      setUploadProgress(prev => ({
        ...prev,
        [documentType]: {
          progress: 0,
          uploading: false,
          error: error instanceof Error ? error.message : 'アップロードに失敗しました'
        }
      }));
    }
  };

  // ドラッグ&ドロップ処理
  const handleDragOver = useCallback((e: React.DragEvent, documentType: string) => {
    e.preventDefault();
    setDragOverDocument(documentType);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOverDocument(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, documentType: string, requirement: DocumentRequirement) => {
    e.preventDefault();
    setDragOverDocument(null);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0], documentType, requirement);
    }
  }, [contractUploadId, onUploadComplete]);

  // ファイル選択処理
  const handleFileSelect = (documentType: string, requirement: DocumentRequirement) => {
    const input = fileInputRefs.current[documentType];
    if (input && input.files && input.files[0]) {
      handleFileUpload(input.files[0], documentType, requirement);
    }
  };

  // ステータスアイコン
  const getStatusIcon = (documentType: string): string => {
    const status = getDocumentStatus(documentType);
    const progress = uploadProgress[documentType];

    if (progress?.uploading) return '⏳';
    if (progress?.error) return '❌';
    if (status?.uploaded) {
      switch (status.status) {
        case 'APPROVED': return '✅';
        case 'REJECTED': return '🔴';
        case 'PENDING': return '🟡';
        case 'EXPIRED': return '⏰';
        default: return '📄';
      }
    }
    return '⭕';
  };

  // ステータステキスト
  const getStatusText = (documentType: string): string => {
    const status = getDocumentStatus(documentType);
    const progress = uploadProgress[documentType];

    if (progress?.uploading) return `アップロード中... ${progress.progress}%`;
    if (progress?.error) return progress.error;
    if (status?.uploaded) {
      switch (status.status) {
        case 'APPROVED': return '承認済み';
        case 'REJECTED': return '差し戻し - 再アップロードが必要';
        case 'PENDING': return '審査中';
        case 'EXPIRED': return '期限切れ - 再アップロードが必要';
        default: return 'アップロード済み';
      }
    }
    return 'アップロードが必要';
  };

  return (
    <div className="document-upload-panel">
      <div className="panel-header">
        <h2>
          {contractType === ContractType.INDIVIDUAL ? '個人契約者' : '法人契約者'}
          必要書類アップロード
        </h2>
        <div className="progress-summary">
          <span>進捗: {contractDetail?.completion_rate || 0}%</span>
          <div className="progress-bar-mini">
            <div 
              className="progress-fill-mini" 
              style={{ width: `${contractDetail?.completion_rate || 0}%` }}
            />
          </div>
        </div>
      </div>

      <div className="document-categories">
        {requirements.categories.map((category, categoryIndex) => (
          <div key={categoryIndex} className="document-category">
            <h3 className="category-title">{category.category_name}</h3>
            <div className="category-documents">
              {category.requirements.map((requirement, reqIndex) => {
                const documentType = requirement.document_type;
                const status = getDocumentStatus(documentType);
                const progress = uploadProgress[documentType];
                const isDragOver = dragOverDocument === documentType;
                const canReupload = status?.status === 'REJECTED' || status?.status === 'EXPIRED';

                return (
                  <div 
                    key={reqIndex} 
                    className={`document-item ${isDragOver ? 'drag-over' : ''} ${status?.uploaded ? 'uploaded' : ''}`}
                  >
                    <div className="document-info">
                      <div className="document-header">
                        <span className="status-icon">{getStatusIcon(documentType)}</span>
                        <h4 className="document-name">{requirement.display_name}</h4>
                        <span className={`status-badge ${status?.status?.toLowerCase() || 'pending'}`}>
                          {getStatusText(documentType)}
                        </span>
                      </div>
                      <p className="document-description">{requirement.description}</p>
                      <div className="document-requirements">
                        <span>対応形式: {requirement.allowed_formats.join(', ')}</span>
                        <span>最大サイズ: {requirement.max_size_mb}MB</span>
                      </div>
                    </div>

                    {(!status?.uploaded || canReupload) && !progress?.uploading && (
                      <div 
                        className="upload-zone"
                        onDragOver={(e) => handleDragOver(e, documentType)}
                        onDragLeave={handleDragLeave}
                        onDrop={(e) => handleDrop(e, documentType, requirement)}
                      >
                        <div className="upload-content">
                          <span className="upload-icon">📤</span>
                          <p>ファイルをドラッグ&ドロップ<br />または</p>
                          <button 
                            className="btn-upload"
                            onClick={() => fileInputRefs.current[documentType]?.click()}
                          >
                            ファイルを選択
                          </button>
                          <input
                            ref={(el) => fileInputRefs.current[documentType] = el}
                            type="file"
                            accept={requirement.allowed_formats.join(',')}
                            style={{ display: 'none' }}
                            onChange={() => handleFileSelect(documentType, requirement)}
                          />
                        </div>
                      </div>
                    )}

                    {progress?.uploading && (
                      <div className="upload-progress">
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{ width: `${progress.progress}%` }}
                          />
                        </div>
                        <span>{progress.progress}%</span>
                      </div>
                    )}

                    {status?.uploaded && (
                      <div className="uploaded-info">
                        <p>📄 {status.filename}</p>
                        <p>アップロード日時: {new Date(status.uploaded_at).toLocaleString()}</p>
                        {status.admin_comment && (
                          <div className="admin-comment">
                            <strong>管理者コメント:</strong>
                            <p>{status.admin_comment}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {contractDetail && contractDetail.completion_rate >= 100 && (
        <div className="completion-notice">
          <div className="notice-icon">🎉</div>
          <div className="notice-content">
            <h3>すべての書類のアップロードが完了しました！</h3>
            <p>管理者による審査を開始いたします。結果はメールでお知らせします。</p>
          </div>
        </div>
      )}
    </div>
  );
};