# 📋 タスクエルダー完全操作ガイド

## 🏛️ Elders Guild タスクエルダーシステム概要

タスクエルダーは、Elders Guildの**タスク賢者**と**エルダーサーベント**が連携する自律タスク管理システムです。

### 🧙‍♂️ システム構成

#### 📋 **タスク賢者** (Task Oracle)
- **場所**: `libs/claude_task_tracker.py`
- **役割**: プロジェクト進捗管理、最適な実行順序の導出
- **機能**: 計画立案、進捗追跡、優先順位判断

#### 🤖 **エルダーサーベント部隊**
- **⚔️ 騎士団**: 緊急対応・品質保証
- **🔨 ドワーフ工房**: 開発・製作
- **🧙‍♂️ ウィザーズ**: 分析・研究  
- **🧝‍♂️ エルフの森**: 監視・メンテナンス

---

## 🚀 タスクエルダーへの指示方法

### 1. **ダッシュボード経由**

#### 🌐 Webダッシュボード (`http://100.76.169.124:5555`)

**📋 タスクエルダーに依頼ボタン**
1. ダッシュボードにアクセス
2. 「🔄 協調セッション」タブを選択
3. 「📋 タスクエルダーに依頼する」ボタンをクリック
4. タスクタイプを選択:
   - `coverage_improvement` - カバレッジ向上
   - `testing_enhancement` - テスト強化
   - `optimization` - 最適化
   - `code_review` - コードレビュー
5. 対象ライブラリを指定（カンマ区切り）
   - 例: `libs/performance_optimizer.py, libs/test_framework.py`

**🧾 クロードエルダーチャット**
1. 右下のチャットアイコンをクリック
2. メッセージを入力:
   ```
   タスクエルダーにカバレッジ向上を依頼
   ```
   ```
   libs/claude_task_tracker.pyのテストを追加して
   ```
   ```
   最適化タスクを開始してください
   ```

### 2. **コマンドライン経由**

#### 🔧 専用コマンド

```bash
# タスクエルダー協調システム
ai-task-elder-delegate <libraries>     # 大規模処理を一括依頼
ai-elf-optimize <task_batch>           # エルフ達による最適化
ai-task-status <batch_id>              # バッチ処理の進捗確認
ai-elder-council-record               # 評議会決定事項の記録

# 基本的な使用例
ai-task-elder-delegate libs/*.py
ai-task-status coverage_boost_20250707_232321
```

#### 📱 Elder Chat API

```bash
# Claude Elder Chat API使用
python3 libs/claude_elder_chat_api.py --message "カバレッジを向上させて"

# 対話モード
python3 libs/claude_elder_chat_api.py

# WebSocketサーバー起動
python3 libs/claude_elder_chat_api.py --mode websocket
```

### 3. **プログラム統合**

#### 🐍 Python統合

```python
from libs.claude_elder_chat_api import ClaudeElderChatAPI
import asyncio

async def main():
    chat_api = ClaudeElderChatAPI()
    
    # タスク委任
    response = await chat_api.process_chat_message(
        "タスクエルダーにcoverage_improvementタスクを依頼"
    )
    print(response['response'])

# 実行
asyncio.run(main())
```

---

## 🎯 具体的な指示例

### 📊 **カバレッジ向上**

**ダッシュボード:**
```
タスクタイプ: coverage_improvement
ライブラリ: libs/performance_optimizer.py, libs/async_worker.py
```

**チャット:**
```
タスクエルダーにカバレッジ向上を依頼
対象: libs/performance_optimizer.py
目標: 95%カバレッジ達成
```

**コマンド:**
```bash
ai-task-elder-delegate libs/performance_optimizer.py
```

### 🧪 **テスト強化**

**チャット:**
```
testing_enhancementタスクを開始
対象: libs/claude_task_tracker.py
新しいエッジケースのテストを追加
```

**プログラム:**
```python
response = await chat_api.process_chat_message(
    "task testing_enhancement libs/claude_task_tracker.py"
)
```

### ⚡ **最適化作業**

**ダッシュボード:**
```
タスクタイプ: optimization
ライブラリ: libs/async_worker_optimization.py, workers/enhanced_task_worker.py
```

**チャット:**
```
optimizationタスクを実行
パフォーマンス改善とメモリ使用量最適化
```

### 🔍 **コードレビュー**

**チャット:**
```
code_reviewタスクを依頼
対象: libs/新しく作成されたモジュール
品質チェックとリファクタリング提案
```

---

## 📈 進捗確認とモニタリング

### 🔍 **タスク進捗確認**

#### ダッシュボード
1. 「🔄 協調セッション」タブで進行中タスク確認
2. 「📋 ログ監視」タブでリアルタイム進捗
3. タスクをクリックして詳細表示

#### チャット
```
タスクの進捗状況を教えて
バッチID: elder_task_20250708_123456
```

#### コマンド
```bash
ai-task-status elder_task_20250708_123456
ai-elder status
```

### 📊 **システム状態監視**

**システム概要確認:**
```
システムの状態を確認
CPU・メモリ使用率は？
```

**エルダーシステム状態:**
```
エルダー評議会の状況は？
4賢者システムの動作状況
```

**サーベント部隊状況:**
```
サーベントの状況を教えて
騎士団・ドワーフ工房の稼働状態
```

---

## 🤖 エルダーサーベント個別指示

