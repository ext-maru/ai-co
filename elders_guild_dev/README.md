# 🏛️ Elders Guild Development Directory

**⚠️ 開発期間中の一時的な配置**

このディレクトリは、Elder Tree分散AIアーキテクチャの開発中にGitHubで実装を確認できるようにするための一時的な配置です。

## 📁 構造

```
elders_guild_dev/
├── shared_libs/          # 共有ライブラリ
│   ├── soul_base.py     # BaseSoulクラス
│   ├── a2a_protocol.py  # A2A通信プロトコル
│   └── __init__.py
└── task_sage/           # Task Sage実装
    ├── soul.py          # メイン魂実装
    ├── abilities/       # 特殊能力
    │   ├── __init__.py
    │   └── task_models.py
    ├── tests/          # テストスイート
    │   └── test_task_sage.py
    └── README.md
```

## 🎯 本来の配置

最終的には `/home/aicompany/elders_guild/` に独立したマイクロサービスとして配置される予定です。

## 📊 実装状況

### ✅ Task Sage
- **完了日**: 2025年7月23日
- **品質**: テストカバレッジ90%、Iron Will 100%
- **機能**: タスク管理、工数見積もり、プロジェクト管理

### 🚧 開発予定
- Knowledge Sage
- Incident Sage
- RAG Sage
- Claude Elder

---
*開発完了後、本番環境への移行を行います*