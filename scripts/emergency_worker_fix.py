#!/usr/bin/env python3
"""
緊急ワーカー修正スクリプト - 4賢者会議緊急対策
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def fix_worker_run_calls():
    """worker.run() を worker.start() に一括修正"""
    
    print("🚨 緊急修正開始: worker.run() → worker.start()")
    
    # 修正対象ファイル
    target_files = [
        "workers/todo_worker.py",
        "workers/dialog_task_worker.py", 
        "workers/email_notification_worker.py",
        "workers/enhanced_pm_worker.py",
        "workers/image_pipeline_worker.py",
        "workers/result_worker.py",
        "workers/slack_monitor_worker.py",
        "workers/slack_polling_worker.py",
        "workers/async_enhanced_task_worker.py",
        "workers/async_pm_worker.py",
        "workers/async_result_worker.py",
        "workers/command_executor_worker.py",
        "workers/test_manager_worker.py"
    ]
    
    fixed_count = 0
    
    for file_path in target_files:
        full_path = PROJECT_ROOT / file_path
        
        if not full_path.exists():
            print(f"⚠️ スキップ: {file_path} (ファイルが存在しません)")
            continue
            
        try:
            # ファイル読み込み
            content = full_path.read_text(encoding='utf-8')
            
            # worker.run() → worker.start() 置換
            original_content = content
            content = re.sub(r'worker\.run\(\)', 'worker.start()', content)
            
            # 変更があった場合のみ保存
            if content != original_content:
                full_path.write_text(content, encoding='utf-8')
                print(f"✅ 修正完了: {file_path}")
                fixed_count += 1
            else:
                print(f"📝 変更なし: {file_path}")
                
        except Exception as e:
            print(f"❌ エラー: {file_path} - {e}")
    
    print(f"\n🎯 修正完了: {fixed_count} ファイル")
    return fixed_count

def add_run_method_to_base_worker():
    """BaseWorkerにrun()メソッドを追加（互換性確保）"""
    
    base_worker_file = PROJECT_ROOT / "core/base_worker.py"
    
    if not base_worker_file.exists():
        print("❌ BaseWorkerファイルが見つかりません")
        return False
        
    try:
        content = base_worker_file.read_text(encoding='utf-8')
        
        # run()メソッドが既に存在するかチェック
        if "def run(self):" in content:
            print("📝 BaseWorker.run()は既に存在します")
            return True
            
        # start()メソッドの後にrun()メソッドを追加
        if "def start(self):" in content:
            # start()メソッドの最後にrun()エイリアスを追加
            run_method = '''
    def run(self):
        """start()メソッドのエイリアス（後方互換性のため）"""
        self.logger.warning("⚠️ run()は非推奨です。start()を使用してください。")
        return self.start()'''
            
            # ファイルの最後に追加
            content = content.rstrip() + "\n" + run_method + "\n"
            
            base_worker_file.write_text(content, encoding='utf-8')
            print("✅ BaseWorker.run()メソッド追加完了")
            return True
        else:
            print("❌ BaseWorkerのstart()メソッドが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ BaseWorker修正エラー: {e}")
        return False

def create_unified_startup_script():
    """統一起動スクリプト作成"""
    
    startup_script = PROJECT_ROOT / "scripts/start_worker.sh"
    
    script_content = '''#!/bin/bash
# 🚀 AI Company 統一ワーカー起動スクリプト
# 4賢者システム提供

set -e

# プロジェクトルート設定
PROJECT_ROOT="/home/aicompany/ai_co"
cd "$PROJECT_ROOT"

# Python環境設定
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
source venv/bin/activate

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <worker_script> [worker_args...]"
    echo "例: $0 workers/pm_worker.py --worker-id pm-001"
    exit 1
fi

WORKER_SCRIPT="$1"
shift  # 最初の引数を削除

# ワーカースクリプト存在確認
if [ ! -f "$WORKER_SCRIPT" ]; then
    echo "❌ エラー: $WORKER_SCRIPT が見つかりません"
    exit 1
fi

echo "🚀 ワーカー起動: $WORKER_SCRIPT"
echo "📂 作業ディレクトリ: $(pwd)"
echo "🐍 Python パス: $PYTHONPATH"

# ワーカー実行
python3 "$WORKER_SCRIPT" "$@"
'''
    
    try:
        startup_script.write_text(script_content)
        startup_script.chmod(0o755)
        print("✅ 統一起動スクリプト作成完了: scripts/start_worker.sh")
        return True
    except Exception as e:
        print(f"❌ 起動スクリプト作成エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🧙‍♂️ 4賢者緊急修正システム開始")
    print("="*50)
    
    # 1. worker.run() → worker.start() 修正
    fixed_files = fix_worker_run_calls()
    
    # 2. BaseWorkerにrun()メソッド追加
    base_worker_fixed = add_run_method_to_base_worker()
    
    # 3. 統一起動スクリプト作成
    startup_script_created = create_unified_startup_script()
    
    print("="*50)
    print("🎯 緊急修正完了")
    print(f"📝 修正ファイル数: {fixed_files}")
    print(f"🔧 BaseWorker修正: {'✅' if base_worker_fixed else '❌'}")
    print(f"📜 起動スクリプト: {'✅' if startup_script_created else '❌'}")
    
    if fixed_files > 0 or base_worker_fixed or startup_script_created:
        print("\n🚀 次のステップ:")
        print("1. 修正内容をgitコミット")
        print("2. scripts/start_worker.sh でワーカー起動テスト")
        print("3. tmuxセッションで環境変数設定")
        
        return True
    else:
        print("\n⚠️ 修正が必要な項目が見つかりませんでした")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)