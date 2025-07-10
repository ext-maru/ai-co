import React, { useState, useEffect } from 'react';
import './SimpleContractReview.css';

// シンプルなステータス定義
export enum SimpleStatus {
  NOT_UPLOADED = 'not_uploaded',     // アップしてない
  NEEDS_REUPLOAD = 'needs_reupload', // NG出て再アップ必要
  APPROVED = 'approved'              // OKでた
}

interface ContractItem {
  id: string;
  user_name: string;
  contract_type: 'individual' | 'corporate';
  status: SimpleStatus;
  created_at: string;
  google_drive_folder_url?: string;
  document_count: number;
  required_document_count: number;
}

interface SimpleContractReviewProps {
  // 必要に応じてpropsを追加
}

export const SimpleContractReview: React.FC<SimpleContractReviewProps> = () => {
  const [contracts, setContracts] = useState<ContractItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<SimpleStatus | 'all'>('all');
  const [loading, setLoading] = useState(false);

  // サンプルデータ（実際はAPIから取得）
  useEffect(() => {
    const sampleData: ContractItem[] = [
      {
        id: '1',
        user_name: '田中太郎',
        contract_type: 'individual',
        status: SimpleStatus.NOT_UPLOADED,
        created_at: '2025-01-10T10:00:00Z',
        google_drive_folder_url: 'https://drive.google.com/drive/folders/xxx',
        document_count: 2,
        required_document_count: 5
      },
      {
        id: '2',
        user_name: '株式会社ABC',
        contract_type: 'corporate',
        status: SimpleStatus.NEEDS_REUPLOAD,
        created_at: '2025-01-09T15:30:00Z',
        google_drive_folder_url: 'https://drive.google.com/drive/folders/yyy',
        document_count: 8,
        required_document_count: 8
      },
      {
        id: '3',
        user_name: '佐藤花子',
        contract_type: 'individual',
        status: SimpleStatus.APPROVED,
        created_at: '2025-01-08T09:15:00Z',
        google_drive_folder_url: 'https://drive.google.com/drive/folders/zzz',
        document_count: 5,
        required_document_count: 5
      }
    ];
    setContracts(sampleData);
  }, []);

  const getStatusLabel = (status: SimpleStatus): string => {
    switch (status) {
      case SimpleStatus.NOT_UPLOADED:
        return 'アップしてない';
      case SimpleStatus.NEEDS_REUPLOAD:
        return 'NG・再アップ必要';
      case SimpleStatus.APPROVED:
        return 'OK完了';
      default:
        return '不明';
    }
  };

  const getStatusColor = (status: SimpleStatus): string => {
    switch (status) {
      case SimpleStatus.NOT_UPLOADED:
        return 'status-not-uploaded';
      case SimpleStatus.NEEDS_REUPLOAD:
        return 'status-needs-reupload';
      case SimpleStatus.APPROVED:
        return 'status-approved';
      default:
        return '';
    }
  };

  const getContractTypeLabel = (type: string): string => {
    return type === 'individual' ? '個人' : '法人';
  };

  const handleStatusChange = async (contractId: string, newStatus: SimpleStatus) => {
    setLoading(true);
    try {
      // TODO: APIコール実装
      // await updateContractStatus(contractId, newStatus);
      
      setContracts(prev => 
        prev.map(contract => 
          contract.id === contractId 
            ? { ...contract, status: newStatus }
            : contract
        )
      );
      
      console.log(`Contract ${contractId} status updated to ${newStatus}`);
    } catch (error) {
      console.error('ステータス更新エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const openGoogleDrive = (url?: string) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  const filteredContracts = contracts.filter(contract => {
    if (filterStatus === 'all') return true;
    return contract.status === filterStatus;
  });

  // 作業中案件（アップしてない、またはNG）のカウント
  const pendingCount = contracts.filter(c => 
    c.status === SimpleStatus.NOT_UPLOADED || c.status === SimpleStatus.NEEDS_REUPLOAD
  ).length;

  return (
    <div className="simple-contract-review">
      <div className="review-header">
        <h1>📋 契約書類チェック</h1>
        <div className="quick-stats">
          <div className="stat-item pending">
            <span className="count">{pendingCount}</span>
            <span className="label">作業中</span>
          </div>
          <div className="stat-item total">
            <span className="count">{contracts.length}</span>
            <span className="label">総件数</span>
          </div>
        </div>
      </div>

      <div className="review-controls">
        <div className="filter-section">
          <label>絞り込み:</label>
          <select 
            value={filterStatus} 
            onChange={(e) => setFilterStatus(e.target.value as SimpleStatus | 'all')}
            className="status-filter"
          >
            <option value="all">すべて</option>
            <option value={SimpleStatus.NOT_UPLOADED}>アップしてない</option>
            <option value={SimpleStatus.NEEDS_REUPLOAD}>NG・再アップ必要</option>
            <option value={SimpleStatus.APPROVED}>OK完了</option>
          </select>
        </div>
        
        <button 
          className="btn-quick-search"
          onClick={() => setFilterStatus(SimpleStatus.NOT_UPLOADED)}
        >
          🔍 作業中案件のみ表示
        </button>
      </div>

      <div className="contracts-grid">
        {filteredContracts.map(contract => (
          <div key={contract.id} className="contract-card">
            <div className="card-header">
              <div className="user-info">
                <h3>{contract.user_name}</h3>
                <span className="contract-type">
                  {getContractTypeLabel(contract.contract_type)}
                </span>
              </div>
              <div className={`status-badge ${getStatusColor(contract.status)}`}>
                {getStatusLabel(contract.status)}
              </div>
            </div>

            <div className="card-body">
              <div className="progress-info">
                <span>書類: {contract.document_count}/{contract.required_document_count}</span>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${(contract.document_count / contract.required_document_count) * 100}%` 
                    }}
                  />
                </div>
              </div>

              <div className="created-date">
                作成: {new Date(contract.created_at).toLocaleDateString('ja-JP')}
              </div>

              {contract.google_drive_folder_url && (
                <button 
                  className="btn-drive"
                  onClick={() => openGoogleDrive(contract.google_drive_folder_url)}
                >
                  📁 Google Driveで確認
                </button>
              )}
            </div>

            <div className="card-actions">
              <div className="status-buttons">
                <button 
                  className={`btn-status ok ${
                    contract.status === SimpleStatus.APPROVED ? 'active' : ''
                  }`}
                  onClick={() => handleStatusChange(contract.id, SimpleStatus.APPROVED)}
                  disabled={loading}
                >
                  ✅ OK
                </button>
                <button 
                  className={`btn-status ng ${
                    contract.status === SimpleStatus.NEEDS_REUPLOAD ? 'active' : ''
                  }`}
                  onClick={() => handleStatusChange(contract.id, SimpleStatus.NEEDS_REUPLOAD)}
                  disabled={loading}
                >
                  ❌ NG
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredContracts.length === 0 && (
        <div className="empty-state">
          <p>条件に合う案件がありません</p>
        </div>
      )}
    </div>
  );
};

export default SimpleContractReview;