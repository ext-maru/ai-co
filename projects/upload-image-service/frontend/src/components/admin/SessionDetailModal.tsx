import React, { useState, useEffect } from 'react';
import { SubmissionSessionDetail, SessionStatus } from '../../types/submission';
import './SessionDetailModal.css';

interface SessionDetailModalProps {
  sessionId: string;
  onClose: () => void;
  onSessionUpdated: () => void;
}

export const SessionDetailModal: React.FC<SessionDetailModalProps> = ({
  sessionId,
  onClose,
  onSessionUpdated
}) => {
  const [session, setSession] = useState<SubmissionSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showQR, setShowQR] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');

  useEffect(() => {
    fetchSessionDetail();
  }, [sessionId]);

  const fetchSessionDetail = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/v1/submission/sessions/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setSession(data);
      }
    } catch (error) {
      console.error('セッション詳細取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchQRCode = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/submission/sessions/${sessionId}/qr`);
      if (response.ok) {
        const data = await response.json();
        setQrCode(data.qr_code_data_url);
        setShowQR(true);
      }
    } catch (error) {
      console.error('QRコード取得エラー:', error);
    }
  };

  const copyUrl = () => {
    if (!session) return;
    const url = `${window.location.origin}/submit/${session.session_url_key}`;
    navigator.clipboard.writeText(url);
    alert('URLをコピーしました');
  };

  const updateStatus = async (newStatus: SessionStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/submission/sessions/${sessionId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      
      if (response.ok) {
        fetchSessionDetail();
        onSessionUpdated();
      }
    } catch (error) {
      console.error('ステータス更新エラー:', error);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="loading">読み込み中...</div>
        </div>
      </div>
    );
  }

  if (!session) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{session.title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="session-detail">
          {/* 基本情報 */}
          <div className="detail-section">
            <h3>基本情報</h3>
            <div className="info-grid">
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
              {session.submitter_email && (
                <div className="info-item">
                  <label>メール</label>
                  <span>{session.submitter_email}</span>
                </div>
              )}
              {session.submitter_phone && (
                <div className="info-item">
                  <label>電話</label>
                  <span>{session.submitter_phone}</span>
                </div>
              )}
              <div className="info-item">
                <label>提出タイプ</label>
                <span>{session.submission_type === 'individual' ? '個人' : '法人'}</span>
              </div>
              <div className="info-item">
                <label>ステータス</label>
                <span className={`status status-${session.status}`}>{getStatusLabel(session.status)}</span>
              </div>
              {session.due_date && (
                <div className="info-item">
                  <label>期限</label>
                  <span>{new Date(session.due_date).toLocaleString('ja-JP')}</span>
                </div>
              )}
              <div className="info-item">
                <label>完了率</label>
                <span>{session.completion_percentage}%</span>
              </div>
            </div>
            {session.description && (
              <div className="description">
                <label>説明</label>
                <p>{session.description}</p>
              </div>
            )}
            {session.admin_notes && (
              <div className="admin-notes">
                <label>管理者メモ</label>
                <p>{session.admin_notes}</p>
              </div>
            )}
          </div>

          {/* 提出URL */}
          <div className="detail-section">
            <h3>提出URL</h3>
            <div className="url-section">
              <input 
                type="text" 
                readOnly 
                value={`${window.location.origin}/submit/${session.session_url_key}`}
                className="url-input"
              />
              <div className="url-actions">
                <button onClick={copyUrl} className="btn-copy">📋 コピー</button>
                <button onClick={fetchQRCode} className="btn-qr">📱 QRコード</button>
              </div>
            </div>
            {showQR && qrCode && (
              <div className="qr-display">
                <img src={qrCode} alt="QRコード" />
              </div>
            )}
          </div>

          {/* アップロードファイル一覧 */}
          <div className="detail-section">
            <h3>アップロードファイル ({session.uploads.length}件)</h3>
            {session.uploads.length === 0 ? (
              <p className="no-data">まだファイルがアップロードされていません</p>
            ) : (
              <div className="uploads-list">
                {session.uploads.map(upload => (
                  <div key={upload.id} className="upload-item">
                    <div className="upload-info">
                      <div className="upload-name">{upload.original_filename}</div>
                      <div className="upload-meta">
                        {upload.document_category && <span className="category">{upload.document_category}</span>}
                        <span className="size">{formatFileSize(upload.file_size)}</span>
                        <span className="date">{new Date(upload.uploaded_at).toLocaleString('ja-JP')}</span>
                      </div>
                      {upload.submitter_comment && (
                        <div className="comment">コメント: {upload.submitter_comment}</div>
                      )}
                    </div>
                    <div className={`upload-status status-${upload.admin_status}`}>
                      {upload.admin_status === 'pending' ? '未確認' : 
                       upload.admin_status === 'approved' ? '承認済み' : '却下'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* アクション */}
          <div className="detail-actions">
            <button 
              className="btn-status"
              onClick={() => updateStatus(SessionStatus.COMPLETED)}
              disabled={session.status === SessionStatus.COMPLETED}
            >
              ✅ 完了にする
            </button>
            <button 
              className="btn-status cancel"
              onClick={() => updateStatus(SessionStatus.CANCELLED)}
              disabled={session.status === SessionStatus.CANCELLED}
            >
              ❌ キャンセル
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

function getStatusLabel(status: SessionStatus): string {
  switch (status) {
    case SessionStatus.CREATED: return '作成済み';
    case SessionStatus.SENT: return '送付済み';
    case SessionStatus.IN_PROGRESS: return '提出中';
    case SessionStatus.COMPLETED: return '完了';
    case SessionStatus.EXPIRED: return '期限切れ';
    case SessionStatus.CANCELLED: return 'キャンセル';
    default: return status;
  }
}

function formatFileSize(bytes: string): string {
  const size = parseInt(bytes);
  if (size < 1024) return size + ' B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
  return (size / (1024 * 1024)).toFixed(1) + ' MB';
}