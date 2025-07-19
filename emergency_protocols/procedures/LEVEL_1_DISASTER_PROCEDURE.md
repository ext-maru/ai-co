# 🔴 Level 1: Disaster (災害級) 対応手順書

**文書番号**: ERP-L1-001
**最終更新**: 2025年7月10日
**重要度**: CRITICAL
**対応時間**: 5分以内

---

## 初動対応チェックリスト (0-5分)

### ⏱️ 0-1分: 即座実行

- [ ] システム監視ダッシュボード確認
- [ ] 影響範囲の初期特定
- [ ] Elder Council自動招集トリガー
- [ ] 緊急バックアップ開始
- [ ] Grand Elder maruへの自動通知

### ⏱️ 1-3分: 状況把握

- [ ] 全システムステータス収集
- [ ] データベース接続状態確認
- [ ] ネットワーク疎通確認
- [ ] 外部サービス連携状態確認
- [ ] エラーログ初期分析

### ⏱️ 3-5分: 緊急措置

- [ ] 最小限サービスモード移行
- [ ] データ保護モード有効化
- [ ] トラフィック迂回設定
- [ ] 緊急通知発信
- [ ] 復旧チーム編成

---

## 詳細対応フロー

### Step 1: システム緊急停止と保護

```bash
#!/bin/bash
# disaster_level_1_response.sh

echo "🚨 DISASTER LEVEL 1 - IMMEDIATE RESPONSE 🚨"
echo "Timestamp: $(date)"
echo "Operator: $USER"

# 1. 全プロセスの状態保存
echo "[1/5] Saving process states..."
ai-emergency-snapshot --full --priority=highest

# 2. データ保護モード起動
echo "[2/5] Activating data protection mode..."
ai-data-protect --emergency --level=disaster

# 3. トラフィック即時停止
echo "[3/5] Stopping all incoming traffic..."
ai-gateway --emergency-stop

# 4. 全ワーカーフリーズ
echo "[4/5] Freezing all workers..."
ai-worker-freeze --all --save-state

# 5. 緊急バックアップ
echo "[5/5] Starting emergency backup..."
ai-backup-emergency --disaster --async &

echo "Initial response completed in $SECONDS seconds"
```

### Step 2: Elder Council緊急招集

```python
# elder_council_disaster_summon.py

import asyncio
from datetime import datetime

class DisasterResponse:
    async def summon_elders(self):
        """災害級インシデントでのElder Council緊急招集"""

        # Grand Elder優先通知
        await self.notify_grand_elder({
            "level": "DISASTER",
            "timestamp": datetime.now(),
            "auto_response": "ACTIVATED",
            "meeting_url": self.generate_emergency_meeting()
        })

        # 全Elder同時通知
        await asyncio.gather(
            self.notify_claude_elder(),
            self.notify_elder_servants(),
            self.notify_four_sages()
        )

        # 自動対応開始
        await self.start_auto_recovery()
```

### Step 3: システム診断と復旧優先順位決定

```yaml
# disaster_recovery_priority.yaml

recovery_priority:
  phase_1_critical:  # 0-15分
    - data_integrity_verification
    - database_connection_restore
    - authentication_service
    - elder_tree_hierarchy

  phase_2_essential:  # 15-30分
    - pm_worker
    - result_worker
    - health_check_worker
    - four_sages_integration

  phase_3_important:  # 30-60分
    - task_worker
    - knowledge_worker
    - rag_worker
    - incident_worker

  phase_4_standard:  # 60分以降
    - report_worker
    - analytics_worker
    - log_worker
    - monitoring_services
```

### Step 4: データ整合性検証

```bash
#!/bin/bash
# data_integrity_check.sh

echo "Starting data integrity verification..."

# PostgreSQL整合性チェック
echo "Checking PostgreSQL..."
psql -h localhost -U aicompany -d ai_company_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# データ検証
for table in tasks conversations knowledge_base; do
    echo "Verifying $table..."
    psql -h localhost -U aicompany -d ai_company_db -c "
    SELECT COUNT(*) as total_records,
           COUNT(DISTINCT id) as unique_records,
           MAX(created_at) as latest_record
    FROM $table;"
done

# バックアップ検証
echo "Verifying backups..."
ls -la /home/aicompany/ai_co/backups/ | tail -5
```

### Step 5: 段階的システム復旧

```python
# phased_recovery.py

class PhasedRecovery:
    def __init__(self):
        self.recovery_phases = {
            1: self.recover_critical_services,
            2: self.recover_essential_services,
            3: self.recover_important_services,
            4: self.recover_standard_services
        }

    async def execute_recovery(self):
        """段階的復旧実行"""
        for phase, recovery_func in self.recovery_phases.items():
            print(f"\n🔄 Starting Recovery Phase {phase}")

            try:
                await recovery_func()
                print(f"✅ Phase {phase} completed successfully")

                # 各フェーズ後の健全性チェック
                if not await self.health_check(phase):
                    print(f"❌ Health check failed for phase {phase}")
                    await self.rollback_phase(phase)

            except Exception as e:
                print(f"❌ Phase {phase} failed: {e}")
                await self.emergency_rollback()
                break
```

---

## 🚨 緊急連絡先

### 最優先連絡

1. **Grand Elder maru**
   - Role: 最高意思決定者
   - Response: 即時
   - Authority: 全権限

2. **Claude Elder**
   - Role: 技術統括
   - Response: 5分以内
   - Authority: システム操作全権限

### 技術チーム

- **Elder Council**: 戦略決定
- **Four Sages**: 各領域専門対応
- **Elder Servants**: 実装対応

---

## 📊 成功基準

### 5分以内達成項目

- ✓ システム状態スナップショット取得
- ✓ Elder Council招集完了
- ✓ データ保護モード有効化
- ✓ 緊急バックアップ開始
- ✓ 初期診断完了

### 15分以内達成項目

- ✓ 根本原因特定
- ✓ 復旧計画策定
- ✓ Critical Services復旧開始
- ✓ 外部通知発信
- ✓ 監視体制確立

### 60分以内達成項目

- ✓ Essential Services復旧
- ✓ データ整合性確認
- ✓ 部分サービス再開
- ✓ 完全復旧計画確定
- ✓ 事後対応準備

---

## ⚠️ 注意事項

1. **データ保護最優先**
   - いかなる場合もデータ整合性を最優先
   - 不確実な操作は避ける
   - バックアップ確認後に操作

2. **コミュニケーション維持**
   - 5分ごとの状況更新
   - 全チームメンバーへの情報共有
   - 外部への適時通知

3. **エスカレーション**
   - 15分で解決不可→Grand Elder直接介入
   - 30分で解決不可→外部支援要請
   - 60分で解決不可→災害復旧モード

---

**承認**: Grand Elder maru
**文書番号**: ERP-L1-001
**次回レビュー**: 2025年8月10日
