# Elders Guild 環境変数管理ルール

## 🔐 環境変数管理の基本原則

### 1. 単一ソースの原則
- **すべての環境変数は `.env` ファイルに集約する**
- 環境変数の検索や自動検出は行わない
- `.env.template` をマスターテンプレートとして管理

### 2. アクセス方法の統一
- **必ず `libs/env_config.py` の `Config` クラス経由でアクセスする**
- 直接 `os.environ` や `os.getenv()` を使用しない
- 統一されたゲッター関数を使用

### 3. セキュリティルール
- `.env` ファイルは絶対にGitにコミットしない（.gitignoreに記載済み）
- ログ出力時はセンシティブ情報を自動マスク
- APIキーやトークンは表示時に必ずマスク処理

## 📋 実装ルール

### 環境変数の読み込み方法

**✅ 正しい方法：**
```python
from libs.env_config import get_config

config = get_config()
api_key = config.ANTHROPIC_API_KEY
slack_token = config.SLACK_BOT_TOKEN
```

**❌ 間違った方法：**
```python
# 直接os.environを使用しない
import os
api_key = os.environ['ANTHROPIC_API_KEY']  # NG

# 独自に.envを読み込まない
from dotenv import load_dotenv
load_dotenv()  # NG
```

### 新しい環境変数の追加手順

1. `.env.template` に追加
```bash
# NEW FEATURE CONFIGURATION
MY_NEW_VARIABLE=your_value_here
```

2. `libs/env_config.py` の `Config` クラスに追加
```python
class Config:
    def __init__(self):
        # ... existing code ...
        self.MY_NEW_VARIABLE = get_env('MY_NEW_VARIABLE', 'default_value')
```

3. 使用する
```python
config = get_config()
value = config.MY_NEW_VARIABLE
```

## 🛠️ 管理コマンド

### セットアップ
```bash
# 初回セットアップ（.envファイル作成、環境構築）
ai-setup

# .envファイルのみ作成
ai-env setup
```

### 確認・検証
```bash
# 環境変数の設定状況確認
ai-env check

# 必須変数の検証
ai-env verify

# 現在の設定表示（マスク付き）
ai-env show
```

## 📁 ファイル構成

```
/home/aicompany/ai_co/
├── .env.template    # 環境変数テンプレート（Git管理対象）
├── .env            # 実際の環境変数（Git管理対象外）
├── libs/
│   └── env_config.py   # 環境変数管理クラス
└── scripts/
    ├── ai-setup        # 環境セットアップスクリプト
    └── ai-env         # 環境変数管理コマンド
```

## ⚠️ 禁止事項

1. **環境変数の自動検出・探索機能の実装禁止**
   - シェルプロファイル、systemd、Docker等からの自動読み込み禁止
   - 複雑な検出ロジックは保守性を下げる

2. **独自の環境変数読み込み処理の実装禁止**
   - 各モジュールで独自に.envを読み込まない
   - 必ず`env_config.py`を使用する

3. **環境変数の直接参照禁止**
   - `os.environ`の直接使用禁止
   - `subprocess`での環境変数継承に注意

## ✅ 必須環境変数一覧

| 変数名 | 説明 | 必須 |
|--------|------|------|
| ANTHROPIC_API_KEY | Claude API キー | ✅ |
| SLACK_BOT_TOKEN | Slack Bot トークン | ⚠️ (Slack機能使用時) |
| SLACK_APP_TOKEN | Slack App トークン | ⚠️ (リアルタイム機能使用時) |
| SLACK_CHANNEL | Slack 通知チャンネル | ⚠️ (Slack機能使用時) |
| PYTHONPATH | プロジェクトパス | ✅ |
| RABBITMQ_HOST | RabbitMQ ホスト | ✅ |

## 🔄 更新履歴

- 2025-01-06: 環境変数管理ルール策定
- シンプルな単一ソース管理方式を採用
- 複雑な自動検出機能を廃止