// 4賢者状態パネルコンポーネント

import React from 'react';
import type { Sage } from '../types/sages';
import styles from './SageStatusPanel.module.css';

interface SageStatusPanelProps {
  sages: Record<string, Sage>;
}

const SageStatusPanel: React.FC<SageStatusPanelProps> = ({ sages }) => {
  const getSageIcon = (type: Sage['type']): string => {
    switch (type) {
      case 'knowledge': return '📚';
      case 'task': return '📋';
      case 'incident': return '🚨';
      case 'rag': return '🔍';
      default: return '🤖';
    }
  };

  const getStatusColor = (status: Sage['status']): string => {
    switch (status) {
      case 'active': return '#10B981'; // green
      case 'processing': return '#F59E0B'; // yellow
      case 'idle': return '#6B7280'; // gray
      case 'error': return '#EF4444'; // red
      default: return '#6B7280';
    }
  };

  const getHealthColor = (health: number): string => {
    if (health >= 80) return '#10B981';
    if (health >= 60) return '#F59E0B';
    if (health >= 40) return '#F97316';
    return '#EF4444';
  };

  return (
    <div className={styles.sageStatusPanel}>
      <h3 className={styles.panelTitle}>🧙‍♂️ 4賢者システム状態</h3>
      <div className={styles.sagesGrid}>
        {Object.values(sages).map((sage) => (
          <div key={sage.id} className={styles.sageCard}>
            <div className={styles.sageHeader}>
              <span className={styles.sageIcon}>{getSageIcon(sage.type)}</span>
              <div className={styles.sageInfo}>
                <h4>{sage.name}</h4>
                <span
                  className={styles.sageStatus}
                  style={{ color: getStatusColor(sage.status) }}
                >
                  {sage.status}
                </span>
              </div>
            </div>

            <div className={styles.sageHealth}>
              <div className={styles.healthBar}>
                <div
                  className={styles.healthFill}
                  style={{
                    width: `${sage.health}%`,
                    backgroundColor: getHealthColor(sage.health)
                  }}
                />
              </div>
              <span className={styles.healthText}>{sage.health}%</span>
            </div>

            {sage.currentTask && (
              <div className={styles.currentTask}>
                <strong>現在のタスク:</strong>
                <p>{sage.currentTask}</p>
              </div>
            )}

            <div className={styles.sageDetails}>
              {sage.type === 'knowledge' && (
                <div>
                  <p>📄 文書: {sage.knowledgeBase.documents}</p>
                  <p>🏷️ カテゴリ: {sage.knowledgeBase.categories.length}</p>
                </div>
              )}

              {sage.type === 'task' && (
                <div>
                  <p>⏳ 待機中: {sage.taskQueue.pending}</p>
                  <p>⚡ 実行中: {sage.taskQueue.active}</p>
                  <p>✅ 完了: {sage.taskQueue.completed}</p>
                </div>
              )}

              {sage.type === 'incident' && (
                <div>
                  <p>🔴 重大: {sage.incidents.critical}</p>
                  <p>🟡 警告: {sage.incidents.warning}</p>
                  <p>✅ 解決済み: {sage.incidents.resolved}</p>
                </div>
              )}

              {sage.type === 'rag' && (
                <div>
                  <p>📊 インデックス: {sage.searchEngine.indexSize}</p>
                  <p>⚡ レイテンシ: {sage.searchEngine.queryLatency}ms</p>
                </div>
              )}
            </div>

            <div className={styles.lastActive}>
              最終更新: {new Date(sage.lastActive).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SageStatusPanel;
