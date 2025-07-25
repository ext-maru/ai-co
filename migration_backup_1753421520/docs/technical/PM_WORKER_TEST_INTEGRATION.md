# PMWorker テスト実行機能 実装ドキュメント

## 概要

PMWorkerにGit Flow運用に加えて、コミット前のテスト実行機能を追加しました。これにより、品質の高いコードのみがリポジトリにコミットされるようになります。

## 主な機能追加

### 1. テスト実行フロー
```
ファイル生成 → テスト実行 → 成功時のみGitコミット
                    ↓
                失敗時はコミットスキップ＆Slack通知
```

### 2. テスト戦略

#### Pythonファイル (.py)
- **構文チェック**: `python3 -m py_compile` で構文エラーを検出
- **ユニットテスト**: 対応するテストファイルが存在する場合は実行
- **インポートチェック**: モジュールが正しくインポートできるか確認

#### その他のファイル
- **.sh**: shellcheckによる構文チェック（未実装）
- **.json**: JSON妥当性検証
- **.yaml/.yml**: YAML妥当性検証

### 3. Git Flow統合
```
auto/task_xxxxx ブランチ作成
    ↓
テスト実行
    ↓ (成功時)
コミット
    ↓
develop へマージ
    ↓
ブランチ削除
```

## 使用方法

### PMWorkerの更新
```bash
# 更新スクリプトを実行
chmod +x /home/aicompany/ai_co/scripts/update_pm_worker_with_tests.sh
cd /home/aicompany/ai_co && ./scripts/update_pm_worker_with_tests.sh
```

### テスト実行の制御
```bash
# テスト実行を有効化（デフォルト）
ai-pm-test enable

# テスト実行を無効化
ai-pm-test disable

# 現在の状態を確認
ai-pm-test status

# テスト設定を表示
ai-pm-test config
```

## 設定ファイル

`/home/aicompany/ai_co/config/pm_test.json`:
```json
{
  "test_before_commit": true,
  "test_timeout": 300,
  "test_strategies": {
    "python_files": {
      "enabled": true,
      "actions": ["syntax_check", "unit_test", "import_check"]
    },
    "shell_scripts": {
      "enabled": true,
      "actions": ["shellcheck", "dry_run"]
    },
    "config_files": {
      "enabled": true,
      "actions": ["json_validate", "yaml_validate"]
    }
  },
  "skip_patterns": [
    "__pycache__",
    "*.pyc",
    "venv/",
    ".git/",
    "*.log"
  ]
}
```

## Slack通知

### テスト成功時
```
🌊 Git Flow 自動処理完了
タスク: code_20250702_123456
ブランチ: auto/task_code_20250702_123456 → develop
テスト: ✅ 成功
ファイル数: 3
ファイル:
  - workers/new_worker.py
  - tests/test_new_worker.py
  - scripts/run_new_worker.sh
```

### テスト失敗時
```
❌ テスト失敗によりコミット中止
タスク: code_20250702_123456
ファイル数: 2
対象ファイル:
  - workers/broken_worker.py
  - scripts/broken_script.py

テストを修正してから再度コミットしてください。
```

## 今後の拡張予定

1. **より詳細なテスト戦略**
   - pytest-covによるカバレッジチェック
   - flake8/blackによるコード品質チェック
   - mypyによる型チェック

2. **パフォーマンステスト**
   - 生成されたコードのベンチマーク
   - メモリ使用量チェック

3. **統合テスト**
   - ワーカー間の連携テスト
   - エンドツーエンドテスト

4. **テストレポート**
   - HTMLレポート生成
   - カバレッジトレンド分析

## トラブルシューティング

### テストが実行されない
```bash
# PMWorkerのログを確認
tail -f /home/aicompany/ai_co/logs/pm_worker.log | grep -E "(テスト|test)"

# テスト実行状態を確認
ai-pm-test status
```

### テストが常に失敗する
```bash
# テスト設定を確認
ai-pm-test config

# 手動でテスト実行
cd /home/aicompany/ai_co
python3 -m py_compile workers/target_file.py
```

### PMWorkerが起動しない
```bash
# エラーログを確認
tail -100 /home/aicompany/ai_co/logs/pm_worker.log

# 依存関係を確認
python3 -c "from libs.test_manager import TestManager"
```

## まとめ

PMWorkerのテスト実行機能により、Elders Guildは以下を実現します：

- ✅ **品質保証**: 構文エラーのあるコードはコミットされない
- ✅ **自動化**: テスト実行からコミットまで全自動
- ✅ **可視性**: テスト結果がSlackで即座に確認可能
- ✅ **柔軟性**: 必要に応じてテスト実行を無効化可能

これにより、Elders Guildはより信頼性の高い自動開発システムとなりました。
