# 🚀 AI Company システム改善実行ガイド

## 概要
このガイドは、AI Companyシステムの主要な問題を解決し、システムを改善するための完全な手順を提供します。

## 実装した機能

### 1. 緊急修正スクリプト (`fix_ai_company_urgent.sh`)
- Slackログファイルの自動クリーンアップ
- ログローテーション設定
- バックアップファイルの整理
- インシデント自動記録

### 2. システム健全性チェッカー (`ai_company_health_check.py`)
- ディスク使用状況チェック
- ログファイル分析
- ワーカー状態確認
- 健全性スコア算出

### 3. ワーカー整理ツール (`organize_workers.py`)
- 重複ワーカーの自動検出
- アーカイブディレクトリへの移動
- インポート更新の提案

### 4. インシデント管理 (`incident_manager.py`)
- エラー発生時の自動インシデント作成
- アクション追跡
- 解決記録
- 類似インシデント検索

### 5. 統合管理ツール (`ai_company_manager.sh`)
- health: 健全性チェック
- fix: 緊急修正
- clean: クリーンアップ
- report: レポート生成
- monitor: リアルタイム監視
- backup: バックアップ作成

## 実行手順

### Step 1: テスト実行
```bash
cd /home/aicompany/ai_co
python3 execute_tests_and_fix.py
```

### Step 2: エラーがある場合は修正
```bash
python3 fix_test_errors.py
```

### Step 3: システム改善を実行
```bash
python3 final_system_improvement.py
```

### Step 4: 結果確認
```bash
# 健全性チェック
bash scripts/ai_company_manager.sh health

# ログ確認
bash scripts/ai_company_manager.sh report

# リアルタイム監視
bash scripts/ai_company_manager.sh monitor
```

### Step 5: システム再起動
```bash
ai-restart
```

## 期待される効果

| 指標 | 改善前 | 改善後 |
|------|--------|--------|
| Slackログファイル数 | 472個/日 | <10個/日 |
| ディスク使用量 | 数GB | <1GB |
| 重複ワーカー | 10+ | 0 |
| インシデント記録率 | 0% | 90%+ |
| システム健全性スコア | 不明 | 80+/100 |

## トラブルシューティング

### pytest が見つからない場合
```bash
pip install pytest pytest-json-report
```

### 権限エラーが発生する場合
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

### RabbitMQが停止している場合
```bash
sudo systemctl start rabbitmq-server
```

## 定期メンテナンス

毎週実行を推奨:
```bash
# クリーンアップ
bash scripts/ai_company_manager.sh clean

# 健全性チェック
bash scripts/ai_company_manager.sh health

# バックアップ
bash scripts/ai_company_manager.sh backup
```

## 作成されたテスト

- `test_emergency_fix.py`: 緊急修正機能のテスト
- `test_health_checker.py`: 健全性チェッカーのテスト
- `test_worker_organizer.py`: ワーカー整理のテスト
- `test_incident_manager.py`: インシデント管理のテスト
- `test_error_intelligence_worker_incident.py`: Error Intelligence Worker改修のテスト
- `test_ai_company_manager.py`: 統合管理ツールのテスト

## 既存機能の活用

以下のAI Company既存機能を活用しています:
- AI Command Executor
- Slack Notifier
- Task Sender
- Log Manager
- Test Manager
- BaseWorker/BaseManager
- Error Intelligence Manager

## まとめ

このシステム改善により:
1. **運用負荷の大幅削減** - 自動化により手動作業が不要に
2. **システム安定性の向上** - ログ管理とリソース最適化
3. **問題追跡の改善** - インシデント管理による可視化
4. **保守性の向上** - 重複コードの整理と構造化

継続的な改善のため、定期的な健全性チェックとメンテナンスを実施してください。

---
*AI Company - より健全で効率的なシステムへ*
