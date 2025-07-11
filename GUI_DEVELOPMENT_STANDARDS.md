# 🎨 エルダーズギルドGUI開発標準

## 🏛️ 基本理念

エルダーズギルドのGUIは、**ファンタジー世界観**と**最新技術**を融合させた、直感的で美しいインターフェースを提供します。

## 🎯 デザイン原則

### 1. **ファンタジー要素の統合**
- 魔法陣アニメーション
- エルダー階層を反映したUI
- 4賢者のビジュアル表現
- RPG風のステータス表示

### 2. **ユーザビリティ**
- 5秒以内に目的達成
- 3クリック以内のナビゲーション
- 直感的なアイコンとラベル
- コンテキストヘルプ常備

### 3. **アクセシビリティ**
- WCAG 2.1 AA準拠
- キーボード完全対応
- スクリーンリーダー対応
- 高コントラストモード

### 4. **パフォーマンス**
- First Contentful Paint < 1.5秒
- Time to Interactive < 3.5秒
- Cumulative Layout Shift < 0.1
- 60fps アニメーション

## 🖼️ ビジュアルデザイン

### カラーパレット
```scss
// プライマリカラー（エルダーズギルド）
$elder-purple: #6B46C1;      // 高貴な紫
$elder-gold: #F59E0B;        // 黄金
$sage-blue: #3B82F6;         // 賢者の青
$knight-red: #DC2626;        // 騎士の赤

// セカンダリカラー
$forest-green: #10B981;      // エルフの森
$dwarf-brown: #92400E;       // ドワーフ工房
$magic-cyan: #06B6D4;        // 魔法の水色
$shadow-gray: #4B5563;       // 影

// 背景色
$bg-dark: #111827;           // ダークモード背景
$bg-light: #F9FAFB;          // ライトモード背景
$bg-elder: #1E1B4B;          // エルダーテーマ背景
```

### タイポグラフィ
```css
/* ヘッダーフォント（ファンタジー風） */
@font-face {
  font-family: 'Elder Runes';
  src: url('/fonts/elder-runes.woff2') format('woff2');
}

/* 本文フォント（読みやすさ重視） */
body {
  font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 16px;
  line-height: 1.8;
}

/* 見出し階層 */
h1 { font-size: 2.5rem; font-family: 'Elder Runes', serif; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
h4 { font-size: 1.25rem; }
```

## 🧩 コンポーネント規格

### ボタンコンポーネント
```typescript
interface ElderButton {
  variant: 'primary' | 'secondary' | 'danger' | 'magic';
  size: 'small' | 'medium' | 'large';
  effect?: 'glow' | 'ripple' | 'magic-circle';
  icon?: string;
  loading?: boolean;
  disabled?: boolean;
}

// 使用例
<ElderButton 
  variant="magic" 
  effect="magic-circle"
  icon="🧙‍♂️"
  onClick={castSpell}
>
  魔法を発動
</ElderButton>
```

### カードコンポーネント
```typescript
interface ElderCard {
  title: string;
  sage?: 'knowledge' | 'task' | 'incident' | 'rag';
  elevation?: 1 | 2 | 3;
  animated?: boolean;
  borderEffect?: 'glow' | 'pulse' | 'none';
}

// 4賢者カード
<ElderCard sage="knowledge" animated>
  <h3>ナレッジ賢者の知恵</h3>
  <p>蓄積された知識: 10,234件</p>
</ElderCard>
```

### ダッシュボードレイアウト
```typescript
interface ElderDashboard {
  layout: 'grid' | 'masonry' | 'scroll';
  theme: 'dark' | 'light' | 'elder';
  sidebar: boolean;
  realtime: boolean;
}

// レイアウト構成
<ElderDashboard theme="elder" realtime>
  <StatusBar />
  <SagesPanels />
  <MetricsGrid />
  <ActivityFeed />
</ElderDashboard>
```

## 📱 レスポンシブデザイン

