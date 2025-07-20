# Elder Flow Orchestrator メソッド不足エラー

## 概要
Elder Flow Engine (`libs/elder_system/flow/elder_flow_engine.py`) が ElderFlowOrchestrator の存在しないメソッドを呼び出しているため、システムが動作しません。

## エラー詳細
```
AttributeError: 'ElderFlowOrchestrator' object has no attribute 'execute_sage_council'
```

## 影響範囲
- Elder Flow全体の実行不可
- `elder-flow execute` コマンドの失敗
- 5フェーズ実行モデルの機能停止

## 根本原因
Elder Flowシステムの進化過程で、以下の不整合が発生：
- **Engine**: 新しい5フェーズモデル（sage_council → servants → quality → report → git）を採用
- **Orchestrator**: 古い統合モデル（execute_task メソッドのみ）のまま

## 必要な修正

### 1. ElderFlowOrchestratorクラスに以下のメソッドを追加

```python
async def execute_sage_council(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 1: 4賢者会議実行"""

async def execute_elder_servants(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 2: エルダーサーバント実行"""

async def execute_quality_gate(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 3: 品質ゲート実行"""

async def execute_council_report(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 4: 評議会報告実行"""

async def execute_git_automation(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 5: Git自動化実行"""
```

### 2. 既存コードの再利用
現在の`execute_task`メソッド内の各フェーズ処理を、新しいメソッドに分離・移行する。

## 実装計画

1. **Phase分離** (1時間)
   - 既存の`_phase_1_council`を`execute_sage_council`に
   - 既存の`_phase_3_execution`を`execute_elder_servants`に
   - 既存の`_phase_4_quality`を`execute_quality_gate`に
   - 既存の`_phase_5_reporting`を`execute_council_report`と`execute_git_automation`に

2. **インターフェース調整** (30分)
   - request/responseフォーマットの統一
   - エラーハンドリングの調整

3. **テスト実装** (1時間)
   - 各メソッドの単体テスト
   - エンドツーエンドテスト

4. **統合確認** (30分)
   - Elder Flow CLIからの実行確認
   - エラーケースの確認

## 期待される効果
- Elder Flow実行の正常化
- 5フェーズモデルの完全動作
- システム全体の安定性向上

## ラベル
- bug
- high-priority
- elder-flow
- breaking-change

## 関連ファイル
- `libs/elder_flow_orchestrator.py`
- `libs/elder_system/flow/elder_flow_engine.py`
- `scripts/elder-flow`

## 再現手順
1. `elder-flow execute "test task" --priority low`
2. Phase 1実行時にAttributeError発生

## 回避策（一時的）
現在はありません。Elder Flow自体が動作しないため、自動Elder Flow適用も機能しません。
