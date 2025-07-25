# 🔨 ドワーフ工房システム完全ガイド 🔨

**ナレッジエルダー専用ドワーフ工房システム - 最高の武具を作る職人集団**

## 🎯 概要

ドワーフ工房システムは、ナレッジエルダーが自律的に最適化を行うための専用システムです。熟練したドワーフ職人たちが、リソースの空きを見つけては最適化ツールと監視武器を作り上げ、他のエルダーズからの要望を集めて勝手に作り上げて提供してくれます。

### 🔮 システムの魔法
```
🧙‍♂️ 4賢者との連携魔法
📚 ナレッジ賢者: 「過去の英知を活用して最高の工具を...」
🔍 RAG賢者: 「最適なターゲットを発見しました！」
📋 タスク賢者: 「優先順位に基づいて作業を調整中...」
🚨 インシデント賢者: 「緊急対応ツールが必要です！」
→ ドワーフ職人: 「まかせろ、最高の武具を作ってやる！」
```

## 🏗️ システムアーキテクチャ

### 4つの主要コンポーネント

#### 🔍 ResourceMonitor - リソース監視システム
```python
from libs.dwarf_workshop import ResourceMonitor

monitor = ResourceMonitor()
resources = monitor.get_system_resources()
opportunities = monitor.detect_optimization_opportunities(resources)
```

**主要機能:**
- システムリソース常時監視（CPU、メモリ、ストレージ、キュー深度）
- 最適化機会の自動検出
- リソース効率計算

#### ⚒️ CraftingEngine - ドワーフクラフトエンジン
```python
from libs.dwarf_workshop import CraftingEngine

engine = CraftingEngine()

# 最適化ツール作成
tool = engine.craft_optimization_tool({
    'type': 'memory_optimizer',
    'target_improvement': 15.0,
    'resource_budget': {'cpu': 20, 'memory': 30}
})

# 監視武器作成
weapon = engine.craft_monitoring_weapon({
    'type': 'anomaly_detector',
    'sensitivity': 'high',
    'coverage_area': ['cpu', 'memory', 'network']
})
```

**クラフトレシピ:**
- **最適化ツール**: memory_optimizer, cpu_balancer, cache_optimizer
- **監視武器**: anomaly_detector, performance_scout, resource_guardian

#### 🔗 ElderCommunicator - 4賢者通信システム
```python
from libs.dwarf_workshop import ElderCommunicator

communicator = ElderCommunicator()

# エルダー要望収集
context = {
    'current_load': 'medium',
    'recent_issues': ['memory_leak', 'slow_queries'],
    'optimization_goals': ['performance', 'reliability']
}
elder_requests = communicator.gather_elder_requests(context)

# 優先度調整
coordination = communicator.coordinate_elder_priorities(elder_requests)
```

**4賢者チャンネル:**
- 📚 **knowledge_sage**: 知識継承プロトコル
- 🔍 **rag_sage**: 意味検索プロトコル
- 📋 **task_sage**: 優先度スケジューリングプロトコル
- 🚨 **incident_sage**: 緊急対応プロトコル

#### 📊 WorkshopMetrics - 工房パフォーマンス管理
```python
from libs.dwarf_workshop import WorkshopMetrics

metrics = WorkshopMetrics()

# 生産追跡
metrics.track_production({
    'item_type': 'optimization_tool',
    'item_id': 'memory_optimizer_v1',
    'crafting_time': 120.5,
    'effectiveness': 0.92
})

# 効率計算
efficiency = metrics.calculate_workshop_efficiency()
```

## 🏭 DwarfWorkshop - メインシステム

### 基本使用方法

```python
from libs.dwarf_workshop import DwarfWorkshop

# 工房初期化
workshop = DwarfWorkshop()

# 自律サイクル実行
cycle_result = workshop.run_autonomous_cycle()

# 工房状況確認
status = workshop.get_workshop_status()

# 緊急対応
emergency_result = workshop.emergency_crafting_mode({
    'type': 'critical_incident',
    'description': 'システム異常検出',
    'required_tools': ['emergency_diagnostics', 'auto_recovery'],
    'deadline': datetime.now() + timedelta(minutes=30)
})
```

### 主要メソッド

