#!/bin/bash
# Elder Tree 有効化スクリプト
# Grand Elder maru 安全第一原則準拠

set -e

echo "🛡️ Elder Tree 有効化スクリプト実行開始"
echo "時刻: $(date)"
echo "実行者: Claude Elder"

# 作業ディレクトリに移動
cd /home/aicompany/ai_co

# バックアップディレクトリ
BACKUP_DIR="/home/aicompany/ai_co/backups/phase_d_backup_20250710_152645"

echo "📋 Phase 1: バックアップからの復旧"
echo "Elder Tree 統合ファイルをバックアップから復旧中..."

# Elder Tree 階層システムの復旧
if [ -f "$BACKUP_DIR/libs/elder_tree_hierarchy.py" ]; then
    cp "$BACKUP_DIR/libs/elder_tree_hierarchy.py" libs/elder_tree_hierarchy.py
    echo "✅ elder_tree_hierarchy.py 復旧完了"
fi

# Four Sages 統合システムの復旧
if [ -f "$BACKUP_DIR/libs/four_sages_integration.py" ]; then
    cp "$BACKUP_DIR/libs/four_sages_integration.py" libs/four_sages_integration.py
    echo "✅ four_sages_integration.py 復旧完了"
fi

# 他のElderライブラリの復旧
for elder_lib in "$BACKUP_DIR"/libs/elder_*.py; do
    if [ -f "$elder_lib" ]; then
        filename=$(basename "$elder_lib")
        cp "$elder_lib" "libs/$filename"
        echo "✅ $filename 復旧完了"
    fi
done

echo "📋 Phase 2: ワーカーファイルの復旧"
echo "Elder Tree 統合済みワーカーファイルを復旧中..."

# ワーカーファイルの復旧
for worker_file in "$BACKUP_DIR"/workers/*.py; do
    if [ -f "$worker_file" ]; then
        filename=$(basename "$worker_file")
        cp "$worker_file" "workers/$filename"
        echo "✅ $filename 復旧完了"
    fi
done

echo "📋 Phase 3: 設定ファイルの復旧"
echo "Elder Tree 関連設定を復旧中..."

# 設定ファイルの復旧
if [ -f "$BACKUP_DIR/config/system.json" ]; then
    cp "$BACKUP_DIR/config/system.json" config/system.json
    echo "✅ system.json 復旧完了"
fi

echo "📋 Phase 4: Elder Tree 統合の有効化"
echo "Elder Tree 統合フラグを有効化中..."

# ELDER_TREE_AVAILABLEフラグの有効化
find workers/ -name "*.py" -exec sed -i 's/ELDER_TREE_AVAILABLE = False/ELDER_TREE_AVAILABLE = True/g' {} \;

# Four Sages統合の有効化
if [ -f "libs/four_sages_integration.py" ]; then
    sed -i 's/ELDER_TREE_AVAILABLE = False/ELDER_TREE_AVAILABLE = True/g' libs/four_sages_integration.py
    echo "✅ Four Sages 統合有効化完了"
fi

echo "📋 Phase 5: Elder Tree 参照の有効化"
echo "ワーカー内の Elder Tree 参照を有効化中..."

# ワーカー内の Elder Tree 参照を有効化
find workers/ -name "*.py" -exec sed -i 's/self\.elder_tree = None/self.elder_tree = get_elder_tree()/g' {} \;

echo "✅ ワーカー Elder Tree 参照有効化完了"

echo "📋 Phase 6: 有効化状況の確認"
echo "Elder Tree 有効化状況を確認中..."

# 有効化状況の確認
echo "ELDER_TREE_AVAILABLE フラグ確認:"
grep -r "ELDER_TREE_AVAILABLE = True" . | head -5

echo "Elder Tree 参照確認:"
grep -r "self\.elder_tree = get_elder_tree()" workers/ | head -5

echo "📋 Phase 7: 統合システム動作確認"
echo "Elder Tree 統合システムの動作確認中..."

# Python 構文チェック
echo "Python 構文チェック:"
python -c "import workers.pm_worker; print('✅ pm_worker 正常')"
python -c "import libs.elder_tree_hierarchy; print('✅ elder_tree_hierarchy 正常')"
python -c "import libs.four_sages_integration; print('✅ four_sages_integration 正常')"

# Elder Tree 機能確認
echo "Elder Tree 機能確認:"
python -c "from libs.elder_tree_hierarchy import get_elder_tree; print('✅ get_elder_tree 正常')"
python -c "from libs.four_sages_integration import FourSagesIntegration; print('✅ FourSagesIntegration 正常')"

echo "🎯 Elder Tree 有効化完了"
echo "=========================================="
echo "📊 有効化結果サマリー:"
echo "- Worker ファイル: $(find workers/ -name '*.py' | wc -l) 個処理"
echo "- Elder Tree 階層: 有効化済み"
echo "- Four Sages 統合: 有効化済み"
echo "- 設定ファイル: 復旧済み"
echo "- 構文チェック: 正常"
echo "- 機能確認: 正常"
echo "=========================================="
echo "✅ Grand Elder maru 安全第一原則準拠完了"
echo "実行完了時刻: $(date)"

# 有効化完了ログ
echo "$(date): Elder Tree 有効化完了" >> /var/log/ai-company/elder_tree_enable.log

echo "🛡️ Elder Tree 有効化スクリプト実行完了"
echo "⚠️  注意: システム再起動を推奨します"
echo "   実行コマンド: ai-restart"