# 🧪 Test Guardian Knight Documentation

## 概要
Test Guardian Knight（テスト守護騎士）は、Elders Guildのコードベースの品質を守る自動テスト実行システムです。システムのアイドル時間を活用して継続的にテストを実行し、問題を早期発見・自動修正します。

## 主な機能

### 1. **継続的テスト実行**
- システムCPU使用率が30%以下の時に自動実行
- デフォルトで5分間隔でテストを巡回
- すべてのユニット、統合、E2Eテストをカバー

### 2. **インテリジェント問題検出**
- テスト失敗パターンの分析
- 連続失敗回数の追跡
- 重要度の自動判定（Critical/High/Medium/Low）

### 3. **自動修正機能**
- **ImportError/ModuleNotFoundError**: 自動インポート修正
- **FileNotFoundError**: テストデータファイルの自動作成
- **AssertionError**: テスト期待値の更新提案
- **TypeError**: 型の不一致を検出して修正

### 4. **詳細な統計とレポート**
- テストセッション履歴の記録
- 成功率、失敗率の追跡
- 自動修正の成功率測定

## 使用方法

### デプロイ
```bash
# デーモンとして起動（推奨）
scripts/deploy-test-guardian

# 10分間隔でテスト実行
scripts/deploy-test-guardian --interval 600

# systemdサービスとして起動
scripts/deploy-test-guardian --mode service

# 停止
scripts/deploy-test-guardian --stop

# ステータス確認
scripts/deploy-test-guardian --status
```

### 設定オプション
- `--interval`: テスト実行間隔（秒）
- `--idle-threshold`: CPU使用率の閾値（%）
- `--no-autofix`: 自動修正を無効化

## アーキテクチャ

```
Test Guardian Knight
├── Patrol（巡回）
│   ├── システム負荷チェック
│   ├── テスト実行
│   └── 失敗検出
├── Investigate（調査）
│   ├── エラーパターン分析
│   ├── 原因特定
│   └── 修正方法決定
└── Resolve（解決）
    ├── 自動修正実行
    ├── 検証テスト
    └── 結果記録
```

## 自動修正の判断基準

### 承認不要で自動修正
1. 明確なインポートエラー（信頼度90%）
2. ファイルパスの問題（信頼度85%）
3. 環境変数の欠落

### 承認が必要な修正
1. テストロジックの変更
2. APIの仕様変更対応
3. 複雑なリファクタリング

## 統計情報

騎士の活動統計は以下に保存されます：
- ログ: `logs/test_guardian.log`
- 履歴: `logs/knights/test_guardian_history.json`
- 個別ログ: `logs/knights/test_guardian_001.log`

## 連携システム

### Elder Council（エルダー評議会）
- 連続5回以上失敗したテストは自動的にエルダー評議会に報告
- 重大な問題（Critical）は即座にエスカレーション

### Unit Progress Tracker
- 日次レポートにテスト実行統計を含める
- 騎士団の活動として記録

## トラブルシューティング

### テストが実行されない
1. CPU使用率を確認（30%以下である必要）
2. プロセスが起動しているか確認: `ps aux | grep test_guardian`
3. ログを確認: `tail -f logs/test_guardian.log`

### 自動修正が機能しない
1. `--no-autofix`オプションが設定されていないか確認
2. 修正権限があるか確認
3. 信頼度スコアが閾値を超えているか確認

## 今後の拡張予定

1. **機械学習による失敗予測**
   - 過去のパターンから失敗を予測
   - プリエンプティブな修正提案

2. **分散テスト実行**
   - 複数のワーカーでテストを並列実行
   - テスト時間の大幅短縮

3. **コード変更連動**
   - ファイル変更を検知して関連テストのみ実行
   - PRごとの影響範囲テスト

---
作成日: 2025年7月7日
最終更新: 2025年7月7日