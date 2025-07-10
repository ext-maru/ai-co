# Elder Tree 段階的ロールバック手順書

## 🛡️ Grand Elder maru 安全第一原則準拠

**作成日**: 2025年7月10日  
**責任者**: Claude Elder  
**承認**: Grand Elder maru

## 📋 ロールバック段階構成

### Level 1: 個別ワーカーElderTree無効化

**対象**: 特定のワーカーのみElderTree統合を無効化
**実行時間**: 約2分
**影響範囲**: 該当ワーカーのみ

#### 手順:
1. **対象ワーカーの特定**
   ```bash
   # 問題のあるワーカーを特定
   grep -r "ELDER_TREE_AVAILABLE" workers/
   ```

2. **個別ワーカーの無効化**
   ```python
   # workers/[target_worker].py の修正
   # Line: from libs.elder_tree_hierarchy import get_elder_tree
   # To: # from libs.elder_tree_hierarchy import get_elder_tree
   
   # Line: ELDER_TREE_AVAILABLE = True
   # To: ELDER_TREE_AVAILABLE = False
   
   # Line: self.elder_tree = get_elder_tree()
   # To: self.elder_tree = None
   ```

3. **ワーカー再起動**
   ```bash
   ai-worker-restart [target_worker]
   ```

4. **動作確認**
   ```bash
   ai-worker-status [target_worker]
   ai-logs --worker [target_worker]
   ```

### Level 2: Four Sages システム無効化

**対象**: 4賢者統合システムの無効化
**実行時間**: 約5分
**影響範囲**: 賢者間協調機能

#### 手順:
1. **Four Sages 統合の無効化**
   ```python
   # libs/four_sages_integration.py の修正
   # Line: ELDER_TREE_AVAILABLE = True
   # To: ELDER_TREE_AVAILABLE = False
   ```

2. **ワーカー内の Four Sages 参照無効化**
   ```bash
   # 全ワーカーの Four Sages 参照を無効化
   find workers/ -name "*.py" -exec sed -i 's/from libs.four_sages_integration import/# from libs.four_sages_integration import/g' {} \;
   ```

3. **システム再起動**
   ```bash
   ai-restart
   ```

4. **Four Sages 機能確認**
   ```bash
   ai-status | grep -i sage
   ```

### Level 3: Elder Tree システム完全無効化

**対象**: Elder Tree階層システム全体の無効化
**実行時間**: 約10分
**影響範囲**: 全Elder Tree機能

#### 手順:
1. **Elder Tree 階層システム無効化**
   ```python
   # libs/elder_tree_hierarchy.py の修正
   # 全関数を no-op にする
   
   def get_elder_tree():
       return None
   
   class ElderMessage:
       def __init__(self, *args, **kwargs):
           pass
   
   class ElderRank:
       GRAND_ELDER = "grand_elder"
       CLAUDE_ELDER = "claude_elder"
       SAGE = "sage"
       COUNCIL_MEMBER = "council_member"
       SERVANT = "servant"
   
   class SageType:
       KNOWLEDGE = "knowledge"
       TASK = "task"
       INCIDENT = "incident"
       RAG = "rag"
   ```

2. **全ワーカーの Elder Tree 参照無効化**
   ```bash
   # 全ワーカーファイルの Elder Tree 参照を無効化
   find workers/ -name "*.py" -exec sed -i 's/ELDER_TREE_AVAILABLE = True/ELDER_TREE_AVAILABLE = False/g' {} \;
   ```

3. **システム全体再起動**
   ```bash
   ai-stop
   sleep 5
   ai-start
   ```

4. **Elder Tree 機能確認**
   ```bash
   ai-status | grep -i elder
   python -c "from libs.elder_tree_hierarchy import get_elder_tree; print(get_elder_tree())"
   ```

### Level 4: システム全体の統合前状態復旧

**対象**: Elder Tree統合前の完全な状態に復旧
**実行時間**: 約15分
**影響範囲**: 全システム

#### 手順:
1. **バックアップからの復旧**
   ```bash
   # 現在のファイルをバックアップ
   mv workers workers_elder_integrated_backup_$(date +%Y%m%d_%H%M%S)
   mv libs libs_elder_integrated_backup_$(date +%Y%m%d_%H%M%S)
   
   # 統合前バックアップから復旧
   BACKUP_DIR="/home/aicompany/ai_co/backups/phase_d_backup_20250710_152645"
   cp -r "$BACKUP_DIR/workers" ./workers_restored
   cp -r "$BACKUP_DIR/libs" ./libs_restored
   ```