### ⚔️ **騎士団への指示**

**緊急対応依頼:**
```
deploy knight
緊急バグ修正とテスト強化を依頼
```

**品質保証:**
```
騎士団に品質チェックを依頼
コードレビューと脆弱性チェック
```

### 🔨 **ドワーフ工房への指示**

**開発作業:**
```
deploy dwarf
新機能の実装とビルド最適化
```

**インフラ改善:**
```
ドワーフ工房にインフラ最適化を依頼
データベース最適化とパフォーマンス改善
```

### 🧙‍♂️ **ウィザーズへの指示**

**分析・調査:**
```
deploy wizard
システム分析とボトルネック調査
```

**研究開発:**
```
ウィザーズに新技術の調査を依頼
AI学習アルゴリズムの改善研究
```

### 🧝‍♂️ **エルフの森への指示**

**監視・メンテナンス:**
```
deploy elf
システム監視の強化とアラート最適化
```

**継続的改善:**
```
エルフの森に継続的改善を依頼
コードの品質維持とリファクタリング
```

---

## 📚 エルダー知恵の活用

### 🔮 **知恵検索**

**一般的な知恵:**
```
wisdom TDD
wisdom カバレッジ向上
wisdom パフォーマンス最適化
```

**具体的な質問:**
```
query テストカバレッジの目標値は？
query 最適化の優先順位判断基準
query コードレビューのベストプラクティス
```

### 🏛️ **エルダー評議会への相談**

**重要な決定:**
```
council アーキテクチャ変更の提案
council 新技術導入の検討
council 品質基準の見直し
```

**戦略的判断:**
```
エルダー評議会を召集
議題: プロジェクトの方向性について
```

---

## ⚠️ トラブルシューティング

### 🔧 **よくある問題と解決法**

#### 1. **タスクが開始されない**
```bash
# システム状態確認
ai-elder status

# エルダーシステム再起動
ai-start

# 手動でタスクエルダー起動
python3 libs/claude_task_tracker.py
```

#### 2. **進捗が更新されない**
```
# チャットで確認
タスクの状況を確認
システム監視の状態は？

# ダッシュボードで確認
ログ監視タブで詳細ログを確認
```

#### 3. **サーベントが応答しない**
```bash
# サーベント状態確認
python3 libs/elder_servant_dispatcher.py --status

# サーベント再起動
python3 libs/elder_servant_dispatcher.py --restart
```

#### 4. **API エラー**
```python
# エラーハンドリング例
try:
    response = await chat_api.process_chat_message(message)
    if not response.get('success'):
        print(f"エラー: {response.get('error')}")
except Exception as e:
    print(f"API エラー: {str(e)}")
```

---

## 🎓 ベストプラクティス

### ✅ **効果的な指示の出し方**

1. **具体的で明確な指示**
   - ❌ "何か最適化して"
   - ✅ "libs/performance_optimizer.pyのメモリ使用量を最適化"

2. **優先順位を明示**
   - ✅ "高優先度: セキュリティ脆弱性修正"
   - ✅ "中優先度: パフォーマンス改善"

3. **期待値を設定**
   - ✅ "カバレッジを90%以上に向上"
   - ✅ "レスポンス時間を50%改善"

4. **制約条件を明記**
   - ✅ "既存APIとの互換性を維持"
   - ✅ "メモリ使用量は現在の120%以下"

### 🚀 **効率的なワークフロー**

1. **事前準備**
   ```bash
   # システム状態確認
   ai-elder status
   
   # 現在の作業状況確認
   ai-task-status
   ```

2. **タスク実行**
   ```
   # ダッシュボードまたはチャットで指示
   # 進捗をモニタリング
   # 必要に応じて調整
   ```

3. **結果確認**
   ```
   # 完了通知を待つ
   # 結果をレビュー
   # 必要に応じて追加指示
   ```

### 🎯 **パフォーマンス最適化**

- **並列処理**: 複数のサーベントタイプに同時指示
- **バッチ処理**: 関連タスクをまとめて依頼
- **優先順位管理**: 重要度に応じてタスク分類

---

## 📞 サポートとお問い合わせ

### 💬 **ヘルプ取得**

**チャット:**
```
help
タスクエルダーの使い方を教えて
```

**コマンド:**
```bash
ai-elder help
python3 libs/claude_elder_chat_api.py --help
```

### 📋 **システム情報**

**設定確認:**
```bash
# 環境設定確認
python3 -c "from libs.env_config import get_config; print(get_config().__dict__)"

# エルダーシステム詳細
ai-elder-council --status
```

**ログ確認:**
```bash
# 最新ログ
tail -f logs/elder_council.log
tail -f logs/task_elder.log
tail -f logs/claude_elder_chat.log
```

---

## 🏛️ エルダー評議会承認事項

**承認日**: 2025年7月8日  
**承認者**: Elders Guild 4賢者評議会 (全員一致)

### 📜 **公式採用決定**
- **タスクエルダー協調システム**: 正式運用開始
- **Claude Elder Chat API**: 標準インターフェース認定
- **エルダーサーベント部隊**: 本格運用許可

### 🎯 **品質基準**
- **応答時間**: 30秒以内
- **成功率**: 95%以上
- **エラー処理**: 完全自動復旧

---

**🚀 Elders Guild タスクエルダーシステムで効率的な開発を！**

*最終更新: 2025年7月8日*