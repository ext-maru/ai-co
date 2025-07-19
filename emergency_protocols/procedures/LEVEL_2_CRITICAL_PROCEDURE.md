# 🟠 Level 2: Critical (重大) 対応手順書

**文書番号**: ERP-L2-001
**最終更新**: 2025年7月10日
**重要度**: HIGH
**対応時間**: 15分以内

---

## 初動対応チェックリスト (0-15分)

### ⏱️ 0-3分: 初期対応

- [ ] 影響サービス特定
- [ ] Four Sages機能状態確認
- [ ] Elder通知発信
- [ ] 部分バックアップ開始
- [ ] 影響ユーザー数把握

### ⏱️ 3-10分: 診断と分離

- [ ] 根本原因調査開始
- [ ] 影響サービス分離
- [ ] 代替ルート設定
- [ ] Four Sages診断実行
- [ ] 復旧計画立案

### ⏱️ 10-15分: 復旧開始

- [ ] 劣化モード移行
- [ ] 部分復旧開始
- [ ] 監視強化設定
- [ ] 進捗報告準備
- [ ] エスカレーション判断

---

## 詳細対応フロー

### Step 1: 影響範囲の特定と分離

```bash
#!/bin/bash
# critical_level_2_response.sh

echo "⚠️ CRITICAL LEVEL 2 - RESPONSE INITIATED ⚠️"
echo "Timestamp: $(date)"
echo "Operator: $USER"

# 1. 影響サービスの特定
echo "[1/5] Identifying affected services..."
ai-service-scan --critical --detailed > /tmp/affected_services.log

# 2. Four Sages状態確認
echo "[2/5] Checking Four Sages status..."
ai-four-sages-status --emergency

# 3. 影響サービスの分離
echo "[3/5] Isolating affected services..."
affected_services=$(cat /tmp/affected_services.log | grep "AFFECTED" | awk '{print $2}')
for service in $affected_services; do
    ai-service-isolate --service=$service --preserve-state
done

# 4. 部分バックアップ
echo "[4/5] Creating partial backup..."
ai-backup-critical --services="$affected_services" --async &

# 5. 劣化モード有効化
echo "[5/5] Enabling degraded mode..."
ai-system-mode --degraded --exclude="$affected_services"

echo "Critical response initiated in $SECONDS seconds"
```

### Step 2: Four Sages緊急診断

```python
# four_sages_critical_diagnosis.py

class FourSagesCriticalDiagnosis:
    async def emergency_diagnosis(self, incident_data):
        """Four Sagesによる緊急診断"""

        diagnosis_results = await asyncio.gather(
            self.knowledge_sage_analyze(incident_data),
            self.task_sage_analyze(incident_data),
            self.incident_sage_analyze(incident_data),
            self.rag_sage_analyze(incident_data)
        )

        # 統合診断結果
        return {
            "root_cause": self.identify_root_cause(diagnosis_results),
            "impact_assessment": self.assess_impact(diagnosis_results),
            "recovery_plan": self.generate_recovery_plan(diagnosis_results),
            "risk_evaluation": self.evaluate_risks(diagnosis_results)
        }

    async def knowledge_sage_analyze(self, data):
        """ナレッジ賢者による過去事例分析"""
        return {
            "similar_incidents": self.search_similar_incidents(data),
            "successful_resolutions": self.find_successful_resolutions(data),
            "lessons_learned": self.extract_lessons(data)
        }
```

### Step 3: 代替サービス起動

```yaml
# critical_failover_config.yaml

failover_mapping:
  authentication_worker:
    primary: "auth_worker_primary"
    secondary: "auth_worker_secondary"
    tertiary: "auth_worker_minimal"

  four_sages_integration:
    primary: "four_sages_full"
    secondary: "four_sages_limited"
    tertiary: "four_sages_emergency"

  task_processing:
    primary: "task_worker_cluster"
    secondary: "task_worker_single"
    tertiary: "task_queue_only"

failover_rules:
  - condition: "primary_failure"
    action: "activate_secondary"
    timeout: 30

  - condition: "secondary_failure"
    action: "activate_tertiary"
    timeout: 60

  - condition: "all_failure"
    action: "escalate_to_disaster"
    timeout: 90
```

### Step 4: 部分復旧プロセス

