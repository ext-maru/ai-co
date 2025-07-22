#!/bin/bash
# Continuous Test Runner
# ファイル変更を監視して自動テスト実行

echo "👀 Watching for file changes..."
echo "Tests will run automatically when you save files"

# pytest-watchがない場合はインストール
poetry add --dev pytest-watch

# 継続的テスト実行
poetry run ptw -- -v --tb=short
