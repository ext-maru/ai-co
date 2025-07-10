import React, { useState, useEffect } from 'react';
import { getUploads, updateUploadStatus } from '../../services/api';
import './ApprovalDashboard.css';

interface Upload {
  id: string;
  filename: string;
  uploadedAt: string;
  status: 'pending' | 'approved' | 'rejected';
  userId: string;
  thumbnailUrl?: string;
  size: number;
}

export const ApprovalDashboard: React.FC = () => {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUploads();
  }, [filter]);

  const loadUploads = async () => {
    setLoading(true);
    try {
      const data = await getUploads({ status: filter === 'all' ? undefined : filter });
      setUploads(data);
    } catch (error) {
      console.error('Failed to load uploads:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (uploadId: string, newStatus: 'approved' | 'rejected') => {
    try {
      await updateUploadStatus(uploadId, newStatus);
      // 楽観的更新
      setUploads(prev => prev.map(upload => 
        upload.id === uploadId ? { ...upload, status: newStatus } : upload
      ));
    } catch (error) {
      console.error('Failed to update status:', error);
      // エラー時は再読み込み
      loadUploads();
    }
  };

  const filteredUploads = uploads.filter(upload => 
    filter === 'all' || upload.status === filter
  );

  return (
    <div className="approval-dashboard">
      <h1>画像承認ダッシュボード</h1>
      
      <div className="filter-buttons">
        <button 
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          すべて ({uploads.length})
        </button>
        <button 
          className={filter === 'pending' ? 'active' : ''}
          onClick={() => setFilter('pending')}
        >
          承認待ち ({uploads.filter(u => u.status === 'pending').length})
        </button>
        <button 
          className={filter === 'approved' ? 'active' : ''}
          onClick={() => setFilter('approved')}
        >
          承認済み ({uploads.filter(u => u.status === 'approved').length})
        </button>
        <button 
          className={filter === 'rejected' ? 'active' : ''}
          onClick={() => setFilter('rejected')}
        >
          却下 ({uploads.filter(u => u.status === 'rejected').length})
        </button>
      </div>

      {loading ? (
        <div className="loading">読み込み中...</div>
      ) : (
        <div className="upload-grid">
          {filteredUploads.map(upload => (
            <div key={upload.id} className={`upload-card ${upload.status}`}>
              {upload.thumbnailUrl && (
                <img src={upload.thumbnailUrl} alt={upload.filename} />
              )}
              <div className="upload-info">
                <h3>{upload.filename}</h3>
                <p>アップロード: {new Date(upload.uploadedAt).toLocaleString()}</p>
                <p>サイズ: {(upload.size / 1024 / 1024).toFixed(2)} MB</p>
                <p>ユーザー: {upload.userId}</p>
              </div>
              
              {upload.status === 'pending' && (
                <div className="action-buttons">
                  <button 
                    className="approve-btn"
                    onClick={() => handleStatusUpdate(upload.id, 'approved')}
                  >
                    承認
                  </button>
                  <button 
                    className="reject-btn"
                    onClick={() => handleStatusUpdate(upload.id, 'rejected')}
                  >
                    却下
                  </button>
                </div>
              )}
              
              <div className={`status-badge ${upload.status}`}>
                {upload.status === 'pending' && '承認待ち'}
                {upload.status === 'approved' && '✓ 承認済み'}
                {upload.status === 'rejected' && '✗ 却下'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
