import React, { useState } from 'react';
import { SubmissionType, SubmissionSessionCreate } from '../../types/submission';
import './CreateSessionModal.css';

interface CreateSessionModalProps {
  onClose: () => void;
  onSessionCreated: () => void;
}

export const CreateSessionModal: React.FC<CreateSessionModalProps> = ({ onClose, onSessionCreated }) => {
  const [formData, setFormData] = useState<SubmissionSessionCreate>({
    submitter_name: '',
    submitter_email: '',
    submitter_phone: '',
    submitter_organization: '',
    submission_type: SubmissionType.INDIVIDUAL,
    title: '',
    description: '',
    admin_notes: '',
    due_date: '',
    max_file_size_mb: 50,
    allowed_file_types: '.pdf,.jpg,.jpeg,.png,.doc,.docx'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // due_dateをISO形式に変換
      const submitData = {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null
      };
      
      console.log('送信データ:', submitData);
      
      const response = await fetch('http://localhost:8000/api/v1/submission/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('セッション作成成功:', result);
        onSessionCreated();
        onClose();
      } else {
        const data = await response.json();
        console.error('セッション作成エラー:', data);
        setError(data.detail || 'セッション作成に失敗しました');
      }
    } catch (error) {
      console.error('ネットワークエラー:', error);
      setError('セッション作成中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>新規提出セッション作成</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="session-form">
          <div className="form-section">
            <h3>提出者情報</h3>
            
            <div className="form-group">
              <label className="required">提出者名</label>
              <input
                type="text"
                required
                value={formData.submitter_name}
                onChange={(e) => setFormData({...formData, submitter_name: e.target.value})}
                placeholder="田中太郎"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>メールアドレス</label>
                <input
                  type="email"
                  value={formData.submitter_email}
                  onChange={(e) => setFormData({...formData, submitter_email: e.target.value})}
                  placeholder="tanaka@example.com"
                />
              </div>

              <div className="form-group">
                <label>電話番号</label>
                <input
                  type="tel"
                  value={formData.submitter_phone}
                  onChange={(e) => setFormData({...formData, submitter_phone: e.target.value})}
                  placeholder="090-1234-5678"
                />
              </div>
            </div>

            <div className="form-group">
              <label>所属組織</label>
              <input
                type="text"
                value={formData.submitter_organization}
                onChange={(e) => setFormData({...formData, submitter_organization: e.target.value})}
                placeholder="株式会社ABC"
              />
            </div>
          </div>

          <div className="form-section">
            <h3>セッション設定</h3>

            <div className="form-group">
              <label className="required">提出タイプ</label>
              <select
                value={formData.submission_type}
                onChange={(e) => setFormData({...formData, submission_type: e.target.value as SubmissionType})}
              >
                <option value={SubmissionType.INDIVIDUAL}>個人契約者用</option>
                <option value={SubmissionType.CORPORATE}>法人契約者用</option>
              </select>
            </div>

            <div className="form-group">
              <label className="required">タイトル</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="契約書類提出のお願い"
              />
            </div>

            <div className="form-group">
              <label>説明文</label>
              <textarea
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="提出者への説明文を入力してください"
              />
            </div>

            <div className="form-group">
              <label>管理者メモ</label>
              <textarea
                rows={2}
                value={formData.admin_notes}
                onChange={(e) => setFormData({...formData, admin_notes: e.target.value})}
                placeholder="内部管理用のメモ"
              />
            </div>
          </div>

          <div className="form-section">
            <h3>制限設定</h3>

            <div className="form-row">
              <div className="form-group">
                <label>提出期限</label>
                <input
                  type="datetime-local"
                  value={formData.due_date}
                  onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>最大ファイルサイズ (MB)</label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={formData.max_file_size_mb}
                  onChange={(e) => setFormData({...formData, max_file_size_mb: parseInt(e.target.value)})}
                />
              </div>
            </div>

            <div className="form-group">
              <label>許可ファイル形式</label>
              <input
                type="text"
                value={formData.allowed_file_types}
                onChange={(e) => setFormData({...formData, allowed_file_types: e.target.value})}
              />
              <small>カンマ区切りで入力（例: .pdf,.jpg,.png）</small>
            </div>
          </div>

          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>
              キャンセル
            </button>
            <button type="submit" className="btn-create" disabled={loading}>
              {loading ? '作成中...' : 'セッション作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};