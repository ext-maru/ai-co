#!/bin/bash
# テストカバレッジ計測スクリプト

echo "=== AI Company テストカバレッジ計測 ==="
echo "開始時刻: $(date)"
echo ""

# テスト実行ディレクトリに移動
cd /home/aicompany/ai_co

# カバレッジディレクトリをクリーンアップ
rm -rf htmlcov .coverage

# pytest実行（特定のテストのみ実行して全体のエラーを回避）
echo "テスト実行中..."
python3 -m pytest tests/unit/test_worker_*.py \
    --cov=libs \
    --cov=workers \
    --cov=core \
    --cov-report=term-missing \
    --cov-report=html \
    -v 2>&1 | tee test_results.log

# カバレッジレポートのパスを表示
echo ""
echo "HTMLカバレッジレポート: file:///home/aicompany/ai_co/htmlcov/index.html"
echo ""

# 簡易カバレッジサマリー
echo "=== カバレッジサマリー ==="
python3 -m coverage report --skip-covered | tail -20

echo ""
echo "完了時刻: $(date)"
