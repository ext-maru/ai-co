# 🏛️ エルダーズギルド プロジェクトテンプレートシステム

## 📋 概要

エルダーズギルドプロジェクトテンプレートシステムは、**コンテキスト制限で前回の進行状況を忘れる問題**を解決し、プロジェクトの標準化と継続性を確保するシステムです。

### 🎯 解決する課題

1. **コンテキスト制限問題**: クロードエルダーが前回の進行状況を忘れる
2. **プロジェクト標準化**: 各プロジェクトの進行方法がバラバラ
3. **重要情報の喪失**: 決定事項や経緯が失われる
4. **継続性の欠如**: 中断後の再開が困難

### 🌟 主要機能

- **プロジェクトテンプレート**: 標準化された進行フローを提供
- **状態管理**: リアルタイムの進捗状況を追跡
- **継続性ログ**: 全ての活動を記録し、コンテキストを維持
- **4賢者統合**: 各フェーズで自動的に専門家に相談
- **チェックリスト**: フェーズ完了の品質保証

## 🎮 利用可能なテンプレート

### 1. Web開発プロジェクト (`web_development`)

```
Phase 1: 要件定義・設計 (7日)
├── 要件整理
├── 技術選定
├── アーキテクチャ設計
└── データベース設計

Phase 2: 基盤実装 (14日)
├── 認証システム
├── データベース構築
├── API基盤
└── フロントエンド基盤

Phase 3: 機能実装 (21日)
├── コア機能実装
├── UI/UX実装
├── テスト実装
└── 統合テスト

Phase 4: 最適化・デプロイ (10日)
├── パフォーマンス最適化
├── セキュリティ強化
├── デプロイ準備
└── 本番デプロイ
```

### 2. AI開発プロジェクト (`ai_development`)

```
Phase 1: 問題定義・データ調査 (10日)
├── 問題定義
├── データ収集
├── データ分析
└── 仮説設定

Phase 2: モデル開発 (14日)
├── ベースライン実装
├── モデル選定
├── 特徴量エンジニアリング
└── モデル学習

Phase 3: 評価・改善 (10日)
├── モデル評価
├── ハイパーパラメータ調整
├── モデル改善
└── バリデーション

Phase 4: 統合・デプロイ (7日)
├── システム統合
├── 推論API実装
├── モニタリング実装
└── 本番デプロイ
```

### 3. 緊急修正プロジェクト (`hotfix`)

```
Phase 1: 緊急調査 (1日)
├── 問題特定
├── 影響範囲調査
├── 原因分析
└── 修正方針決定

Phase 2: 修正実装 (2日)
├── 修正実装
├── 単体テスト
├── 統合テスト
└── 影響確認

Phase 3: 緊急デプロイ (1日)
├── デプロイ準備
├── 本番デプロイ
├── 動作確認
└── 監視強化
```

## 🚀 基本使用方法

### 1. テンプレート一覧確認

```bash
# 利用可能なテンプレート表示
ai-project-template templates
```

### 2. プロジェクト作成

```bash
# Web開発プロジェクト作成
ai-project-template create "新しいWebアプリ" web_development

# AI開発プロジェクト作成
ai-project-template create "画像分類モデル" ai_development

# 緊急修正プロジェクト作成
ai-project-template create "ログイン障害修正" hotfix
```

### 3. プロジェクト状況確認

```bash
# 状況レポート表示
ai-project-template status project_20250710_143022_a1b2c3d4

# プロジェクト一覧表示
ai-project-template list
```

### 4. フェーズ進行

```bash
# 次のフェーズに進む
ai-project-template advance project_20250710_143022_a1b2c3d4
```

### 5. コンテキスト確認

```bash
# 詳細コンテキスト表示
ai-project-template context project_20250710_143022_a1b2c3d4

# JSON形式でコンテキスト出力（継続性確保）
ai-project-template context project_20250710_143022_a1b2c3d4 --format json
```

## 🧙‍♂️ 4賢者統合機能

### 自動相談システム

各フェーズで自動的に適切な賢者に相談が行われます：