### ブレークポイント
```scss
$mobile: 640px;      // スマートフォン
$tablet: 768px;      // タブレット
$desktop: 1024px;    // デスクトップ
$wide: 1280px;       // ワイドスクリーン
$ultrawide: 1536px;  // ウルトラワイド

// 使用例
@media (min-width: $tablet) {
  .elder-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

### タッチ対応
- 最小タップ領域: 44x44px
- スワイプジェスチャー対応
- ロングプレスメニュー
- ピンチズーム（グラフ・画像）

## ⚡ アニメーション仕様

### 基本トランジション
```css
/* エルダーズギルド標準トランジション */
.elder-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 魔法エフェクト */
@keyframes magic-glow {
  0% { box-shadow: 0 0 5px $elder-purple; }
  50% { box-shadow: 0 0 20px $elder-purple, 0 0 40px $elder-gold; }
  100% { box-shadow: 0 0 5px $elder-purple; }
}

/* ローディングアニメーション */
.elder-loading {
  animation: magic-circle-rotate 2s linear infinite;
}
```

### インタラクション
- ホバー: 即座に反応（transition: 0.15s）
- クリック: リップルエフェクト
- ドラッグ: ゴースト要素表示
- 成功/エラー: パーティクルエフェクト

## 🔧 実装ガイドライン

### Next.js + TypeScript
```typescript
// 基本コンポーネント構造
import { FC } from 'react';
import styles from './ElderComponent.module.scss';

interface ElderComponentProps {
  // Props定義
}

export const ElderComponent: FC<ElderComponentProps> = (props) => {
  // 4賢者フック
  const { knowledge } = useKnowledgeSage();
  const { tasks } = useTaskOracle();
  
  return (
    <div className={styles.container}>
      {/* コンポーネント実装 */}
    </div>
  );
};
```

### 状態管理
```typescript
// Zustand を使用した状態管理
import { create } from 'zustand';

interface ElderUIState {
  theme: 'dark' | 'light' | 'elder';
  sidebarOpen: boolean;
  notifications: Notification[];
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useElderUI = create<ElderUIState>((set) => ({
  theme: 'elder',
  sidebarOpen: true,
  notifications: [],
  toggleTheme: () => set((state) => ({ 
    theme: state.theme === 'dark' ? 'light' : 'dark' 
  })),
  toggleSidebar: () => set((state) => ({ 
    sidebarOpen: !state.sidebarOpen 
  })),
}));
```

## 🧪 テスト要件

### 単体テスト
```typescript
// コンポーネントテスト例
import { render, screen, fireEvent } from '@testing-library/react';
import { ElderButton } from './ElderButton';

describe('ElderButton', () => {
  it('魔法エフェクトが正しく発動する', () => {
    const handleClick = jest.fn();
    render(
      <ElderButton effect="magic-circle" onClick={handleClick}>
        Cast Spell
      </ElderButton>
    );
    
    const button = screen.getByText('Cast Spell');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalled();
    expect(button).toHaveClass('magic-circle-effect');
  });
});
```

### E2Eテスト
```typescript
// Playwright によるE2Eテスト
import { test, expect } from '@playwright/test';

test('エルダーダッシュボードの動作確認', async ({ page }) => {
  await page.goto('/dashboard');
  
  // 4賢者パネルの確認
  await expect(page.locator('.knowledge-sage-panel')).toBeVisible();
  await expect(page.locator('.task-oracle-panel')).toBeVisible();
  
  // リアルタイム更新の確認
  await page.waitForSelector('.metrics-update', { timeout: 5000 });
});
```

## 📊 品質メトリクス

### パフォーマンス目標
| メトリクス | 目標値 | 測定方法 |
|-----------|--------|----------|
| FCP | < 1.5s | Lighthouse |
| TTI | < 3.5s | Lighthouse |
| CLS | < 0.1 | Lighthouse |
| FPS | 60 | Chrome DevTools |

### アクセシビリティ目標
| 項目 | 基準 | チェックツール |
|------|------|---------------|
| 色コントラスト | 4.5:1以上 | axe DevTools |
| キーボード操作 | 100%対応 | 手動テスト |
| ARIA属性 | 適切に実装 | ESLint plugin |
| フォーカス表示 | 明確に表示 | 手動テスト |

## 🚀 デプロイチェックリスト

- [ ] Lighthouseスコア 90以上
- [ ] 全ブラウザテスト完了
- [ ] レスポンシブ動作確認
- [ ] アクセシビリティ監査パス
- [ ] パフォーマンステスト合格
- [ ] セキュリティヘッダー設定
- [ ] エラー監視設定
- [ ] A/Bテスト準備

---

**"Beautiful UI with Elder's Magic!"** ✨