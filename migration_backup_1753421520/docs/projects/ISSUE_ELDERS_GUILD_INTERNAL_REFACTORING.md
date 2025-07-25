# 🏛️ [Elders Guild] 内部A2A標準化リファクタリング

## 📋 概要
新生elders_guildディレクトリ内の既存システムを、技術負債なくpython-a2a + FastAPI標準に内部リファクタリングする。

## 🎯 背景
現在の新生Elders Guildには以下の技術負債が存在：
- `shared_libs/a2a_protocol.py`: 306行のカスタムA2A実装
- 4賢者のBaseSoul継承によるカスタム通信
- 標準化されていないエージェント間通信

## 🔧 実装フェーズ

### Phase 1: 内部基盤標準化（週1-2）
- [ ] FastAPI Gateway A2A対応
  - [ ] `src/elder_tree/api/main.py`の拡張
  - [ ] A2Aエージェントレジストリ実装
  - [ ] 既存エンドポイントのA2A統合
- [ ] 依存関係更新
  - [ ] `docker/pyproject.toml`への追加パッケージ
  - [ ] httpx, structlog等の追加
- [ ] Docker環境でのA2A通信テスト
  - [ ] コンテナ間通信確認
  - [ ] 分散環境での動作検証

### Phase 2: 4賢者A2A変換（週3-5）
- [ ] Knowledge Sage変換
  - [ ] `a2a_agent.py`新規作成
  - [ ] ビジネスロジック分離（`business_logic.py`）
  - [ ] 既存機能の移行とテスト
- [ ] Task Sage変換
  - [ ] 同様の構造で実装
  - [ ] プロジェクト管理機能のA2A化
- [ ] Incident Sage変換
  - [ ] 品質監視機能のA2A実装
  - [ ] アラート機能の統合
- [ ] RAG Sage変換
  - [ ] 検索機能のA2A対応
  - [ ] キャッシュ機能の移行

### Phase 3: カスタム実装削除（週6）
- [ ] `shared_libs/`完全削除
  - [ ] `soul_base.py`削除
  - [ ] `a2a_protocol.py`削除
- [ ] 旧実装の`soul.py`ファイル削除
- [ ] 依存関係のクリーンアップ

### Phase 4: 統合テスト・文書化（週7）
- [ ] 分散環境統合テスト
- [ ] パフォーマンステスト
- [ ] 監視システム統合
- [ ] ドキュメント更新

## 📈 期待される効果
- **技術負債削除**: 306行以上のカスタムコード削除
- **標準化**: python-a2a準拠の実装
- **保守性向上**: 業界標準ツールの活用
- **拡張性**: 新サービス追加が容易に

## 🎯 成功基準
- [ ] すべてのカスタムA2A実装削除
- [ ] 4賢者すべてのA2A標準化完了
- [ ] 統合テスト100%成功
- [ ] パフォーマンス劣化なし

## 📅 タイムライン
- Phase 1: 週1-2（3-10日）
- Phase 2: 週3-5（11-25日）
- Phase 3: 週6（26-30日）
- Phase 4: 週7（31-35日）

合計: 約5週間

## 🏷️ ラベル
- `elders-guild`
- `a2a-migration`
- `refactoring`
- `technical-debt`

## 👥 担当
- 実装: クロードエルダー
- レビュー: グランドエルダーmaru

## 📚 関連ドキュメント
- [内部リファクタリング計画](elders_guild/docs/migration/NEW_ELDERS_GUILD_A2A_REFACTORING_PLAN.md)
- [A2A移行マスタープラン](elders_guild/docs/migration/ELDERS_GUILD_A2A_MIGRATION_PLAN.md)