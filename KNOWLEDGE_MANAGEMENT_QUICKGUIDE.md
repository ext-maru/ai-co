# 📚 Elders Guild Knowledge Management System v5.3 - Quick Guide

## 🎯 概要

Elders Guild Knowledge Management Systemは、プロジェクト全体のナレッジを統合・追跡・可視化するシステムです。

## ✅ 修正完了内容

### EMOJIキーエラーの修正
- **問題**: 存在しないEMOJIキー（search, camera, chart等）の使用
- **解決**: 全11ファイルで15個の未知のキーを適切な代替キーに置換
- **結果**: 全モジュールが正常動作

### 修正されたキーマッピング
```
search → info
camera → image
chart → monitor
check → success
map → network
document → file
book → template
clock → info
wrench → info
shield → info
```

## 📊 生成されたドキュメント

### 1. 統合ナレッジドキュメント
- **場所**: `/home/aicompany/ai_co/knowledge_base/CONSOLIDATED_KNOWLEDGE/`
- **内容**: 
  - プロジェクト統計（438ファイル、63,949行）
  - システムアーキテクチャ
  - 全ワーカー・マネージャーの詳細
  - ナレッジベースドキュメント一覧

### 2. インタラクティブレポート
- **場所**: `/home/aicompany/ai_co/web/`
- **アクセス**: http://localhost:8080/
- **内容**:
  - ビジュアルな統計ダッシュボード
  - システムアーキテクチャ図
  - 実装詳細のテーブル表示

### 3. 進化トラッキング
- **場所**: `/home/aicompany/ai_co/knowledge_base/evolution_tracking/`
- **内容**:
  - スナップショット（現在の状態）
  - 進化レポート（変更履歴）
  - 比較データ（差分情報）

## 🚀 使用方法

### 基本コマンド

```bash
# ナレッジ統合実行
ai-knowledge consolidate

# 進化追跡
ai-knowledge evolve

# 進化追跡（ビジュアライゼーション付き）
ai-knowledge evolve --visualize

# ステータス確認
ai-knowledge status

# スケジューラー起動
ai-knowledge schedule
```

### ステータス確認

```bash
cd /home/aicompany/ai_co && python3 knowledge_status_summary.py
```

### Webレポート閲覧

```bash
# Webサーバー起動
cd /home/aicompany/ai_co && python3 start_knowledge_web_server.py

# ブラウザでアクセス
http://localhost:8080/knowledge_report_20250704_171606.html
http://localhost:8080/evolution_viz_20250704_171607.html
```

## 📈 システム統計（2025-07-04時点）

- **プロジェクトバージョン**: 2e69db1
- **総ファイル数**: 438
- **総行数**: 63,949
- **ワーカー数**: 19
- **マネージャー数**: 17
- **コマンド数**: 57

## 🔧 トラブルシューティング

### EMOJIキーエラーが再発した場合
```bash
cd /home/aicompany/ai_co && python3 fix_all_emoji_keys.py
```

### Slack通知が機能しない場合
- 環境変数 `SLACK_WEBHOOK_URL` を設定
- または `config/ai_company.conf` で設定

## 🎊 今後の活用

1. **定期実行**: cronで日次/週次でナレッジ統合を実行
2. **CI/CD統合**: GitHubアクションで自動実行
3. **レポート共有**: 生成されたHTMLをチームで共有
4. **進化分析**: 時系列でプロジェクトの成長を可視化

---

**Knowledge is Power! 🚀**
