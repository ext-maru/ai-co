# Elders Guild ナレッジベース

## 🐛 バグ修正履歴

### Pattern #014: Slack通知とワーカー安定性問題 (2025-07-05)

#### 問題の症状
- Slack通知が送信されない、または大幅に遅延する
- "Connection reset by peer" エラーが頻発（73回以上）
- TaskWorkerが時々停止する
- ResultWorkerのログに「Slack通知: 有効」と表示されるが実際には送信されない

#### 原因
1. **SlackNotifierの実装問題**
   - HTTPレスポンスの詳細をログに記録していない
   - エラー時でも常にTrueを返していた可能性

2. **RabbitMQ接続の不安定性**
   - ハートビート設定が不適切
   - 接続が切れた際の再接続処理が不十分

3. **二重通知の問題**
   - TaskWorkerとResultWorkerの両方でSlack通知を送信
   - 処理の遅延と競合状態を引き起こす

#### 解決方法
1. **SlackNotifierの修正**
   ```python
   # libs/slack_notifier.py を修正
   - HTTPステータスコードの適切なチェック
   - レスポンスボディのログ記録
   - タイムアウトと接続エラーの個別処理
   ```

2. **ワーカー安定性の改善**
   ```bash
   # RabbitMQのハートビート設定を60秒に変更
   sudo rabbitmqctl eval 'application:set_env(rabbit, heartbeat, 60).'

   # Elders Guildを再起動
   bash scripts/fix_worker_stability.sh
   ```

3. **自動監視の実装**
   ```bash
   # ワーカーの健全性を5分ごとにチェック
   nohup python3 scripts/monitor_workers.py > logs/monitor.log 2>&1 &
   ```

#### 関連ファイル
- `/root/ai_co/libs/slack_notifier.py` - 修正版SlackNotifier
- `/root/ai_co/scripts/fix_worker_stability.sh` - 安定性改善スクリプト
- `/root/ai_co/scripts/monitor_workers.py` - ワーカー監視スクリプト
- `/root/ai_co/scripts/monitor_slack_notifications.py` - Slack通知監視スクリプト

#### 予防策
1. ワーカーの定期的な監視を継続
2. ログファイルのエラーパターンを定期的にチェック
3. TaskWorkerの二重通知を無効化することを検討
4. RabbitMQの接続パラメータを適切に設定

#### テスト方法
```bash
# Slack通知のテスト
python3 << 'EOF'
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
result = notifier.test_notification()
print(result)
EOF

# ワーカーの状態確認
ps aux | grep -E "(task_worker|result_worker|pm_worker)" | grep -v grep

# エラーログの確認
tail -f logs/*.log | grep -E '(ERROR|Exception|Connection reset)'
```

---

### Pattern #015: ディレクトリ構造の再編成 (2025-07-05)

#### 背景
プロジェクトが成長し、libs/に21個、scripts/に20個のファイルが混在。機能別の整理が必要になった。

#### 実施内容
1. **新しいディレクトリ構造**
   ```
   core/       - システムコア（workers, monitoring, queue）
   features/   - 機能別モジュール（ai, conversation, database, notification, integration）
   utils/      - ユーティリティ（scripts, helpers）
   tests/      - テストコード
   ```