```bash
# 4賢者への相談
ai-project-template consult project_20250710_143022_a1b2c3d4 --knowledge
ai-project-template consult project_20250710_143022_a1b2c3d4 --task
ai-project-template consult project_20250710_143022_a1b2c3d4 --incident
ai-project-template consult project_20250710_143022_a1b2c3d4 --rag "認証実装のベストプラクティス"
```

### 相談事項の例

**Phase 1: 要件定義・設計**
- 🧙‍♂️ **ナレッジ賢者**: 類似プロジェクトの成功事例と失敗事例を教えて
- 🚨 **インシデント賢者**: 実装時に注意すべきセキュリティリスクを教えて

**Phase 2: 基盤実装**
- 📋 **タスク賢者**: 機能実装の最適な順序と並列化可能なタスクを教えて
- 🔍 **RAG賢者**: 最新のパフォーマンス最適化手法を教えて

## ✅ チェックリスト機能

### フェーズ完了チェック

```bash
# チェックリスト表示・管理
ai-project-template checklist project_20250710_143022_a1b2c3d4

# 項目1をチェック
ai-project-template checklist project_20250710_143022_a1b2c3d4 --check 1

# 項目2のチェック解除
ai-project-template checklist project_20250710_143022_a1b2c3d4 --uncheck 2
```

### チェック項目の例

**Phase 1: 要件定義・設計**
- [ ] 要件書レビュー完了
- [ ] 技術選定理由書作成
- [ ] アーキテクチャ図作成
- [ ] データベース設計書作成

**Phase 2: 基盤実装**
- [ ] 認証システム実装・テスト
- [ ] データベース作成・マイグレーション
- [ ] API基盤実装
- [ ] フロントエンド基盤実装

## 🔄 継続性機能

### コンテキスト保持

システムは以下の情報を自動的に記録・保持します：

1. **プロジェクト状態**: 現在のフェーズ、進捗、ステータス
2. **活動履歴**: 全ての操作とその結果
3. **決定事項**: 重要な判断と理由
4. **次のアクション**: 次に実行すべきタスク

### セッション間の引き継ぎ

新しいセッションでプロジェクトを再開する場合：

```bash
# 前回の状況を完全に復元
ai-project-template context project_20250710_143022_a1b2c3d4

# 継続性ログから前回の活動を確認
ai-project-template status project_20250710_143022_a1b2c3d4
```

## 📊 状況レポート例

```
🏛️ エルダーズギルド プロジェクト状況レポート
=============================================

📋 プロジェクト情報
- 名前: 新しいWebアプリ
- ID: project_20250710_143022_a1b2c3d4
- テンプレート: web_development
- 現在のフェーズ: Phase 1: 要件定義・設計
- 状態: active
- 作成日: 2025-07-10 14:30:22
- 更新日: 2025-07-10 15:45:33

🎯 現在のタスク
- 要件整理
- 技術選定
- アーキテクチャ設計
- データベース設計

✅ チェックリスト
- [ ] 要件書レビュー完了
- [ ] 技術選定理由書作成
- [ ] アーキテクチャ図作成
- [ ] データベース設計書作成

🧙‍♂️ エルダー相談事項
- knowledge_sage: 類似プロジェクトの成功事例と失敗事例を教えて
- incident_sage: 実装時に注意すべきセキュリティリスクを教えて

📈 最近の活動
- 2025-07-10 15:45:33: phase_advanced
- 2025-07-10 14:30:22: project_created

🔄 フェーズ進捗
Phase 1 / 4
```

## 🎯 実践的な活用例

### 1. 新規Webアプリケーション開発

```bash
# 1. プロジェクト作成
ai-project-template create "ECサイト構築" web_development

# 2. 初期状況確認
ai-project-template status project_20250710_143022_a1b2c3d4

# 3. Phase 1完了後、次のフェーズに進む
ai-project-template advance project_20250710_143022_a1b2c3d4

# 4. 4賢者に相談
ai-project-template consult project_20250710_143022_a1b2c3d4 --knowledge
```

### 2. AI機械学習プロジェクト

