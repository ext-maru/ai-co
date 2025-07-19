import React from 'react';

interface FileUploadProgressProps {
  progress: number;
  status: 'uploading' | 'completed' | 'error';
}

export const FileUploadProgress: React.FC<FileUploadProgressProps> = ({ progress, status }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
        return '#2196F3';
      case 'completed':
        return '#4CAF50';
      case 'error':
        return '#F44336';
      default:
        return '#9E9E9E';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return `アップロード中... ${progress}%`;
      case 'completed':
        return '完了';
      case 'error':
        return 'エラー';
      default:
        return '待機中';
    }
  };

  return (
    <div style={{ marginTop: '8px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '4px'
      }}>
        <span style={{ fontSize: '12px', color: '#666' }}>
          {getStatusText()}
        </span>
      </div>
      <div style={{
        width: '100%',
        height: '4px',
        backgroundColor: '#e0e0e0',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        <div
          style={{
            width: `${progress}%`,
            backgroundColor: getStatusColor(),
            height: '4px',
            borderRadius: '2px',
            transition: 'width 0.3s ease'
          }}
        />
      </div>
    </div>
  );
};
