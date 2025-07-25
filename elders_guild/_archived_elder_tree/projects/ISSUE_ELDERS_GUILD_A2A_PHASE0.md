# 🏛️ [Elders Guild] Phase 0: A2A移行準備・基盤構築

## 📋 概要
Elders GuildのA2A移行マスタープラン(EG-MIGRATION-001)のPhase 0実装。新A2A開発環境の整備と技術仕様策定を行う。

## 🎯 背景
現在のElders Guildには1,670行の技術負債（カスタムA2A実装）が存在。これをpython-a2a + FastAPIベースの標準実装に移行するための準備フェーズ。

## 🔧 タスクリスト

### 開発環境整備（3-4日）
- [ ] 新A2A開発環境セットアップ
  - [ ] `elders_guild_a2a_v3`ディレクトリ作成
  - [ ] python-a2a, fastapi, uvicorn環境構築
  - [ ] 仮想環境とパッケージ管理
- [ ] 標準ディレクトリ構造作成
  - [ ] agents/ - A2Aエージェント実装
  - [ ] tests/ - テストコード
  - [ ] configs/ - 設定ファイル
  - [ ] scripts/ - ユーティリティスクリプト
  - [ ] docs/ - ドキュメント
- [ ] CI/CD Pipeline基盤
  - [ ] GitHub Actions設定（無効化ポリシー考慮）
  - [ ] テスト自動化設定
  - [ ] 品質チェック統合
- [ ] テストフレームワーク
  - [ ] pytest設定
  - [ ] カバレッジ測定設定
  - [ ] TDD用テンプレート作成

### 技術仕様策定（2-3日）
- [ ] A2Aエージェント標準仕様書
  - [ ] BaseElderAgent仕様
  - [ ] スキル定義標準
  - [ ] エラーハンドリング標準
- [ ] 通信プロトコル仕様書
  - [ ] メッセージフォーマット
  - [ ] 認証・認可仕様
  - [ ] 非同期通信パターン
- [ ] テスト戦略文書
  - [ ] 単体テスト方針
  - [ ] 統合テスト方針
  - [ ] 分散環境テスト方針
- [ ] デプロイメント手順書
  - [ ] Docker構成
  - [ ] 環境変数管理
  - [ ] スケーリング戦略

## 📈 期待される成果
- 技術負債のない新しいA2A基盤の準備完了
- 標準化された開発環境
- 明確な技術仕様とガイドライン

## 🎯 成功基準
- [ ] すべての環境構築タスク完了
- [ ] すべての技術仕様書作成完了
- [ ] 開発チームレビュー承認

## 📅 タイムライン
- 開発環境整備: 3-4日
- 技術仕様策定: 2-3日
- 合計: 5-7日（週1-2）

## 🏷️ ラベル
- `elders-guild`
- `a2a-migration`
- `phase-0`
- `infrastructure`

## 👥 担当
- 実装: クロードエルダー
- レビュー: グランドエルダーmaru

## 📚 関連ドキュメント
- [A2A移行マスタープラン](elders_guild/docs/migration/ELDERS_GUILD_A2A_MIGRATION_PLAN.md)
- [内部リファクタリング計画](elders_guild/docs/migration/NEW_ELDERS_GUILD_A2A_REFACTORING_PLAN.md)