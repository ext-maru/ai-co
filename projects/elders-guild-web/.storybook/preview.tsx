/**
 * Storybook Preview Configuration
 * 🧙‍♂️ Four Sages評議会決定 - Visual Testing環境設定
 *
 * エルダーズギルド Storybookプレビュー設定
 * 実装日: 2025年7月11日
 */

import React from 'react';
import type { Preview } from '@storybook/react';
import { ThemeProvider } from '../src/components/providers/ThemeProvider';
import '../src/app/globals.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },

    // ビューポート設定
    viewport: {
      viewports: {
        eldersDesktop: {
          name: 'Elders Desktop',
          styles: {
            width: '1440px',
            height: '900px',
          },
        },
        eldersTablet: {
          name: 'Elders Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        eldersMobile: {
          name: 'Elders Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
      },
    },

    // エルダーズギルドテーマ設定
    backgrounds: {
      default: 'elders-dark',
      values: [
        {
          name: 'elders-dark',
          value: '#0a0a0a',
        },
        {
          name: 'elders-light',
          value: '#fafafa',
        },
        {
          name: 'sage-green',
          value: '#10b981',
        },
        {
          name: 'knowledge-blue',
          value: '#3b82f6',
        },
      ],
    },

    // Chromatic設定
    chromatic: {
      // スナップショット遅延（アニメーション対応）
      delay: 300,
      // アニメーション無効化
      pauseAnimationAtEnd: true,
      // ビューポート設定
      viewports: [375, 768, 1440],
      // 言語モード
      modes: {
        'ja-dark': {
          locale: 'ja',
          theme: 'dark',
        },
        'en-light': {
          locale: 'en',
          theme: 'light',
        },
      },
    },

    // ドキュメント設定
    docs: {
      theme: {
        brandTitle: 'エルダーズギルド UI Library',
        brandUrl: 'https://elders-guild.dev',
        brandImage: '/elders-guild-logo.png',
        brandTarget: '_self',
      },
    },
  },

  // グローバルデコレーター
  decorators: [
    (Story, context) => {
      const theme = context.globals.theme || 'dark';
      const locale = context.globals.locale || 'ja';

      return (
        <ThemeProvider defaultTheme={theme}>
          <div
            className={`elders-guild-storybook ${theme}`}
            data-locale={locale}
          >
            <Story />
          </div>
        </ThemeProvider>
      );
    },
  ],

  // グローバル設定
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'エルダーズギルドテーマ',
      defaultValue: 'dark',
      toolbar: {
        icon: 'paintbrush',
        items: [
          { value: 'dark', title: 'Dark Mode', icon: 'moon' },
          { value: 'light', title: 'Light Mode', icon: 'sun' },
        ],
        dynamicTitle: true,
      },
    },
    locale: {
      name: 'Locale',
      description: '言語設定',
      defaultValue: 'ja',
      toolbar: {
        icon: 'globe',
        items: [
          { value: 'ja', title: '日本語', icon: 'flag' },
          { value: 'en', title: 'English', icon: 'flag' },
        ],
      },
    },
    sageMode: {
      name: 'Sage Mode',
      description: '4賢者モード',
      defaultValue: 'all',
      toolbar: {
        icon: 'user',
        items: [
          { value: 'all', title: 'All Sages' },
          { value: 'knowledge', title: 'Knowledge Sage' },
          { value: 'task', title: 'Task Sage' },
          { value: 'incident', title: 'Incident Sage' },
          { value: 'rag', title: 'RAG Sage' },
        ],
      },
    },
  },

  // タグ設定
  tags: ['autodocs', 'elders-guild', 'four-sages'],
};

export default preview;

/**
 * 🧙‍♂️ Four Sages評価
 *
 * ✅ Knowledge Sage: Visual Testing完全環境構築
 * ✅ Task Sage: 効率的なStory開発環境
 * ✅ Incident Sage: デバッグ・検証機能完備
 * ✅ RAG Sage: 多言語・マルチテーマ対応
 *
 * プレビュー機能:
 * - エルダーズギルドテーマ統合
 * - 多言語切り替え
 * - 4賢者モード選択
 * - Chromatic最適化
 * - カスタムビューポート
 *
 * 次のステップ: コンポーネントStories作成
 */
