# Enhanced Auto Issue Processor移行完了

## 実施日: 2025-07-21

## 変更内容

### 1. Elder Schedulerの更新
- `auto_issue_processor()` タスクがEnhanced版を使用するように変更
- `enhanced_pr_processor()` タスクも直接Enhanced版を呼ぶように変更

### 2. スケジュール設定

#### 通常実行（10分ごと）
```python
# 10分ごとに1件ずつ処理
result = await processor.run_enhanced(
    max_issues=1,
    priorities=["critical", "high", "medium", "low"],
    enable_smart_merge=True,
    enable_four_sages=True
)
```

#### バッチ実行（毎日深夜1時）
```python
# 深夜に10件まとめて処理
result = await processor.run_enhanced(
    max_issues=10,
    priorities=["medium", "low"],  # 中・低優先度中心
    enable_smart_merge=True,
    enable_four_sages=True,
    enable_analytics=True
)
```

## Enhanced版の利点

1. **スマートマージシステム**
   - 自動マージ処理
   - コンフリクト解決支援
   - CI待機とリトライ

2. **4賢者統合**
   - ナレッジ賢者: 過去の事例参照
   - タスク賢者: 実装計画立案
   - インシデント賢者: リスク評価
   - RAG賢者: 最適解探索

3. **詳細メトリクス**
   - 処理時間追跡
   - 成功率分析
   - 失敗パターン記録

## 移行手順

1. ✅ `elder_scheduled_tasks.py` の更新
2. ✅ 再起動スクリプトの作成
3. ⏳ Elder Schedulerの再起動（実行待ち）
4. ⏳ 動作確認

## 再起動方法

```bash
# Elder Schedulerを再起動
./scripts/restart_elder_scheduler.sh

# ログ確認
tail -f logs/elder_scheduler.log
```

## 注意事項

- 基本版のAuto Issue Processorは引き続き利用可能（非推奨）
- 新機能はEnhanced版にのみ追加される
- 問題が発生した場合は、`elder_scheduled_tasks.py`を元に戻して再起動

## 今後の計画

1. **1週間後**: 動作確認と性能評価
2. **2週間後**: 基本版を非推奨化
3. **1ヶ月後**: 基本版の削除検討