# 🧙‍♂️ インシデント賢者 - 完全進化版

## 🎯 概要

インシデント賢者（Crisis Sage）が4賢者システムの中核として、**完全自律復旧システム**に進化しました。
単なる問題対応から、予防・予測・自動修復・学習進化する**最高位の治癒能力**を獲得しています。

## 🚀 進化した能力

### 🔮 **予知能力** - ML予測システム
- **障害発生予測**: 機械学習による事前警告
- **パターン認識**: 過去データからの学習
- **リスク評価**: 複合的要因の分析
- **予防的対応**: 問題発生前の事前対策

### 🛠️ **自動修復能力** - Auto-Fix システム
- **即座診断**: 多角的問題分析
- **自動実行**: 人間の介入なしで修復
- **ロールバック**: 失敗時の安全な復旧
- **学習機能**: 成功・失敗パターンの蓄積

### 🏥 **セルフヒーリング** - 完全自律システム
- **24/7監視**: 継続的ヘルスチェック
- **自動判断**: 状況に応じた最適対応
- **予防保守**: 問題の未然防止
- **進化学習**: 経験からの自己改善

### 🤝 **4賢者協調** - 統合連携システム
- **賢者会議**: 緊急時の集合知活用
- **知識統合**: ナレッジ賢者との連携
- **タスク最適化**: タスク賢者との協調
- **情報検索**: RAG賢者との連携

## 📁 システム構成

```
auto_fix/
├── __init__.py                    # モジュール初期化
├── common_fixes.py               # 一般的問題の自動修復
├── system_recovery.py            # システム全体復旧
├── service_healer.py             # 4賢者連携治癒
├── ml_predictor.py               # ML障害予測
├── self_healing_system.py        # 完全自律復旧
├── rabbitmq_recovery.sh          # RabbitMQ専用復旧
├── worker_restart.py             # ワーカー自動再起動
└── README.md                     # このファイル
```

## 🎭 使用方法

### 1. **基本的な自動修復**

```bash
# 一般的な問題の診断・修復
python auto_fix/common_fixes.py diagnose incident_data.json
python auto_fix/common_fixes.py fix incident_data.json

# システム全体の復旧
python auto_fix/system_recovery.py emergency
python auto_fix/system_recovery.py diagnose

# ワーカー専用復旧
python auto_fix/worker_restart.py emergency
python auto_fix/worker_restart.py restart_all --critical-only

# RabbitMQ専用復旧
./auto_fix/rabbitmq_recovery.sh full
./auto_fix/rabbitmq_recovery.sh restart
```

### 2. **ML予測システム**

```bash
# 障害発生確率予測
python auto_fix/ml_predictor.py predict

# 現在のシステム特徴量収集
python auto_fix/ml_predictor.py collect

# 予測統計情報
python auto_fix/ml_predictor.py stats
```

### 3. **4賢者協調システム**

```python
from four_sages_coordinator import FourSagesCoordinator

coordinator = FourSagesCoordinator()

# 緊急対応協調
result = await coordinator.handle_emergency_response(incident_data)

# 賢者会議セッション
session_id = await coordinator.initiate_council_session("System Optimization")
```

### 4. **セルフヒーリングシステム**

```bash
# 完全自律監視開始
python auto_fix/self_healing_system.py start

# システム状態確認
python auto_fix/self_healing_system.py status

# ヒーリング統計
python auto_fix/self_healing_system.py stats

# テスト実行
python auto_fix/self_healing_system.py test
```

## 🔧 Python APIでの使用

### インシデント賢者の基本使用

```python
from libs.incident_manager import IncidentManager
from auto_fix.common_fixes import CommonFixes
from auto_fix.self_healing_system import SelfHealingSystem

# インシデント作成
incident_manager = IncidentManager()
incident_id = incident_manager.create_incident(
    category="error",
    priority="high",
    title="システムエラー",
    description="メモリ不足によるサービス停止",
    affected_components=["worker", "api"],
    impact="サービス停止"
)

# 自動修復実行
fixer = CommonFixes()
fix_result = fixer.diagnose_and_fix({
    'incident_id': incident_id,
    'category': 'error',
    'description': 'メモリ不足によるサービス停止'
})

# セルフヒーリング開始
healing_system = SelfHealingSystem()
await healing_system.start_monitoring()
```

