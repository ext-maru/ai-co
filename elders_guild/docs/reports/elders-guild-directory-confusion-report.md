# エルダーズギルド ディレクトリ構造混乱レポート

## 🚨 発見された問題

### 1. ソースコード配置の混乱

#### 現在の状況:
```
/elders_guild/
├── ancient_magic/          # ✅ 正しく配置（8つの古代魔法）
├── knowledge_sage/         # ✅ soul.py存在（662行）
├── task_sage/             # ✅ soul.py存在
├── rag_sage/              # ✅ soul.py存在
├── incident_sage/         # ❌ soul.pyが存在しない！
│   ├── a2a_agent.py       # ビジネスロジックのみ
│   └── business_logic.py
└── src/                   # ❌ 誤って作成されたディレクトリ
    ├── elder_tree/        # Elder Tree v2実装
    ├── knowledge_sage/    # soul.py存在（683行 - より新しい？）
    ├── task_sage/        # soul.py存在
    ├── rag_sage/         # soul.py存在
    └── incident_sage/    # soul.py存在（1423行）

```

### 2. 具体的な問題点

1. **incident_sageのsoul.pyが誤った場所にある**
   - 正: `/elders_guild/incident_sage/soul.py`
   - 現: `/elders_guild/src/incident_sage/soul.py`

2. **他の3賢者は重複している**
   - knowledge_sage、task_sage、rag_sageは両方の場所にsoul.pyが存在
   - どちらが正式版か不明確

3. **Elder Tree v2が誤った場所にある**
   - 現: `/elders_guild/src/elder_tree/`
   - 正: 未定（要検討）

### 3. 影響範囲

- importパスの混乱
- テストコードの動作不良の可能性
- 開発者の混乱
- ドキュメントの不正確さ

## 🎯 推奨対応

### Phase 1: 緊急対応
1. **incident_sage/soul.pyの移動**
   ```bash
   mv /elders_guild/src/incident_sage/soul.py /elders_guild/incident_sage/
   ```

2. **重複ファイルの比較・統合**
   - 各賢者のsoul.pyを比較し、新しい方を採用
   - src配下の独自実装があれば、適切に統合

### Phase 2: 構造整理
1. **Elder Treeの配置決定**
   - `/elders_guild/elder_tree/` または
   - `/libs/elder_tree/` または
   - 別プロジェクトとして分離

2. **src/ディレクトリの削除**
   - 必要なファイルを移動後、srcディレクトリを削除

### Phase 3: ドキュメント更新
1. **ディレクトリ構造図の更新**
2. **importパスの修正**
3. **開発ガイドの更新**

## 📊 ファイル比較結果

| ファイル | 直下 | src配下 | 差分 |
|---------|------|---------|------|
| knowledge_sage/soul.py | 662行 | 683行 | +21行 |
| task_sage/soul.py | 存在 | 存在 | 要確認 |
| rag_sage/soul.py | 存在 | 存在 | 要確認 |
| incident_sage/soul.py | なし | 1423行 | - |

## 🔴 緊急度: 高

この問題は開発の混乱を招くため、早急な対応が必要です。

---
**作成日**: 2025-07-23
**作成者**: Claude Elder