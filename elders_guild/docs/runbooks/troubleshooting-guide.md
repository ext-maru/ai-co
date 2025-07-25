# Auto Issue Processor A2A トラブルシューティングガイド

## 🔍 概要

このガイドでは、Auto Issue Processor A2Aで発生する一般的な問題とその解決方法を説明します。

## 🚨 よくある問題と解決方法

### 1. 認証・権限関連

#### GitHub認証エラー
```
Error: Bad credentials
```

**原因**: GitHub Personal Access Tokenが無効または期限切れ

**解決方法**:
```bash
# 1. 現在のトークン状態確認
gh auth status

# 2. 新しいトークンを生成
# GitHub.com → Settings → Developer settings → Personal access tokens → Generate new token
# 必要なスコープ: repo, workflow, read:org

# 3. 環境変数を更新
export GITHUB_TOKEN="ghp_新しいトークン"
echo "GITHUB_TOKEN=ghp_新しいトークン" >> .env

# 4. 権限確認
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### Claude API認証エラー
```
Error: Invalid API key
```

**解決方法**:
```bash
# 1. APIキーの確認
echo $CLAUDE_API_KEY

# 2. 正しいキーを設定
export CLAUDE_API_KEY="sk-ant-api03-正しいキー"

# 3. 接続テスト
python3 -c "
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(
    model='claude-3-opus-20240229',
    messages=[{'role': 'user', 'content': 'test'}],
    max_tokens=10
)
print('Claude API: OK')
"
```

### 2. 処理エラー

#### Issue #156: RAG Manager process_requestエラー
```
AttributeError: 'RagManager' object has no attribute 'process_request'
```

**一時的な回避策**:
```python
# libs/rag_manager_patch.py として保存
from libs.rag_manager import RagManager

async def process_request_patch(self, request):
    """一時的なprocess_requestメソッド"""
    query = request.get("query", "")
    try:
        results = self.search_knowledge(query)
        return {
            "status": "success",
            "results": results[:5]  # 上位5件
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": []
        }

