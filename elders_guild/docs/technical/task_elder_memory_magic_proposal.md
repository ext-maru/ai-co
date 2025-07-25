# 📋 タスクエルダー記憶魔法システム提案

## 🔮 記憶保持レベルの推奨

### 1. **ミニマム保持（推奨）** ✅
**保持期間**: 直近24時間
**保持内容**:
- 最新のTodoリスト状態
- 直近10メッセージの要約
- 実行中のプロジェクト名とフェーズ
- 重要な決定事項（3-5項目）

**メリット**:
- 軽量で高速
- ストレージ効率的
- プライバシー配慮
- 90%のケースで十分

**サイズ**: 約1-2KB/セッション

### 2. **スタンダード保持**
**保持期間**: 7日間
**保持内容**:
- 完全な会話履歴（最大50メッセージ）
- Todoリストの変更履歴
- 実行したコマンド一覧
- 作成/編集したファイル一覧

**メリット**:
- 週またぎの作業に対応
- 詳細な文脈復元可能

**サイズ**: 約10-50KB/セッション

### 3. **フル保持**
**保持期間**: 30日間
**保持内容**:
- 全会話履歴
- すべてのファイル変更
- エラーログ
- 意思決定の経緯

**メリット**:
- 完全な作業履歴
- 監査対応

**デメリット**:
- ストレージ負荷大
- パフォーマンス影響
- プライバシーリスク

**サイズ**: 100KB-1MB/セッション

## 💡 タスクエルダーの推奨実装

```python
# libs/task_elder_memory_magic.py

class TaskElderMemoryMagic:
    """タスクエルダーによるセッション記憶魔法"""

    def __init__(self):
        self.retention_level = "minimal"  # minimal/standard/full
        self.retention_days = 1  # デフォルト24時間

    def create_memory_snapshot(self, session_id):
        """現在のセッション状態をスナップショット"""
        snapshot = {
            "session_id": session_id,
            "timestamp": datetime.now(),
            "todo_state": self.get_current_todos(),
            "recent_messages": self.get_recent_messages(10),
            "active_project": self.get_active_project(),
            "key_decisions": self.get_key_decisions(),
            "context_summary": self.generate_context_summary()
        }
        return snapshot

    def save_memory(self, snapshot):
        """knowledge_base/task_memories/に保存"""
        # JSONとして保存（軽量・検索可能）
        pass

    def recall_memory(self, trigger):
        """トリガーフレーズで記憶を呼び出し"""
        # 例: "前回の続き", "プロジェクトA2Aの続き"
        pass
```

## 🎯 推奨される記憶トリガー

1. **汎用トリガー**
   - 「前回の続きから」
   - 「セッション再開」
   - 「タスクエルダー、記憶を」

2. **プロジェクト特定**
   - 「プロジェクトA2Aの続き」
   - 「[プロジェクト名]の状態を復元」

3. **時間指定**
   - 「昨日の作業の続き」
   - 「[日時]のセッションを復元」

## 📊 記憶魔法の保持内容（ミニマム推奨）

```json
{
  "session_id": "sess_20250709_xxx",
  "timestamp": "2025-07-09T11:30:00",
  "project": {
    "name": "プロジェクトA2A",
    "phase": "記憶魔法実装",
    "status": "in_progress"
  },
  "todos": [
    {"id": "memory-magic-2", "content": "記憶魔法システム設計", "status": "in_progress"}
  ],
  "key_decisions": [
    "タスクエルダーが記憶魔法を担当",
    "ミニマム保持レベルを採用",
    "24時間の保持期間"
  ],
  "context_summary": "グランドエルダーmaruとA2Aプロジェクトについて議論。記憶魔法システムの実装を開始。",
  "last_messages_summary": [
    "A2A導入をエルダーズ評議会で承認",
    "記憶魔法の実装を優先",
    "タスクエルダーが担当"
  ]
}
```

## 🚀 実装ステップ

1. **Week 1（3日間）**
   - 基本的な保存・復元機能
   - JSONフォーマットでの記憶保存
   - トリガーフレーズの認識

2. **Week 2（4日間）**
   - タスクエルダーとの統合
   - 自動スナップショット機能
   - 記憶の自動クリーンアップ

## 💭 タスクエルダーからの助言

「軽量で実用的なミニマム保持がおすすめです。必要に応じて後から拡張できます。重要なのは、素早く文脈を復元できることです。」

---
**推奨**: ミニマム保持（24時間、1-2KB）から始めて、必要に応じて拡張