```python
# partial_recovery_process.py

class PartialRecovery:
    def __init__(self):
        self.recovery_stages = [
            self.verify_data_integrity,
            self.restore_critical_functions,
            self.reconnect_dependencies,
            self.validate_functionality,
            self.gradual_traffic_restore
        ]

    async def execute_partial_recovery(self, affected_services):
        """部分復旧の実行"""
        recovery_report = {
            "start_time": datetime.now(),
            "affected_services": affected_services,
            "stages": {}
        }

        for idx, stage in enumerate(self.recovery_stages):
            stage_name = stage.__name__
            print(f"\n🔄 Executing Stage {idx+1}: {stage_name}")

            try:
                result = await stage(affected_services)
                recovery_report["stages"][stage_name] = {
                    "status": "success",
                    "result": result,
                    "timestamp": datetime.now()
                }

            except Exception as e:
                recovery_report["stages"][stage_name] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now()
                }

                # 失敗時のロールバック
                if not await self.rollback_stage(idx):
                    raise CriticalRecoveryError(f"Rollback failed at stage {stage_name}")

        return recovery_report
```

### Step 5: 監視とエスカレーション

```bash
#!/bin/bash
# critical_monitoring.sh

# 継続的監視スクリプト
monitor_critical_recovery() {
    local start_time=$(date +%s)
    local timeout=900  # 15分

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        # タイムアウトチェック
        if [ $elapsed -gt $timeout ]; then
            echo "⚠️ TIMEOUT: Escalating to DISASTER level"
            ai-escalate --to-disaster --reason="Critical recovery timeout"
            break
        fi

        # 復旧状態チェック
        recovery_status=$(ai-recovery-status --json)

        if echo "$recovery_status" | jq -e '.status == "completed"' > /dev/null; then
            echo "✅ Recovery completed successfully"
            break
        fi

        # 進捗表示
        progress=$(echo "$recovery_status" | jq -r '.progress')
        echo "Recovery progress: $progress% (Elapsed: $elapsed seconds)"

        sleep 10
    done
}

# 監視開始
monitor_critical_recovery
```

---

## 📊 判断基準とエスカレーション

### エスカレーション条件

| 条件 | アクション | タイミング |
|------|-----------|-----------|
| 15分経過で未解決 | Disaster Levelへ昇格 | 自動 |
| データ損失リスク検出 | Grand Elder通知 | 即時 |
| 複数システム波及 | Elder Council招集 | 5分以内 |
| セキュリティ侵害疑い | 緊急セキュリティ対応 | 即時 |

### 復旧成功基準

- ✓ 影響サービスの80%以上復旧
- ✓ データ整合性100%維持
- ✓ パフォーマンス70%以上回復
- ✓ エラー率が通常の3倍以内
- ✓ 新規エラー発生なし（5分間）

---

## 🔧 技術詳細

### 劣化モード設定

```json
{
  "degraded_mode_config": {
    "disabled_features": [
      "advanced_analytics",
      "batch_processing",
      "non_essential_notifications"
    ],
    "resource_limits": {
      "cpu_limit": "80%",
      "memory_limit": "70%",
      "connection_limit": 1000
    },
    "priority_services": [
      "authentication",
      "core_api",
      "data_persistence"
    ]
  }
}
```

### Four Sages限定モード

```python
# four_sages_limited_mode.py

class FourSagesLimitedMode:
    """Four Sages機能制限モード"""

    def __init__(self):
        self.active_sages = {
            "knowledge": True,    # 知識参照は維持
            "task": False,       # 新規タスク生成停止
            "incident": True,    # インシデント対応維持
            "rag": False        # RAG検索停止
        }

    def get_available_sage(self, sage_type):
        """利用可能な賢者を取得"""
        if self.active_sages.get(sage_type, False):
            return self.sages[sage_type]
        else:
            return self.get_fallback_sage(sage_type)
```

---

## 📋 チェックリスト

### 対応開始時

- [ ] インシデント記録開始
- [ ] 影響範囲ドキュメント作成
- [ ] チームメンバー割り当て
- [ ] コミュニケーションチャネル確立
- [ ] 監視ダッシュボード設定

### 対応中

- [ ] 5分ごとの進捗更新
- [ ] エスカレーション判断
- [ ] 暫定対策の効果測定
- [ ] 追加リソース必要性評価
- [ ] 外部影響の継続監視

### 対応完了後

- [ ] 根本原因分析
- [ ] 再発防止策立案
- [ ] ドキュメント更新
- [ ] チーム振り返り実施
- [ ] 改善提案作成

---

**承認**: Grand Elder maru
**文書番号**: ERP-L2-001
**次回レビュー**: 2025年8月10日
