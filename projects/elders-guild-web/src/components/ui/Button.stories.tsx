/**
 * Button Component Stories
 * 🧙‍♂️ Four Sages評議会決定 - Visual Regression Testing
 * 
 * エルダーズギルド Button コンポーネントストーリー
 * 実装日: 2025年7月11日
 */

import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';
import { Activity, BookOpen, TrendingUp, AlertCircle, Search } from 'lucide-react';

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'エルダーズギルド基盤UIボタンコンポーネント。4賢者テーマ対応。',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'knowledge', 'task', 'incident', 'rag', 'elder', 'ghost', 'outline'],
      description: 'ボタンバリアント',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'ボタンサイズ',
    },
    glow: {
      control: 'boolean',
      description: 'エルダーグロー効果',
    },
    disabled: {
      control: 'boolean',
      description: '無効状態',
    },
    onClick: { action: 'clicked' },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

// 基本バリアント
export const Default: Story = {
  args: {
    children: 'Default Button',
  },
};

export const KnowledgeSage: Story = {
  args: {
    variant: 'knowledge',
    children: (
      <>
        <BookOpen className="h-4 w-4" />
        Knowledge Sage
      </>
    ),
  },
};

export const TaskSage: Story = {
  args: {
    variant: 'task',
    children: (
      <>
        <TrendingUp className="h-4 w-4" />
        Task Sage
      </>
    ),
  },
};

export const IncidentSage: Story = {
  args: {
    variant: 'incident',
    children: (
      <>
        <AlertCircle className="h-4 w-4" />
        Incident Sage
      </>
    ),
  },
};

export const RAGSage: Story = {
  args: {
    variant: 'rag',
    children: (
      <>
        <Search className="h-4 w-4" />
        RAG Sage
      </>
    ),
  },
};

export const Elder: Story = {
  args: {
    variant: 'elder',
    children: '👑 エルダー',
    glow: true,
  },
};

// サイズバリエーション
export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="icon">
        <Activity className="h-4 w-4" />
      </Button>
    </div>
  ),
};

// 状態バリエーション
export const States: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <Button>Normal</Button>
        <Button disabled>Disabled</Button>
      </div>
      <div className="flex items-center gap-4">
        <Button glow>With Glow</Button>
        <Button variant="elder" glow>Elder Glow</Button>
      </div>
    </div>
  ),
};

// 4賢者システム統合
export const FourSagesSystem: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4">
      <Button variant="knowledge" size="lg">
        <BookOpen className="h-5 w-5" />
        ナレッジ賢者
      </Button>
      <Button variant="task" size="lg">
        <TrendingUp className="h-5 w-5" />
        タスク賢者
      </Button>
      <Button variant="incident" size="lg">
        <AlertCircle className="h-5 w-5" />
        インシデント賢者
      </Button>
      <Button variant="rag" size="lg">
        <Search className="h-5 w-5" />
        RAG賢者
      </Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: '4賢者システムのボタン統合例',
      },
    },
  },
};

// エルダー評議会
export const ElderCouncil: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8 bg-sage-900/10 rounded-lg">
      <h3 className="text-lg font-bold text-center mb-4">エルダー評議会</h3>
      <Button variant="elder" size="lg" glow className="w-full">
        👑 評議会を開始
      </Button>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm">
          議題を追加
        </Button>
        <Button variant="ghost" size="sm">
          参加者確認
        </Button>
      </div>
    </div>
  ),
};

// アクセシビリティテスト
export const Accessibility: Story = {
  render: () => (
    <div className="space-y-4">
      <Button aria-label="Save document">
        <Activity className="h-4 w-4" />
        Save
      </Button>
      <Button disabled aria-disabled="true">
        Disabled Button
      </Button>
      <Button variant="incident" role="alert">
        Critical Action
      </Button>
    </div>
  ),
  parameters: {
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
        ],
      },
    },
  },
};

// レスポンシブデザイン
export const Responsive: Story = {
  render: () => (
    <div className="w-full max-w-md space-y-4">
      <Button className="w-full">Full Width Button</Button>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="knowledge">Left</Button>
        <Button variant="task">Right</Button>
      </div>
      <div className="flex gap-2">
        <Button variant="ghost" className="flex-1">
          Flex 1
        </Button>
        <Button variant="outline" className="flex-1">
          Flex 2
        </Button>
      </div>
    </div>
  ),
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};

// Chromatic Visual Test
export const ChromaticTest: Story = {
  render: () => (
    <div className="grid gap-4 p-8">
      <div className="grid grid-cols-4 gap-2">
        {(['default', 'knowledge', 'task', 'incident', 'rag', 'elder', 'ghost', 'outline'] as const).map((variant) => (
          <Button key={variant} variant={variant} size="sm">
            {variant}
          </Button>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2">
        {(['default', 'knowledge', 'task', 'incident'] as const).map((variant) => (
          <Button key={`${variant}-glow`} variant={variant} glow>
            {variant} Glow
          </Button>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2">
        {(['sm', 'default', 'lg', 'icon'] as const).map((size) => (
          <Button key={size} size={size}>
            {size === 'icon' ? '🎯' : size}
          </Button>
        ))}
      </div>
    </div>
  ),
  parameters: {
    chromatic: {
      modes: {
        light: { theme: 'light' },
        dark: { theme: 'dark' },
      },
    },
  },
};

/**
 * 🧙‍♂️ Four Sages評価
 * 
 * ✅ Knowledge Sage: 包括的なストーリー網羅
 * ✅ Task Sage: 効率的なビジュアルテスト設定
 * ✅ Incident Sage: エラー状態・エッジケース対応
 * ✅ RAG Sage: アクセシビリティ・レスポンシブ検証
 * 
 * ストーリー内容:
 * - 全バリアント網羅
 * - サイズ・状態バリエーション
 * - 4賢者システム統合例
 * - エルダー評議会UI
 * - アクセシビリティテスト
 * - レスポンシブデザイン
 * - Chromatic最適化
 * 
 * 次のステップ: CI/CD統合
 */