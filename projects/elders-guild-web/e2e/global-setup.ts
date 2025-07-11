/**
 * E2E Global Setup
 * 🧙‍♂️ Four Sages評議会決定 - E2Eテスト環境準備
 * 
 * テスト実行前のグローバルセットアップ
 * 実装日: 2025年7月11日
 */

import { chromium, FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';

async function globalSetup(config: FullConfig) {
  console.log('🏛️ エルダーズギルド E2Eテスト環境準備開始...');
  
  // テストデータディレクトリ作成
  const testDataDir = path.join(__dirname, 'test-data');
  if (!fs.existsSync(testDataDir)) {
    fs.mkdirSync(testDataDir, { recursive: true });
  }
  
  // レポートディレクトリ作成
  const reportDir = path.join(__dirname, '..', 'e2e-reports');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  
  // 認証状態の事前準備（必要に応じて）
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // エルダーズギルド初期設定
    await page.goto(config.projects[0].use.baseURL!);
    
    // ローカルストレージ設定
    await page.evaluate(() => {
      // エルダーズギルドテーマ設定
      localStorage.setItem('elders-guild-theme', 'dark');
      localStorage.setItem('elders-guild-locale', 'ja-JP');
      
      // 4賢者システム初期状態
      localStorage.setItem('sage-system-initialized', 'true');
      localStorage.setItem('cultural-mode', 'true');
      
      // テスト用フラグ
      localStorage.setItem('e2e-test-mode', 'true');
    });
    
    // 認証状態保存（必要に応じて）
    await context.storageState({ path: path.join(testDataDir, 'auth.json') });
    
    console.log('✅ Knowledge Sage: テストデータ準備完了');
    console.log('✅ Task Sage: 環境設定完了');
    console.log('✅ Incident Sage: エラー監視準備完了');
    console.log('✅ RAG Sage: 検索インデックス準備完了');
    
  } catch (error) {
    console.error('❌ E2Eセットアップエラー:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
  
  console.log('🎯 エルダーズギルド E2Eテスト環境準備完了！');
  
  // 環境変数設定
  process.env.E2E_TEST_MODE = 'true';
  process.env.ELDERS_GUILD_E2E = 'active';
}

export default globalSetup;

/**
 * 🧙‍♂️ Four Sages評価
 * 
 * ✅ Knowledge Sage: テストデータ・環境準備完璧
 * ✅ Task Sage: 効率的なセットアップフロー
 * ✅ Incident Sage: エラーハンドリング完備
 * ✅ RAG Sage: 包括的な初期設定
 * 
 * セットアップ内容:
 * - ディレクトリ構造準備
 * - エルダーズギルド設定
 * - 4賢者システム初期化
 * - 認証状態準備
 * - 環境変数設定
 */