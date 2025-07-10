// 4賢者統合メインコンポーネント（簡易版）

import React, { useEffect } from 'react';
import useSagesStore from '../stores/sagesStore';
import SageStatusPanel from './SageStatusPanel';

const FourSagesIntegration: React.FC = () => {
  const {
    sages,
    systemHealth,
    connectionStatus,
    fetchSagesData,
    initializeWebSocket,
  } = useSagesStore();

  useEffect(() => {
    // 初期データ取得
    fetchSagesData();

    // WebSocket接続開始
    initializeWebSocket();

    // 定期的なデータ更新（30秒間隔）
    const interval = setInterval(() => {
      if (connectionStatus === 'connected') {
        fetchSagesData();
      }
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  }, [fetchSagesData, initializeWebSocket, connectionStatus]);

  const getConnectionStatusColor = (): string => {
    switch (connectionStatus) {
      case 'connected': return '#10B981';
      case 'connecting': return '#F59E0B';
      case 'disconnected': return '#6B7280';
      case 'error': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getConnectionStatusText = (): string => {
    switch (connectionStatus) {
      case 'connected': return '接続中';
      case 'connecting': return '接続中...';
      case 'disconnected': return '切断';
      case 'error': return 'エラー';
      default: return '不明';
    }
  };

  const getSystemHealthColor = (): string => {
    if (systemHealth.overall >= 80) return '#10B981';
    if (systemHealth.overall >= 60) return '#F59E0B';
    if (systemHealth.overall >= 40) return '#F97316';
    return '#EF4444';
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#F3F4F6',
      padding: '20px'
    }}>
      {/* システムヘッダー */}
      <div style={{
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <div>
          <h1 style={{
            margin: '0 0 4px 0',
            color: '#1F2937',
            fontSize: '2rem',
            fontWeight: 700
          }}>
            🧙‍♂️ AI Company 4賢者統合システム
          </h1>
          <p style={{
            margin: '0',
            color: '#6B7280',
            fontSize: '1rem'
          }}>
            Knowledge • Task • Incident • RAG
          </p>
        </div>

        <div style={{
          display: 'flex',
          gap: '24px',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span style={{
              fontSize: '0.75rem',
              color: '#9CA3AF',
              textTransform: 'uppercase',
              fontWeight: 500
            }}>
              接続状態:
            </span>
            <span style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: getConnectionStatusColor()
            }}>
              {getConnectionStatusText()}
            </span>
          </div>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span style={{
              fontSize: '0.75rem',
              color: '#9CA3AF',
              textTransform: 'uppercase',
              fontWeight: 500
            }}>
              システム健全性:
            </span>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: getSystemHealthColor()
              }} />
              <span style={{
                fontSize: '0.875rem',
                fontWeight: 600,
                color: '#374151'
              }}>
                {systemHealth.overall}%
              </span>
            </div>
          </div>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span style={{
              fontSize: '0.75rem',
              color: '#9CA3AF',
              textTransform: 'uppercase',
              fontWeight: 500
            }}>
              最終同期:
            </span>
            <span style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: '#374151'
            }}>
              {new Date(systemHealth.lastSyncTime).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* 賢者状態パネル */}
      <SageStatusPanel sages={sages} />

      {/* 開発中パネル */}
      <div style={{
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        margin: '20px 0',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          margin: '0 0 16px 0',
          color: '#1F2937',
          fontSize: '1.5rem',
          fontWeight: 600
        }}>
          🚧 開発中機能
        </h3>
        <div style={{
          padding: '40px 20px',
          textAlign: 'center',
          color: '#6B7280',
          background: '#F9FAFB',
          borderRadius: '4px'
        }}>
          <p>協調セッション・コンセンサス形成・クロス学習機能は開発中です</p>
        </div>
      </div>
    </div>
  );
};

export default FourSagesIntegration;
