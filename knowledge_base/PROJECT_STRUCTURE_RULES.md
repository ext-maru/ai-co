# プロジェクト構造標準化ルール

**エルダー評議会令第34号 - プロジェクト構造標準化令**
**制定日: 2025年7月19日**

## 🎯 目的
- プロジェクトルートディレクトリの整理整頓
- ファイルの役割と配置場所の明確化
- メンテナンス性とナビゲーション性の向上

## 🗂️ 標準ディレクトリ構造

```
ai_co/
├── README.md                   # プロジェクト概要（ルート必須）
├── CLAUDE.md                   # クロードエルダー開発ガイド（ルート必須）
├── CONTRIBUTING.md             # 貢献ガイド（ルート必須）
├── Dockerfile*                 # Docker設定（ルート必須）
├── docker-compose*.yml         # Docker Compose設定（ルート必須）
├── requirements*.txt           # Python依存関係（ルート必須）
├── pytest*.ini                 # pytest設定（ルート必須）
├── Makefile*                   # ビルド設定（ルート必須）
├── .github/                    # GitHub設定（ルート必須）
│
├── docs/                       # すべてのドキュメント
│   ├── reports/               # レポート・分析結果
│   │   ├── *_REPORT.md
│   │   ├── *_ANALYSIS.md
│   │   └── *_RESULTS.md
│   ├── guides/                # ガイド・ベストプラクティス
│   │   ├── *_GUIDE.md
│   │   ├── *_PRACTICES.md
│   │   └── *_WORKFLOW.md
│   ├── policies/              # ポリシー・プロトコル
│   │   ├── *_POLICY.md
│   │   └── *_PROTOCOL.md
│   └── technical/             # 技術文書
│       ├── *_README.md
│       └── *_TECHNICAL.md
│
├── scripts/                    # すべての実行スクリプト
│   ├── ai-commands/           # AIコマンドツール
│   │   ├── ai-commit-*
│   │   ├── ai-elder*
│   │   └── ai-*-guard
│   ├── monitoring/            # モニタリングスクリプト
│   │   ├── monitor_*.py
│   │   └── *_watchdog.sh
│   ├── analysis/              # 分析ツール
│   │   ├── analyze_*.py
│   │   └── diagnose_*.py
│   ├── utilities/             # ユーティリティ
│   │   ├── fix_*.py
│   │   ├── patch_*.py
│   │   └── execute_*.py
│   ├── deployment/            # デプロイメント
│   │   ├── deploy_*.py
│   │   ├── setup_*.py
│   │   └── start_*.py
│   └── testing/               # テスト実行
│       └── run_*.py
│
├── tests/                      # すべてのテストファイル
│   ├── test_*.py
│   └── conftest.py
│
├── libs/                       # ライブラリコード
├── configs/                    # 設定ファイル
├── data/                       # データファイル
│   ├── *.db
│   └── *.json
├── daily_reports/              # 日次レポート
├── knowledge_base/             # ナレッジベース
└── generated_reports/          # 自動生成レポート
```

## 📋 ファイル配置ルール

### 1. ルートディレクトリ最小化
**原則**: ルートには必須ファイルのみを配置

**ルート必須ファイル**:
- `README.md` - プロジェクト概要
- `CLAUDE.md` - クロードエルダー開発ガイド
- `CONTRIBUTING.md` - 貢献ガイド
- `Dockerfile*` - Docker設定
- `docker-compose*.yml` - Docker Compose設定
- `requirements*.txt` - Python依存関係
- `pytest*.ini` - pytest設定
- `Makefile*` - ビルド設定
- `.gitignore`, `.gitattributes` - Git設定

**その他のファイルは適切なサブディレクトリへ移動**

### 2. ドキュメント配置

| ファイルタイプ | 配置先 | 例 |
|------------|--------|-----|
| レポート・分析 | `docs/reports/` | `*_REPORT.md`, `*_ANALYSIS.md` |
| ガイド・手順書 | `docs/guides/` | `*_GUIDE.md`, `*_PRACTICES.md` |
| ポリシー・規約 | `docs/policies/` | `*_POLICY.md`, `*_PROTOCOL.md` |
| 技術文書 | `docs/technical/` | `POSTGRESQL_*.md`, `*_TECHNICAL.md` |

### 3. スクリプト配置

| スクリプトタイプ | 配置先 | 例 |
|--------------|--------|-----|
| AIコマンド | `scripts/ai-commands/` | `ai-commit-*`, `ai-elder*` |
| モニタリング | `scripts/monitoring/` | `monitor_*.py` |
| 分析ツール | `scripts/analysis/` | `analyze_*.py`, `diagnose_*.py` |
| ユーティリティ | `scripts/utilities/` | `fix_*.py`, `execute_*.py` |
| デプロイメント | `scripts/deployment/` | `deploy_*.py`, `setup_*.py` |
| テスト実行 | `scripts/testing/` | `run_*.py` |

### 4. テストファイル配置
- すべての `test_*.py` → `tests/`
- `conftest.py` → `tests/`
- テスト用フィクスチャ → `tests/fixtures/`

### 5. データファイル配置
- データベース（`*.db`） → `data/`
- 設定JSON → `configs/`
- 分析結果JSON → `data/` または `generated_reports/`

## 🚨 ルール違反時の対応

### 自動検知
1. **インシデント賢者**が定期的にプロジェクト構造を監視
2. ルール違反を検知した場合、自動でインシデント作成
3. クロードエルダーに通知

### 修正プロセス
1. **即座修正**: クロードエルダーが違反ファイルを適切な場所に移動
2. **参照更新**: 移動したファイルへの参照パスを更新
3. **記録**: 知識ベースに違反と修正内容を記録
4. **予防**: 同様の違反を防ぐためのルール強化

## 📝 例外事項

以下のファイルは特別な理由によりルートディレクトリに配置を許可：
- `.env.example` - 環境変数テンプレート
- `LICENSE` - ライセンスファイル
- `CHANGELOG.md` - 変更履歴

## 🔄 定期レビュー

- **月次レビュー**: プロジェクト構造の健全性チェック
- **四半期レビュー**: ルールの見直しと更新
- **年次監査**: 全体的な構造最適化

## 📚 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md) - プロジェクト構造ルールセクション
- [PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) - 詳細構造説明
- [DOCUMENTATION_INDEX.md](../docs/DOCUMENTATION_INDEX.md) - ドキュメント索引

---

**施行日**: 2025年7月19日
**承認者**: エルダー評議会
**最終更新**: 2025年7月19日
