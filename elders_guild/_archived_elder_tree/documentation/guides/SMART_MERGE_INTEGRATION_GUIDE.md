# スマートマージシステム統合ガイド

## 概要
enhanced_auto_issue_processorにスマートマージ機能が統合されました。
PRが作成されると自動的にマージを試行します。

## 機能
- **自動マージ試行**: PR作成後、自動的にマージを試行
- **スマートリトライ**: CI待機、ブランチ更新などを自動処理
- **コンフリクト解決**: 安全なコンフリクトは自動解決
- **進捗レポート**: イシューコメントで状況を報告

## 使用方法

### 1. 環境変数設定
```bash
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"
```

### 2. 実行
```bash
python3 -m libs.integrations.github.enhanced_auto_issue_processor
```

### 3. 動作確認
- イシューが自動処理される
- PRが作成される
- スマートマージが自動実行される
- 結果がイシューにコメントされる

## 設定

### コンフリクト解決を無効化
```python
processor = EnhancedAutoIssueProcessor()
processor.conflict_resolution_enabled = False
```

### マージ監視時間の調整
```python
# _attempt_smart_merge メソッド内
merge_result = await self.smart_merge_system.handle_pull_request(
    pr_number=pr.number,
    monitoring_duration=600,  # 10分間監視
    auto_merge=True
)
```

## トラブルシューティング

### マージが失敗する場合
1. ブランチ保護ルールを確認
2. CI/CDの設定を確認
3. 権限設定を確認

### ログの確認
```bash
# 詳細ログを有効化
export LOG_LEVEL=DEBUG
```

作成日時: 2025-07-20 19:24:18
