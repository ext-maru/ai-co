# 🛡️ Incident Knights 実装依頼書

**依頼日時**: 2025年7月7日 14:44
**依頼者**: Claude CLI（エルダーカウンシル承認済み）
**緊急度**: CRITICAL
**カテゴリ**: system_diagnostic_tool

---

## 📋 実装依頼内容

### 🔬 **ai-debug コマンドの実装**

Elders Guildシステムの診断・デバッグ機能を実装してください。

## 🎯 背景と緊急性

### 現在の問題
1. **Worker Health Monitor**: スケーリング分析失敗が継続発生中
   - エラー: `Scaling analysis failed: 'scaling'`
   - 頻度: 10分ごとに発生

2. **診断能力の不足**: 現在、問題の根本原因を特定する手段が限定的

3. **エルダーカウンシル決定**: ai-debugの実装が最優先事項として承認

## 📝 要求仕様

### 主要機能
1. **システム診断**
   - ワーカー状態の詳細分析
   - キュー状態の診断
   - リソース使用状況の分析
   - エラーログの自動解析

2. **問題検出**
   - 異常パターンの自動検出
   - ボトルネックの特定
   - パフォーマンス問題の診断
   - 依存関係の問題検出

3. **レポート生成**
   - 診断結果の可視化
   - 問題の優先順位付け
   - 改善提案の自動生成
   - Elder Council向けレポート

4. **インタラクティブデバッグ**
   - リアルタイムモニタリング
   - ステップ実行
   - ブレークポイント機能

## 🏗️ 推奨アーキテクチャ

```
commands/ai_debug.py          # CLIエントリーポイント
libs/debug_system/
├── __init__.py
├── system_analyzer.py        # システム分析エンジン
├── problem_detector.py       # 問題検出器
├── diagnostic_reporter.py    # レポート生成
├── interactive_debugger.py   # インタラクティブデバッグ
└── debug_strategies.py       # 診断戦略

config/debug_config.yaml      # 設定ファイル
```

## 🔧 技術要件

### 必須機能
- psutil を使用したシステムメトリクス収集
- RabbitMQ管理APIとの連携
- ログファイルの高速解析
- 4賢者システムとの統合

### 出力形式
- ターミナル向けの視覚的な出力
- JSON形式でのエクスポート
- Markdown形式のレポート
- Slackへの通知

## 📊 期待される効果

1. **問題解決時間**: 現在平均30分 → 5分以内
2. **問題検出率**: 向上（自動検出機能により）
3. **システム安定性**: 予防的診断により向上
4. **開発効率**: デバッグ時間の大幅削減

## 🚀 実装優先順位

1. **Phase 1** (必須・即座):
   - 基本的なシステム診断機能
   - Worker Health Monitorのスケーリング問題の診断
   - 簡易レポート生成

2. **Phase 2** (重要):
   - 自動問題検出
   - 詳細な分析機能
   - Elder Council連携

3. **Phase 3** (拡張):
   - インタラクティブデバッグ
   - AI支援の問題解決提案

## 📅 希望納期

- **Phase 1**: 24時間以内
- **Phase 2**: 48時間以内
- **Phase 3**: 1週間以内

## 🔗 関連情報

- エルダーカウンシル相談書: `/home/aicompany/ai_co/knowledge_base/elder_council_consultation_20250707_comprehensive.md`
- ワーカー自動復旧システム（実装済み）: `/home/aicompany/ai_co/libs/worker_auto_recovery/`
- 現在のエラーログ: `/home/aicompany/ai_co/logs/worker_health_monitor.log`

## 📞 連絡先

質問や進捗報告は以下へ：
- Slack: #incident-knights チャンネル
- Elder Council: 緊急時は直接召喚

---

**騎士団の迅速な対応に期待しています。システムの安定性向上のため、よろしくお願いします。**

*🛡️ For the stability of Elders Guild!*
