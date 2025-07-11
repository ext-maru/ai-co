/**
 * Storybook Configuration
 * 🧙‍♂️ Four Sages評議会決定 - Visual Regression Testing基盤
 * 
 * エルダーズギルド Storybook設定
 * 実装日: 2025年7月11日
 */

import type { StorybookConfig } from '@storybook/nextjs';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.stories.@(js|jsx|ts|tsx|mdx)',
    '../src/**/*.story.@(js|jsx|ts|tsx|mdx)',
  ],
  
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
    '@storybook/addon-viewport',
    '@storybook/addon-docs',
    '@chromatic-com/storybook',
  ],
  
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
  
  staticDirs: ['../public'],
  
  // TypeScript設定
  typescript: {
    check: false,
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => {
        return prop.parent
          ? !/node_modules/.test(prop.parent.fileName)
          : true;
      },
    },
  },
  
  // Webpack設定カスタマイズ
  webpackFinal: async (config) => {
    // エイリアス設定
    config.resolve = {
      ...config.resolve,
      alias: {
        ...config.resolve?.alias,
        '@': require('path').resolve(__dirname, '../src'),
      },
    };
    
    return config;
  },
  
  // エルダーズギルド特有設定
  env: (config) => ({
    ...config,
    STORYBOOK_ELDERS_GUILD: 'true',
    STORYBOOK_FOUR_SAGES: 'active',
  }),
  
  docs: {
    autodocs: 'tag',
  },
  
  // プレビュー設定
  previewHead: (head) => `
    ${head}
    <style>
      /* エルダーズギルドテーマ */
      .elders-guild-theme {
        --sage-primary: #10b981;
        --knowledge-primary: #3b82f6;
        --task-primary: #f59e0b;
        --incident-primary: #ef4444;
        --rag-primary: #8b5cf6;
        --elder-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      }
    </style>
  `,
};

export default config;

/**
 * 🧙‍♂️ Four Sages評価
 * 
 * ✅ Knowledge Sage: Storybook最新ベストプラクティス適用
 * ✅ Task Sage: 効率的なビルド・開発設定
 * ✅ Incident Sage: エラー検出・デバッグ支援
 * ✅ RAG Sage: 包括的なドキュメント生成
 * 
 * 設定特徴:
 * - Next.js完全統合
 * - TypeScript対応
 * - エルダーズギルドテーマ統合
 * - Chromatic連携準備
 * - アクセシビリティテスト
 * 
 * 次のステップ: Preview設定・Stories作成
 */