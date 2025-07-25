# 🏛️ Ancient Magic System 使用ガイド

**最終更新**: 2025-07-21  
**作成者**: クロードエルダー（Claude Elder）

## 📋 目次

1. [クイックスタート](#クイックスタート)
2. [基本的な使い方](#基本的な使い方)
3. [高度な使用例](#高度な使用例)
4. [パフォーマンスチューニング](#パフォーマンスチューニング)
5. [トラブルシューティング](#トラブルシューティング)
6. [ベストプラクティス](#ベストプラクティス)

## 🚀 クイックスタート

### インストール確認
```bash
# コマンドが利用可能か確認
ai-ancient-magic --help

# 利用可能な魔法を確認
ai-ancient-magic list
```

### 最初の監査
```bash
# 現在のディレクトリを監査
ai-ancient-magic audit

# 健康診断（最も簡単）
ai-ancient-magic health
```

## 📖 基本的な使い方

### 1. 健康診断コマンド
プロジェクトの全体的な品質状態を素早く確認：

```bash
# デフォルト（直近7日間）
ai-ancient-magic health

# 期間を指定
ai-ancient-magic health --days 30

# 出力例
🏥 Diagnosing Elders Guild health...

🎉 Guild Health Score: 92.3/100 - 🟢 Excellent

📊 Statistics:
  total_auditors: 6
  successful_audits: 6
  failed_audits: 0
  total_violations: 12
```

### 2. 包括的監査
全ての古代魔法を使用した詳細な監査：

```bash
# 基本的な包括的監査
ai-ancient-magic audit --comprehensive

# 特定のディレクトリを対象
ai-ancient-magic audit --target ./src --comprehensive

# 結果をファイルに保存
ai-ancient-magic audit --comprehensive --output audit_report.json
```

### 3. 個別魔法の実行
特定の観点のみを監査：

```bash
# Git履歴品質のみチェック
ai-ancient-magic single git --target .

# TDD遵守状況のみチェック
ai-ancient-magic single tdd --target ./tests

# 利用可能な魔法タイプ
# - integrity: 誠実性・Iron Will監査
# - tdd: TDDサイクル監査
# - flow: Elder Flow遵守監査
# - sages: 4賢者協調監査
# - git: Git履歴品質監査
# - servant: サーバント監査
```

## 🎯 高度な使用例

### 1. CI/CDパイプライン統合
```yaml
# .github/workflows/ancient-magic.yml
name: Ancient Magic Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Ancient Magic Audit
        run: |
          ai-ancient-magic audit --comprehensive --output audit.json
          
      - name: Check Health Score
        run: |
          score=$(jq '.guild_health_score' audit.json)
          if (( $(echo "$score < 70" | bc -l) )); then
            echo "❌ Health score too low: $score"
            exit 1
          fi
```

### 2. Pre-commitフック
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 軽量な品質チェック
ai-ancient-magic single integrity --target . || {
    echo "❌ Integrity check failed"
    exit 1
}

echo "✅ Ancient Magic checks passed"
```

### 3. 定期監査スクリプト
```bash
#!/bin/bash
# scripts/weekly-audit.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="audit_reports"
mkdir -p "$REPORT_DIR"

# 包括的監査を実行
ai-ancient-magic audit \
    --comprehensive \
    --output "$REPORT_DIR/audit_$DATE.json"

# 健康スコアを抽出
score=$(jq '.guild_health_score' "$REPORT_DIR/audit_$DATE.json")
echo "Health Score: $score" > "$REPORT_DIR/summary_$DATE.txt"

# Slackに通知（オプション）
# curl -X POST -H 'Content-type: application/json' \
#     --data "{\"text\":\"Weekly Audit Complete. Score: $score\"}" \
#     YOUR_SLACK_WEBHOOK_URL
```

## ⚡ パフォーマンスチューニング

### 1. キャッシュの活用
```python
# Python APIでキャッシュを有効化
from libs.ancient_elder.audit_cache import AuditCache, CachedAuditEngine
from libs.ancient_elder.audit_engine import AncientElderAuditEngine

# キャッシュ付きエンジンを作成
cache = AuditCache(ttl_hours=24)
engine = AncientElderAuditEngine()
cached_engine = CachedAuditEngine(engine, cache)

# 2回目以降は高速
result = await cached_engine.run_comprehensive_audit(target)
```

### 2. 部分的な監査
大規模プロジェクトでは部分的な監査を推奨：

```bash
# srcディレクトリのみ
ai-ancient-magic audit --target ./src

# テストファイルのみTDDチェック
ai-ancient-magic single tdd --target ./tests

# 直近の変更のみ監査（Git Chronicle）
ai-ancient-magic single git --target . --days 7
```

### 3. タイムアウト設定
```python
# TDD Guardianのタイムアウト設定
target = {
    "path": ".",
    "quick_mode": True,  # 高速モード
    "timeout": 30        # 30秒でタイムアウト
}
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. "Command not found"エラー
```bash
# PATHに追加
export PATH="$PATH:/home/aicompany/ai_co/scripts"

# または直接実行
/home/aicompany/ai_co/scripts/ai-ancient-magic list
```

#### 2. タイムアウトエラー
```bash
# TDD Guardianがタイムアウトする場合
# quick_modeを使用（現在未実装のため、個別実行を推奨）
ai-ancient-magic single integrity --target .
ai-ancient-magic single git --target .
# TDDはスキップ
```

#### 3. Git関連エラー
```bash
# Gitリポジトリでない場合
cd /path/to/git/repo
ai-ancient-magic audit

# 権限エラーの場合
sudo chown -R $(whoami) .git
```

#### 4. メモリ不足
```bash
# 大規模プロジェクトの場合、部分実行
find ./src -name "*.py" -type f | head -20 | while read f; do
    ai-ancient-magic single integrity --target "$f"
done
```

### デバッグモード
```bash
# 詳細ログを有効化
export ANCIENT_MAGIC_DEBUG=1
ai-ancient-magic audit

# Pythonで直接実行してエラーを確認
python3 /home/aicompany/ai_co/commands/ai_ancient_magic.py list
```

## 💡 ベストプラクティス

### 1. 定期的な実行
- **日次**: `ai-ancient-magic health` で健康状態確認
- **週次**: `ai-ancient-magic audit --comprehensive` で詳細監査
- **コミット前**: `ai-ancient-magic single integrity` で品質チェック

### 2. 段階的な改善
1. まず健康スコア70以上を目指す
2. 個別の違反を優先度順に修正
3. Critical → High → Medium → Low の順で対応

### 3. チーム運用
```bash
# チーム共通の設定ファイル
cat > .ancient-magic.json << EOF
{
  "minimum_health_score": 80,
  "required_auditors": ["integrity", "git", "tdd"],
  "cache_ttl_hours": 48,
  "timeout_seconds": 60
}
EOF
```

### 4. 違反の修正例

#### Conventional Commits違反
```bash
# 悪い例
git commit -m "updated files"

# 良い例
git commit -m "feat: add user authentication module"
git commit -m "fix: resolve memory leak in worker process"
```

#### TODO/FIXME違反
```python
# 悪い例
# TODO: これを後で実装する
def incomplete_function():
    pass

# 良い例
def complete_function():
    """完全に実装された機能"""
    return process_data()
```

#### ブランチ命名違反
```bash
# 悪い例
git checkout -b my-branch

# 良い例
git checkout -b feature/issue-123-user-auth
git checkout -b fix/issue-456-memory-leak
```

## 📊 結果の解釈

### Health Scoreの意味
- **90-100**: 優秀 - エルダーズギルド基準を完全に満たしている
- **70-89**: 良好 - 軽微な改善点はあるが、全体的に健全
- **50-69**: 要注意 - 複数の問題があり、改善が必要
- **0-49**: 危険 - 重大な問題が多数存在、緊急対応が必要

### 違反の重要度
- **🚨 CRITICAL**: 即座に修正が必要（セキュリティリスク、ビルド破壊など）
- **⚠️ HIGH**: 重要な問題（品質基準違反、パフォーマンス問題など）
- **📋 MEDIUM**: 中程度の問題（規約違反、改善推奨事項など）
- **💡 LOW**: 軽微な問題（スタイル違反、最適化提案など）

## 🆘 サポート

問題が解決しない場合：

1. [Issue文書](../issues/issue-ancient-magic-system.md)を確認
2. エラーログを収集：
   ```bash
   ai-ancient-magic audit 2>&1 | tee ancient_magic_error.log
   ```
3. エルダー評議会に報告（Issue作成）

---

**Remember: Quality is not an act, it is a habit! 🏛️**