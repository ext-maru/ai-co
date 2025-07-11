import React, { useState } from 'react';

const GoogleDriveGuide = () => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: "Step 1: Google Cloud Consoleでプロジェクト作成",
      content: (
        <div>
          <p>1. <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer">Google Cloud Console</a> にアクセス</p>
          <p>2. 新しいプロジェクトを作成（例：「upload-image-service」）</p>
          <div className="code-block">
            プロジェクト名: upload-image-service<br/>
            組織: （任意）
          </div>
        </div>
      )
    },
    {
      title: "Step 2: Google Drive APIを有効化",
      content: (
        <div>
          <p>1. 左メニューから「APIとサービス」→「ライブラリ」を選択</p>
          <p>2. 「Google Drive API」を検索</p>
          <p>3. 「有効にする」ボタンをクリック</p>
          <div className="warning-box">
            ⚠️ APIの有効化には数分かかる場合があります
          </div>
        </div>
      )
    },
    {
      title: "Step 3: サービスアカウントを作成",
      content: (
        <div>
          <p>1. 「APIとサービス」→「認証情報」を選択</p>
          <p>2. 「認証情報を作成」→「サービスアカウント」をクリック</p>
          <p>3. 以下の情報を入力:</p>
          <div className="code-block">
            サービスアカウント名: upload-service-drive<br/>
            サービスアカウントID: upload-service-drive<br/>
            説明: Upload Image Service用Google Drive連携
          </div>
          <p>4. 「作成して続行」をクリック</p>
          <p>5. ロールの選択は「なし」のまま「完了」</p>
        </div>
      )
    },
    {
      title: "Step 4: 認証キーをダウンロード",
      content: (
        <div>
          <p>1. 作成したサービスアカウントをクリック</p>
          <p>2. 「キー」タブを選択</p>
          <p>3. 「キーを追加」→「新しいキーを作成」</p>
          <p>4. 「JSON」形式を選択してダウンロード</p>
          <div className="success-box">
            ✅ ダウンロードされたJSONファイルが認証ファイルです
          </div>
        </div>
      )
    },
    {
      title: "Step 5: Google Driveでフォルダを準備",
      content: (
        <div>
          <p>1. <a href="https://drive.google.com" target="_blank" rel="noopener noreferrer">Google Drive</a> にアクセス</p>
          <p>2. 新しいフォルダを作成（例：「契約書類アップロード」）</p>
          <p>3. フォルダを右クリック→「共有」を選択</p>
          <p>4. サービスアカウントのメールアドレスを追加</p>
          <div className="code-block">
            メールアドレス: upload-service-drive@プロジェクトID.iam.gserviceaccount.com<br/>
            権限: 編集者
          </div>
        </div>
      )
    },
    {
      title: "Step 6: フォルダIDを取得",
      content: (
        <div>
          <p>1. Google Driveで作成したフォルダを開く</p>
          <p>2. ブラウザのURLからフォルダIDをコピー</p>
          <div className="code-block">
            URL例: https://drive.google.com/drive/folders/1ABC123def456GHI789jkl<br/>
            フォルダID: 1ABC123def456GHI789jkl
          </div>
          <div className="success-box">
            ✅ このフォルダIDを設定画面で使用します
          </div>
        </div>
      )
    },
    {
      title: "Step 7: システムで設定",
      content: (
        <div>
          <p>1. 「Google Drive設定」画面を開く</p>
          <p>2. 「Google Drive連携を有効にする」をチェック</p>
          <p>3. ダウンロードした認証ファイル（JSON）をアップロード</p>
          <p>4. 親フォルダIDを入力</p>
          <p>5. 「接続テスト」ボタンで動作確認</p>
          <div className="success-box">
            ✅ 「接続テスト」が成功すれば設定完了です！
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="google-drive-guide">
      <div className="guide-header">
        <h3>📁 Google Drive連携セットアップガイド</h3>
        <p>7つのステップで簡単にGoogle Drive連携を設定できます</p>
      </div>

      <div className="step-navigation">
        {steps.map((step, index) => (
          <button
            key={index}
            className={`step-button ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
            onClick={() => setCurrentStep(index)}
          >
            {index + 1}
          </button>
        ))}
      </div>

      <div className="step-content">
        <h4>{steps[currentStep].title}</h4>
        {steps[currentStep].content}
      </div>

      <div className="step-controls">
        <button
          className="btn btn-secondary"
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
        >
          前へ
        </button>
        <span className="step-indicator">
          {currentStep + 1} / {steps.length}
        </span>
        <button
          className="btn"
          onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))}
          disabled={currentStep === steps.length - 1}
        >
          次へ
        </button>
      </div>

      <style jsx>{`
        .google-drive-guide {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .guide-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .step-navigation {
          display: flex;
          justify-content: center;
          gap: 10px;
          margin-bottom: 30px;
        }

        .step-button {
          width: 40px;
          height: 40px;
          border: 2px solid #ddd;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.3s ease;
        }

        .step-button.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }

        .step-button.completed {
          background: #28a745;
          color: white;
          border-color: #28a745;
        }

        .step-content {
          background: white;
          padding: 30px;
          border-radius: 10px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          min-height: 300px;
          margin-bottom: 20px;
        }

        .step-content h4 {
          color: #333;
          margin-bottom: 20px;
        }

        .step-content p {
          margin-bottom: 15px;
          line-height: 1.6;
        }

        .step-content a {
          color: #667eea;
          text-decoration: none;
        }

        .step-content a:hover {
          text-decoration: underline;
        }

        .code-block {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 5px;
          font-family: monospace;
          margin: 15px 0;
          border-left: 4px solid #667eea;
        }

        .warning-box {
          background: #fff3cd;
          border: 1px solid #ffeaa7;
          padding: 15px;
          border-radius: 5px;
          margin: 15px 0;
        }

        .success-box {
          background: #d4edda;
          border: 1px solid #c3e6cb;
          padding: 15px;
          border-radius: 5px;
          margin: 15px 0;
        }

        .step-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 20px;
        }

        .step-indicator {
          font-weight: bold;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default GoogleDriveGuide;
