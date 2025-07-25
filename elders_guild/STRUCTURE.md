# 新エルダーズギルド構造

## 📁 ディレクトリ構成

```
elders_guild/
├── quality/                    # 品質管理エンジン
│   ├── static_analysis_engine.py
│   ├── test_automation_engine.py
│   ├── comprehensive_quality_engine.py
│   ├── quality_pipeline_orchestrator.py
│   └── unified_quality_pipeline.py
│
├── quality_servants/           # 品質サーバント (python-a2a)
│   ├── quality_watcher_servant.py      # Block A: 静的解析
│   ├── test_forge_servant.py           # Block B: テスト自動化
│   ├── comprehensive_guardian_servant.py # Block C: 包括品質
│   ├── quality_watcher_judgment.py     # 判定システム
│   └── test_forge_judgment.py          # テスト判定
│
├── elder_servants/             # エルダーサーバント群
│   ├── base/                   # 基底クラス
│   ├── dwarf_workshop/         # ドワーフ工房（開発）
│   ├── elf_forest/            # エルフの森（監視）
│   ├── rag_wizards/           # RAGウィザード（調査）
│   └── coordination/          # 協調システム
│
├── elder_system/              # エルダーシステムコア
│   ├── flow/                  # Elder Flow エンジン
│   │   ├── elder_flow_engine.py
│   │   └── pid_lock_manager.py
│   ├── council/               # エルダー評議会
│   └── tree/                  # エルダーツリー
│
├── four_sages/                # 4賢者システム
│   ├── knowledge/             # ナレッジ賢者
│   ├── task/                  # タスク賢者
│   ├── incident/              # インシデント賢者
│   └── rag/                   # RAG賢者
│
├── ancient_elder/             # 古代エルダーシステム
│   ├── audit_engine.py        # 監査エンジン
│   ├── flow_compliance_auditor.py
│   └── strict_output_validator.py
│
├── claude_elder/              # Claude Elder統合
│   ├── claude_elder_process.py
│   ├── claude_elder_chat_api.py
│   └── claude_elder_auto_flow_interceptor.py
│
├── elder_flow/                # Elder Flow オーケストレーション
│   └── elder_flow_orchestrator.py
│
├── scripts/                   # 実行スクリプト
│   ├── start-quality-servants.sh
│   └── stop-quality-servants.sh
│
├── tests/                     # テストファイル
│   ├── quality/
│   ├── servants/
│   └── integration/
│
├── docs/                      # ドキュメント
│   ├── philosophy/            # 設計思想
│   └── architecture/          # アーキテクチャ
│
├── elder_cli.py              # Elder統合CLI
└── __init__.py
```

## 🎯 主要コンポーネント

### 1. **品質パイプライン** (Issue #309)
- Execute & Judge パターン
- 3ブロック構成（A/B/C）
- One Servant, One Command原則

### 2. **4賢者システム**
- ナレッジ賢者: 知識管理・学習
- タスク賢者: タスク管理・優先順位
- インシデント賢者: 障害対応・自動復旧
- RAG賢者: 情報検索・最適解発見

### 3. **Elder Flow**
- 自動化開発フロー
- A2A魂モード（独立プロセス）
- PIDロック機能

### 4. **エルダーサーバント**
- ドワーフ工房: 開発・製作
- エルフの森: 監視・メンテナンス
- RAGウィザード: 調査・研究
- インシデント騎士団: 緊急対応

## 🔧 使用方法

```bash
# 品質サーバント起動
./elders_guild/scripts/start-quality-servants.sh

# Elder Flow実行
elder flow execute "タスク名" --priority high

# 品質チェック実行
elder quality check /path/to/project

# 4賢者会議招集
elder council summon --topic "技術課題"
```

## 📚 関連ドキュメント
- [AI決定者パラダイム](docs/philosophy/AI_DECISION_MAKER_PARADIGM.md)
- [Execute & Judge パターン](docs/architecture/EXECUTE_JUDGE_PATTERN.md)
- [A2A通信仕様](docs/architecture/A2A_COMMUNICATION.md)