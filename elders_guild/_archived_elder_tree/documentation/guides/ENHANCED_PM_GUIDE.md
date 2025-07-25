# 拡張PMワーカー統合ガイド

## 🎯 概要

拡張PMワーカーは、要件定義から本番反映まで全てのフェーズを管理する真のプロジェクトマネージャーです。

## 🏗️ アーキテクチャ

```
要件定義 → 設計 → 開発 → テスト → 本番反映
   ↓        ↓      ↓       ↓        ↓
[要件DB] [設計DB] [タスク] [SE-Tester] [Git]
```

## 📋 主な機能

### 1. **プロジェクトライフサイクル管理**
- 要件定義書の自動生成と管理
- 設計書データベース（アーキテクチャ、DB、API設計）
- 開発タスクのトラッキング
- テスト結果の記録と分析
- デプロイメント履歴

### 2. **自動モード切替**
- **シンプルモード**: 従来のファイル配置のみ
- **プロジェクトモード**: 複雑なタスクで自動的に有効化

### 3. **SE-Tester統合**
- テストフェーズで自動的にSE-Testerワーカーと連携
- テスト失敗時の自動修正
- テスト結果のプロジェクトDBへの記録

### 4. **ナレッジベース連携**
- 過去のプロジェクト経験から学習
- ベストプラクティスの自動適用
- エラーパターンの認識と回避

## 🚀 使用方法

### 基本的な使い方

```bash
# 1. セットアップ（自動）
python3 auto_setup_enhanced_pm.py

# 2. 通常のタスク送信（自動でモード判定）
ai-send "ユーザー管理APIを作成してください" code

# 3. 明示的にプロジェクトモード
ai-send "マイクロサービスアーキテクチャで..." code --project-mode
```

### プロジェクトステータス確認

```python
from libs.project_design_manager import ProjectDesignManager

pm = ProjectDesignManager()
status = pm.get_project_status("proj_20250102_123456")
print(pm.generate_project_report("proj_20250102_123456"))
```

## 📊 データベース構造

### projects テーブル
- プロジェクトの基本情報
- ステータス管理（planning/designing/developing/testing/deployed）

### requirements テーブル
- 機能要件、非機能要件、技術要件
- 優先度管理

### designs テーブル
- アーキテクチャ設計
- データベース設計
- API設計
- バージョン管理

### development_tasks テーブル
- 個別の開発タスク
- ワーカー割り当て
- 実行結果

### test_results テーブル
- テスト種別（unit/integration/e2e）
- 成功/失敗の記録
- カバレッジ情報

## 🔄 フェーズ遷移

1. **Planning（計画）**
   - 要件抽出
   - 優先度設定
   - 要件定義書生成

2. **Design（設計）**
   - アーキテクチャ分析
   - 設計書作成
   - レビュー（将来実装）

3. **Development（開発）**
   - ファイル配置
   - Git管理
   - 進捗トラッキング

4. **Testing（テスト）**
   - SE-Testerとの連携
   - 自動修正
   - 結果記録

5. **Deployment（本番反映）**
   - Gitコミット
   - リリースノート生成
   - 通知

## 🎯 ベストプラクティス

### プロジェクトモードを活用すべきケース
- 5つ以上のファイルを作成するタスク
- アーキテクチャ設計を含むタスク
- 複数のワーカーが関与するタスク
- 長期的なメンテナンスが必要なタスク

### 設計書の活用
- 全ての設計をJSONで構造化
- バージョン管理で変更履歴を追跡
- 他のプロジェクトでの再利用

### テストフェーズの最適化
- SE-Testerを常に有効化
- テスト失敗パターンをナレッジベースに蓄積
- カバレッジ目標の設定

## 📈 メトリクス

プロジェクト管理で収集されるメトリクス：
- フェーズごとの所要時間
- タスク成功率
- テストカバレッジ
- 修正回数
- コード品質指標

## 🔧 カスタマイズ

### 設定ファイル（config/pm_enhanced.json）

```json
{
  "pm": {
    "se_testing_enabled": true,
    "project_mode_threshold": 2,
    "auto_design_generation": true,
    "phases": {
      "planning": {"timeout": 300, "required": true},
      "design": {"timeout": 600, "required": true},
      "development": {"timeout": 1800, "required": true},
      "testing": {"timeout": 900, "required": false},
      "deployment": {"timeout": 300, "required": true}
    }
  }
}
```

## 🚨 トラブルシューティング

### データベースエラー
```bash
# DBの再初期化
rm db/project_designs.db
python3 -c "from libs.project_design_manager import ProjectDesignManager; ProjectDesignManager()"
```

### フェーズがスタックした場合
```python
# 手動でフェーズを進める
pm = ProjectDesignManager()
pm.update_phase_status("proj_xxx", "testing", "completed")
```

## 🎉 まとめ

拡張PMワーカーにより、Elders Guildは単なるコード生成ツールから、完全なソフトウェア開発ライフサイクル管理システムへと進化しました。要件定義から本番反映まで、全てのフェーズを自動的に管理し、品質を保証します。
