import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const SubmissionPage = () => {
  const { sessionId } = useParams();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8002';

  useEffect(() => {
    fetchSession();
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error('セッション情報の取得に失敗しました');
      }
      const data = await response.json();
      setSession(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (selectedFiles) => {
    const newFiles = Array.from(selectedFiles).map(file => ({
      file,
      id: Date.now() + Math.random(),
      uploaded: false
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleFileInputChange = (e) => {
    handleFileSelect(e.target.files);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      alert('アップロードするファイルを選択してください');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach(({ file }) => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('ファイルのアップロードに失敗しました');
      }

      const result = await response.json();

      // セッション情報を更新
      await fetchSession();

      // ファイルリストをクリア
      setFiles([]);

      alert('ファイルのアップロードが完了しました');
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'not_uploaded':
        return 'まだファイルがアップロードされていません';
      case 'needs_reupload':
        return '確認結果: NG - 再度アップロードが必要です';
      case 'approved':
        return '確認結果: OK - 承認されました';
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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return <div className="loading">セッション情報を読み込み中...</div>;
  }

  if (error) {
    return (
      <div className="App">
        <div className="error">
          エラー: {error}
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="App">
        <div className="error">
          セッションが見つかりません
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="header">
        <h1>契約書類アップロード</h1>
        <p>{session.submitter_name} 様</p>
      </div>

      <div className="container">
        <div className="session-info">
          <div>
            <label>提出タイプ</label>
            <span>
              {session.submission_type === 'individual' ? '個人契約者用' : '法人契約者用'}
            </span>
          </div>
          <div>
            <label>現在のステータス</label>
            <span className={`status ${getStatusClass(session.status)}`}>
              {getStatusText(session.status)}
            </span>
          </div>
        </div>

        {session.description && (
          <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '6px' }}>
            <strong>説明:</strong> {session.description}
          </div>
        )}

        <h3>必要書類の説明</h3>
        {session.submission_type === 'individual' ? (
          <ul>
            <li>身分証明書（運転免許証、パスポートなど）</li>
            <li>住民票（3ヶ月以内）</li>
            <li>契約書（署名済み）</li>
          </ul>
        ) : (
          <ul>
            <li>会社登記簿謄本（3ヶ月以内）</li>
            <li>代表者身分証明書</li>
            <li>契約書（署名済み）</li>
            <li>印鑑証明書</li>
          </ul>
        )}

        <div
          className={`file-upload ${dragOver ? 'drag-over' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.gif"
            onChange={handleFileInputChange}
          />
          <div className="file-upload-icon">📁</div>
          <div className="file-upload-text">
            ファイルをドラッグ&ドロップ<br />または<br />クリックしてファイルを選択
          </div>
          <div className="file-upload-hint">
            PDF、JPG、PNG、GIF形式のファイルを選択できます
          </div>
        </div>

        {files.length > 0 && (
          <div className="uploaded-files">
            <h4>選択されたファイル:</h4>
            {files.map(({ file, id }) => (
              <div key={id} className="uploaded-file">
                <div>
                  <div className="uploaded-file-name">{file.name}</div>
                  <div className="uploaded-file-size">{formatFileSize(file.size)}</div>
                </div>
                <button
                  className="btn btn-danger"
                  onClick={() => removeFile(id)}
                >
                  削除
                </button>
              </div>
            ))}
            <button
              className="btn"
              onClick={uploadFiles}
              disabled={uploading}
              style={{ marginTop: '20px' }}
            >
              {uploading ? 'アップロード中...' : 'ファイルをアップロード'}
            </button>
          </div>
        )}

        {session.uploaded_files && session.uploaded_files.length > 0 && (
          <div style={{ marginTop: '30px' }}>
            <h4>アップロード済みファイル:</h4>
            {session.uploaded_files.map((file, index) => (
              <div key={index} className="uploaded-file">
                <div>
                  <div className="uploaded-file-name">{file.filename}</div>
                  <div className="uploaded-file-size">{formatFileSize(file.size)}</div>
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {new Date(file.uploaded_at).toLocaleString('ja-JP')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SubmissionPage;
