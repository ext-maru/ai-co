# 📁 エルダーサーバント実装テンプレート

このディレクトリには、エルダーサーバント32体制の実装に使用するテンプレートファイルが格納されています。

## 🧪 TDDテンプレート

### elder_servant_tdd_template.py
エルダーサーバント実装用のTDD（Test Driven Development）テンプレートです。

#### 使用方法

1. **テンプレートのコピー**
   ```bash
   cp templates/elder_servant_tdd_template.py tests/elder_servants/test_[サーバント名].py
   ```

2. **クラス名の変更**
   ```python
   # Before
   class TemplateServant(ElderServantBase):

   # After (例: CodeCrafterの場合)
   class CodeCrafterServant(DwarfServant):
   ```

3. **TDDサイクルの実行**
   ```bash
   # RED: テストが失敗することを確認
   pytest tests/elder_servants/test_code_crafter.py -v

   # GREEN: 最小限の実装でテストを通す
   # (実装を少しずつ追加)

   # REFACTOR: コードを改善
   # (リファクタリング後も必ずテストを実行)
   ```

#### テンプレートの特徴

- **Iron Will品質基準準拠**: 95%以上のカバレッジ目標
- **包括的テストケース**: 正常系・異常系・境界値・セキュリティ
- **非同期テスト対応**: async/awaitパターン
- **パフォーマンステスト**: 処理時間・並行処理の検証
- **統合テスト**: 4賢者システム・Elder Flow連携

#### カスタマイズポイント

1. **サーバント固有の能力**
   ```python
   self.capabilities = [
       ServantCapability.CODE_GENERATION,  # 実際の能力に変更
       ServantCapability.TESTING,
   ]
   ```

2. **専門的なテストケース**
   ```python
   @pytest.mark.asyncio
   async def test_specialized_functionality(self, servant):
       # サーバント固有の機能をテスト
       pass
   ```

3. **ドメイン設定**
   ```python
   # ドワーフ工房の場合
   return TemplateServant("servant_name", ServantDomain.DWARF_WORKSHOP)

   # RAGウィザーズの場合
   return TemplateServant("servant_name", ServantDomain.RAG_WIZARDS)
   ```

## 📋 実装チェックリスト

### Phase 1: テスト設計（RED）
- [ ] サーバント名とドメインの決定
- [ ] 必要な能力（capabilities）の定義
- [ ] 主要なテストケースの実装
- [ ] テストが失敗することの確認

### Phase 2: 最小実装（GREEN）
- [ ] テストを通す最小限の実装
- [ ] 基本的なprocess_request実装
- [ ] validate_request実装
- [ ] get_capabilities実装

### Phase 3: 改善（REFACTOR）
- [ ] コードの構造改善
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング強化
- [ ] ドキュメント追加

### Phase 4: 統合（INTEGRATE）
- [ ] 4賢者システムとの連携
- [ ] Elder Flowとの統合
- [ ] ServantRegistryへの登録
- [ ] 本番環境でのテスト

## 🎯 品質基準

### テストカバレッジ目標
- **ユニットテスト**: 95%以上
- **統合テスト**: 85%以上
- **E2Eテスト**: 80%以上

### Iron Will基準クリア項目
- [ ] 根本解決度: 95%以上
- [ ] 依存関係完全性: 100%
- [ ] テストカバレッジ: 95%以上
- [ ] セキュリティスコア: 90%以上
- [ ] パフォーマンス基準: 85%以上
- [ ] 保守性指標: 80%以上

## 🚀 次のステップ

1. **テンプレートの実際の使用**
   - Issue #69（基盤修正）でテンプレート適用
   - Issue #70（ドワーフ工房前半）で8体のサーバント実装

2. **テンプレートの改善**
   - 実装中に発見した課題の反映
   - より効率的なTDDパターンの追加

3. **自動化の検討**
   - サーバント生成スクリプトの作成
   - CI/CDパイプラインとの統合

---
**エルダー評議会承認**: 本テンプレートを公式TDD基準として採用
