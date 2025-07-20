# 📚 AI Company Web 専用ナレッジ

## 🎯 プロジェクト概要
- **目的**: エルダーズギルドのWebインターフェース提供
- **特徴**: ファンタジーテーマのダッシュボード、リアルタイム監視
- **使用技術スタック**: React + TypeScript + Python Flask + SQLite
- **主要な設計判断**: SPA + REST API、WebSocket通信

## 🛠️ 技術固有知識

### React + TypeScript
- **特有のパターン**:
  - カスタムフックでのエルダー状態管理
  - ファンタジーテーマコンポーネント設計
  - TypeScript厳格モードでの型定義

- **最適化手法**:
  - React.memoによる再レンダリング制御
  - useMemoでの計算結果キャッシュ
  - 仮想スクロールでの大量データ表示

- **トラブルシューティング**:
  - WebSocket再接続ロジック
  - CORS設定の調整
  - ビルドサイズ最適化

### Python Flask バックエンド
- **特有のパターン**:
  - エルダー認証ミドルウェア
  - 非同期タスク処理統合
  - SQLAlchemyでのDB管理

- **最適化手法**:
  - コネクションプーリング
  - レスポンスキャッシング
  - バックグラウンドジョブ最適化

## 📋 プロジェクト固有のベストプラクティス

### コーディング規約
```typescript
// ファンタジーテーマの命名規則
interface ElderDashboardProps {
  elderName: string;
  magicPower: number;
  guildStatus: 'active' | 'sleeping' | 'meditating';
}

// コンポーネント構造
components/
├── elders/      # エルダー関連
├── magic/       # 魔法効果UI
└── guild/       # ギルド管理
```

### テストパターン
```typescript
// エルダーコンポーネントテスト
describe('ElderDashboard', () => {
  it('should display elder status correctly', () => {
    // ファンタジー要素を含むテスト
  });
});
```

### デプロイメント手順
1. フロントエンドビルド: `npm run build`
2. バックエンドテスト: `pytest`
3. Docker化: `docker-compose up`
4. ヘルスチェック確認

## 🚨 よくある問題と解決策

### プロジェクト特有のエラー
1. **WebSocket接続断**
   - 原因: Flaskのタイムアウト設定
   - 解決: ping/pongメカニズム実装

2. **ファンタジーアニメーション遅延**
   - 原因: CSS transition過多
   - 解決: will-changeプロパティ活用

3. **エルダー状態同期問題**
   - 原因: 複数タブでの状態管理
   - 解決: BroadcastChannel API使用

### パフォーマンス問題
- **大量エルダー表示時の遅延**
  - react-windowによる仮想化
  - 遅延読み込み実装

### セキュリティ考慮事項
- JWT認証の実装
- XSS対策（DOMPurify使用）
- SQLインジェクション防止

## 🔄 中央知識ベースとの連携

### 参照している共通パターン
- TDD開発手法
- エラーハンドリング標準
- ログ出力規約

### 貢献した共通知識
- WebSocketリアルタイム通信パターン
- ファンタジーUI/UXガイドライン
- React + Flask統合手法

### 同期状況
- 最終同期: 2025年7月11日
- 次回同期: 自動（毎週）
- 昇華待ち: WebSocket再接続パターン

## 📈 メトリクス・統計

### コード品質
- テストカバレッジ: 87%
- TypeScript厳格度: strict
- バンドルサイズ: 245KB (gzipped)

### パフォーマンス
- 初期読み込み: 1.2秒
- API平均応答: 150ms
- WebSocket遅延: <50ms

---

**最終更新**: 2025年7月11日
**管理者**: ナレッジ賢者 + Webプロジェクトチーム
**次回レビュー**: 2025年7月18日
