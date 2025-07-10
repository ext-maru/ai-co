# 📋 Elders Guild インシデント管理システム

既存のエラー管理機能を拡張した包括的なインシデント管理システムです。

## 🎯 概要

このシステムは、Elders Guildプロジェクトで発生するあらゆる問題を一元管理します：

- **エラー** - システムエラー、例外（既存のerror_handlingと連携）
- **障害** - サービス停止、機能不全
- **要求** - 新機能要求、サービス要求  
- **変更** - 設定変更、構成変更
- **セキュリティ** - セキュリティインシデント
- **パフォーマンス** - 処理遅延、リソース問題

## 📁 ディレクトリ構造

```
incident_management/
├── README.md                    # このファイル
├── incident_history.json        # インシデント履歴DB
├── INCIDENT_PATTERNS_KB.md      # インシデントパターンナレッジ
├── incident_manager.py          # コア管理システム
├── error_incident_bridge.py     # エラー管理との統合
└── auto_fix/                    # 自動修正スクリプト（今後実装）
```

## 🚀 使い方

### 1. インシデントの作成

```bash
python incident_manager.py create \
  --category error \
  --priority high \
  --title "RabbitMQ接続エラー" \
  --description "ワーカーがRabbitMQに接続できない" \
  --components worker_base rabbitmq_client \
  --impact "全ワーカー停止"
```

### 2. インシデントの一覧表示

```bash
# 全てのオープンインシデント
python incident_manager.py list

# カテゴリ別
python incident_manager.py list --category failure
```

### 3. インシデントの更新

```bash
python incident_manager.py update \
  --id INC-20250104-0001 \
  --status in_progress
```

### 4. インシデントの解決

```bash
python incident_manager.py resolve \
  --id INC-20250104-0001 \
  --actions "RabbitMQサービス再起動" "接続設定修正" \
  --root-cause "RabbitMQサービスの異常停止" \
  --preventive "自動監視スクリプト追加" "ヘルスチェック強化"
```

### 5. レポート生成

```bash
# 統計レポート
python incident_manager.py report

# パターン分析
python incident_manager.py analyze
```

## 🔄 既存システムとの統合

### エラー管理との連携

```bash
# 既存のエラー履歴を移行
python error_incident_bridge.py migrate

# 統合レポートの生成
python error_incident_bridge.py report

# 整合性チェック
python error_incident_bridge.py check
```

### プログラムからの利用

```python
from incident_manager import IncidentManager

# インスタンス作成
manager = IncidentManager()

# インシデント作成
incident_id = manager.create_incident(
    category="failure",
    priority="critical",
    title="データベース接続断",
    description="PostgreSQLへの接続が切断された",
    affected_components=["db_client", "worker_analytics"],
    impact="分析処理の停止"
)

# 解決
manager.resolve_incident(
    incident_id=incident_id,
    actions_taken=["接続プール再初期化", "タイムアウト値調整"],
    root_cause="接続プールの枯渇",
    preventive_measures=["接続プール監視追加"]
)
```

## 📊 インシデントカテゴリ詳細

| カテゴリ | 用途 | 優先度目安 | 例 |
|----------|------|-----------|-----|
| error | プログラムエラー | High-Critical | ModuleNotFoundError, TypeError |
| failure | サービス障害 | Critical | ワーカー停止、DB接続断 |
| request | 機能要求 | Low-Medium | 新機能追加、改善要望 |
| change | 設定変更 | Medium | config更新、環境変更 |
| security | セキュリティ | Critical | 認証エラー、不正アクセス |
| performance | 性能問題 | Medium-High | 処理遅延、メモリリーク |

## 🚨 優先度ガイドライン

| 優先度 | 応答時間 | 解決時間 | 基準 |
|--------|----------|----------|------|
| Critical | 即時 | 4時間 | サービス停止、データ損失リスク |
| High | 30分 | 24時間 | 主要機能の障害 |
| Medium | 4時間 | 3日 | 副次機能の問題 |
| Low | 24時間 | 1週間 | 改善要望、軽微な問題 |

## 🔧 自動化との連携

### AI Command Executorでの利用

```python
from libs.ai_command_helper import AICommandHelper
helper = AICommandHelper()

# インシデント対応スクリプトの作成
incident_script = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# インシデント作成
python /path/to/incident_manager.py create \\
  --category failure \\
  --priority critical \\
  --title "ワーカー全停止" \\
  --description "全ワーカーが応答なし" \\
  --components all_workers \\
  --impact "処理完全停止"

# 自動復旧試行
systemctl restart ai-company-workers
"""

helper.create_bash_command(incident_script, "handle_worker_failure")
```

## 📈 メトリクス

システムは以下のメトリクスを自動追跡：

- **MTTR** (Mean Time To Resolve) - 平均解決時間
- **MTBF** (Mean Time Between Failures) - 平均故障間隔  
- **再発率** - 同一問題の再発頻度
- **カテゴリ別統計** - 問題の傾向分析
- **コンポーネント別影響度** - 最も問題が多いコンポーネント

## 🔄 継続的改善

1. **定期レビュー**
   - 週次: オープンインシデントの確認
   - 月次: パターン分析とKB更新
   - 四半期: プロセス改善

2. **ナレッジ蓄積**
   - 解決済みインシデントからパターン抽出
   - INCIDENT_PATTERNS_KB.mdへの追記
   - 自動修正スクリプトの開発

3. **予防策の実装**
   - 頻発パターンの根本対策
   - 監視・アラートの強化
   - 自動復旧機能の拡充

## 🎯 今後の拡張予定

- [ ] Slack通知統合
- [ ] 自動エスカレーション
- [ ] インシデント予測（ML活用）
- [ ] ダッシュボード UI
- [ ] SLA管理機能
- [ ] 外部チケットシステム連携

---

**インシデント管理により、Elders Guildシステムの安定性と信頼性を継続的に向上させます！**