2. **Elder Tree 統合コード完全削除**
   ```bash
   # Elder Tree 関連ファイルを完全削除
   rm -f libs/elder_*.py
   rm -f libs/four_sages_integration.py
   
   # ワーカーからElderTree統合コードを完全削除
   find workers/ -name "*.py" -exec sed -i '/elder_tree/d' {} \;
   find workers/ -name "*.py" -exec sed -i '/ELDER_TREE/d' {} \;
   find workers/ -name "*.py" -exec sed -i '/four_sages/d' {} \;
   ```

3. **設定ファイル復旧**
   ```bash
   cp "$BACKUP_DIR/config/*" ./config/
   cp "$BACKUP_DIR/CLAUDE.md" ./
   ```

4. **システム完全再起動**
   ```bash
   ai-stop
   sleep 10
   ai-start
   ```

5. **統合前状態確認**
   ```bash
   ai-status
   ai-health
   python -c "import workers.pm_worker; print('PM Worker loaded successfully')"
   ```

## 🚨 緊急時即座ロールバック (5分以内)

**重大障害発生時の緊急手順**

### 緊急手順:
1. **即座停止**
   ```bash
   ai-stop
   ```

2. **Elder Tree フラグ一括無効化**
   ```bash
   # 全Elder Tree参照を即座無効化
   find . -name "*.py" -exec sed -i 's/ELDER_TREE_AVAILABLE = True/ELDER_TREE_AVAILABLE = False/g' {} \;
   ```

3. **クリティカルワーカーのみ起動**
   ```bash
   # 最小限のワーカーのみ起動
   ai-worker-start pm_worker
   ai-worker-start result_worker
   ai-worker-start health_check
   ```

4. **Elder Tree 完全無効化**
   ```bash
   # Elder Tree 階層システム完全無効化
   echo "def get_elder_tree(): return None" > libs/elder_tree_hierarchy.py
   ```

5. **システム確認**
   ```bash
   ai-status
   ai-health
   ```

## 🔄 Graceful Degradation 動作確認

各レベルでの動作確認項目:

### Level 1 確認項目:
- [ ] 対象ワーカーが正常起動
- [ ] Elder Tree 機能が無効化されている
- [ ] 他のワーカーは影響を受けない
- [ ] 基本機能は正常動作

### Level 2 確認項目:
- [ ] Four Sages 統合が無効化
- [ ] ワーカー間通信は正常
- [ ] Elder Tree 階層は残存
- [ ] 基本機能は正常動作

### Level 3 確認項目:
- [ ] Elder Tree 階層が完全無効化
- [ ] 全ワーカーが正常起動
- [ ] 基本機能は正常動作
- [ ] パフォーマンスに影響なし

### Level 4 確認項目:
- [ ] 統合前状態に完全復旧
- [ ] Elder Tree 関連コードが完全削除
- [ ] 全システムが安定動作
- [ ] 機能低下がない

## 📊 ロールバック成功基準

### 技術基準:
- システム起動時間: 5分以内
- 機能テスト成功率: 100%
- エラーログ: 0件
- メモリ使用量: 正常範囲

### 業務基準:
- 基本機能動作: 100%
- レスポンス時間: 統合前レベル
- 安定性: 24時間連続動作
- データ整合性: 完全保持

## 🎯 復旧確認チェックリスト

### 即座確認 (5分以内):
- [ ] システム起動完了
- [ ] 基本API応答
- [ ] ワーカー起動確認
- [ ] エラーログ確認

### 詳細確認 (30分以内):
- [ ] 全機能動作テスト
- [ ] パフォーマンス測定
- [ ] メモリ使用量確認
- [ ] データ整合性確認

### 継続監視 (24時間):
- [ ] 安定性監視
- [ ] エラー発生監視
- [ ] パフォーマンス監視
- [ ] リソース使用量監視

## 🏛️ Elder 階層報告体制

### 報告義務:
1. **Level 1-2**: Claude Elder → Grand Elder maru 報告
2. **Level 3-4**: 緊急評議会招集
3. **緊急時**: 即座報告 (5分以内)

### 報告内容:
- ロールバック実行理由
- 影響範囲と時間
- 復旧手順と結果
- 今後の対策

---

**Grand Elder maru 最終承認**: 2025年7月10日  
**次回見直し**: 2025年7月17日  
**緊急連絡**: Claude Elder 直通

🛡️ **品質第一×安全第一** 🛡️