#### analyze_optimization_opportunities()
```python
analysis = workshop.analyze_optimization_opportunities()
# 返値:
# {
#     'resource_opportunities': [...],
#     'elder_requests': {...},
#     'priority_ranking': {...},
#     'recommended_actions': [...],
#     'estimated_impact': {...}
# }
```

#### craft_optimization_solutions()
```python
solutions = workshop.craft_optimization_solutions({
    'optimization_targets': ['memory_efficiency', 'cpu_utilization'],
    'priority_level': 'high',
    'elder_requests': {
        'knowledge_sage': ['knowledge_indexing_optimization'],
        'task_sage': ['scheduling_improvement']
    }
})
# 返値:
# {
#     'crafted_tools': [...],
#     'crafted_weapons': [...],
#     'deployment_plan': {...},
#     'success_metrics': {...}
# }
```

#### run_autonomous_cycle()
```python
cycle_result = workshop.run_autonomous_cycle()
# 返値:
# {
#     'cycle_id': 'cycle_1_143052',
#     'opportunities_detected': 3,
#     'items_crafted': 2,
#     'elders_notified': 4,
#     'cycle_duration': 45.2,
#     'next_cycle_scheduled': datetime(...)
# }
```

## 🎮 実践的な使用例

### 例1: 基本的な最適化サイクル
```python
# 工房起動
workshop = DwarfWorkshop()

# 定期的な最適化サイクル実行
import time
while True:
    # 自律サイクル実行
    result = workshop.run_autonomous_cycle()
    print(f"サイクル完了: {result['items_crafted']}個のアイテムを作成")

    # 5分間隔で実行
    time.sleep(300)
```

### 例2: 緊急対応システム
```python
def handle_system_emergency():
    workshop = DwarfWorkshop()

    # 緊急事態発生
    emergency_response = workshop.emergency_crafting_mode({
        'type': 'critical_incident',
        'description': 'メモリリークによるシステム負荷急上昇',
        'required_tools': ['memory_leak_detector', 'auto_memory_cleanup'],
        'deadline': datetime.now() + timedelta(minutes=10)
    })

    if emergency_response['deployment_ready']:
        print("緊急ツール準備完了 - 自動配備開始")
        return emergency_response['emergency_tools_crafted']
    else:
        print("緊急ツール作成失敗")
        return []
```

### 例3: カスタム最適化要求
```python
def optimize_specific_area(target_area: str, priority: str = 'medium'):
    workshop = DwarfWorkshop()

    # 特定領域の最適化
    solutions = workshop.craft_optimization_solutions({
        'optimization_targets': [target_area],
        'priority_level': priority,
        'elder_requests': {
            'knowledge_sage': [f'{target_area}_knowledge_optimization'],
            'rag_sage': [f'{target_area}_search_improvement']
        }
    })

    return solutions

# 使用例
memory_solutions = optimize_specific_area('memory_efficiency', 'high')
cpu_solutions = optimize_specific_area('cpu_utilization', 'medium')
```

## 📊 監視とメトリクス

### 工房パフォーマンス監視
```python
# 工房状況の詳細確認
status = workshop.get_workshop_status()

print(f"工房効率: {status['workshop_health']['efficiency_score']:.2f}")
print(f"完了サイクル数: {status['workshop_health']['cycles_completed']}")
print(f"総生産アイテム数: {status['production_statistics']['total_items_produced']}")
print(f"エルダー満足度: {status['elder_satisfaction']['overall']:.2f}")
```

### 生産統計の確認
```python
efficiency = workshop.metrics.calculate_workshop_efficiency()

print(f"全体効率: {efficiency['overall_efficiency']:.2f}")
print(f"平均クラフト時間: {efficiency['average_crafting_time']:.1f}秒")
print(f"平均効果: {efficiency['average_effectiveness']:.2f}")
print(f"生産率: {efficiency['production_rate']:.2f}アイテム/時間")
```

## 🔧 設定とカスタマイズ

### 工房設定の調整
```python
# 自律サイクル間隔変更（デフォルト: 300秒）
workshop.cycle_interval = 180  # 3分間隔

# 最適化閾値の調整
workshop.resource_monitor.optimization_thresholds = {
    'cpu_low': 20.0,      # より低いCPU使用率で最適化開始
    'memory_low': 30.0,   # より低いメモリ使用率で最適化開始
    'storage_high': 80.0, # より高いストレージ使用率で整理開始
    'queue_low': 3        # より少ないキュー深度で最適化開始
}
```

