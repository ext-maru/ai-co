# 🕐 イシュー自動処理システム Cron設定ガイド

## 📋 前提条件

1. **GitHub Token設定**
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

2. **動作確認**
   ```bash
   # 手動実行でテスト
   cd /home/aicompany/ai_co
   ./scripts/auto_issue_processor_cron.sh
   ```

## ⏰ Cron設定

### 1. crontabを編集
```bash
crontab -e
```

### 2. 以下の行を追加

#### 1時間毎に実行（推奨）
```cron
# イシュー自動処理システム（1時間毎）
0 * * * * GITHUB_TOKEN=your_token /home/aicompany/ai_co/scripts/auto_issue_processor_cron.sh >> /home/aicompany/ai_co/logs/cron_auto_issue.log 2>&1
```

#### 営業時間内のみ（9:00-18:00）
```cron
# イシュー自動処理システム（営業時間内のみ）
0 9-18 * * * GITHUB_TOKEN=your_token /home/aicompany/ai_co/scripts/auto_issue_processor_cron.sh >> /home/aicompany/ai_co/logs/cron_auto_issue.log 2>&1
```

#### 1日3回実行（軽量版）
```cron
# イシュー自動処理システム（9時、13時、17時）
0 9,13,17 * * * GITHUB_TOKEN=your_token /home/aicompany/ai_co/scripts/auto_issue_processor_cron.sh >> /home/aicompany/ai_co/logs/cron_auto_issue.log 2>&1
```

## 🔧 環境変数の設定方法

### Option 1: .bashrcに追加
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: systemd環境ファイル
```bash
# /etc/environment に追加
GITHUB_TOKEN=your_token_here
```

### Option 3: 専用設定ファイル
```bash
# /home/aicompany/ai_co/.env ファイルを作成
echo 'GITHUB_TOKEN=your_token_here' > /home/aicompany/ai_co/.env

# スクリプトを修正して.envを読み込む
```

## 📊 ログ確認

### リアルタイム監視
```bash
tail -f /home/aicompany/ai_co/logs/auto_issue_processor/*.log
```

### 最新のログ確認
```bash
ls -lt /home/aicompany/ai_co/logs/auto_issue_processor/ | head -5
```

### エラーログのみ抽出
```bash
grep "❌" /home/aicompany/ai_co/logs/auto_issue_processor/*.log
```

## 🛡️ セキュリティ注意事項

1. **GitHub Tokenの保護**
   - 最小限の権限（repo:read, repo:write）のみ付与
   - 定期的にトークンをローテーション
   - ログにトークンが出力されないよう注意

2. **処理制限**
   - 1時間あたり最大3イシューまで
   - 同時実行は1イシューのみ
   - エラー時は自動停止

## 🚨 トラブルシューティング

### Token認証エラー
```bash
# GitHub Token確認
echo $GITHUB_TOKEN

# Token権限確認
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Cron実行されない
```bash
# Cronサービス確認
systemctl status cron

# Cron実行ログ確認
grep CRON /var/log/syslog
```

### Python依存関係エラー
```bash
# 必要なパッケージインストール
pip install PyGithub
```

## 📈 運用監視

### 処理統計の確認
```bash
# 本日の処理数
grep "処理完了" /home/aicompany/ai_co/logs/auto_issue_processor/$(date +%Y%m%d)*.log | wc -l

# 処理成功率
# TODO: 統計スクリプト作成予定
```

---
**作成日**: 2025/01/19
**作成者**: クロードエルダー
**ステータス**: 運用準備完了
