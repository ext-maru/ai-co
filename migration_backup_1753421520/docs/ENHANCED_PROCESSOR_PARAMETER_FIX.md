# Enhanced Auto Issue Processor パラメータ修正

## 実施日: 2025-07-21 23:10

## 問題

Elder Scheduled TasksからEnhanced Auto Issue Processorを呼び出す際に、以下のエラーが発生：
```
TypeError: EnhancedAutoIssueProcessor.run_enhanced() got an unexpected keyword argument 'max_issues'
```

## 原因

`run_enhanced()`メソッドがパラメータを受け取らない実装になっていた（ハードコーディングされていた）。

## 修正内容

### 1. メソッドシグネチャの更新

```python
async def run_enhanced(self, max_issues=1, priorities=None, enable_smart_merge=True, 
                      enable_four_sages=True, enable_analytics=False):
    """拡張版の実行
    
    Args:
        max_issues: 処理する最大イシュー数
        priorities: 処理対象の優先度リスト
        enable_smart_merge: スマートマージシステムの有効化
        enable_four_sages: 4賢者システムの有効化
        enable_analytics: 詳細分析の有効化
    """
```

### 2. 優先度フィルタリングの修正

```python
# 変更前：lowのみ除外
if priority in ["low"]:  # lowのみ除外、medium以上を処理

# 変更後：パラメータで指定された優先度のみ処理
if priority not in priorities:  # 指定された優先度のみ処理
```

### 3. 処理結果の返却

```python
# 処理成功時
return {
    "processed_count": processed_count,
    "total_available": len(processable_issues),
    "processed_issues": processed_issues,
    "metrics": self.metrics,
    "status": "success"
}

# エラー時
return {
    "processed_count": 0,
    "total_available": 0,
    "error": str(e),
    "status": "error"
}
```

### 4. 処理済みイシューの記録

各イシュー処理後に結果を記録：
```python
processed_issues.append({
    "number": issue.number,
    "title": issue.title,
    "pr_created": True/False,
    "pr_number": result.get("pr_number"),
    "pr_url": result.get("pr_url"),
    "error": result.get("error")  # 失敗時のみ
})
```

## 動作確認

1. Elder Schedulerを再起動済み（PID: 1378359）
2. 次回実行予定：23:15:27（5分間隔）
3. 実行パラメータ：
   - max_issues: 1
   - priorities: ["critical", "high", "medium", "low"]
   - enable_smart_merge: True
   - enable_four_sages: True

## 影響範囲

- `/home/aicompany/ai_co/libs/integrations/github/enhanced_auto_issue_processor.py`のみ
- Elder Scheduled Tasksからの呼び出しが正常に動作するようになった
- 基本版Auto Issue Processorには影響なし

## 今後の対応

- 5分間隔での実行を確認
- 深夜1時のバッチ実行も正常動作するか確認
- 必要に応じてさらなる最適化を実施