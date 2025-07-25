# 🏷️ 命名規約違反分析レポート
## エルダーズギルド 命名規約準拠状況調査

**作成日**: 2025-07-23  
**責任者**: Claude Elder  
**根拠**: docs/standards/NAMING_CONVENTIONS_AND_DIRECTORY_RULES.md

---

## 🚨 重大な命名規約違反

### ❌ **Tier 1: 絶対禁止ディレクトリ**

#### **1. `src/` ディレクトリ（重複の温床）**
```
❌ ./deployment/contract-upload-system/frontend/src
❌ ./elders_guild_safe_backup_20250723_203104/src  # バックアップ内
```
**影響**: Issue #302の原因となった禁止パターン
**対応**: 即座削除またはリネーム必須

#### **2. `config/` ディレクトリ（単数形禁止）**
```
❌ ./config                                      # ルート違反
❌ ./elders_guild/config                         # 重複違反
❌ ./task_sage/config                           # 4賢者内違反
❌ ./tests/integration/config                   # テスト内違反
❌ ./elders_guild/task_sage/config              # バックアップ内違反
❌ ./elders_guild/backup_before_final_integration/task_sage/config
❌ ./elders_guild/backup_before_final_integration/rag_sage/config
```
**正しい命名**: `configs/` （複数形必須）

---

## 🔧 修正計画

### 📋 **Phase 1: 現行システム修正（優先度：高）**

#### **Step 1: ルートconfig修正**
```bash
# 1. 既存configディレクトリの確認
ls -la ./config/
ls -la ./configs/  # 既存のconfigsがあるか確認

# 2. 安全な移行
if [ -d "./configs" ]; then
    # configsが既に存在する場合は統合
    mv ./config/* ./configs/ 2>/dev/null || true
    rmdir ./config
else
    # configsが存在しない場合はリネーム
    mv ./config ./configs
fi
```

#### **Step 2: 4賢者システム内config修正**
```bash
# task_sage内のconfig修正
if [ -d "./task_sage/config" ]; then
    mv ./task_sage/config ./task_sage/configs
fi

# Import path更新が必要な場合
find ./task_sage -name "*.py" -exec grep -l "config/" {} \; | \
xargs sed -i 's|config/|configs/|g'
```

#### **Step 3: テスト内config修正**
```bash
# テスト内のconfig修正
if [ -d "./tests/integration/config" ]; then
    mv ./tests/integration/config ./tests/integration/configs
fi
```

### 📋 **Phase 2: バックアップディレクトリ処理（優先度：中）**

#### **バックアップ内違反の対応方針**
- `elders_guild_safe_backup_20250723_203104/` - 保持（履歴保存）
- `elders_guild/backup_before_final_integration/` - 保持（履歴保存）
- `elders_guild/config`, `elders_guild/task_sage/config` - 削除候補

### 📋 **Phase 3: 外部システム対応（優先度：低）**

#### **contract-upload-system内src**
```bash
# フロントエンドプロジェクトのため例外として保持
# ただし、docs/standards/PROJECT_STRUCTURE_STANDARDS.md に例外記録
```

---

## ✅ 修正後の期待される構造

### **修正前 → 修正後**
```
❌ ./config/                    → ✅ ./configs/
❌ ./task_sage/config/          → ✅ ./task_sage/configs/
❌ ./tests/integration/config/  → ✅ ./tests/integration/configs/
❌ ./elders_guild/config/       → ✅ 削除（重複排除）
```

### **Import Path変更**
```python
# 修正前
from config.settings import CONFIG
import config.database as db

# 修正後  
from configs.settings import CONFIG
import configs.database as db
```

---

## 🛡️ 再発防止策

### **1. 自動チェック統合**
```bash
# pre-commit hook追加
./scripts/check_naming_compliance.py --strict
```

### **2. 命名規約チェッカー強化**
```bash
# 禁止パターン自動検知
./scripts/check_project_duplicates.py --naming-strict
```

### **3. 開発者教育**
- 新機能開発時の命名規約確認必須化
- コードレビュー時の命名チェック強化

---

## 📊 影響度評価

### **高影響**
- `./config/` → `./configs/` - 全体設定への影響
- `./task_sage/config/` → `./task_sage/configs/` - 4賢者システムへの影響

### **中影響**  
- `./tests/integration/config/` → `./tests/integration/configs/` - テストへの影響

### **低影響**
- バックアップディレクトリ内の違反 - 過去データのため影響小

---

## 🎯 実行推奨順序

1. **即座実行**: ルートconfig修正
2. **計画実行**: 4賢者システム内config修正
3. **段階実行**: テスト内config修正
4. **最終確認**: Import path整合性チェック
5. **文書更新**: 例外ケースの正式記録

**この修正により、命名規約完全準拠とIssue #302再発防止を実現します。**

---
**🏛️ Generated with [Claude Code](https://claude.ai/code)**  
**Co-Authored-By: Claude <noreply@anthropic.com>**