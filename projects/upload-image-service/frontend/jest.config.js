/**
 * Jest Configuration for Upload Image Service Frontend
 * 🧙‍♂️ Four Sages評議会決定 - Phase 1緊急対応
 * 
 * React Testing Library + Jest 環境構築
 * 実装日: 2025年7月10日
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  
  // Module name mapping for CSS and static assets
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': 'jest-transform-stub',
  },
  
  // Module paths
  moduleDirectories: ['node_modules', '<rootDir>/src'],
  
  // File extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Transform configuration
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
      },
    }],
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  
  // Test match patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx,js,jsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx,js,jsx}',
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/index.tsx',
    '!src/setupTests.ts',
    '!src/**/*.d.ts',
    '!src/types/**/*',
  ],
  
  // Coverage thresholds (Four Sages評議会決定: 90%目標)
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Critical components require higher coverage
    './src/components/admin/SimpleContractReview.tsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/components/contract/ContractUploadFlow.tsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
  
  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  
  // Coverage directory
  coverageDirectory: 'coverage',
  
  // Test path ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/build/',
    '/dist/',
  ],
  
  // Clear mocks
  clearMocks: true,
  
  // Restore mocks
  restoreMocks: true,
  
  // Verbose output
  verbose: true,
  
  // Error on deprecated features
  errorOnDeprecated: true,
  
  // Max workers for performance
  maxWorkers: '50%',
  
  // Globals
  globals: {
    'ts-jest': {
      tsconfig: {
        jsx: 'react-jsx',
      },
    },
  },
  
  // TypeScript path mapping support
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
};

/**
 * 🧙‍♂️ Four Sages評価
 * 
 * ✅ Knowledge Sage: 最新のベストプラクティス適用
 * ✅ Task Sage: 段階的カバレッジ目標設定
 * ✅ Incident Sage: 重要コンポーネント90%カバレッジ必須
 * ✅ RAG Sage: TypeScript・モジュール解決完全対応
 * 
 * 次のステップ:
 * 1. setupTests.ts 作成
 * 2. package.json テストスクリプト追加
 * 3. CI/CD統合準備
 */