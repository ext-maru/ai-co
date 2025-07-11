import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const AdminPage = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    submitter_name: '',
    submitter_email: '',
    submission_type: 'individual',
    description: ''
  });
  const [creating, setCreating] = useState(false);

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001';

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/sessions`);
      if (!response.ok) {
        throw new Error('セッション一覧の取得に失敗しました');
      }
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('セッションの作成に失敗しました');
      }

      const result = await response.json();

      // フォームをリセット
      setFormData({
        submitter_name: '',
        submitter_email: '',
        submission_type: 'individual',
        description: ''
      });

      // セッション一覧を更新
      await fetchSessions();

      alert(`セッションが作成されました。\nURL: ${window.location.origin}/submission/${result.session_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'not_uploaded':
        return 'アップしてない';
      case 'needs_reupload':
        return 'NG - 再アップ必要';
      case 'approved':
        return 'OK';
      default:
        return status;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'not_uploaded':
        return 'not-uploaded';
      case 'needs_reupload':
        return 'needs-reupload';
      case 'approved':
        return 'approved';
      default:
        return '';
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('URLをコピーしました');
  };

  const updateSessionStatus = async (sessionId, newStatus) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/submission/sessions/${sessionId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        throw new Error('ステータスの更新に失敗しました');
      }

      await fetchSessions();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="loading">セッション一覧を読み込み中...</div>;
  }

  return (
    <div className="App">
      <div className="header">
        <h1>契約書類アップロード管理システム</h1>
        <p>提出セッション管理</p>
        <div style={{ marginTop: '20px' }}>
          <Link to="/settings" className="btn btn-secondary">
            Google Drive設定
          </Link>
        </div>
      </div>

      {error && (
        <div className="error">
          エラー: {error}
        </div>
      )}

      <div className="container">
        <h2>新しい提出セッション作成</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="submitter_name">提出者名</label>
            <input
              type="text"
              id="submitter_name"
              name="submitter_name"
              value={formData.submitter_name}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="submitter_email">提出者メールアドレス</label>
            <input
              type="email"
              id="submitter_email"
              name="submitter_email"
              value={formData.submitter_email}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="submission_type">提出タイプ</label>
            <select
              id="submission_type"
              name="submission_type"
              value={formData.submission_type}
              onChange={handleInputChange}
            >
              <option value="individual">個人契約者用</option>
              <option value="corporate">法人契約者用</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="description">説明（任意）</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows="3"
            />
          </div>

          <button type="submit" className="btn" disabled={creating}>
            {creating ? '作成中...' : 'セッション作成'}
          </button>
        </form>
      </div>

      <div className="container">
        <h2>提出セッション一覧</h2>
        {sessions.length === 0 ? (
          <p>まだセッションはありません。</p>
        ) : (
          <div className="sessions-list">
            {sessions.map((session) => (
              <div key={session.id} className="session-card">
                <h3>{session.submitter_name}</h3>
                <div className="session-info">
                  <div>
                    <label>提出タイプ</label>
                    <span>
                      {session.submission_type === 'individual' ? '個人契約者用' : '法人契約者用'}
                    </span>
                  </div>
                  <div>
                    <label>ステータス</label>
                    <span className={`status ${getStatusClass(session.status)}`}>
                      {getStatusText(session.status)}
                    </span>
                  </div>
                  <div>
                    <label>メールアドレス</label>
                    <span>{session.submitter_email}</span>
                  </div>
                  <div>
                    <label>作成日時</label>
                    <span>{new Date(session.created_at).toLocaleString('ja-JP')}</span>
                  </div>
                </div>

                {session.description && (
                  <div style={{ marginTop: '10px' }}>
                    <label style={{ fontSize: '12px', color: '#666' }}>説明</label>
                    <p style={{ margin: '5px 0', color: '#333' }}>{session.description}</p>
                  </div>
                )}

                <div className="session-actions">
                  <button
                    className="btn"
                    onClick={() => copyToClipboard(`${window.location.origin}/submission/${session.id}`)}
                  >
                    URLをコピー
                  </button>
                  <Link
                    to={`/submission/${session.id}`}
                    className="btn btn-secondary"
                  >
                    提出ページを表示
                  </Link>

                  <select
                    value={session.status}
                    onChange={(e) => updateSessionStatus(session.id, e.target.value)}
                    style={{ marginLeft: '10px', padding: '8px' }}
                  >
                    <option value="not_uploaded">アップしてない</option>
                    <option value="needs_reupload">NG - 再アップ必要</option>
                    <option value="approved">OK</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPage;
