# Runbooks

Auto Issue Processor A2Aの運用ランブックとオペレーション手順書です。

## 📋 ランブック一覧

### 🔥 主要ランブック
- **[日常運用ガイド](daily-operations-guide.md)** - 日次・週次・月次タスク
- **[インシデント対応ガイド](incident-response-guide.md)** - P1-P4レベル別対応手順
- **[トラブルシューティングガイド](troubleshooting-guide.md)** - 問題解決の完全ガイド

### 📝 専門ドキュメント
- **[最新改善事項](recent-improvements-july-2025.md)** - 2025年7月の改善・Issue #156-158対応
- **[Cron設定ガイド](cron-setup-guide.md)** - 自動実行設定

## 🎯 用途別ガイド

### 🚨 緊急時対応
1. **[インシデント対応ガイド](incident-response-guide.md)** ← **緊急時はここ**
2. **[トラブルシューティング](troubleshooting-guide.md)** - 具体的解決方法

### 📅 日常運用
1. **[日常運用ガイド](daily-operations-guide.md)** - チェックリスト形式
2. **[最新改善事項](recent-improvements-july-2025.md)** - 最新機能と対処法

### 🔧 設定・メンテナンス
1. **[Cron設定ガイド](cron-setup-guide.md)** - 自動実行設定
2. **トラブルシューティング** - 設定関連問題

## 🔧 監視・診断ツール

### リアルタイム監視
- **[monitor_auto_issue_processor.sh](../../scripts/monitor_auto_issue_processor.sh)** - メイン監視スクリプト

### 診断ツール
```bash
# システム健全性チェック
./scripts/check_system_health.sh

# パフォーマンス分析
python3 scripts/analyze_performance.py

# セキュリティ監査
python3 scripts/security_audit.py
```

## ⚡ クイックアクション

### 緊急時の即座対応
```bash
# システム停止
sudo systemctl stop auto-issue-processor

# ログ確認
tail -f logs/auto_issue_processor.log | grep ERROR

# 再起動
sudo systemctl restart auto-issue-processor
```

### よくある問題の確認
```bash
# Issue #156-158の確認
grep -E "(RAG|process_request|security_issues)" logs/auto_issue_processor.log | tail -10

# 処理状況確認
gh pr list --search "Auto-fix" --state open
```

## 🔗 関連ドキュメント

- **[ユーザーガイド](../user-guides/)** - 使用方法
- **[API リファレンス](../api/)** - 技術仕様
- **[開発者ガイド](../developer-guides/)** - 開発参加

---
*最終更新: 2025年7月21日*