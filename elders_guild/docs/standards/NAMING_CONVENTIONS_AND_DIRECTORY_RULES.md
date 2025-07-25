# 🏷️ エルダーズギルド 命名規約・ディレクトリ構造ルール
## 開発者向け実践ガイド - 想定しない名前で作り始めない

**策定日**: 2025-07-23  
**根拠**: Issue #302 解決教訓  
**対象**: 全エルダーズギルド開発者  
**更新頻度**: 四半期見直し

---

## 🎯 このドキュメントの目的

### 📚 Issue #302 から学んだ教訓
> **「想定しない名前で作り始めない」**
> 
> 重複ディレクトリ (`incident_sage/` vs `src/incident_sage/`) による混乱を二度と起こさないため、全開発者が従うべき明確なルールを策定

### ✅ 達成目標
- **迷わない開発**: どこに何を置くかが即座に判断可能
- **一貫性保証**: 全プロジェクトで統一された構造
- **将来性確保**: スケールしても破綻しない命名体系

---

## 📁 ディレクトリ命名規約

### 🏛️ Tier 1: 必須遵守ディレクトリ

#### **プロジェクトルート固定ディレクトリ**
```bash
# 絶対に変更してはならないディレクトリ名
docs/               # ドキュメント（複数形必須）
libs/               # ライブラリ（複数形必須）
core/               # コアシステム
shared_libs/        # 共有ライブラリ
scripts/            # スクリプト（複数形必須）
tests/              # テスト（複数形必須）
configs/            # 設定（複数形必須）
workers/            # ワーカー（複数形必須）
data/               # データ
logs/               # ログ（複数形必須）
```

#### **4賢者システム固定名**
```bash
# 4賢者は必ずこの名前（変更禁止）
incident_sage/      # インシデント対応賢者
knowledge_sage/     # 知識管理賢者
task_sage/          # タスク管理賢者
rag_sage/          # 検索分析賢者
```

### 🔧 Tier 2: 標準パターンディレクトリ

#### **機能別ディレクトリパターン**
```bash
# パターン1: [機能名]_[種別]/
api_gateway/        # API関連
data_processor/     # データ処理
auth_service/       # 認証サービス

# パターン2: [組織名]/
elder_servants/     # エルダーサーバント
ancient_magic/      # 古代魔法
```

#### **用途別ディレクトリパターン**
```bash
# 開発・運用関連
deployment/         # デプロイメント
monitoring/         # 監視
infrastructure/     # インフラ
orchestration/      # オーケストレーション

# テンポラリ関連
tmp/               # 一時ファイル
backups/           # バックアップ（複数形必須）
archives/          # アーカイブ（複数形必須）
```

### 🚨 禁止ディレクトリ名

#### **絶対禁止**
```bash
❌ src/               # 重複の温床（Issue #302の原因）
❌ source/            # srcと同じ理由
❌ app/               # 曖昧すぎる
❌ code/              # 曖昧すぎる
❌ main/              # 曖昧すぎる
❌ system/            # 曖昧すぎる
❌ module/            # 曖昧すぎる
❌ component/         # 曖昧すぎる
```

#### **混乱を招く名前**
```bash
❌ lib/               # libsに統一
❌ script/            # scriptsに統一
❌ test/              # testsに統一
❌ config/            # configsに統一
❌ doc/               # docsに統一
❌ log/               # logsに統一
```

## 📄 ファイル命名規約

### 🐍 Python ファイル

#### **標準ファイル名**
```python
# 必須標準ファイル
__init__.py         # パッケージ初期化（必須）
soul.py             # メイン実装ファイル
business_logic.py   # ビジネスロジック分離
a2a_agent.py       # A2A通信エージェント

# モデル・設定ファイル
[module]_models.py  # データモデル（例: incident_models.py）
[module]_config.py  # 設定ファイル（例: auth_config.py）
[module]_utils.py   # ユーティリティ（例: data_utils.py）

# テストファイル
test_[module].py    # ユニットテスト（例: test_incident_sage.py）
```

#### **命名パターン**
```python
✅ 正しいパターン:
business_logic.py      # アンダースコア区切り
incident_models.py     # 複数形推奨（modelsは常に複数）
auth_handler.py        # 機能_役割 パターン
api_client.py          # 略語_機能 パターン

❌ 禁止パターン:
BusinessLogic.py       # キャメルケース禁止
business-logic.py      # ハイフン禁止
businesslogic.py       # 結合禁止
Business_Logic.py      # 大文字混在禁止
```

### 📚 ドキュメントファイル

#### **標準ドキュメント名**
```markdown
# プロジェクト必須ドキュメント
README.md              # プロジェクト概要（必須）
CLAUDE.md              # Claude CLI設定（必須）
CHANGELOG.md           # 変更履歴
LICENSE.md             # ライセンス

# 技術ドキュメント（大文字アンダースコア）
API_REFERENCE.md       # API仕様書
PROJECT_STRUCTURE_STANDARDS.md  # 構造標準
NAMING_CONVENTIONS_AND_DIRECTORY_RULES.md  # 命名規約

# ガイドドキュメント（小文字アンダースコア）
user_guide.md          # ユーザーガイド
developer_guide.md     # 開発者ガイド
installation_guide.md  # インストールガイド
```