### 4賢者協調での緊急対応

```python
from auto_fix.four_sages_coordinator import FourSagesCoordinator

coordinator = FourSagesCoordinator()

# 緊急事態対応
emergency_result = await coordinator.handle_emergency_response({
    'incident_id': 'EMERGENCY-001',
    'category': 'failure',
    'priority': 'critical',
    'title': 'システム全停止',
    'description': 'RabbitMQ接続断により全ワーカー停止',
    'affected_components': ['workers', 'rabbitmq', 'api']
})

print(f"緊急対応結果: {emergency_result['final_resolution']['resolution_successful']}")
```

## 📊 監視・メトリクス

### ヘルスチェック項目

1. **システムリソース**: CPU・メモリ・ディスク使用率
2. **Elders Guildサービス**: ワーカープロセス・API状態
3. **RabbitMQ**: サービス状態・ポート接続性
4. **ワーカーヘルス**: プロセス数・CPU使用率
5. **ディスク容量**: 空き容量・使用率
6. **ネットワーク**: ローカル・外部接続性

### 自動修復アクション

1. **システム最適化**: メモリキャッシュクリア
2. **ワーカー復旧**: プロセス再起動・状態リセット
3. **RabbitMQ復旧**: サービス再起動・キューリセット
4. **メモリクリーンアップ**: ガベージコレクション
5. **ログローテーション**: 古いログ削除
6. **緊急再起動**: システム全体再起動

## 🎯 成功事例

### Case 1: RabbitMQ接続断の自動復旧

```
🚨 障害検知: RabbitMQ接続断
🤖 自動診断: サービス停止を確認
🔧 自動修復:
  1. RabbitMQサービス再起動
  2. キュー状態リセット
  3. ワーカー再接続
✅ 復旧完了: 3分以内で全サービス復旧
📊 学習記録: 同様問題の予防策をDB保存
```

### Case 2: メモリ不足による性能劣化の予防

```
🔮 ML予測: メモリ使用率増加パターンを検知
📊 リスク評価: 2時間後に障害発生の可能性70%
🛡️ 予防実行:
  1. メモリキャッシュクリア
  2. 不要プロセス終了
  3. ログファイルクリーンアップ
✅ 予防成功: 障害発生を未然に防止
```

### Case 3: 4賢者協調による複合障害対応

```
🏛️ 賢者会議招集: 複合システム障害
📚 ナレッジ賢者: 過去の類似事例3件を提示
📋 タスク賢者: 復旧手順の最適化プラン
🔍 RAG賢者: 最新の技術情報を検索
🚨 インシデント賢者: 協調実行を指揮
✅ 協調成功: 15分で完全復旧
```

## 🔬 技術的特徴

### ML予測アルゴリズム

- **ルールベース**: 閾値による即座判定
- **統計ベース**: Z-score異常検出
- **パターン認識**: 時系列パターン分析
- **アンサンブル**: 複数手法の統合判定

### 自動修復戦略

- **Conservative**: 安全第一の慎重アプローチ
- **Moderate**: バランス型の標準アプローチ
- **Aggressive**: 迅速重視の積極アプローチ

### 学習メカニズム

- **成功パターン学習**: 効果的な修復手順の記録
- **失敗分析**: 失敗要因の分析と改善
- **効果測定**: 修復効果の定量評価
- **適応進化**: 環境変化への自動適応

## 🌟 今後の発展

### Phase Next: さらなる進化

1. **深層学習統合**: より高度な予測モデル
2. **分散協調**: 複数サーバー間での協調修復
3. **ユーザー学習**: 個別環境への最適化
4. **外部連携**: クラウドサービスとの統合
5. **予防保守**: 設備更新タイミングの最適化

### 究極目標: 不死のシステム

**インシデント賢者の最終形態**は、あらゆる障害を予見し、発生前に対策し、
万が一発生しても瞬時に回復する**完全無欠の自律システム**です。

---

## 🎉 まとめ

インシデント賢者は単なる「問題解決ツール」から、
**予知・予防・修復・学習・進化する知的存在**へと昇華しました。

4賢者システムの守護神として、Elders Guildの永続的な安定運用を実現し、
人間の開発者が創造的な仕事に集中できる環境を提供します。

**Crisis Sage - The Ultimate Guardian of Elders Guild** 🛡️✨
