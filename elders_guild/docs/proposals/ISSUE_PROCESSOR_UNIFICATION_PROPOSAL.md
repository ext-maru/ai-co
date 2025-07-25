# Issue Processor統一提案

## 現状の課題
- Auto Issue Processor（基本版）とEnhanced Auto Issue Processor（拡張版）が並存
- 機能の重複とメンテナンスコストの増大
- どちらを使うべきか不明確

## 提案：Enhanced版への統一

### 1. 統一の利点
- **機能の一元化**: Enhanced版は基本版の全機能を含む
- **高度な機能**: スマートマージ、4賢者統合、詳細メトリクス
- **メンテナンス性向上**: 1つのコードベースに集約
- **将来の拡張性**: 新機能追加が容易

### 2. 移行計画

#### Phase 1: 設定の統一（1週間）
```python
# elder_scheduled_tasks.pyを更新
def auto_issue_processor():
    """10分ごとのIssue処理"""
    # 基本版から拡張版に切り替え
    from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor
    processor = EnhancedAutoIssueProcessor()
    await processor.run_enhanced(max_issues=1)  # 10分ごとなので1件ずつ
```

#### Phase 2: 非推奨化（2週間）
- `auto_issue_processor.py`に非推奨警告を追加
- ドキュメントを更新
- 利用箇所の洗い出し

#### Phase 3: 統合完了（1ヶ月）
- 基本版の削除
- Enhanced版を`auto_issue_processor.py`にリネーム
- テストとドキュメントの更新

### 3. 設定例

```yaml
# 推奨設定
issue_processor:
  # 通常実行（10分ごと）
  regular:
    max_issues: 1
    priorities: ["critical", "high", "medium", "low"]
    enable_smart_merge: true
    enable_four_sages: true
    
  # バッチ実行（1日1回）
  batch:
    max_issues: 10
    priorities: ["medium", "low"]  # 通常実行で処理されない分
    enable_analytics: true
```

### 4. リスクと対策
- **リスク**: Enhanced版の不具合が全体に影響
- **対策**: 段階的移行とロールバック計画

### 5. 期待効果
- コード削減: 約30%（重複部分の削除）
- バグ修正工数: 50%削減（1箇所の修正で済む）
- 新機能追加速度: 2倍（統一されたアーキテクチャ）

## 結論
Enhanced Auto Issue Processorへの統一により、システムの保守性と拡張性が大幅に向上します。段階的な移行により、リスクを最小化しながら統合を進めることができます。