```bash
# 1. AIプロジェクト作成
ai-project-template create "顧客離反予測モデル" ai_development

# 2. データ分析フェーズでRAG賢者に相談
ai-project-template consult project_20250710_143022_a1b2c3d4 --rag "顧客離反予測の最新手法"

# 3. チェックリスト確認
ai-project-template checklist project_20250710_143022_a1b2c3d4
```

### 3. 緊急障害対応

```bash
# 1. 緊急修正プロジェクト作成
ai-project-template create "ログイン障害修正" hotfix

# 2. インシデント賢者に緊急相談
ai-project-template consult project_20250710_143022_a1b2c3d4 --incident

# 3. 修正完了後、フェーズ進行
ai-project-template advance project_20250710_143022_a1b2c3d4
```

## 🔗 他システムとの連携

### 既存プロジェクト管理システムとの統合

```bash
# 既存のai-projectコマンドと連携
ai-project create "新プロジェクト" --template-id project_20250710_143022_a1b2c3d4

# ダッシュボードでテンプレートプロジェクト表示
ai-project dashboard
```

### 4賢者システムとの連携

- **ナレッジ賢者**: 過去の類似プロジェクトから知見を抽出
- **タスク賢者**: 最適なタスク実行順序を提案
- **インシデント賢者**: 潜在的なリスクを予測・警告
- **RAG賢者**: 最新の技術情報を提供

## 🚀 高度な機能

### カスタムテンプレート作成

```python
# カスタムテンプレート例
custom_template = ProjectTemplate(
    "custom_development",
    "カスタム開発プロジェクト用テンプレート"
).add_phase(
    "Phase 1: 調査・分析",
    ["要件分析", "技術調査", "リスク分析"],
    5
).add_checklist(
    "Phase 1: 調査・分析",
    ["要件定義書作成", "技術選定完了", "リスク評価完了"]
).add_elder_consultation(
    "Phase 1: 調査・分析",
    "knowledge_sage",
    "類似プロジェクトの成功要因を分析して"
)
```

### 自動化トリガー

```python
# 条件に基づく自動実行
template.add_status_trigger(
    "checklist_completed",
    "advance_phase_automatically"
)
```

## 📝 ベストプラクティス

### 1. プロジェクト開始時

- 適切なテンプレートを選択
- 初期コンテキストを設定
- 4賢者への相談を活用

### 2. フェーズ移行時

- チェックリストの完了を確認
- 成果物の品質をチェック
- 次フェーズの準備を整理

### 3. 継続性確保

- 定期的な状況レポート確認
- 重要な決定事項の記録
- セッション間でのコンテキスト引き継ぎ

### 4. 品質保証

- 各フェーズでの4賢者相談
- チェックリストの完全実行
- 継続的なリスク評価

## 🛠️ トラブルシューティング

### データベースエラー

```bash
# データベースを初期化
python3 -c "from libs.project_template_system import ProjectTemplateSystem; pts = ProjectTemplateSystem(); print('DB initialized')"
```

### プロジェクトが見つからない

```bash
# プロジェクト一覧で確認
ai-project-template list

# 正確なプロジェクトIDを使用
ai-project-template status project_20250710_143022_a1b2c3d4
```

## 🎯 今後の拡張計画

### Phase 1: 基本機能強化

- [ ] カスタムテンプレート作成UI
- [ ] 自動化トリガーの拡充
- [ ] エクスポート・インポート機能

### Phase 2: 高度な統合

- [ ] 既存プロジェクト管理システム統合
- [ ] Slack/Teams通知連携
- [ ] GitHub Issues連携

### Phase 3: AI機能強化

- [ ] 自動フェーズ判定
- [ ] 進捗予測機能
- [ ] 自動チェックリスト生成

## 📞 サポート

- **技術的問題**: インシデント賢者が自動対応
- **使い方**: `ai-project-template help`
- **機能要望**: タスク賢者が優先順位を判断

---

**🏛️ エルダーズギルドプロジェクトテンプレートシステムで、コンテキストを失うことなく、標準化されたプロジェクト管理を実現しよう！**

*作成: タスクエルダー*
*最終更新: 2025年7月11日*