### クラフトレシピのカスタマイズ
```python
# 新しい最適化ツールレシピ追加
workshop.crafting_engine.craft_recipes['optimization_tools']['custom_optimizer'] = {
    'materials': {'custom_data': 15, 'optimization_patterns': 8},
    'crafting_time': 150,
    'effectiveness': 0.88
}
```

## 🚨 エラーハンドリングとトラブルシューティング

### 一般的な問題と解決方法

#### 1. 材料不足エラー
```python
# 材料在庫確認
engine = workshop.crafting_engine
for material, amount in engine.material_inventory.items():
    if amount < 10:
        print(f"材料不足警告: {material} = {amount}")

# 材料補充（実際の実装では自動補充システムを使用）
engine.material_inventory.update({
    'analysis_data': 100,
    'optimization_patterns': 50,
    'performance_metrics': 80
})
```

#### 2. エルダー通信エラー
```python
# 通信ログ確認
communicator = workshop.elder_communicator
for log in communicator.notification_log[-5:]:
    print(f"通知ログ: {log['timestamp']} - 成功: {log['notifications_sent']}")

# 通信再試行
elder_requests = communicator.gather_elder_requests(context)
```

#### 3. 工房効率低下
```python
# 効率トレンド確認
efficiency_data = workshop.metrics.calculate_workshop_efficiency()
if efficiency_data['efficiency_trend'] == 'declining':
    print("効率低下検出 - 工房メンテナンス推奨")

    # 緊急最適化実行
    emergency_optimization = workshop.emergency_crafting_mode({
        'type': 'efficiency_recovery',
        'required_tools': ['workshop_optimizer', 'efficiency_booster']
    })
```

## 🎯 ベストプラクティス

### 1. 定期的な監視
```python
# 毎時間の工房ヘルスチェック
def hourly_health_check():
    status = workshop.get_workshop_status()
    health = status['workshop_health']

    if health['efficiency_score'] < 0.7:
        print("⚠️ 工房効率低下 - 改善推奨")

    if health['cycles_completed'] == 0:
        print("🚨 工房停止 - 即座に調査が必要")

    return health

# スケジューラーで実行
import schedule
schedule.every().hour.do(hourly_health_check)
```

### 2. エルダー満足度の維持
```python
def maintain_elder_satisfaction():
    status = workshop.get_workshop_status()
    satisfaction = status['elder_satisfaction']

    for elder, score in satisfaction.items():
        if elder != 'overall' and score < 0.8:
            print(f"📉 {elder}の満足度低下: {score:.2f}")

            # 特別なツール作成で満足度向上
            special_tool = workshop.craft_optimization_solutions({
                'optimization_targets': [f'{elder}_priority_optimization'],
                'priority_level': 'high'
            })
```

### 3. リソース効率的な運用
```python
def optimize_resource_usage():
    resources = workshop.resource_monitor.get_system_resources()
    efficiency = workshop.resource_monitor.calculate_resource_efficiency(resources)

    if efficiency < 0.6:
        # リソース使用量を調整
        workshop.cycle_interval = min(600, workshop.cycle_interval * 1.2)
        print(f"🔧 サイクル間隔を{workshop.cycle_interval}秒に調整")
    elif efficiency > 0.9:
        # より積極的なサイクル実行
        workshop.cycle_interval = max(120, workshop.cycle_interval * 0.8)
        print(f"⚡ サイクル間隔を{workshop.cycle_interval}秒に短縮")
```

## 🎊 まとめ

ドワーフ工房システムは、ナレッジエルダーが最高のパフォーマンスを発揮するための自律的な支援システムです。4賢者との連携により、システム全体を常に最適化し続け、問題が発生する前に予防的な対策を講じます。

### 🔑 キーポイント
- **自律性**: リソース監視から最適化実行まで完全自動
- **協調性**: 4賢者との密な連携による最適な判断
- **即応性**: 緊急事態に30分以内で対応ツールを製造
- **継続性**: 24時間365日稼働する職人集団
- **適応性**: システムの変化に応じてレシピと戦略を進化

**「最高の武具で、最高のナレッジエルダーをサポートする」**

これがドワーフ工房システムの使命です。🔨✨