# パッチ適用
RagManager.process_request = process_request_patch
```

#### Issue #157: 非同期処理エラー
```
TypeError: object NoneType can't be used in 'await' expression
```

**解決方法**:
```python
# 非同期関数の修正
async def safe_async_call(func, *args, **kwargs):
    """Noneチェック付き非同期呼び出し"""
    if func is None:
        return {"status": "skipped", "reason": "Function is None"}
    
    try:
        result = await func(*args, **kwargs)
        return result if result is not None else {"status": "empty"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

#### Issue #158: security_issuesキーエラー
```
KeyError: 'security_issues'
```

**解決方法**:
```python
# 品質ゲート結果の安全な取得
def get_security_issues(quality_results):
    """security_issuesを安全に取得"""
    return quality_results.get("security_issues", 0)

# または辞書のデフォルト値設定
quality_results.setdefault("security_issues", 0)
quality_results.setdefault("security_scan", "not_performed")
```

### 3. Git関連エラー

#### ブランチ作成エラー
```
Error: A branch named 'auto-fix-issue-123' already exists
```

**解決方法**:
```bash
# 1. 既存ブランチの確認
git branch -a | grep auto-fix

# 2. 古いブランチの削除
git branch -D auto-fix-issue-123
git push origin --delete auto-fix-issue-123

# 3. タイムスタンプ付きブランチ名を使用
export AUTO_ISSUE_USE_TIMESTAMP=true
```

#### マージコンフリクト
```
Error: Merge conflict in file
```

**解決方法**:
```bash
# 1. 最新のmainを取得
git checkout main
git pull origin main

# 2. ブランチをリベース
git checkout auto-fix-issue-123
git rebase main

# 3. コンフリクト解決
git status  # コンフリクトファイル確認
# ファイルを編集してコンフリクトマーカーを削除
git add .
git rebase --continue
```

### 4. パフォーマンス問題

#### 処理速度低下
**症状**: Issue処理に10分以上かかる

**診断**:
```bash
# プロファイリング実行
python3 -m cProfile -o profile.stats \
  libs/integrations/github/auto_issue_processor.py

# 結果分析
python3 -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
"
```

**解決方法**:
```python
# 1. 並列度の調整
os.environ["AUTO_ISSUE_MAX_PARALLEL"] = "3"

# 2. キャッシュサイズの増加
from libs.performance_optimizer import get_performance_optimizer
optimizer = get_performance_optimizer()
optimizer.config["cache_size"] = 200

# 3. タイムアウトの調整
optimizer.config["operation_timeout"] = 300
```

#### メモリ使用量過多
**症状**: メモリ使用率が80%を超える

**解決方法**:
```python
# 1. メモリプロファイリング
from memory_profiler import profile

@profile
def memory_intensive_function():
    # 処理

# 2. ガベージコレクション強制
import gc
gc.collect()

# 3. 大きなオブジェクトの解放
del large_object
gc.collect()
```

### 5. ログ・監視関連

#### ログが出力されない
**解決方法**:
```bash
# 1. ログレベル確認
export AUTO_ISSUE_LOG_LEVEL=DEBUG

# 2. ログディレクトリの権限確認
ls -la logs/
chmod 755 logs/
chmod 644 logs/*.log

# 3. ログローテーション確認
cat /etc/logrotate.d/auto-issue-processor
```

#### 監視ツールが動作しない
```bash
# 1. 依存関係確認
which watch
which jq

# 2. 手動実行
bash -x ./scripts/monitor_auto_issue_processor.sh

# 3. 権限確認
chmod +x scripts/monitor_auto_issue_processor.sh
```

## 🛠️ 診断コマンド集

### システム全体の健全性チェック
```bash
python3 scripts/health_check.py --full
```

### 特定のIssueのデバッグ
```bash
python3 libs/integrations/github/auto_issue_processor.py \
  --debug \
  --issue 123 \
  --dry-run
```

### 4賢者システムのテスト
```python
# scripts/test_four_sages.py
import asyncio
from libs.elder_flow_four_sages_complete import consult_four_sages

async def test_sages():
    context = {
        "issue_number": 123,
        "issue_title": "Test Issue",
        "issue_body": "Test description"
    }
    
    result = await consult_four_sages(context)
    for sage, advice in result.items():
        print(f"{sage}: {advice.get('status')}")

asyncio.run(test_sages())
```

## 🔄 リカバリ手順

### 完全リセット
```bash
# 1. サービス停止
sudo systemctl stop auto-issue-processor

# 2. キャッシュクリア
rm -rf cache/*
rm -f /tmp/auto_issue_processor.*

# 3. データベース再構築
mv data/auto_issue_processor.db data/auto_issue_processor.db.bak
python3 scripts/init_database.py

# 4. サービス再起動
sudo systemctl start auto-issue-processor
```

### 部分的リカバリ
```bash
# 特定のIssueの処理履歴削除
python3 -c "
import json
with open('logs/auto_issue_processing.json', 'r') as f:
    data = json.load(f)
data['recent_issues'] = [i for i in data['recent_issues'] if i != 123]
with open('logs/auto_issue_processing.json', 'w') as f:
    json.dump(data, f)
"
```

## 📚 参考情報

### ログファイルの場所
- メインログ: `logs/auto_issue_processor.log`
- エラーログ: `logs/error.log`
- 処理履歴: `logs/auto_issue_processing.json`
- 監視ログ: `logs/monitoring.log`

### 設定ファイル
- 環境変数: `.env`
- システム設定: `configs/auto_issue_processor.yaml`
- 品質ゲート: `configs/quality_gate.yaml`

### 便利なエイリアス
```bash
# ~/.bashrc に追加
alias aip-status='systemctl status auto-issue-processor'
alias aip-logs='tail -f logs/auto_issue_processor.log'
alias aip-errors='grep ERROR logs/auto_issue_processor.log | tail -20'
alias aip-monitor='./scripts/monitor_auto_issue_processor.sh'
```

## 🔗 関連ドキュメント

- [最新改善事項](recent-improvements-july-2025.md) - Issue #156-158の詳細
- [インシデント対応ガイド](incident-response-guide.md)
- [日常運用ガイド](daily-operations-guide.md)

---
*最終更新: 2025年7月21日*