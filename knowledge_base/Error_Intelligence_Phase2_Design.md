# 🔧 エラー智能判断システム Phase 2 - 自動修正機能 設計書

## 📋 概要

Phase 2では、Phase 1で分析・分類したエラーを実際に自動修正する機能を実装します。目標は60%のエラーを自動修正することです。

## 🎯 Phase 2の目標

1. **自動修正実行率**: 60%以上
2. **修正成功率**: 80%以上（試行したものの中で）
3. **平均修正時間**: 30秒以内
4. **リトライ成功率**: 50%以上

## 🏗️ アーキテクチャ

### コンポーネント構成

```
┌─────────────────────┐
│ ErrorIntelligence   │ Phase 1
│     Manager         │ (分析・判断)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   AutoFixExecutor   │ Phase 2
│  (自動修正エンジン)  │ (新規)
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐ ┌─────────────┐
│FixStore│ │RetryManager │
│ (履歴)  │ │(リトライ管理)│
└─────────┘ └─────────────┘
```

### 主要コンポーネント

1. **AutoFixExecutor**
   - 修正戦略の実行
   - 安全性チェック
   - ロールバック機能
   - 実行結果の検証

2. **FixStrategyOptimizer**
   - 修正戦略の最適化
   - 成功率に基づく優先順位付け
   - コンテキスト考慮

3. **RetryOrchestrator**
   - 修正後の自動リトライ
   - 段階的バックオフ
   - 成功判定

4. **FixHistoryAnalyzer**
   - 修正履歴の分析
   - パターン学習
   - 成功率計算

## 📊 自動修正カテゴリと戦略

### 1. 依存関係エラー (dependency)
```python
strategies = {
    'pip_install': {
        'command': 'pip install {package}',
        'safety_check': True,
        'rollback': 'pip uninstall -y {package}'
    },
    'requirements_update': {
        'command': 'pip freeze > requirements.txt',
        'safety_check': False
    }
}
```

### 2. ファイルシステムエラー (filesystem)
```python
strategies = {
    'create_file': {
        'command': 'touch {filepath}',
        'safety_check': True,
        'pre_check': 'dirname exists'
    },
    'create_directory': {
        'command': 'mkdir -p {dirpath}',
        'safety_check': True
    },
    'fix_permissions': {
        'command': 'chmod {mode} {filepath}',
        'safety_check': True
    }
}
```

### 3. ネットワークエラー (network)
```python
strategies = {
    'retry_with_backoff': {
        'attempts': 3,
        'backoff': 'exponential',
        'max_delay': 30
    },
    'check_connectivity': {
        'command': 'ping -c 1 8.8.8.8',
        'timeout': 5
    }
}
```

### 4. RabbitMQエラー (rabbitmq)
```python
strategies = {
    'restart_service': {
        'command': 'sudo systemctl restart rabbitmq-server',
        'verify': 'sudo systemctl is-active rabbitmq-server'
    },
    'clear_queue': {
        'command': 'sudo rabbitmqctl purge_queue {queue_name}',
        'safety_check': True
    }
}
```

### 5. 権限エラー (permission)
```python
strategies = {
    'add_execute': {
        'command': 'chmod +x {filepath}',
        'verify': 'test -x {filepath}'
    },
    'change_owner': {
        'command': 'chown aicompany:aicompany {filepath}',
        'requires_sudo': True
    }
}
```

## 🔒 安全性機能

### 1. Pre-execution Checks
- ファイルのバックアップ
- システム状態の記録
- 依存関係の確認

### 2. Execution Monitoring
- タイムアウト設定
- リソース使用制限
- プロセス監視

### 3. Post-execution Validation
- 修正の検証
- 副作用のチェック
- 成功判定

### 4. Rollback Mechanism
- 自動ロールバック
- 状態復元
- エラー通知

## 📈 学習と最適化

### 1. 成功率トラッキング
```sql
CREATE TABLE fix_history (
    id INTEGER PRIMARY KEY,
    error_pattern TEXT,
    fix_strategy TEXT,
    success BOOLEAN,
    execution_time REAL,
    side_effects TEXT,
    timestamp DATETIME
);
```

### 2. 戦略の重み付け
- 成功率に基づく優先順位
- 実行時間の考慮
- 副作用の最小化

### 3. コンテキスト学習
- 環境による成功率の違い
- 時間帯による影響
- 他のプロセスとの相互作用

## 🔄 実行フロー

1. **エラー受信**
   - Phase 1から分析結果を受信
   - 修正可能性を再評価

2. **戦略選択**
   - 履歴から最適な戦略を選択
   - 複数戦略の組み合わせを検討

3. **安全性チェック**
   - 実行前の環境確認
   - バックアップ作成

4. **修正実行**
   - コマンド実行
   - タイムアウト監視
   - 出力記録

5. **検証**
   - 修正の成功判定
   - 副作用チェック

6. **リトライ判定**
   - 元のタスクを再実行するか判定
   - 追加修正が必要か評価

7. **学習**
   - 結果を記録
   - 成功率を更新

## 🎯 成功指標

### Phase 2完了時の目標
- **自動修正試行率**: 70%（修正可能と判断されたエラーの中で）
- **修正成功率**: 80%（試行した修正の中で）
- **総合自動修正率**: 56%（全エラーの中で）
- **平均修正時間**: 20秒
- **ロールバック発生率**: < 5%

### 段階的目標
1. **Week 1**: 基本的なファイルシステムエラーの修正（30%）
2. **Week 2**: 依存関係エラーの修正追加（45%）
3. **Week 3**: ネットワーク・権限エラー対応（55%）
4. **Week 4**: 最適化と目標達成（60%）

## 🚀 実装計画

### Step 1: AutoFixExecutor基盤
- 基本的な実行エンジン
- 安全性機能
- ロールバック機能

### Step 2: 各カテゴリの修正実装
- filesystem修正
- dependency修正
- permission修正

### Step 3: 高度な機能
- 複合エラーの修正
- 戦略の組み合わせ
- 並列修正

### Step 4: 学習と最適化
- 履歴分析
- 戦略最適化
- パフォーマンス改善

---

**Phase 2により、AI Companyは自己修復能力を獲得します。**
