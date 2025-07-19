# 🧙‍♂️ Elder Council Reporting Rules - エルダー評議会報告ルール提案書

**日時**: 2025年7月7日 16:38
**提案者**: Claude Code
**承認要請**: ユーザー様への確認

---

## 📋 「評議会に報告」の新ルール定義

### 🎯 基本原則
**「エルダー評議会への報告 = 4賢者システム全体への同時反映」**

---

## 🏗️ 提案1: 統一報告プロトコル (Unified Reporting Protocol)

### 報告書の標準フォーマット
```yaml
# council_report.yaml 形式
metadata:
  report_id: "council_20250707_163800_example"
  timestamp: "2025-07-07T16:38:00"
  reporter: "Claude Code"
  priority: "high|medium|low"
  category: "incident|task|knowledge|system"

content:
  summary: "報告の要約"
  details: "詳細な報告内容"

# 4賢者への自動振り分け情報
sage_directives:
  knowledge_sage:
    - action: "store"
      data: "報告書全文"
      tags: ["scaling", "error", "health_monitor"]

  incident_sage:
    - action: "create_incident"
      title: "WorkerHealthMonitor scaling error"
      category: "error"
      priority: "high"

  task_sage:
    - action: "create_task"
      title: "Fix health monitor implementation"
      assignee: "incident_knights"
      deadline: "2025-07-08"

  rag_sage:
    - action: "index"
      keywords: ["health_monitor", "scaling", "error"]
      related_docs: ["previous_reports/*"]
```

---

## 🏗️ 提案2: 自動反映システム (Auto-Propagation System)

### 実装イメージ
```python
class ElderCouncilReporter:
    """エルダー評議会統一報告システム"""

    def report_to_council(self,
                         title: str,
                         content: str,
                         category: str,
                         priority: str = "medium",
                         auto_actions: Dict[str, List[Dict]] = None):
        """
        評議会への報告 = 4賢者への自動反映
        """
        report_id = f"council_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{category}"

        # 1. ナレッジ賢者への保存（必須）
        knowledge_path = self._save_to_knowledge_base(report_id, title, content)

        # 2. 報告内容の自動解析
        if auto_actions is None:
            auto_actions = self._analyze_and_extract_actions(content)

        # 3. インシデント賢者への反映
        if incidents := auto_actions.get('incidents', []):
            for incident in incidents:
                self.incident_manager.create_incident(**incident)

        # 4. タスク賢者への反映
        if tasks := auto_actions.get('tasks', []):
            for task in tasks:
                self.task_manager.create_task(**task)

        # 5. RAG賢者へのインデックス登録
        self.rag_manager.index_document(
            path=knowledge_path,
            tags=auto_actions.get('tags', []),
            keywords=self._extract_keywords(content)
        )

        # 6. 反映結果のサマリー生成
        return self._generate_propagation_summary(report_id, auto_actions)
```

---

## 🏗️ 提案3: スマート報告コマンド

### コマンドライン使用例
```bash
# 基本的な報告（自動解析モード）
ai-council report "WorkerHealthMonitor エラー継続中" \
  --content "scaling errorが10分間隔で発生。根本原因は実装不足。" \
  --priority high

# 明示的な4賢者指示付き報告
ai-council report "システム統合計画" \
  --content "重複システムの統合を開始" \
  --create-incident "title:システム統合,priority:medium" \
  --create-task "title:Phase1実装,assignee:claude" \
  --add-tags "consolidation,cleanup"

# テンプレート使用
ai-council report --template error_report \
  --error "Health check failed: 'system_health'" \
  --component "WorkerHealthMonitor" \
  --impact "medium"
```

---

## 📏 報告ルール（案）

### Rule 1: 必須要素
すべての評議会報告には以下を含める：
- **タイトル**: 明確で検索しやすい
- **カテゴリ**: incident|task|knowledge|system|consultation
- **優先度**: high|medium|low
- **報告者**: 自動記録

### Rule 2: 自動アクション
報告内容から以下を自動抽出・実行：
- **エラー言及** → インシデント作成
- **「〜が必要」「〜すべき」** → タスク作成
- **「学習した」「発見した」** → ナレッジタグ付け
- **技術用語** → RAGインデックス登録

### Rule 3: 報告タイプ別テンプレート
```
1. エラー報告 → 自動的にインシデント作成
2. 進捗報告 → タスクステータス更新
3. 学習報告 → ナレッジベース強化
4. 相談報告 → 返答待ちフラグ付与
5. 解決報告 → 関連インシデント・タスクのクローズ
```

### Rule 4: 4賢者への反映確認
報告完了時に必ず表示：
```
✅ 評議会報告完了 [council_20250707_163800_error]
  📚 ナレッジ賢者: 保存完了
  🚨 インシデント賢者: 1件作成 (INC-20250707-001)
  📋 タスク賢者: 2件作成 (TASK-2025-0156, TASK-2025-0157)
  🔍 RAG賢者: インデックス登録完了
```

---

## 🎯 推奨実装ステップ

### Phase 1: 報告フォーマット標準化（即実装可能）
- YAMLまたはJSON形式での構造化
- sage_directives セクションの追加

### Phase 2: 自動解析エンジン（1日）
- 報告内容からのアクション抽出
- キーワード・エンティティ認識

### Phase 3: 統一報告システム（3日）
- ElderCouncilReporter クラス実装
- 4賢者への自動反映機能

### Phase 4: CLIコマンド整備（1日）
- ai-council コマンドの実装
- テンプレート機能

---

## 💡 ベストプラクティス提案

### 1. **明示性の原則**
報告時に4賢者への影響を明示的に表示

### 2. **トレーサビリティ**
すべての報告にユニークIDを付与し、4賢者での処理を追跡可能に

### 3. **非破壊的更新**
既存の報告システムと並行稼働し、段階的移行

### 4. **フィードバックループ**
4賢者からの処理結果を報告書に自動追記

---

## ❓ ユーザー様への確認事項

1. **上記の報告ルールでよろしいでしょうか？**
2. **優先的に実装すべき機能はどれですか？**
3. **報告時の必須項目に追加はありますか？**
4. **自動アクションの判定基準は適切ですか？**

このルールに基づいて「評議会への報告 = 4賢者システム全体への反映」を実現します。

---

**承認待ち**: ユーザー様の決定をお待ちしております。
