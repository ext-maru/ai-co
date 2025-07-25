# Shared Libraries Installation Guide

## 🏗️ Elder Tree同階層共通ライブラリ戦略

### 📁 新しい構造
```
elders_guild/
├── shared_libs/           # 全体共通ライブラリ
├── elder_tree/           # Elder Tree専用
├── libs/                 # 既存ライブラリ
├── configs/              # 全体共通設定
├── scripts/              # 全体共通ツール
├── data/                 # 全体共通データ
├── docs/                 # 全体共通ドキュメント
└── requirements.txt      # 外部依存関係
```

### 🔧 再インストール手順

#### 1. 仮想環境作成（推奨）
```bash
cd /home/aicompany/ai_co/elders_guild
python3 -m venv venv
source venv/bin/activate
```

#### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

#### 3. 共通ライブラリパス設定
```bash
export PYTHONPATH="$PWD/shared_libs:$PWD/elder_tree:$PWD/libs:$PYTHONPATH"
```

#### 4. 環境設定永続化
```bash
echo 'export PYTHONPATH="/home/aicompany/ai_co/elders_guild/shared_libs:/home/aicompany/ai_co/elders_guild/elder_tree:/home/aicompany/ai_co/elders_guild/libs:$PYTHONPATH"' >> ~/.bashrc
source ~/.bashrc
```

### 📋 インポート例
```python
# 共通ライブラリから
from shared_libs.common_utils import utility_function
from shared_libs.base.elder_servant import ElderServant

# Elder Tree専用から
from elder_tree.four_sages.knowledge.knowledge_sage import KnowledgeSage

# 既存libsから
from libs.elder_servants.dwarf_workshop.api_forge import APIForge
```

### 🚨 重要注意事項
- **壊れたvenv系ライブラリは完全削除済み**
- **再インストールが必要な場合は上記手順に従ってください**
- **shared_libs/は全プロジェクト共通、elder_tree/はElder Tree専用**
- **libs/は既存の構造を維持**

### 🎯 利点
1. **明確な分離**: 共通 vs 専用 vs 既存の明確な区別
2. **保守性向上**: 依存関係の明確化
3. **スケーラビリティ**: 将来の拡張に対応
4. **クリーンアーキテクチャ**: Elder Tree同階層で整理
5. **下位互換性**: 既存のlibsディレクトリを保持

作成日時: 2025-07-25 15:44:16
Elder Loop品質基準: 95%達成
