import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    google_drive_enabled: false,
    google_drive_parent_folder_id: '',
    google_drive_folder_name_format: '[{session_id}]_{submitter_name}',
    google_drive_auto_create_folders: true,
    google_drive_share_with_submitter: true,
    credentials_uploaded: false
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [credentialsFile, setCredentialsFile] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001';

  useEffect(() => {
    fetchSettings();
    testConnection();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/google-drive/settings`);
      if (!response.ok) {
        throw new Error('設定の取得に失敗しました');
      }
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/google-drive/test-connection`);
      const data = await response.json();
      setConnectionStatus(data);
    } catch (err) {
      setConnectionStatus({
        connected: false,
        error: err.message
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCredentialsUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setError('JSONファイルを選択してください');
      return;
    }

    setCredentialsFile(file);
  };

  const uploadCredentials = async () => {
    if (!credentialsFile) {
      setError('認証ファイルを選択してください');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('credentials', credentialsFile);

      const response = await fetch(`${API_BASE}/api/v1/admin/google-drive/upload-credentials`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('認証ファイルのアップロードに失敗しました');
      }

      setSuccess('認証ファイルがアップロードされました');
      setCredentialsFile(null);
      await fetchSettings();
      await testConnection();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/google-drive/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error('設定の保存に失敗しました');
      }

      setSuccess('設定が保存されました');
      await testConnection();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/google-drive/test-connection`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.connected) {
        setSuccess('Google Drive接続テストが成功しました');
        setConnectionStatus(data);
      } else {
        setError(`接続テストに失敗しました: ${data.error}`);
        setConnectionStatus(data);
      }
    } catch (err) {
      setError(err.message);
      setConnectionStatus({
        connected: false,
        error: err.message
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return <div className="loading">設定を読み込み中...</div>;
  }

  return (
    <div className="App">
      <div className="header">
        <h1>Google Drive設定</h1>
        <p>Google Drive連携の設定を管理します</p>
        <div style={{ marginTop: '20px' }}>
          <Link to="/admin" className="btn btn-secondary">
            管理画面に戻る
          </Link>
        </div>
      </div>

      {error && (
        <div className="error">
          エラー: {error}
        </div>
      )}

      {success && (
        <div className="success">
          {success}
        </div>
      )}

      <form onSubmit={handleSave}>
        <div className="settings-section">
          <h3>基本設定</h3>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="google_drive_enabled"
                checked={settings.google_drive_enabled}
                onChange={handleInputChange}
                style={{ marginRight: '10px' }}
              />
              Google Drive連携を有効にする
            </label>
          </div>

          <div className="connection-status">
            <div className={`connection-status ${connectionStatus?.connected ? 'connected' : 'disconnected'}`}>
              <div className="connection-dot"></div>
              <span>
                {connectionStatus?.connected ? '接続中' : '未接続'}
                {connectionStatus?.error && ` - ${connectionStatus.error}`}
              </span>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleTestConnection}
              disabled={testing}
              style={{ marginLeft: '15px' }}
            >
              {testing ? 'テスト中...' : '接続テスト'}
            </button>
          </div>
        </div>

        <div className="settings-section">
          <h3>認証設定</h3>

          <div className="form-group">
            <label>Google Cloud Console認証ファイル (credentials.json)</label>
            <input
              type="file"
              accept=".json"
              onChange={handleCredentialsUpload}
              style={{ marginBottom: '10px' }}
            />
            {credentialsFile && (
              <div style={{ marginTop: '10px' }}>
                <p>選択されたファイル: {credentialsFile.name}</p>
                <button
                  type="button"
                  className="btn"
                  onClick={uploadCredentials}
                  disabled={saving}
                >
                  {saving ? 'アップロード中...' : '認証ファイルをアップロード'}
                </button>
              </div>
            )}
            {settings.credentials_uploaded && (
              <p style={{ color: '#28a745', fontSize: '14px' }}>
                ✓ 認証ファイルがアップロード済みです
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="google_drive_parent_folder_id">
              親フォルダID
              <span style={{ fontSize: '12px', color: '#666', display: 'block' }}>
                Google DriveのURLから取得: https://drive.google.com/drive/folders/【ここがフォルダID】
              </span>
            </label>
            <input
              type="text"
              id="google_drive_parent_folder_id"
              name="google_drive_parent_folder_id"
              value={settings.google_drive_parent_folder_id}
              onChange={handleInputChange}
              placeholder="例: 1ABC123def456GHI789jkl"
            />
          </div>
        </div>

        <div className="settings-section">
          <h3>フォルダ設定</h3>

          <div className="settings-grid">
            <div className="form-group">
              <label htmlFor="google_drive_folder_name_format">
                フォルダ名フォーマット
                <span style={{ fontSize: '12px', color: '#666', display: 'block' }}>
                  {'{session_id}'} と {'{submitter_name}'} が使用できます
                </span>
              </label>
              <input
                type="text"
                id="google_drive_folder_name_format"
                name="google_drive_folder_name_format"
                value={settings.google_drive_folder_name_format}
                onChange={handleInputChange}
                placeholder="例: [{session_id}]_{submitter_name}"
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="google_drive_auto_create_folders"
                  checked={settings.google_drive_auto_create_folders}
                  onChange={handleInputChange}
                  style={{ marginRight: '10px' }}
                />
                フォルダの自動作成
              </label>
              <span style={{ fontSize: '12px', color: '#666', display: 'block' }}>
                セッション作成時にGoogle Driveにフォルダを自動作成します
              </span>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="google_drive_share_with_submitter"
                  checked={settings.google_drive_share_with_submitter}
                  onChange={handleInputChange}
                  style={{ marginRight: '10px' }}
                />
                提出者との共有
              </label>
              <span style={{ fontSize: '12px', color: '#666', display: 'block' }}>
                提出者のメールアドレスにフォルダの読み取り権限を付与します
              </span>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h3>使用方法</h3>
          <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '6px', fontSize: '14px' }}>
            <h4>セットアップ手順:</h4>
            <ol>
              <li>Google Cloud Consoleでプロジェクトを作成</li>
              <li>Google Drive APIを有効化</li>
              <li>サービスアカウントを作成し、JSONキーをダウンロード</li>
              <li>上記の「認証ファイル」からJSONファイルをアップロード</li>
              <li>Google Driveで親フォルダを作成</li>
              <li>親フォルダをサービスアカウントと共有（編集権限）</li>
              <li>親フォルダのIDを上記「親フォルダID」に入力</li>
              <li>「接続テスト」で動作を確認</li>
            </ol>

            <h4>詳細なセットアップガイド:</h4>
            <p>
              <a
                href="https://docs.google.com/document/d/1example-setup-guide"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#007bff' }}
              >
                Google Drive連携セットアップガイド
              </a>
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button
            type="submit"
            className="btn"
            disabled={saving}
          >
            {saving ? '保存中...' : '設定を保存'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SettingsPage;
