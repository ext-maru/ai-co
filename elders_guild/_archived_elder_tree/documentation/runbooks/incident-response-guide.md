# Auto Issue Processor A2A インシデント対応ガイド

## 🚨 概要

このガイドでは、Auto Issue Processor A2Aで発生する可能性のあるインシデントと、その対応手順を説明します。

## 📊 インシデントレベル定義

| レベル | 説明 | 対応時間 | 例 |
|--------|------|----------|-----|
| **P1 (Critical)** | システム完全停止 | 即座 | 全処理停止、データ損失 |
| **P2 (High)** | 主要機能の障害 | 1時間以内 | PR作成失敗、4賢者エラー |
| **P3 (Medium)** | 部分的な機能低下 | 4時間以内 | 品質ゲート失敗、遅延 |
| **P4 (Low)** | 軽微な問題 | 翌営業日 | UI表示不具合、警告 |

## 🔥 P1: Critical インシデント

### システム完全停止

#### 症状
- Auto Issue Processorが全く動作しない
- すべてのAPIがタイムアウト
- ログ出力が停止

#### 対応手順

```bash
# 1. 初期診断（5分以内）
systemctl status auto-issue-processor
ps aux | grep auto_issue_processor
tail -f /var/log/syslog | grep auto-issue

# 2. 緊急再起動試行
sudo systemctl restart auto-issue-processor

# 3. 手動起動（サービス起動失敗時）
cd /home/aicompany/ai_co
source venv/bin/activate
python3 libs/integrations/github/auto_issue_processor.py --emergency-mode

# 4. 依存サービス確認
# GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Claude API
curl -H "x-api-key: $CLAUDE_API_KEY" https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-opus-20240229","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

#### エスカレーション
15分以内に復旧しない場合:
1. インシデント賢者に自動通知
2. エルダー評議会緊急招集
3. グランドエルダーmaruへの報告

### データベース接続エラー

#### 症状
```
Error: connection to database failed
sqlite3.OperationalError: database is locked
```

#### 対応手順
```bash
# 1. ロック解除
fuser -k data/auto_issue_processor.db

# 2. データベース整合性チェック
sqlite3 data/auto_issue_processor.db "PRAGMA integrity_check;"

# 3. 必要に応じてバックアップから復元
cp backups/auto_issue_processor_latest.db data/auto_issue_processor.db

# 4. 再起動
systemctl restart auto-issue-processor
```

## ⚡ P2: High インシデント

### PR作成失敗の連続

#### 症状
- 複数のIssueでPR作成が失敗
- エラー: "Failed to create pull request"

#### 対応手順
```python
# 1. GitHub権限確認
import subprocess
result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
print(result.stdout)

# 2. ブランチ状態確認
subprocess.run(["git", "branch", "-a"], check=True)
subprocess.run(["git", "status"], check=True)

# 3. 一時的な回避策
# safe_git_operations.pyを使用
from libs.integrations.github.safe_git_operations import SafeGitOperations
safe_git = SafeGitOperations()
safe_git.cleanup_failed_branches()
```

### 4賢者システムエラー（Issue #156-158関連）

#### 症状
- RAG賢者の`process_request`エラー
- 非同期処理でNoneTypeエラー
- security_issuesキーエラー

#### 対応手順
```python
# 1. 個別賢者の状態確認
from libs.knowledge_sage import KnowledgeSage
from libs.task_sage import TaskSage
from libs.incident_sage import IncidentSage
from libs.rag_manager import RagManager

# 各賢者の初期化テスト
try:
    knowledge = KnowledgeSage()
    print("Knowledge Sage: OK")
except Exception as e:
    print(f"Knowledge Sage Error: {e}")

# 2. 一時的な回避（RAG賢者）
# process_requestメソッドの追加
class RagManagerPatch:
    async def process_request(self, request):
        # 既存のsearch_knowledgeをラップ
        query = request.get("query", "")
        results = await self.search_knowledge(query)
        return {"status": "success", "results": results}

# 3. 品質ゲートのパッチ
# security_issuesのデフォルト値設定
quality_results.setdefault("security_issues", 0)
```

## 🔧 P3: Medium インシデント

### 処理遅延

#### 症状
- 平均処理時間が5分を超える
- キューに10件以上のIssueが滞留

#### 対応手順
```bash
# 1. ボトルネック特定
python3 scripts/analyze_performance.py --last-hour

# 2. リソース確認
htop  # CPU/メモリ使用率確認
iotop  # ディスクI/O確認

# 3. 並列度調整
export AUTO_ISSUE_MAX_PARALLEL=3  # 一時的に並列度を下げる

# 4. キャッシュクリア
python3 -c "
from libs.performance_optimizer import get_performance_optimizer
optimizer = get_performance_optimizer()
optimizer.clear_cache()
"
```

### 品質ゲート頻繁な失敗

#### 症状
- 50%以上のIssueで品質ゲートが失敗
- "Quality gate failed"エラー

#### 対応手順
```bash
# 1. 品質基準の確認
cat configs/quality_gate.yaml

# 2. 一時的な基準緩和
export QUALITY_GATE_MIN_SCORE=50  # 通常は70

# 3. 詳細ログ有効化
export AUTO_ISSUE_DEBUG_QUALITY=true
```

## 📋 P4: Low インシデント

### ログローテーション失敗

#### 症状
- ログファイルが肥大化
- ディスク使用率警告

#### 対応手順
```bash
# 手動ローテーション
logrotate -f /etc/logrotate.d/auto-issue-processor

# 古いログの削除
find logs/ -name "*.log.gz" -mtime +30 -delete
```

## 🔍 診断ツール

### 包括的診断スクリプト

```bash
#!/bin/bash
# scripts/diagnose_system.sh

echo "=== Auto Issue Processor Diagnostics ==="
echo "Time: $(date)"

# サービス状態
echo -e "\n[Service Status]"
systemctl status auto-issue-processor --no-pager

# リソース使用状況
echo -e "\n[Resource Usage]"
free -h
df -h /
ps aux | grep auto_issue | head -5

# 最新のエラー
echo -e "\n[Recent Errors]"
grep -i error logs/auto_issue_processor.log | tail -10

# API接続性
echo -e "\n[API Connectivity]"
curl -s -o /dev/null -w "GitHub API: %{http_code}\n" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# 処理統計
echo -e "\n[Processing Stats]"
tail -1 logs/auto_issue_processing.json | jq '.'
```

## 📞 エスカレーションマトリクス

| インシデントタイプ | 初期対応 | エスカレーション先 | タイムアウト |
|-------------------|---------|------------------|------------|
| システム停止 | 運用チーム | インシデント賢者 → エルダー評議会 | 15分 |
| データ損失 | 運用チーム | エルダー評議会 → グランドエルダー | 即座 |
| セキュリティ侵害 | セキュリティチーム | グランドエルダー | 即座 |
| パフォーマンス低下 | 運用チーム | タスク賢者 | 1時間 |

## 🔗 関連ドキュメント

- [日常運用ガイド](daily-operations-guide.md)
- [トラブルシューティングガイド](troubleshooting-guide.md)
- [最新改善事項](recent-improvements-july-2025.md)

---
*最終更新: 2025年7月21日*