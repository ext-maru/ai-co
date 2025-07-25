# Issue #311: Docker環境修正 - python-a2a互換性対応

**作成日**: 2025年7月23日  
**完了日**: 2025年7月23日  
**担当者**: クロードエルダー（Claude Elder）  
**ステータス**: ✅ **完了**

## 🎯 概要

Flask移行（Issue #310）後のDocker環境における問題を修正。

## 📋 問題点

1. **ModuleNotFoundError**: Pythonモジュールが見つからない
2. **ポート競合**: 既存サービスとのポート競合
3. **初期化エラー**: PostgreSQL初期化スクリプトのエラー

## 🔧 実施内容

### 1. モジュール構造修正
```bash
# 全ディレクトリに__init__.py追加
src/
├── __init__.py  # 追加
└── elder_tree/
    ├── __init__.py  # 追加
    ├── agents/
    │   └── __init__.py  # 追加
    ├── workflows/
    │   └── __init__.py  # 追加
    └── servants/
        └── __init__.py  # 追加
```

### 2. Docker設定更新
- Dockerfileのビルドコンテキスト修正
- PYTHONPATHの適切な設定
- ポートマッピングの修正

### 3. PostgreSQL初期化
- ユーザー名の不一致を修正
- 権限設定の更新

## 📊 成果

- **修正前**: コンテナ起動失敗
- **修正後**: 全コンテナ正常起動

## 🚀 技術的詳細

### Docker Compose修正
```yaml
services:
  knowledge_sage:
    build: .  # ルートディレクトリでビルド
    environment:
      - PYTHONPATH=/app/src
```

### __main__.py実装
```python
# 動的モジュールローディング
agent_modules = {
    "knowledge_sage": "elder_tree.agents.knowledge_sage",
    "task_sage": "elder_tree.agents.task_sage",
    # ...
}
```

## 📚 関連ドキュメント

- [Docker再起動ループガイド](../../../guides/troubleshooting/docker-container-restart-loop.md)
- [Issue #310: Flask移行](issue-310-flask-migration.md)
- [Issue #312: フォルダ統合](../../elders-guild/issues/issue-312-folder-consolidation.md)

## 🏷️ ラベル

- bug
- docker
- infrastructure
- high-priority