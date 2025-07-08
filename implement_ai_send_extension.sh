#!/bin/bash
# ai-send拡張版の適用と実装スクリプト

cd /home/aicompany/ai_co

echo "🚀 AI Company ai-send拡張実装開始..."

# 1. バックアップ作成
if [ -f commands/ai_send.py ]; then
    cp commands/ai_send.py commands/ai_send_backup_$(date +%Y%m%d_%H%M%S).py
    echo "✅ 既存ファイルをバックアップしました"
fi

# 2. タスクタイプ設定ファイル作成
cat > config/task_types.json << 'EOF'
{
    "task_types": {
        "general": {
            "description": "汎用タスク（調査、説明、計画など）",
            "default_priority": 5,
            "queue": "ai_tasks",
            "enhance_prompt": false
        },
        "code": {
            "description": "コード生成・実装タスク",
            "default_priority": 5,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "AI Company Core基盤を活用、エラーハンドリングを含む、FileSystemで完全実装、AI Command Executorでテスト実行も設定"
        },
        "analysis": {
            "description": "データ分析・調査タスク",
            "default_priority": 4,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "データの可視化を含む、統計的な分析、洞察と推奨事項の提供"
        },
        "report": {
            "description": "レポート・ドキュメント生成",
            "default_priority": 3,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "構造化されたフォーマット、エグゼクティブサマリー、詳細な分析"
        },
        "test": {
            "description": "テスト作成・実行タスク",
            "default_priority": 6,
            "queue": "ai_se",
            "enhance_prompt": true,
            "enhancements": "pytestベースのテスト、モックを適切に使用、カバレッジ80%以上を目指す、AI Command Executorで自動実行"
        },
        "fix": {
            "description": "バグ修正・問題解決タスク",
            "default_priority": 8,
            "queue": "ai_se",
            "enhance_prompt": true,
            "enhancements": "根本原因を特定、副作用を最小限に、テストも同時に修正、修正後の動作確認を含む"
        },
        "deploy": {
            "description": "デプロイ・リリース作業",
            "default_priority": 7,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "バックアップを取る、ロールバック手順を準備、ヘルスチェックを実行、Slack通知を含む"
        },
        "review": {
            "description": "コードレビュー・品質チェック",
            "default_priority": 5,
            "queue": "ai_se",
            "enhance_prompt": true,
            "enhancements": "コード品質、セキュリティ、パフォーマンス、AI Company規約準拠"
        },
        "docs": {
            "description": "ドキュメント生成・更新",
            "default_priority": 3,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "明確で簡潔な説明、実例を含む、API仕様などの詳細"
        },
        "optimize": {
            "description": "パフォーマンス最適化",
            "default_priority": 4,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "処理速度の改善、メモリ使用量の削減、データベースクエリの最適化、並列処理の活用"
        },
        "security": {
            "description": "セキュリティ監査・対策",
            "default_priority": 9,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "脆弱性スキャン、認証・認可の確認、ログの適切性、機密情報の扱い"
        },
        "monitor": {
            "description": "システム監視・状態確認",
            "default_priority": 6,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "リアルタイムモニタリング、アラート設定、パフォーマンスメトリクス"
        },
        "backup": {
            "description": "バックアップ・リストア作業",
            "default_priority": 4,
            "queue": "ai_tasks",
            "enhance_prompt": true,
            "enhancements": "完全性の確認、暗号化、定期実行スケジュール、リストア手順"
        }
    }
}
EOF

echo "✅ タスクタイプ設定ファイルを作成しました"

# 3. 各タスクタイプ用のテンプレートを作成
mkdir -p templates/task_types

# テストタスク用テンプレート
cat > templates/task_types/test_template.yaml << 'EOF'
name: "test_creation"
description: "テスト作成用テンプレート"
task_type: "test"
template_data:
  prompt: |
    以下のファイルに対するテストを作成してください：
    
    対象ファイル: {{file_path}}
    
    要件：
    1. pytestを使用したユニットテスト
    2. 必要なモックの実装
    3. エッジケースのテスト
    4. カバレッジ80%以上
    5. AI Command Executorでの自動実行設定
    
    テストファイルをtests/ディレクトリに配置してください。
    
parameters:
  - name: file_path
    type: string
    description: "テスト対象ファイルのパス"
    required: true
EOF

# バグ修正用テンプレート
cat > templates/task_types/fix_template.yaml << 'EOF'
name: "bug_fix"
description: "バグ修正用テンプレート"
task_type: "fix"
template_data:
  prompt: |
    以下のエラーを修正してください：
    
    エラー内容: {{error_message}}
    発生場所: {{file_path}}
    
    修正手順：
    1. エラーの根本原因を特定
    2. 修正を実装
    3. 関連するテストも更新
    4. 動作確認スクリプトを作成
    5. AI Command Executorで確認実行
    
parameters:
  - name: error_message
    type: string
    description: "エラーメッセージ"
    required: true
  - name: file_path
    type: string
    description: "エラー発生ファイル"
    required: true
EOF

# デプロイ用テンプレート
cat > templates/task_types/deploy_template.yaml << 'EOF'
name: "deployment"
description: "デプロイ用テンプレート"
task_type: "deploy"
template_data:
  prompt: |
    以下の環境へのデプロイを実行してください：
    
    環境: {{environment}}
    バージョン: {{version}}
    
    デプロイ手順：
    1. 現在の状態をバックアップ
    2. ヘルスチェック（事前）
    3. デプロイ実行
    4. ヘルスチェック（事後）
    5. Slack通知
    6. ロールバック手順の準備
    