#### **ドキュメント命名パターン**
```markdown
✅ 正しいパターン:
# 標準・仕様書（大文字アンダースコア）
API_SPECIFICATION.md
CODING_STANDARDS.md
SECURITY_POLICY.md

# ガイド・手順書（小文字アンダースコア）
setup_guide.md
troubleshooting_guide.md
best_practices.md

❌ 禁止パターン:
api-reference.md       # ハイフン禁止
ApiReference.md        # キャメルケース禁止
api_Reference.md       # 大文字小文字混在禁止
```

## 🏗️ ディレクトリ構造パターン

### 🏛️ 4賢者システム構造（確定版）

```
[sage_name]/
├── __init__.py              # モジュール初期化
├── soul.py                  # 魂実装（メイン）
├── business_logic.py        # ビジネスロジック
├── a2a_agent.py            # A2A通信エージェント
├── abilities/               # 固有能力
│   ├── __init__.py
│   └── [sage_name]_models.py
├── tests/                   # テストコード
│   ├── __init__.py
│   ├── test_[sage_name].py
│   └── test_[sage_name]_comprehensive.py
└── configs/                 # 賢者固有設定（オプション）
    └── [sage_name]_config.yaml
```

### 🛠️ サービス・ライブラリ構造

```
[service_name]/
├── __init__.py              # モジュール初期化
├── main.py                  # メインエントリーポイント
├── [service]_handler.py     # メインハンドラー
├── models/                  # データモデル
│   ├── __init__.py
│   └── [model_name].py
├── services/                # ビジネスサービス
│   ├── __init__.py
│   └── [service_name]_service.py
├── utils/                   # ユーティリティ
│   ├── __init__.py
│   └── [util_name].py
├── tests/                   # テストコード
│   ├── __init__.py
│   ├── test_[service].py
│   └── fixtures/
│       └── test_data.py
└── configs/                 # 設定ファイル
    └── [service]_config.yaml
```

### 📦 共通ライブラリ構造

```
libs/
├── [category]/              # カテゴリ別分類
│   ├── __init__.py
│   ├── [lib_name]/
│   │   ├── __init__.py
│   │   ├── [main_module].py
│   │   ├── utils.py
│   │   └── tests/
│   │       └── test_[lib_name].py
│   └── common/              # カテゴリ共通
│       ├── __init__.py
│       └── [common_module].py
└── shared/                  # 全体共通
    ├── __init__.py
    └── [shared_module].py
```

## 🔍 Import Path設計規則

### 🎯 絶対Import標準パターン

#### **4賢者システムimport**
```python
# 標準パターン（推奨）
from incident_sage.abilities.incident_models import Incident
from knowledge_sage.business_logic import KnowledgeProcessor
from task_sage.a2a_agent import TaskSageAgent
from rag_sage.soul import RAGSageSoul

# 共通ライブラリimport
from shared_libs.soul_base import BaseSoul
from shared_libs.utilities import utility_function
```

#### **ライブラリ・サービスimport**
```python
# ライブラリimport
from libs.category.lib_name.main_module import MainClass
from libs.shared.common_module import shared_function

# コアシステムimport
from core.base_manager import BaseManager
from core.config import Config

# ワーカーimport
from workers.worker_name import WorkerClass
```

#### **相対import禁止例**
```python
❌ 絶対禁止:
from ..shared_libs.soul_base import BaseSoul
from .abilities.models import Model
from ...core.config import Config
```

### 📋 Import階層設計原則

#### **依存関係の明示**
```python
# レイヤー1: 基盤
from shared_libs.soul_base import BaseSoul

# レイヤー2: コア機能
from core.base_manager import BaseManager

# レイヤー3: 4賢者
from incident_sage.business_logic import IncidentProcessor

# レイヤー4: アプリケーション
from workers.incident_worker import IncidentWorker
```

## 🛡️ 重複防止チェック規則

### 🔍 開発開始前必須チェック

#### **1. 既存確認コマンド**
```bash
# ディレクトリ重複確認
find . -name "*[新機能名]*" -type d | grep -v __pycache__ | grep -v .git

# ファイル重複確認
find . -name "*[新機能名]*" -type f | grep -v __pycache__ | grep -v .git

# Import参照確認
grep -r "from.*[新機能名]" . --include="*.py"
```

#### **2. 命名規約チェック**
```bash
# 命名規約チェックスクリプト実行
./scripts/check_naming_conventions.py --target [新機能名]

# ディレクトリ構造チェック
./scripts/check_directory_structure.py --target [新機能名]
```

### 📊 コミット前必須チェック

#### **自動チェックスクリプト**
```bash
# 包括的重複チェック
./scripts/pre_commit_checks.py

# Import path一貫性チェック
./scripts/check_import_consistency.py

# 命名規約準拠チェック
./scripts/check_naming_compliance.py
```

