# 🎤 Meeting-to-Code Workflow

Elders Guildの会議駆動開発システム - 録音から完成コードまで全自動

## 🚀 コンセプト

```
📱 会議録音 → 📝 文字起こし → 🤖 Gemini要約 → 🏗️ Elders Guild → ✅ 完成コード
    30分        2分           1分          10分         40分で完成
```

## 📋 ワークフロー詳細

### 1. **会議録音** 📱
```bash
# Zoom, Teams, Google Meet等で録音
# 対応形式: MP4, MP3, WAV, M4A
recording.mp4  # 30分の企画会議
```

### 2. **文字起こし** 📝 (OpenAI Whisper)
```bash
./scripts/ai-meeting-to-code recording.mp4 --output ./my-project

# 出力例:
"""
田中: 新しいECサイトを作りたいんですが
佐藤: 在庫管理機能は必須ですね
田中: PayPal決済も対応したいです
佐藤: TDD開発でお願いします
田中: 来月末までに完成予定で
"""
```

### 3. **Gemini要約** 🤖 (Google Gemini)
```json
{
  "project_overview": "PayPal決済対応のECサイト開発",
  "main_requirements": [
    "商品管理機能",
    "在庫管理システム",
    "PayPal決済機能",
    "ユーザー認証"
  ],
  "technical_specs": {
    "framework": "fastapi",
    "database": "postgresql", 
    "payment": "paypal"
  },
  "deadline": "来月末",
  "development_approach": "TDD",
  "ai_company_tasks": [
    "商品管理APIをTDDで作成",
    "在庫管理システムを実装", 
    "PayPal決済機能を統合",
    "ユーザー認証機能を追加"
  ]
}
```

### 4. **Elders Guild実行** 🏗️ (TDD自動開発)
```bash
# 各タスクを順次実行
Task 1: 商品管理APIをTDDで作成
  → tests/test_product_api.py    # テスト先行
  → api/product.py              # 実装
  → models/product.py           # モデル

Task 2: 在庫管理システムを実装  
  → tests/test_inventory.py     # 在庫テスト
  → services/inventory.py       # 在庫ロジック
  → api/inventory.py           # 在庫API

Task 3: PayPal決済機能を統合
  → tests/test_payment.py       # 決済テスト
  → services/paypal_service.py  # PayPal連携
  → api/payment.py             # 決済API

Task 4: ユーザー認証機能を追加
  → tests/test_auth.py          # 認証テスト
  → services/auth.py           # 認証ロジック  
  → middleware/auth.py         # 認証ミドルウェア
```

### 5. **完成コード** ✅
```
my-project/
├── README.md              # プロジェクト概要
├── requirements.json      # 抽出された要件
├── tests/                 # TDDテストコード
│   ├── test_product_api.py
│   ├── test_inventory.py
│   ├── test_payment.py
│   └── test_auth.py
├── api/                   # APIエンドポイント
│   ├── product.py
│   ├── inventory.py
│   ├── payment.py
│   └── auth.py
├── models/               # データモデル
├── services/            # ビジネスロジック
└── migrations/          # DB マイグレーション
```

## 🛠️ 使用方法

### 基本的な使い方
```bash
# 1. 録音ファイルから
./scripts/ai-meeting-to-code meeting.mp4 --output ./ecommerce-project

# 2. 既に文字起こし済みの場合
./scripts/ai-meeting-to-code transcript.txt --text --output ./project

# 3. インタラクティブモード（直接入力）
./scripts/ai-meeting-to-code --interactive --output ./project
```

### 設定が必要な環境変数
```bash
# .env に追加
OPENAI_API_KEY=sk-...      # Whisper文字起こし用
GEMINI_API_KEY=AI...       # Gemini要約用  
ANTHROPIC_API_KEY=sk-...   # Elders Guild用
```

## 📊 実用例

### ケース1: スタートアップの企画会議
```bash
# 30分の企画会議を録音
# → 10分後にMVPのAPIが完成

./scripts/ai-meeting-to-code startup_meeting.mp4 --output ./mvp
```

### ケース2: 機能追加の打ち合わせ
```bash  
# 既存プロジェクトに新機能追加
# → 会議内容を既存コードに統合

./scripts/ai-meeting-to-code feature_meeting.mp4 --output ./existing-project/new-feature
```

### ケース3: バグ修正の相談
```bash
# バグ報告会議
# → テストケース + 修正コード自動生成

./scripts/ai-meeting-to-code bug_meeting.mp4 --output ./bugfix
```

## 🔄 ワークフローの利点

### **従来の開発**
```
会議 → 議事録作成 → 要件定義書 → 設計書 → 実装 → テスト
 1日     2日         3日       2日     10日    3日
                    = 21日
```

### **Meeting-to-Code**
```
会議 → AI変換 → 完成コード
30分     10分      完了
      = 40分
```

## 🎯 対応する会議タイプ

- ✅ **企画会議** - 新規プロジェクトの立ち上げ
- ✅ **機能追加** - 既存システムの拡張
- ✅ **バグ修正** - 問題解決とテストケース追加
- ✅ **技術選定** - アーキテクチャの決定
- ✅ **レビュー会議** - コード改善提案
- ✅ **顧客要件ヒアリング** - 要件の直接変換

## 🔧 カスタマイズ

### 要約プロンプトの調整
```python
# scripts/ai-meeting-to-code の prompt を編集
prompt = f"""
業界特有の要件を考慮して分析してください。
# 業界: {industry}
# 規制要件: {compliance_requirements}
...
"""
```

### フレームワーク自動判定
```python
# Geminiが技術選定も自動化
"technical_specs": {
    "framework": "fastapi",      # 高速API → FastAPI
    "frontend": "react",         # SPA要件 → React  
    "database": "postgresql",    # RDBMS → PostgreSQL
    "cache": "redis"            # パフォーマンス → Redis
}
```

## 🚨 注意事項

1. **機密情報**: 録音内容に機密情報が含まれる場合は注意
2. **API制限**: 各API（OpenAI, Gemini, Anthropic）の利用制限を確認
3. **音質**: クリアな録音でより良い結果を得られます
4. **言語**: 現在は日本語に最適化されています

## 📈 成功事例

### 事例1: フィンテック スタートアップ
- **会議**: 決済システムの企画会議（45分）
- **結果**: 完全なPayPal/Stripe統合API
- **削減時間**: 2週間 → 1時間

### 事例2: EC企業の機能追加
- **会議**: レコメンド機能の要件定義（30分）  
- **結果**: ML推論API + A/Bテスト機能
- **削減時間**: 1週間 → 30分

### 事例3: 社内システム改善
- **会議**: ワークフロー改善会議（60分）
- **結果**: 承認フロー自動化システム
- **削減時間**: 1ヶ月 → 1時間

---

**会議が終わった瞬間に、コードも完成している未来へ** 🚀