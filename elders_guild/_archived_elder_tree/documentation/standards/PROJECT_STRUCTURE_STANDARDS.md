# 🏛️ エルダーズギルド プロジェクト構造標準化ガイドライン
## Issue #302 教訓に基づく開発構造統一規約

**策定日**: 2025-07-23  
**根拠**: Issue #302 重複ディレクトリ問題解決の教訓  
**適用範囲**: 全エルダーズギルドプロジェクト  
**承認**: グランドエルダーmaru様承認済み

---

## 🎯 策定目的

### 🚨 解決すべき問題
- **重複ディレクトリの禁止**: 同一機能の複数配置によるマトソウ
- **Import path統一**: 一貫した依存関係の表現
- **開発効率向上**: 迷わない構造による生産性向上

### ✅ 達成目標
1. **ゼロ・アンビギイティ**: 全ての機能が一意の場所に配置
2. **予測可能性**: 命名規約により配置場所が予測可能
3. **スケーラビリティ**: 将来の拡張に対応する柔軟性

---

## 📁 標準ディレクトリ構造

### 🏛️ プロジェクトルート基本構造

```
project_root/
├── README.md                    # プロジェクト概要（必須）
├── CLAUDE.md                    # Claude CLI設定（必須）
├── requirements.txt             # 依存関係（必須）
├── .gitignore                   # Git除外設定（必須）
│
├── docs/                        # 全ドキュメント
│   ├── standards/              # 標準・規約
│   ├── guides/                 # ガイド・チュートリアル
│   ├── projects/               # プロジェクト固有ドキュメント
│   ├── api/                    # API仕様書
│   └── reports/                # レポート・分析結果
│
├── src/                         # 🚨 原則禁止（例外は後述）
├── libs/                        # 共通ライブラリ
├── core/                        # コアシステム（基盤）
├── shared_libs/                 # 4賢者共通ライブラリ
│
├── [sage_name]/                 # 4賢者システム（プロジェクトルート直下）
│   ├── __init__.py             # モジュール初期化
│   ├── soul.py                 # 魂実装（メイン）
│   ├── business_logic.py       # ビジネスロジック
│   ├── a2a_agent.py           # A2A通信エージェント
│   ├── abilities/              # 固有能力
│   │   ├── __init__.py
│   │   └── [sage_name]_models.py
│   └── tests/                  # テストコード
│       ├── __init__.py
│       └── test_[sage_name].py
│
├── workers/                     # ワーカープロセス
├── scripts/                     # 実行スクリプト
│   ├── deployment/             # デプロイメント
│   ├── monitoring/             # 監視スクリプト
│   ├── quality/                # 品質チェック
│   └── utilities/              # ユーティリティ
│
├── tests/                       # 統合テスト
│   ├── unit/                   # ユニットテスト
│   ├── integration/            # 統合テスト
│   └── fixtures/               # テストデータ
│
├── configs/                     # 設定ファイル
├── data/                        # データファイル
├── logs/                        # ログファイル
└── venv/                        # 仮想環境（Git除外）
```

## 📋 命名規約

### 🏷️ ディレクトリ命名規則

#### **必須規約**
```
✅ 正しい命名例:
- incident_sage/        # アンダースコア区切り
- knowledge_sage/       # 小文字のみ
- shared_libs/          # 略語可（libsは標準略語）
- docs/                 # 短縮形推奨

❌ 禁止命名例:
- incident-sage/        # ハイフン禁止
- IncidentSage/         # キャメルケース禁止
- incidentSage/         # キャメルケース禁止
- Incident_Sage/        # 大文字小文字混在禁止
```

#### **特別なディレクトリ**
```
🚨 絶対禁止:
- src/                  # 重複の温床となるため原則禁止
- lib/                  # libsに統一
- include/              # Pythonでは使用しない
- bin/                  # scriptsに統一

⚠️ 要注意:
- temp/ → tmp/          # 一時ファイルはtmpに統一
- backup/ → backups/    # 複数形推奨
- config/ → configs/    # 複数形推奨
```

### 🏷️ ファイル命名規則

#### **Python ファイル**
```
✅ 正しい命名:
- soul.py              # 機能メインファイル
- business_logic.py    # アンダースコア区切り
- incident_models.py   # 複数形推奨（models, tests等）
- __init__.py          # パッケージ初期化

❌ 禁止命名:
- Soul.py              # 大文字開始禁止
- business-logic.py    # ハイフン禁止
- incidentModel.py     # キャメルケース禁止
```

#### **ドキュメントファイル**
```
✅ 正しい命名:
- PROJECT_STRUCTURE_STANDARDS.md    # 大文字アンダースコア
- API_REFERENCE.md                  # 略語可
- user_guide.md                     # 小文字アンダースコア

❌ 禁止命名:
- project-structure.md              # ハイフン禁止
- ProjectStructure.md               # キャメルケース禁止
```

## 🚨 重複防止ルール

### 📍 配置の一意性原則

#### **1機能1場所の原則**
```
✅ 正しい配置:
incident_sage/
├── soul.py                    # インシデント賢者の唯一の実装
├── business_logic.py          # 唯一のビジネスロジック
└── abilities/
    └── incident_models.py     # 唯一のモデル定義

❌ 重複配置（絶対禁止）:
incident_sage/
├── soul.py
└── v2/
    └── soul.py               # 重複！禁止！

src/
└── incident_sage/
    └── soul.py               # 重複！禁止！
```

#### **実験的開発の許可パターン**
```
✅ 許可される実験構造:
experiments/                   # 実験専用ディレクトリ
├── incident_sage_v2/         # バージョン明示
├── new_feature_prototype/     # プロトタイプ明示
└── poc_integration/           # POC明示

注意：実験完了後は必ず統合または削除する
```

