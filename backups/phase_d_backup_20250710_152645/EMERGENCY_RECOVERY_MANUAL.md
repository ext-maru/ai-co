# 緊急時復旧プロセス完全マニュアル

## 🚨 Elder Tree 統合システム緊急時復旧手順

**最終更新**: 2025年7月10日  
**責任者**: Claude Elder  
**承認**: Grand Elder maru  
**緊急度**: CRITICAL

---

## 📋 緊急時分類と対応

### 🔴 Critical Level 1: システム全体停止

**症状**: 
- AI Company システム完全停止
- 全ワーカー応答不能
- Elder Tree 関連エラーでシステム起動不可

**対応時間**: 5分以内

#### 即座実行手順:
```bash
# Step 1: システム強制停止
sudo pkill -f "ai-company"
sudo pkill -f "python.*worker"

# Step 2: Elder Tree 緊急無効化
cd /home/aicompany/ai_co
find . -name "*.py" -exec sed -i 's/ELDER_TREE_AVAILABLE = True/ELDER_TREE_AVAILABLE = False/g' {} \;

# Step 3: 最小限構成で起動
echo "def get_elder_tree(): return None" > libs/elder_tree_hierarchy.py
echo "ELDER_TREE_AVAILABLE = False" >> libs/elder_tree_hierarchy.py

# Step 4: 基本ワーカーのみ起動
ai-worker-start pm_worker
ai-worker-start result_worker
ai-worker-start health_check

# Step 5: 状態確認
ai-status
ai-health
```

### 🟠 Critical Level 2: 部分的機能障害

**症状**: 
- 一部ワーカーが Elder Tree エラーで停止
- Four Sages 統合エラー
- 間歇的な応答遅延

**対応時間**: 10分以内

#### 段階的復旧手順:
```bash
# Step 1: 問題箇所の特定
ai-logs | grep -i "elder\|sage" | tail -20

# Step 2: 該当ワーカーの Elder Tree 無効化
# 問題のワーカーファイルを編集
sed -i 's/ELDER_TREE_AVAILABLE = True/ELDER_TREE_AVAILABLE = False/g' workers/[problem_worker].py

# Step 3: Four Sages 統合無効化
echo "ELDER_TREE_AVAILABLE = False" > libs/four_sages_integration.py

# Step 4: 該当ワーカー再起動
ai-worker-restart [problem_worker]

# Step 5: 全体状況確認
ai-status
```

### 🟡 Critical Level 3: パフォーマンス劣化

**症状**: 
- 応答時間が著しく遅延
- Elder Tree 階層通信でボトルネック
- メモリ使用量異常増加

**対応時間**: 15分以内

#### 最適化復旧手順:
```bash
# Step 1: リソース使用量確認
top -p $(pgrep -f "python.*worker")
free -h

# Step 2: Elder Tree 通信最適化
# Four Sages 統合の一時的無効化
mv libs/four_sages_integration.py libs/four_sages_integration.py.disabled

# Step 3: ワーカー軽量化
# 各ワーカーの Elder Tree 機能を段階的無効化
find workers/ -name "*.py" -exec sed -i 's/self\.elder_tree = get_elder_tree()/self.elder_tree = None/g' {} \;

# Step 4: システム軽量再起動
ai-restart --light

# Step 5: パフォーマンス確認
ai-metrics
```

---

## 🛠️ 復旧手順詳細

### Phase 1: 緊急診断 (2分以内)

```bash
#!/bin/bash
# 緊急診断スクリプト

echo "=== Elder Tree 緊急診断開始 ==="
echo "時刻: $(date)"

# 1. システム状態確認
echo "1. システム状態:"
systemctl status ai-company 2>/dev/null || echo "Service not running"

# 2. プロセス確認
echo "2. プロセス状態:"
pgrep -f "python.*worker" | wc -l
echo "アクティブワーカー数: $(pgrep -f 'python.*worker' | wc -l)"

# 3. Elder Tree 関連エラー確認
echo "3. Elder Tree エラー:"
tail -20 /var/log/ai-company/error.log 2>/dev/null | grep -i elder || echo "No Elder Tree errors"

# 4. メモリ使用量
echo "4. メモリ使用量:"
free -h | grep Mem

# 5. ディスク使用量
echo "5. ディスク使用量:"
df -h | grep -E "/$|/home"

echo "=== 緊急診断完了 ==="
```

### Phase 2: 緊急復旧 (3分以内)

```bash
#!/bin/bash
# 緊急復旧スクリプト

echo "=== Elder Tree 緊急復旧開始 ==="

# 1. システム停止
echo "1. システム停止中..."
ai-stop 2>/dev/null || sudo pkill -f "ai-company"

# 2. Elder Tree 無効化
echo "2. Elder Tree 無効化中..."
cd /home/aicompany/ai_co
find . -name "*.py" -exec sed -i 's/ELDER_TREE_AVAILABLE = True/ELDER_TREE_AVAILABLE = False/g' {} \;

# 3. 最小限ライブラリ設定
echo "3. 最小限ライブラリ設定中..."
echo "def get_elder_tree(): return None" > libs/elder_tree_hierarchy.py

# 4. 基本ワーカー起動
echo "4. 基本ワーカー起動中..."
ai-worker-start pm_worker
sleep 2
ai-worker-start result_worker
sleep 2
ai-worker-start health_check

# 5. 状態確認
echo "5. 復旧状態確認..."
ai-status

echo "=== 緊急復旧完了 ==="
```

