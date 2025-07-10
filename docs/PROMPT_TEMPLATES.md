# 🎯 Elders Guild プロンプトテンプレート管理システム

## 概要

ワーカー毎に最適化されたプロンプトテンプレートを管理し、動的にプロンプトを生成するシステムです。

## 主な機能

### 1. テンプレート管理
- ワーカー種別ごとのテンプレート定義
- バージョン管理とロールバック
- テンプレートのインポート/エクスポート

### 2. 動的プロンプト生成
- Jinja2テンプレートエンジン使用
- RAGコンテキストの自動統合
- 環境変数の安全な処理

### 3. パフォーマンス追跡
- プロンプトの使用履歴記録
- 成功/失敗率の追跡
- パフォーマンススコアリング

## クイックスタート

### インストール
```bash
cd /home/aicompany/ai_co
./scripts/integrate_prompt_templates.sh
```

### 基本的な使い方

#### テンプレート一覧表示
```bash
ai-prompt list
ai-prompt list --worker task
```

#### テンプレート詳細表示
```bash
ai-prompt show task default
ai-prompt show task code_generation --version 2
```

#### プロンプト生成テスト
```bash
ai-prompt generate task default \
  --vars task_id=test_001 \
  user_prompt="Create a web scraper"
```

#### 新規テンプレート作成
```bash
# テンプレートファイル作成
cat > my_template.j2 << 'TEMPLATE'
Task: {{ task_id }}
Request: {{ user_prompt }}
Additional: {{ custom_var }}
TEMPLATE

# 登録
ai-prompt create task my_custom my_template.j2 \
  --variables task_id,user_prompt,custom_var \
  --description "My custom template"
```

## ワーカーへの統合

### 基本的な統合
```python
from core import BaseWorker
from core.prompt_template_mixin import PromptTemplateMixin

class MyWorker(BaseWorker, PromptTemplateMixin):
    def __init__(self):
        BaseWorker.__init__(self, worker_type='my_worker')
        PromptTemplateMixin.__init__(self)
    
    def process_message(self, ch, method, properties, body):
        # プロンプト生成
        prompt = self.generate_prompt(
            template_name='default',
            variables={
                'task_id': task['id'],
                'user_prompt': task['prompt']
            }
        )
        
        # Claudeで実行
        result = self.execute_claude(prompt)
```

### カスタムテンプレート使用
```python
# テンプレート選択ロジック
def select_template(self, task):
    if task['type'] == 'code':
        return 'code_generation'
    elif 'complex' in task['prompt']:
        return 'advanced'
    return 'default'

# 使用
template = self.select_template(task)
prompt = self.generate_prompt(template_name=template, variables=vars)
```

## テンプレート構造

### 変数
- `{{ variable }}` - 基本的な変数展開
- `{{ variable | default('value') }}` - デフォルト値付き
- `{% if condition %} ... {% endif %}` - 条件分岐
- `{% for item in list %} ... {% endfor %}` - ループ

### 組み込み変数
- `task_id` - タスクID
- `task_type` - タスクタイプ
- `user_prompt` - ユーザーのリクエスト
- `rag_context` - RAGで取得した関連情報
- `worker_type` - ワーカータイプ
- `worker_id` - ワーカーID

### 環境変数
- `${ENV_VAR}` - 環境変数を参照（自動展開）

## 管理コマンド

### テンプレート操作
```bash
# 更新
ai-prompt update task default new_template.j2

# ロールバック
ai-prompt rollback task default 1

# エクスポート
ai-prompt export /tmp/templates

# インポート
ai-prompt import /tmp/templates/task_templates.json
```

### 履歴確認
```bash
# 使用履歴
ai-prompt history task default --limit 20

# パフォーマンス確認
ai-prompt stats task default
```

## 設定ファイル

`config/prompt.json`:
```json
{
  "prompt": {
    "db_path": "db/prompt_templates.db",
    "template_dir": "config/prompts",
    "enable_rag": true,
    "rag_limit": 3,
    "default_templates": {
      "task": "default",
      "pm": "default"
    }
  }
}
```

## ベストプラクティス

### 1. テンプレート設計
- 明確で具体的な指示を含める
- 必要な変数を明示的に定義
- RAGコンテキストを活用

### 2. バージョン管理
- 重要な変更前にバックアップ
- 意味のあるdescriptionを付ける
- 定期的にエクスポート

### 3. パフォーマンス最適化
- 成功率の高いテンプレートを分析
- 低スコアのテンプレートを改善
- A/Bテストの実施

## トラブルシューティング

### テンプレートが見つからない
```bash
# データベース確認
sqlite3 db/prompt_templates.db "SELECT * FROM prompt_templates;"

# 再初期化
python3 -c "from libs.prompt_template_manager import PromptTemplateManager; m = PromptTemplateManager(); m.initialize()"
```

### プロンプト生成エラー
```bash
# テンプレート検証
ai-prompt validate task default

# 変数確認
ai-prompt show task default
```

## 拡張機能

### カスタムフィルター
```python
# Jinja2カスタムフィルター追加
def capitalize_words(text):
    return ' '.join(word.capitalize() for word in text.split())

manager.jinja_env.filters['capitalize_words'] = capitalize_words
```

### 動的テンプレート選択
```python
def get_best_template(self, task):
    # パフォーマンススコアに基づいて最適なテンプレートを選択
    scores = self.prompt_manager.get_template_scores(self.worker_type)
    return max(scores, key=lambda x: x['score'])['template_name']
```

## 今後の拡張予定

- [ ] A/Bテスト機能
- [ ] 自動最適化
- [ ] テンプレート推薦システム
- [ ] マルチ言語対応
- [ ] GUIエディタ

---

プロンプトテンプレート管理により、各ワーカーが最適なプロンプトを使用し、タスク処理の精度と効率が向上します。