## 🎓 実践的な開発フロー

### 🚀 新機能開発標準手順

#### **Step 1: 計画・確認フェーズ**
```bash
# 1. 機能名決定（命名規約確認）
NEW_FEATURE="payment_processor"  # アンダースコア小文字

# 2. 既存重複確認
find . -name "*payment*" -type d
find . -name "*processor*" -type d

# 3. 配置場所決定
# 4賢者: [sage_name]/
# ライブラリ: libs/[category]/[lib_name]/
# サービス: [service_name]/
```

#### **Step 2: ディレクトリ作成フェーズ**
```bash
# 標準構造作成
mkdir -p ${NEW_FEATURE}/{abilities,tests,configs}

# 必須ファイル作成
touch ${NEW_FEATURE}/__init__.py
touch ${NEW_FEATURE}/soul.py
touch ${NEW_FEATURE}/business_logic.py
touch ${NEW_FEATURE}/abilities/__init__.py
touch ${NEW_FEATURE}/abilities/${NEW_FEATURE}_models.py
touch ${NEW_FEATURE}/tests/__init__.py
touch ${NEW_FEATURE}/tests/test_${NEW_FEATURE}.py
```

#### **Step 3: 実装フェーズ**
```bash
# Import path標準化確認
grep -n "from.*${NEW_FEATURE}" ${NEW_FEATURE}/*.py

# 動作確認
python3 -c "from ${NEW_FEATURE}.business_logic import MainClass; print('OK')"
```

#### **Step 4: 品質チェックフェーズ**
```bash
# 自動チェック実行
./scripts/pre_commit_checks.py --target ${NEW_FEATURE}

# 命名規約チェック
./scripts/check_naming_conventions.py --target ${NEW_FEATURE}

# 重複チェック
./scripts/check_duplicates.py --target ${NEW_FEATURE}
```

### 🔧 既存コードリファクタリング手順

#### **安全なディレクトリ名変更**
```bash
# 1. 影響範囲調査
OLD_NAME="old_feature"
NEW_NAME="new_feature"

grep -r "from.*${OLD_NAME}" . --include="*.py" > impact_analysis.txt
grep -r "import.*${OLD_NAME}" . --include="*.py" >> impact_analysis.txt

# 2. Git履歴保持移動
git mv ${OLD_NAME} ${NEW_NAME}

# 3. Import path一括置換
find . -name "*.py" -exec sed -i "s/from ${OLD_NAME}/from ${NEW_NAME}/g" {} \;
find . -name "*.py" -exec sed -i "s/import ${OLD_NAME}/import ${NEW_NAME}/g" {} \;

# 4. 動作確認
python3 -c "from ${NEW_NAME}.main import MainClass; print('Refactoring OK')"
```

## 📋 チェックリスト

### ✅ 新機能開発チェックリスト

#### **開発開始前**
- [ ] 機能名が命名規約に準拠している
- [ ] 既存重複がないことを確認済み
- [ ] 配置場所が標準パターンに従っている
- [ ] ディレクトリ構造が標準に準拠している

#### **実装中**
- [ ] ファイル命名が規約に準拠している
- [ ] Import pathが絶対importパターンに従っている
- [ ] 必須ファイル（__init__.py, tests等）が存在する
- [ ] ドキュメント作成済み

#### **コミット前**
- [ ] 自動チェックスクリプト実行・合格
- [ ] 動作確認テスト実行・合格
- [ ] Import path一貫性確認済み
- [ ] 重複検知スクリプト実行・合格

### ✅ レビュー時チェックリスト

#### **構造確認**
- [ ] プロジェクト構造標準準拠
- [ ] ディレクトリ命名規約準拠
- [ ] ファイル命名規約準拠
- [ ] Import path標準化

#### **品質確認**
- [ ] 重複ディレクトリ・ファイルなし
- [ ] 相対import使用なし
- [ ] 必須ドキュメント更新済み
- [ ] テストコード存在・合格

## 🎯 まとめ

### 🏛️ エルダーズギルドの決意

**「想定しない名前で作り始めない」**

Issue #302 の教訓を活かし、この命名規約・ディレクトリ構造ルールを全員が徹底遵守することで：

1. **迷わない開発環境**: 即座に配置場所が判断可能
2. **一貫したコードベース**: 全プロジェクトで統一された構造
3. **スケーラブルな成長**: 将来の拡張に対応する柔軟性

### ✅ 必須遵守事項
- **命名規約**: アンダースコア小文字統一
- **重複禁止**: 1機能1場所の原則
- **絶対Import**: 相対import完全禁止
- **自動チェック**: コミット前必須実行

**これらのルールを守ることで、エルダーズギルドは永続的に高品質なコードベースを維持します。**

---
**🏛️ Generated with [Claude Code](https://claude.ai/code)**  
**Co-Authored-By: Claude <noreply@anthropic.com>**