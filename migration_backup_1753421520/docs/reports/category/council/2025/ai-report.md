# ai-report コマンド

## 概要

`ai-report`は、Elders Guildシステムの包括的なレポートを生成するコマンドです。4賢者統合システムと連携し、システムの状態、パフォーマンス、インシデント、学習状況などを分析・可視化します。

## 使用方法

```bash
ai-report [OPTIONS]
```

## オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--type` | `-t` | レポートタイプを指定 | `overview` |
| `--format` | `-f` | 出力フォーマット | `markdown` |
| `--output` | `-o` | 出力ファイルパス | 自動生成 |
| `--period` | `-p` | レポート対象期間（日数） | `7` |
| `--schedule` | `-s` | 定期レポートスケジュール | なし |
| `--template` | | カスタムテンプレートファイル | なし |
| `--visualize` | `-v` | ビジュアライゼーションを含める | `false` |
| `--compare-with` | | 比較対象期間（日数） | なし |

## レポートタイプ

### overview（システム概要）
システム全体の概要を提供します。
- 総タスク数と完了率
- アクティブワーカー数
- システム稼働時間
- キューステータス

```bash
ai-report --type overview
```

### sages（4賢者システム）
4賢者の個別ステータスと協調状況を表示します。
- 各賢者の健全性
- 専門分野別のメトリクス
- 賢者間の協調成功率

```bash
ai-report --type sages --format html
```

### performance（パフォーマンス）
システムパフォーマンスの詳細分析を提供します。
- 平均応答時間
- タスク完了率
- システム可用性
- リソース使用率（CPU、メモリ、ディスク）

```bash
ai-report --type performance --period 30
```

### incidents（インシデント）
インシデントの統計と分析を表示します。
- 総インシデント数
- 解決率と平均解決時間
- インシデントタイプ別の分析

```bash
ai-report --type incidents
```

### learning（学習状況）
AI学習・進化の状況を報告します。
- 学習セッション数
- コンセンサス成功率
- 賢者間知識転送
- 知識成長率

```bash
ai-report --type learning
```

### comparison（期間比較）
異なる期間のメトリクスを比較します。

```bash
ai-report --type comparison --period 7 --compare-with 14
```

### custom（カスタム）
カスタムテンプレートを使用してレポートを生成します。

```bash
ai-report --type custom --template my_template.md
```

### scheduled（定期レポート）
定期的なレポート生成を設定します。

```bash
ai-report --type scheduled --schedule daily
```

## 出力フォーマット

### Markdown
読みやすいMarkdown形式で出力します。GitHubやドキュメントツールに最適です。

```bash
ai-report --format markdown
```

### HTML
インタラクティブなHTML形式で出力します。ブラウザで表示でき、チャートも含まれます。

```bash
ai-report --format html --visualize
```

### JSON
プログラムから処理しやすいJSON形式で出力します。

```bash
ai-report --format json --output report.json
```

## 使用例

### 基本的な使用
```bash
# デフォルト（過去7日間の概要をMarkdownで）
ai-report

# 特定の出力先を指定
ai-report --output ~/reports/weekly_report.md
```

### 高度な使用
```bash
# 過去30日間の4賢者レポートをHTMLで生成（ビジュアライゼーション付き）
ai-report --type sages --period 30 --format html --visualize --output sages_report.html

# 期間比較レポート（今週と先週を比較）
ai-report --type comparison --period 7 --compare-with 14

# カスタムテンプレートを使用
ai-report --type custom --template templates/executive_summary.md

# 定期レポートの設定（毎日実行）
ai-report --type scheduled --schedule daily --format html
```

## レポートの内容

### エグゼクティブサマリー
- 重要指標の概要
- 前期間との比較
- 注目すべき変化やトレンド

### 4賢者ステータス
- **📚 ナレッジ賢者**: 知識蓄積と学習パターン
- **📋 タスク賢者**: タスク管理と最適化
- **🚨 インシデント賢者**: 問題検知と自動復旧
- **🔍 RAG賢者**: 検索精度とコンテキスト強化

### パフォーマンス指標
- システム応答性
- リソース使用効率
- スケーラビリティ指標

### 推奨アクション
- システム最適化の提案
- 潜在的な問題への対処法
- 改善機会の特定

## テンプレートのカスタマイズ

Jinja2テンプレートを使用してレポートをカスタマイズできます：

```jinja2
# custom_report.md
# {{title}}

生成日時: {{generated_at}}

## 主要指標
- タスク総数: {{total_tasks}}
- 完了率: {{completion_rate}}%

## カスタムセクション
{{custom_data}}
```

## 定期レポートの管理

定期レポートは`reports/`ディレクトリに設定ファイルとして保存されます：

```json
{
  "report_type": "overview",
  "format": "html",
  "period": 7,
  "schedule": "weekly",
  "output_dir": "/home/aicompany/ai_co/reports"
}
```

## トラブルシューティング

### コンポーネント初期化エラー
一部のコンポーネントが初期化できない場合でも、利用可能なデータでレポートを生成します。

### 大量データの処理
長期間のレポートを生成する場合、処理に時間がかかることがあります。`--period`を調整してください。

### テンプレートエラー
カスタムテンプレートでエラーが発生した場合、テンプレート構文を確認してください。

## 関連コマンド

- `ai-status`: システムステータスの即時確認
- `ai-monitor`: リアルタイム監視
- `ai-analyze`: 詳細分析ツール

## 更新履歴

- v2.0.0: 4賢者統合システムとの連携を追加
- v1.0.0: 初期リリース
