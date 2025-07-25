# 🔄 Elders Guild 統合ロールバック緊急ガイド

## 🚨 緊急ロールバック手順

### ⚡ 即座実行（3分以内）
```bash
cd /home/aicompany/ai_co

# 1. 現在の統合版をバックアップ（念のため）
mv elders_guild elders_guild_integrated_$(date +%Y%m%d_%H%M%S)

# 2. 統合前状態に完全復元
cp -r elders_guild_backup_20250723_201711 elders_guild

# 3. 復元確認
ls -la elders_guild/ | grep -E "(incident_sage|knowledge_sage|rag_sage|task_sage)"

echo "✅ ロールバック完了 - 統合前状態に復元"
```

### 🔍 復元検証
```bash
# 重複ディレクトリが戻っているか確認
ls elders_guild/incident_sage/     # 直下版
ls elders_guild/src/incident_sage/ # src版

# 基本動作確認
python3 -c "from elders_guild.knowledge_sage.soul import KnowledgeSage; print('復元成功')"
```

## 📊 ロールバック後の状態

### 復元される構造
```
elders_guild/
├── incident_sage/              # 直下版（A2A機能付き）
├── knowledge_sage/             # 直下版（A2A機能付き）
├── rag_sage/                  # 直下版（A2A機能付き）
├── task_sage/                 # 直下版（A2A機能付き）
├── shared_libs/               # 直下版
└── src/
    ├── incident_sage/         # src版（基本機能）
    ├── knowledge_sage/        # src版（基本機能）
    ├── rag_sage/             # src版（基本機能）
    ├── task_sage/            # src版（基本機能）
    ├── shared_libs/          # src版
    └── elder_tree/           # エルダーツリー
```

## 🛡️ 部分ロールバック

### 特定賢者のみ復元
```bash
# Knowledge Sageのみロールバック
cp -r elders_guild_backup_20250723_201711/knowledge_sage elders_guild/
cp -r elders_guild_backup_20250723_201711/src/knowledge_sage elders_guild/src/
```

## 📋 ロールバック理由と対応

### よくあるロールバック理由
1. **import エラー**: `from src.` が動作しない
2. **A2A依存問題**: python-a2aが不足
3. **テスト失敗**: 統合後のテストで予期しないエラー
4. **Elder Tree問題**: エルダーツリーとの連携不具合

### 対応方法
- **即座ロールバック**: 上記手順で3分以内に復元
- **問題分析**: ロールバック後に統合ログを分析
- **段階的再統合**: 問題解決後の段階的再統合実施

## 🔧 ロールバック後の復旧確認

### 必須チェック項目
- [ ] 直下の4賢者ディレクトリ存在確認
- [ ] src配下の4賢者ディレクトリ存在確認
- [ ] 基本import動作確認
- [ ] 実行スクリプト動作確認
- [ ] テスト実行可能性確認

---
**緊急時連絡**: Claude Elder統合チーム  
**バックアップ場所**: `/home/aicompany/ai_co/elders_guild_backup_20250723_201711`  
**復旧保証**: 3分以内の完全復元