### 🔍 重複検知チェックリスト

#### **開発開始前チェック**
- [ ] 同名ディレクトリが他に存在しないか？
- [ ] 同機能を実装する別の場所はないか？
- [ ] import pathが一意になっているか？

#### **コミット前チェック**
- [ ] 重複検知スクリプト実行済みか？
- [ ] Import pathが標準に準拠しているか？
- [ ] ディレクトリ命名規約に準拠しているか？

## 📦 Import Path標準化

### 🎯 絶対Import原則

#### **推奨パターン**
```python
✅ 正しいimport:
# 4賢者システム
from incident_sage.abilities.incident_models import Incident
from knowledge_sage.business_logic import KnowledgeProcessor

# 共通ライブラリ
from shared_libs.soul_base import BaseSoul
from libs.elder_servants.base.elder_servant_base import ElderServantBase

# コアシステム
from core.base_manager import BaseManager
```

#### **禁止パターン**
```python
❌ 禁止import:
# 相対import（階層変更に脆弱）
from ..shared_libs.soul_base import BaseSoul
from .abilities.incident_models import Incident

# sys.path操作（非標準）
import sys
sys.path.append("/some/path")
```

### 🔧 Import Path設計原則

#### **1. 予測可能性**
```python
# モジュール名からパスが予測可能
from incident_sage.abilities.incident_models import Incident
# → incident_sage/abilities/incident_models.py
```

#### **2. 階層の明示性**
```python
# 依存関係が明確
from shared_libs.soul_base import BaseSoul      # 共通基盤
from incident_sage.abilities.incident_models import Incident  # 固有機能
```

#### **3. リファクタリング耐性**
```python
# ディレクトリ移動に耐性がある
from libs.utilities.helper import utility_function  # OK
# 相対importは移動で破綻する
from ..utilities.helper import utility_function     # NG
```

## 🛠️ 実装ガイドライン

### 📝 新機能開発手順

#### **Step 1: 配置場所決定**
```bash
# 1. 既存確認
find . -name "*[機能名]*" -type d

# 2. 命名規約確認
# 機能名_sage/ または 機能名/ （標準パターンに従う）

# 3. 重複検知スクリプト実行
./scripts/check_duplicates.py --target-name [機能名]
```

#### **Step 2: ディレクトリ作成**
```bash
# 標準構造作成
mkdir -p [機能名]/{abilities,tests}
touch [機能名]/__init__.py
touch [機能名]/abilities/__init__.py
touch [機能名]/tests/__init__.py
```

#### **Step 3: ファイル作成**
```bash
# 標準ファイル作成
touch [機能名]/soul.py
touch [機能名]/business_logic.py
touch [機能名]/abilities/[機能名]_models.py
touch [機能名]/tests/test_[機能名].py
```

### 🔧 リファクタリング手順

#### **安全なディレクトリ移動**
```bash
# 1. 影響範囲調査
grep -r "from old_location" . --include="*.py"

# 2. Git追跡を保持した移動
git mv old_location new_location

# 3. Import path一括置換
find . -name "*.py" -exec sed -i 's/from old_location/from new_location/g' {} \;

# 4. 動作確認
python3 -c "from new_location.module import Class; print('OK')"
```

## 🔍 品質保証

### 📊 自動チェック項目

#### **重複検知**
```bash
# ディレクトリ重複チェック
./scripts/check_directory_duplicates.py

# ファイル重複チェック  
./scripts/check_file_duplicates.py

# Import path統一チェック
./scripts/check_import_consistency.py
```

#### **命名規約チェック**
```bash
# ディレクトリ命名チェック
./scripts/check_directory_naming.py

# ファイル命名チェック
./scripts/check_file_naming.py
```

### 📋 手動チェックリスト

#### **新機能追加時**
- [ ] ディレクトリ命名規約準拠確認
- [ ] ファイル命名規約準拠確認
- [ ] Import path標準化確認
- [ ] 重複検知スクリプト実行・合格
- [ ] 動作確認テスト実行・合格

#### **コードレビュー時**
- [ ] プロジェクト構造標準準拠確認
- [ ] Import path一貫性確認
- [ ] ドキュメント更新確認
- [ ] テストコード存在確認

## 🚨 例外処理規程

### ⚠️ 例外を許可する場合

#### **1. レガシーコード移行期間**
```
legacy_migration/              # 移行専用
├── old_system/               # 旧システム（削除予定）
└── migration_scripts/        # 移行スクリプト
```

#### **2. 外部ライブラリ統合**
```
third_party/                  # サードパーティ
├── vendor/                   # ベンダー提供
└── patches/                  # パッチ適用
```

#### **3. 実験的開発**
```
experiments/                  # 実験専用
├── [実験名]_prototype/       # プロトタイプ
└── poc_[機能名]/            # POC
```

### 📋 例外申請プロセス
1. **技術的正当性**: なぜ標準に従えないのか
2. **期限設定**: いつまでに標準化するか
3. **影響範囲**: 他システムへの影響は？
4. **承認取得**: グランドエルダーmaru様承認

## 🎓 まとめ

### ✅ 必須遵守事項
1. **1機能1場所**: 重複配置の絶対禁止
2. **命名規約**: アンダースコア小文字統一
3. **絶対Import**: 相対import禁止
4. **自動チェック**: コミット前必須実行

### 🏛️ エルダーズギルドの約束
**「想定しない名前で作り始めない」** - Issue #302の教訓を活かし、予測可能で一貫した構造を維持し、全員が迷わず開発できる環境を実現します。

---
**🏛️ Generated with [Claude Code](https://claude.ai/code)**  
**Co-Authored-By: Claude <noreply@anthropic.com>**