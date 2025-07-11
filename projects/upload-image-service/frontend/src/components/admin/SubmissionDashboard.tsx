import React, { useState, useEffect } from 'react';
import { SubmissionSessionResponse, SubmissionStatistics, SessionStatus } from '../../types/submission';
import { CreateSessionModal } from './CreateSessionModal';
import { SessionDetailModal } from './SessionDetailModal';
import './SubmissionDashboard.css';

export const SubmissionDashboard: React.FC = () => {
  const [sessions, setSessions] = useState<SubmissionSessionResponse[]>([]);
  const [statistics, setStatistics] = useState<SubmissionStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<SessionStatus | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  useEffect(() => {
    fetchSessions();
    fetchStatistics();
  }, [filterStatus]);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }
      
      const response = await fetch(`http://localhost:8000/api/v1/submission/sessions?${params}`);
      const data = await response.json();
      
      if (response.ok) {
        setSessions(data.items || []);
      } else {
        console.error('セッション取得エラー:', data);
      }
    } catch (error) {
      console.error('セッション取得エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/submission/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('統計取得エラー:', error);
    }
  };

  const getStatusLabel = (status: SessionStatus): string => {
    switch (status) {
      case SessionStatus.CREATED: return '作成済み';
      case SessionStatus.SENT: return '送付済み';
      case SessionStatus.IN_PROGRESS: return '提出中';
      case SessionStatus.COMPLETED: return '完了';
      case SessionStatus.EXPIRED: return '期限切れ';
      case SessionStatus.CANCELLED: return 'キャンセル';
      default: return status;
    }
  };

  const getStatusColor = (status: SessionStatus): string => {
    switch (status) {
      case SessionStatus.CREATED: return 'status-created';
      case SessionStatus.SENT: return 'status-sent';
      case SessionStatus.IN_PROGRESS: return 'status-in-progress';
      case SessionStatus.COMPLETED: return 'status-completed';
      case SessionStatus.EXPIRED: return 'status-expired';
      case SessionStatus.CANCELLED: return 'status-cancelled';
      default: return '';
    }
  };

  const getSubmissionTypeLabel = (type: string): string => {
    switch (type) {
      case 'individual': return '個人';
      case 'corporate': return '法人';
      case 'custom': return 'カスタム';
      default: return type;
    }
  };

  const copySubmissionUrl = (session: SubmissionSessionResponse) => {
    const url = `${window.location.origin}/submit/${session.session_url_key}`;
    navigator.clipboard.writeText(url);
    alert('提出URLをコピーしました');
  };

  const handleSessionCreated = () => {
    setShowCreateModal(false);
    fetchSessions();
    fetchStatistics();
  };

  return (
    <div className="submission-dashboard">
      <div className="dashboard-header">
        <h1>📋 提出管理ダッシュボード</h1>
        <button 
          className="btn-create-session"
          onClick={() => setShowCreateModal(true)}
        >
          ➕ 新規提出セッション作成
        </button>
      </div>

      {/* 統計情報 */}
      {statistics && (
        <div className="statistics-section">
          <div className="stat-card">
            <div className="stat-number">{statistics.total_sessions}</div>
            <div className="stat-label">総セッション数</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{statistics.active_sessions}</div>
            <div className="stat-label">アクティブ</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{statistics.completed_sessions}</div>
            <div className="stat-label">完了済み</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{statistics.total_uploads}</div>
            <div className="stat-label">総ファイル数</div>
          </div>
        </div>
      )}

      {/* フィルター */}
      <div className="dashboard-controls">
        <div className="filter-section">
          <label>ステータス絞り込み:</label>
          <select 
            value={filterStatus} 
            onChange={(e) => setFilterStatus(e.target.value as SessionStatus | 'all')}
            className="status-filter"
          >
            <option value="all">すべて</option>
            <option value={SessionStatus.CREATED}>作成済み</option>
            <option value={SessionStatus.SENT}>送付済み</option>
            <option value={SessionStatus.IN_PROGRESS}>提出中</option>
            <option value={SessionStatus.COMPLETED}>完了</option>
            <option value={SessionStatus.EXPIRED}>期限切れ</option>
          </select>
        </div>
        
        <button 
          className="btn-refresh"
          onClick={fetchSessions}
          disabled={loading}
        >
          🔄 更新
        </button>
      </div>

      {/* セッション一覧 */}
      <div className="sessions-grid">
        {loading ? (
          <div className="loading-message">読み込み中...</div>
        ) : sessions.length === 0 ? (
          <div className="empty-message">
            <p>該当するセッションがありません</p>
          </div>
        ) : (
          sessions.map(session => (
            <div key={session.id} className="session-card">
              <div className="session-header">
                <div className="session-title">
                  <h3>{session.title}</h3>
                  <span className="session-type">
                    {getSubmissionTypeLabel(session.submission_type)}
                  </span>
                </div>
                <div className={`session-status ${getStatusColor(session.status)}`}>
                  {getStatusLabel(session.status)}
                </div>
              </div>

              <div className="session-info">
                <div className="submitter-info">
                  <strong>提出者:</strong> {session.submitter_name}
                  {session.submitter_organization && (
                    <span className="organization">({session.submitter_organization})</span>
                  )}
                </div>
                
                {session.due_date && (
                  <div className="due-date">
                    <strong>期限:</strong> {new Date(session.due_date).toLocaleDateString('ja-JP')}
                    {session.days_until_due <= 3 && session.days_until_due > 0 && (
                      <span className="urgent">（あと{session.days_until_due}日）</span>
                    )}
                    {session.is_expired && (
                      <span className="expired">（期限切れ）</span>
                    )}
                  </div>
                )}

                <div className="session-stats">
                  <span>📄 {session.upload_count} ファイル</span>
                </div>

                <div className="created-date">
                  作成: {new Date(session.created_at).toLocaleDateString('ja-JP')}
                </div>
              </div>

              <div className="session-actions">
                <button 
                  className="btn-detail"
                  onClick={() => setSelectedSession(session.id)}
                >
                  📋 詳細
                </button>
                <button 
                  className="btn-copy-url"
                  onClick={() => copySubmissionUrl(session)}
                >
                  🔗 URL コピー
                </button>
                <button 
                  className="btn-qr"
                  onClick={() => window.open(`/api/v1/submission/sessions/${session.id}/qr`, '_blank')}
                >
                  📱 QR
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* モーダル */}
      {showCreateModal && (
        <CreateSessionModal 
          onClose={() => setShowCreateModal(false)}
          onSessionCreated={handleSessionCreated}
        />
      )}

      {selectedSession && (
        <SessionDetailModal 
          sessionId={selectedSession}
          onClose={() => setSelectedSession(null)}
          onSessionUpdated={fetchSessions}
        />
      )}
    </div>
  );
};