### Phase 3: 段階的復旧 (10分以内)

```bash
#!/bin/bash
# 段階的復旧スクリプト

echo "=== Elder Tree 段階的復旧開始 ==="

# 1. 基本機能確認
echo "1. 基本機能確認中..."
ai-health

# 2. 追加ワーカー起動
echo "2. 追加ワーカー起動中..."
WORKERS="task_worker test_worker authentication_worker"
for worker in $WORKERS; do
    echo "  - $worker 起動中..."
    ai-worker-start $worker
    sleep 3
done

# 3. 機能テスト
echo "3. 機能テスト実行中..."
ai-test-basic

# 4. パフォーマンス確認
echo "4. パフォーマンス確認中..."
ai-metrics

# 5. 全体状況確認
echo "5. 全体状況確認..."
ai-status --detailed

echo "=== 段階的復旧完了 ==="
```

---

## 🔍 トラブルシューティング

### Elder Tree 関連エラーパターン

#### パターン1: インポートエラー
```
ImportError: cannot import name 'get_elder_tree' from 'libs.elder_tree_hierarchy'
```

**解決方法**:
```bash
# libs/elder_tree_hierarchy.py を最小限実装に変更
echo "def get_elder_tree(): return None" > libs/elder_tree_hierarchy.py
```

#### パターン2: Four Sages 統合エラー
```
AttributeError: 'NoneType' object has no attribute 'send_message'
```

**解決方法**:
```bash
# Four Sages 統合を無効化
echo "ELDER_TREE_AVAILABLE = False" > libs/four_sages_integration.py
```

#### パターン3: メモリリーク
```
MemoryError: Unable to allocate array with shape and data type
```

**解決方法**:
```bash
# Elder Tree 階層通信を無効化
find workers/ -name "*.py" -exec sed -i 's/self\.elder_tree = get_elder_tree()/self.elder_tree = None/g' {} \;
```

### 復旧確認チェックリスト

#### 即座確認 (5分以内)
- [ ] システムプロセスが起動している
- [ ] 基本API (pm_worker) が応答する
- [ ] エラーログにCriticalエラーがない
- [ ] メモリ使用量が正常範囲内

#### 詳細確認 (30分以内)
- [ ] 全ワーカーが正常起動
- [ ] 基本機能テストが全て通る
- [ ] パフォーマンスが許容範囲内
- [ ] データ整合性が保たれている

#### 継続監視 (24時間)
- [ ] 安定性に問題がない
- [ ] エラー発生率が正常
- [ ] リソース使用量が安定
- [ ] 機能劣化がない

---

## 📞 エスカレーション手順

### Level 1: 自動復旧失敗 (15分経過)
**Action**: Elder Council 緊急招集
```bash
# 自動Elder Council召集
ai-elder-council-emergency "Elder Tree Recovery Failed"
```

### Level 2: 手動復旧失敗 (30分経過)
**Action**: Grand Elder maru 直接報告
```bash
# Grand Elder への緊急報告
ai-grand-elder-report "Critical System Failure - Manual Recovery Failed"
```

### Level 3: 完全復旧不可 (60分経過)
**Action**: 全システムバックアップからの復旧
```bash
# 完全バックアップ復旧
/home/aicompany/ai_co/backups/phase_d_backup_20250710_152645/full_system_restore.sh
```

---

## 🎯 復旧後対応

### 即座対応
1. インシデント報告書作成
2. 根本原因分析
3. 再発防止策立案
4. システム監視強化

### 中期対応
1. Elder Tree 設計見直し
2. 冗長化機能追加
3. 自動復旧機能強化
4. 監視アラート改善

### 長期対応
1. アーキテクチャ再設計
2. 障害回復力向上
3. 運用プロセス改善
4. 緊急時対応訓練

---

## 📋 連絡先・リソース

### 緊急連絡先
- **Claude Elder**: 常時対応可能
- **Grand Elder maru**: 重大インシデント時
- **Elder Council**: 30分以内に召集可能

### 重要リソース
- **バックアップ場所**: `/home/aicompany/ai_co/backups/phase_d_backup_20250710_152645/`
- **ログファイル**: `/var/log/ai-company/`
- **設定ファイル**: `/home/aicompany/ai_co/config/`
- **復旧スクリプト**: `/home/aicompany/ai_co/scripts/recovery/`

---

**🛡️ Grand Elder maru 品質第一原則準拠**  
**📅 最終更新**: 2025年7月10日  
**⏰ 次回見直し**: 2025年7月17日

🚨 **緊急時は迷わず実行！** 🚨