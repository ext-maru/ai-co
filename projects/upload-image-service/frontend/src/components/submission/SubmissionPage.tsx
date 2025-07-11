import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { SubmissionSessionDetail, SubmissionType } from '../../types/submission';
import './SubmissionPage.css';

export const SubmissionPage: React.FC = () => {
  const { urlKey } = useParams<{ urlKey: string }>();
  const [session, setSession] = useState<SubmissionSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (urlKey) {
      fetchSession();
    }
  }, [urlKey]);

  const fetchSession = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/submission/submit/${urlKey}`);
      if (response.ok) {
        const data = await response.json();
        setSession(data);
      } else if (response.status === 404) {
        setError('このURLは無効です。管理者にお問い合わせください。');
      } else {
        setError('セッション情報の取得に失敗しました。');
      }
    } catch (error) {
      setError('ネットワークエラーが発生しました。');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !session) return;

    // ファイルサイズチェック
    const maxSizeMB = parseInt(session.max_file_size_mb);
    if (file.size > maxSizeMB * 1024 * 1024) {
      alert(`ファイルサイズが${maxSizeMB}MBを超えています。`);
      return;
    }

    // ファイルタイプチェック
    const allowedTypes = session.allowed_file_types.split(',');
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      alert(`許可されていないファイル形式です。\n許可形式: ${session.allowed_file_types}`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_category', getDocumentCategory());

    try {
      const response = await fetch(`http://localhost:8000/api/v1/submission/submit/${urlKey}/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        alert('ファイルが正常にアップロードされました。');
        fetchSession(); // リロード
      } else {
        const error = await response.json();
        alert(`アップロードエラー: ${error.detail || 'アップロードに失敗しました'}`);
      }
    } catch (error) {
      alert('ネットワークエラーが発生しました。');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const getDocumentCategory = () => {
    if (!session) return '';
    
    return session.submission_type === SubmissionType.INDIVIDUAL ? '個人書類' : '法人書類';
  };

  if (loading) {
    return (
      <div className="submission-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="submission-container">
        <div className="error-box">
          <h2>エラー</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (session.status === 'completed') {
    return (
      <div className="submission-container">
        <div className="completion-box">
          <div className="completion-icon">✅</div>
          <h2>提出完了</h2>
          <p>すべての書類の提出が完了しました。</p>
          <p>ご協力ありがとうございました。</p>
        </div>
      </div>
    );
  }

  if (session.status === 'expired' || session.is_expired) {
    return (
      <div className="submission-container">
        <div className="error-box">
          <h2>期限切れ</h2>
          <p>この提出セッションは期限切れです。</p>
          <p>管理者にお問い合わせください。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="submission-container">
      <div className="submission-header">
        <h1>{session.title}</h1>
        <div className="submission-info">
          <div className="info-item">
            <label>提出者</label>
            <span>{session.submitter_name}</span>
          </div>
          {session.submitter_organization && (
            <div className="info-item">
              <label>所属</label>
              <span>{session.submitter_organization}</span>
            </div>
          )}
          {session.due_date && (
            <div className="info-item">
              <label>提出期限</label>
              <span>{new Date(session.due_date).toLocaleString('ja-JP')}</span>
            </div>
          )}
        </div>
      </div>

      {session.description && (
        <div className="submission-description">
          <h3>説明</h3>
          <p>{session.description}</p>
        </div>
      )}

      <div className="upload-section">
        <h3>書類アップロード</h3>
        
        <div className="upload-requirements">
          <p>📋 必要書類タイプ: <strong>{getDocumentCategory()}</strong></p>
          <p>📁 許可ファイル形式: <strong>{session.allowed_file_types}</strong></p>
          <p>📏 最大ファイルサイズ: <strong>{session.max_file_size_mb}MB</strong></p>
        </div>

        <div className="upload-area">
          <input
            type="file"
            id="file-upload"
            onChange={handleFileUpload}
            disabled={uploading}
            accept={session.allowed_file_types}
            style={{ display: 'none' }}
          />
          <label htmlFor="file-upload" className={`upload-button ${uploading ? 'disabled' : ''}`}>
            <div className="upload-icon">📤</div>
            <p>{uploading ? 'アップロード中...' : 'クリックしてファイルを選択'}</p>
            {uploading && (
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
              </div>
            )}
          </label>
        </div>

        {session.uploads.length > 0 && (
          <div className="uploaded-files">
            <h4>アップロード済みファイル ({session.uploads.length}件)</h4>
            <div className="file-list">
              {session.uploads.map(upload => (
                <div key={upload.id} className="file-item">
                  <div className="file-info">
                    <span className="file-name">📄 {upload.original_filename}</span>
                    <span className="file-date">{new Date(upload.uploaded_at).toLocaleString('ja-JP')}</span>
                  </div>
                  <div className={`file-status status-${upload.admin_status}`}>
                    {upload.admin_status === 'pending' ? '確認中' :
                     upload.admin_status === 'approved' ? '承認済み' : '要再提出'}
                  </div>
                  {upload.admin_comment && (
                    <div className="admin-comment">
                      💬 管理者コメント: {upload.admin_comment}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="completion-status">
        <div className="progress-indicator">
          <div className="progress-text">
            完了度: {session.completion_percentage}%
          </div>
          <div className="progress-bar-full">
            <div 
              className="progress-fill-full" 
              style={{ width: `${session.completion_percentage}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};