2. **移動したファイル**
   - workers/* → core/workers/
   - libs/health_checker.py等 → core/monitoring/
   - libs/rag_manager.py等 → features/ai/
   - libs/conversation_*.py → features/conversation/
   - libs/slack_notifier*.py → features/notification/
   - scripts/test_*.py → tests/

3. **import文の自動更新**
   - update_imports.pyスクリプトで24ファイルを一括更新
   - sys.path.append('/root/ai_co')を追加

4. **設定ファイルパスの修正**
   - SlackNotifierのconfig pathを絶対パスに変更
   - Path("/root/ai_co/config/slack.conf")

5. **後方互換性**
   - シンボリックリンク作成
   - scripts → utils/scripts
   - workers → core/workers

#### 注意点
- PYTHONPATH=/root/ai_co の設定が必要
- 新しいファイルは適切なディレクトリに配置
- DIRECTORY_STRUCTURE.mdを参照

---

### Pattern #016: Slack通知V2デグレ修正 (2025-07-05)

#### 問題の症状
- `'NoneType' object has no attribute 'get'` エラーが発生
- 拡張版Slack通知が送信されない
- result_worker.pyでSlack通知処理が失敗

#### 原因
1. **データ検証不足**
   - `result_worker.py`でNoneデータが渡される
   - `slack_notifier_v2.py`でデータ型チェックが不十分

2. **時刻データ処理の問題**
   - datetime型とstring型の混在
   - end_timeのNone処理が不適切

3. **エラー処理の脆弱性**
   - 例外発生時のフォールバック機能なし

#### 解決方法
1. **データ検証の強化**
   ```python
   # result_worker.py:53-55
   if not result or not isinstance(result, dict):
       logger.error("Slack通知送信エラー: 無効な結果データ")
       return
   ```

2. **安全な時刻処理**
   ```python
   # slack_notifier_v2.py:109-118
   end_time = task_data.get('end_time')
   if not end_time:
       end_time = datetime.now()
   elif isinstance(end_time, str):
       try:
           end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
       except ValueError:
           end_time = datetime.now()
   ```

3. **フォールバック機能の実装**
   ```python
   # result_worker.py:106-116
   if not success and self.slack_notifier_v1.enabled:
       fallback_message = f"タスク {task_data['task_id']} が完了しました"
       self.slack_notifier_v1.send_notification(fallback_message)
   ```

#### 関連ファイル
- `/root/ai_co/core/workers/result_worker.py` - データ検証とフォールバック機能
- `/root/ai_co/features/notification/slack_notifier_v2.py` - 例外処理強化

#### テスト方法
```bash
# 修正後のテスト
python3 -c "
from features.notification.slack_notifier_v2 import SlackNotifierV2
from datetime import datetime
notifier = SlackNotifierV2()
test_data = {'task_id': 'test_001', 'status': 'completed', 'end_time': datetime.now()}
print('✅ Success' if notifier.send_enhanced_task_notification(test_data) else '❌ Failed')
"
```

---

## 📚 その他のパターン

### Pattern #001-013
（以前のパターンはここに記載）

---

### Pattern #017: ai-xxx系コマンドの動作確認完了 (2025-07-05)

#### 実施したテスト
5つのai-xxx系コマンドすべての動作を確認しました。

1. **ai-git コマンド**
   - ✅ ヘルプ表示: 正常
   - ✅ status機能: 正常
   - 🔀 Git操作支援機能が稼働中

2. **ai-dialog コマンド**
   - ✅ ヘルプ表示: 正常
   - ❌ 実行: ModuleNotFoundError (libs モジュールが見つからない)
   - 💬 対話型セッション開始機能（要修正）

3. **ai-reply コマンド**
   - ✅ ヘルプ表示: 正常
   - ✅ 実行: 正常（応答送信成功）
   - 💬 対話応答機能が稼働中

4. **ai-help コマンド**
   - ✅ メインヘルプ: 正常
   - ✅ 詳細ヘルプ: 正常
   - 📚 包括的ヘルプシステムが稼働中

5. **ai-help-comprehensive コマンド**
   - ✅ 包括的ヘルプ: 正常
   - ✅ カテゴリ別表示: 正常
   - 📚 詳細なヘルプシステムが稼働中

#### 発見された問題
- **ai-dialog**: Python環境でlibsモジュールが見つからない
- Pattern #015のディレクトリ構造変更の影響と推測される

#### 修正が必要なもの
- ai-dialogコマンドのimport文修正
- 新しいディレクトリ構造に対応したパス設定

#### 正常に動作するコマンド
- ai-git: Gitflowワークフロー支援
- ai-reply: 対話応答機能
- ai-help: 基本ヘルプシステム
- ai-help-comprehensive: 包括的ヘルプシステム

---

### Pattern #018: エルダーズ知識管理システムの実装 (2025-07-07)

#### 実装内容
PostgreSQLとpgvectorを使用した意味検索可能な知識管理システムを構築しました。

1. **システム構成**
   - **PostgreSQL 16** + **pgvector 0.8.0**: ベクトルデータベース
   - **OpenAI text-embedding-ada-002**: 埋め込みベクトル生成
   - **Python**: システム実装言語

2. **データベース構造**
   ```sql
   - knowledge_categories: 知識カテゴリ管理
   - elders: 知識提供者（エルダー）情報
   - knowledge_entries: 知識エントリ（1536次元ベクトル付き）
   - knowledge_relations: 知識間の関連性
   - search_history: 検索履歴とフィードバック
   ```

3. **実装したコンポーネント**
   - `/root/ai_co/features/ai/elders_knowledge_manager.py`: コア管理クラス
   - `/root/ai_co/utils/scripts/ai-elder`: CLIインターフェース
   - `/root/ai_co/config/elders.conf`: 設定ファイル
   - `/root/ai_co/data/sample_knowledge.json`: サンプルデータ

4. **主な機能**
   - **意味検索**: ベクトル類似度による高度な検索
   - **フォールバック検索**: 埋め込み不可時のテキスト検索
   - **知識管理**: エルダー、カテゴリ、関連性の管理
   - **一括インポート**: JSONファイルからの大量データ投入
   - **フィードバック機能**: 検索結果の評価記録

5. **CLIコマンド**
   ```bash
   # 知識を検索
   ai-elder search "検索クエリ"

   # 新しい知識を追加
   ai-elder add "タイトル" "内容" --category "技術" --tags "Python" "AI"

   # カテゴリ・エルダー一覧
   ai-elder list-categories
   ai-elder list-elders

   # JSONインポート
   ai-elder import data.json
   ```

#### セットアップ手順
1. PostgreSQL 16のインストールと設定
2. pgvector 0.8.0のビルドとインストール
3. データベースとスキーマの作成
4. Pythonライブラリのインストール（psycopg2-binary, openai, numpy, tiktoken）
5. PostgreSQLの認証設定（trust認証）

#### 注意事項
- OpenAI APIキーが未設定の場合は、テキスト検索のフォールバックモードで動作
- 初期データが少ない場合、ivfflatインデックスの性能警告が表示される
- 仮想環境での実行を推奨

#### 今後の拡張案
- Webインターフェースの追加
- 自動学習機能（検索フィードバックからの改善）
- マルチモーダル対応（画像、音声）
- 分散検索対応

---

最終更新: 2025-07-07 15:30
