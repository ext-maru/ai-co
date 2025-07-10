# Elders Guild Code Generation Templates

Elders Guildには、さまざまな種類のコードを自動生成するためのテンプレートが用意されています。

## 📋 利用可能なテンプレート

### 1. REST API Endpoint (`rest_api`)
FastAPIまたはFlaskを使用したREST APIエンドポイントを生成します。

**特徴:**
- CRUD操作の自動生成
- リクエスト検証
- エラーハンドリング
- 自動ドキュメント生成
- テストコード付き

**使用例:**
```bash
./scripts/ai-codegen generate rest_api \
  --params '{"framework": "fastapi", "resource_name": "product", "auth_required": true}' \
  --output ./generated/api
```

### 2. Database Model (`database_model`)
SQLAlchemyモデルとCRUD操作を生成します。

**特徴:**
- モデル定義
- CRUD操作クラス
- マイグレーションファイル
- リレーションシップ対応
- ソフトデリート機能

**使用例:**
```bash
./scripts/ai-codegen generate database_model \
  --params '{"model_name": "User", "fields": {"email": "string", "is_active": "boolean"}}' \
  --output ./generated/models
```

### 3. CLI Command (`cli_command`)
Clickベースのコマンドラインツールを生成します。

**特徴:**
- サブコマンド対応
- 引数とオプションの自動処理
- ヘルプテキスト生成
- エラーハンドリング
- 設定ファイル対応

**使用例:**
```bash
./scripts/ai-codegen generate cli_command \
  --params '{"command_name": "myctl", "description": "My Control CLI"}' \
  --output ./generated/cli
```

## 🚀 使い方

### 1. テンプレート一覧の表示
```bash
./scripts/ai-codegen list
```

### 2. テンプレート情報の確認
```bash
./scripts/ai-codegen info rest_api
```

### 3. コード生成

#### パラメータファイルを使用
```bash
# params.json
{
  "framework": "fastapi",
  "resource_name": "user",
  "operations": ["list", "get", "create", "update", "delete"],
  "auth_required": true
}

./scripts/ai-codegen generate rest_api --params params.json --output ./src
```

#### インタラクティブモード
```bash
./scripts/ai-codegen generate rest_api --interactive --output ./src
```

## 📝 パラメータ詳細

### REST API Template

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|------------|
| framework | str | No | Webフレームワーク (fastapi/flask) | fastapi |
| resource_name | str | Yes | リソース名 (例: user, product) | - |
| operations | list | No | CRUD操作のリスト | ["list", "get", "create", "update", "delete"] |
| auth_required | bool | No | 認証が必要か | true |
| validation | bool | No | リクエスト検証を含めるか | true |

### Database Model Template

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|------------|
| model_name | str | Yes | モデル名 (例: User, Product) | - |
| fields | dict | Yes | フィールド定義 {name: type} | - |
| relationships | list | No | リレーションシップ定義 | [] |
| indexes | list | No | インデックス定義 | [] |
| soft_delete | bool | No | ソフトデリート機能を含めるか | true |

### CLI Command Template

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|------------|
| command_name | str | Yes | コマンド名 | - |
| description | str | Yes | コマンドの説明 | - |
| arguments | list | No | 位置引数のリスト | [] |
| options | list | No | オプションのリスト | [] |
| subcommands | list | No | サブコマンドのリスト | [] |
| confirmation | bool | No | 実行前の確認が必要か | false |
| async_command | bool | No | 非同期コマンドとして生成 | false |

## 🔧 カスタムテンプレートの追加

新しいテンプレートを追加するには：

1. `/home/aicompany/ai_co/templates/code_gen/` に新しいテンプレートファイルを作成
2. `template_info` 辞書でテンプレート情報を定義
3. `generate()` メソッドを実装
4. `template_registry.py` にインポートして登録

例:
```python
class MyTemplate:
    def __init__(self):
        self.template_info = {
            "name": "My Template",
            "version": "1.0.0",
            "description": "My custom template",
            "parameters": {
                "param1": {"type": "str", "required": True}
            }
        }
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, str]:
        # Generate code files
        return {
            "file1.py": "content1",
            "file2.py": "content2"
        }
```

## 📊 生成されるファイル構造

### REST API (FastAPI)
```
generated/
├── models/
│   └── product.py          # Pydanticモデル
├── routers/
│   └── product.py          # APIエンドポイント
└── tests/
    └── test_product.py     # テストコード
```

### Database Model
```
generated/
├── models/
│   └── user.py             # SQLAlchemyモデル
├── crud/
│   └── user_crud.py        # CRUD操作
└── migrations/
    └── 20240101_create_user.py  # マイグレーション
```

### CLI Command
```
generated/
├── myctl/
│   ├── __init__.py
│   └── cli.py              # CLIメインファイル
├── tests/
│   └── test_myctl_cli.py   # テストコード
├── setup.py                # セットアップスクリプト
├── README.md               # ドキュメント
└── config.example.json     # 設定ファイル例
```

## 🎯 ベストプラクティス

1. **パラメータファイルの使用**: 複雑な設定はJSONファイルで管理
2. **バージョン管理**: 生成されたコードもGitで管理
3. **カスタマイズ**: 生成後のコードは必要に応じて編集
4. **テスト**: 生成されたテストコードを実行して動作確認
5. **ドキュメント**: 生成されたREADMEを更新

## 🔗 関連リンク

- [TDD開発ガイド](TDD_WITH_CLAUDE_CLI.md)
- [ワーカーテンプレート](../templates/README.md)
- [Elders Guild開発ガイド](DEVELOPMENT_GUIDE.md)