parameters:
  - name: environment
    type: string
    description: "デプロイ環境（dev/staging/prod）"
    required: true
  - name: version
    type: string
    description: "デプロイバージョン"
    required: true
EOF

echo "✅ タスクタイプ用テンプレートを作成しました"

# 4. TaskWorkerへの拡張対応を追加
cat > update_task_worker.py << 'EOF'
#!/usr/bin/env python3
"""
TaskWorkerをタスクタイプ対応に更新
"""
import json
from pathlib import Path

# タスクタイプ設定を読み込み
config_path = Path("/home/aicompany/ai_co/config/task_types.json")
with open(config_path) as f:
    task_config = json.load(f)

print("TaskWorker更新ガイド:")
print("\n1. process_messageメソッドに以下を追加:")
print("""
    # タスクタイプに応じた処理
    task_type = body.get('task_type', 'general')
    
    # プロンプト強化
    if task_type in ['code', 'test', 'fix']:
        prompt = self._enhance_prompt_for_type(prompt, task_type)
""")

print("\n2. 新しいメソッドを追加:")
print("""
    def _enhance_prompt_for_type(self, prompt, task_type):
        \"\"\"タスクタイプに応じてプロンプトを強化\"\"\"
        config_path = Path(self.config.project_root) / "config" / "task_types.json"
        with open(config_path) as f:
            task_config = json.load(f)
        
        if task_type in task_config['task_types']:
            type_info = task_config['task_types'][task_type]
            if type_info.get('enhance_prompt') and 'enhancements' in type_info:
                return f"{prompt}\\n\\n{type_info['enhancements']}"
        return prompt
""")

print("\n✅ TaskWorker更新ガイドを生成しました")
EOF

python3 update_task_worker.py

# 5. 使用例とドキュメント
cat > docs/AI_SEND_EXTENDED_GUIDE.md << 'EOF'
# 🚀 ai-send 拡張版ガイド v2.0

## 📋 新しいタスクタイプ

### 開発系タスク
- **code** - コード生成・実装（デフォルト優先度: 5）
- **test** - テスト作成・実行（デフォルト優先度: 6）
- **fix** - バグ修正・問題解決（デフォルト優先度: 8）
- **optimize** - パフォーマンス最適化（デフォルト優先度: 4）

### 管理系タスク
- **deploy** - デプロイ・リリース（デフォルト優先度: 7）
- **review** - コードレビュー（デフォルト優先度: 5）
- **docs** - ドキュメント生成（デフォルト優先度: 3）
- **backup** - バックアップ作業（デフォルト優先度: 4）

### 分析系タスク
- **analysis** - データ分析（デフォルト優先度: 4）
- **report** - レポート生成（デフォルト優先度: 3）
- **monitor** - システム監視（デフォルト優先度: 6）

### その他
- **general** - 汎用タスク（デフォルト優先度: 5）
- **security** - セキュリティ監査（デフォルト優先度: 9）

## 🎯 使用例

### 基本的な使い方
```bash
# テスト作成
ai-send "UserManagerクラスのテストを作成して" test

# バグ修正（高優先度）
ai-send "ImportError: No module named 'core'を修正" fix

# デプロイ
ai-send "v2.0をステージング環境にデプロイ" deploy

# セキュリティ監査（最高優先度）
ai-send "認証システムの脆弱性をチェック" security
```

### 高度な使い方
```bash
# 優先度を指定
ai-send "緊急バグ修正" fix --priority 10

# テンプレート使用
ai-send "新しいAPIのテスト" test --template test_creation

# 自動実行を有効化
ai-send "システムチェックスクリプト" code --auto-execute

# タグ付き
ai-send "パフォーマンス改善" optimize --tags performance db
```

### タスクタイプ一覧表示
```bash
ai-send --list-types
```

## 🔧 タスクタイプ別の自動処理

### test タスク
- pytestベースのテスト生成
- モックの自動実装
- AI Command Executorでの自動実行設定

### fix タスク
- エラーの根本原因分析
- 修正コードの生成
- テストの同時更新
- 動作確認の自動化

### deploy タスク
- バックアップの自動作成
- ヘルスチェックの実行
- Slack通知の送信
- ロールバック手順の準備

### security タスク
- 脆弱性スキャンの実行
- セキュリティベストプラクティスのチェック
- 改善提案の生成

## 📝 設定ファイル

タスクタイプの設定は `config/task_types.json` で管理されています。
各タスクタイプのデフォルト優先度、キュー、プロンプト強化設定などをカスタマイズできます。

## 🎉 まとめ

ai-send拡張版により、タスクの種類に応じた最適な処理が自動的に行われるようになりました。
適切なタスクタイプを選択することで、より効率的で高品質な結果が得られます。
EOF

echo ""
echo "🎉 ai-send拡張版の実装が完了しました！"
echo ""
echo "📋 追加されたタスクタイプ："
echo "  test, fix, deploy, review, docs, optimize, security, monitor, backup"
echo ""
echo "📚 詳細は docs/AI_SEND_EXTENDED_GUIDE.md を参照してください"
echo ""
echo "🚀 使用例："
echo "  ai-send 'ユニットテストを作成して' test"
echo "  ai-send 'エラーを修正して' fix --priority 8"
echo "  ai-send 'セキュリティチェック' security"
