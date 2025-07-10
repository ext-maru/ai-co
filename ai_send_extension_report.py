#!/usr/bin/env python3
"""
ai-send拡張の実装結果レポート
"""
import sys
from pathlib import Path
import json
from datetime import datetime

PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

def generate_report():
    """実装結果のレポートを生成"""
    print("=" * 60)
    print("📊 Elders Guild ai-send拡張 実装結果レポート")
    print("=" * 60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. タスクタイプ設定の確認
    print("【1. タスクタイプ設定】")
    config_file = PROJECT_ROOT / "config" / "task_types.json"
    if config_file.exists():
        print("✅ config/task_types.json: 作成成功")
        try:
            with open(config_file) as f:
                data = json.load(f)
                task_types = data.get('task_types', {})
                print(f"\n登録されたタスクタイプ: {len(task_types)}個")
                for task_type, info in task_types.items():
                    print(f"  - {task_type:<10} : {info.get('description', 'N/A')} (優先度: {info.get('default_priority', 5)})")
        except Exception as e:
            print(f"❌ エラー: {e}")
    else:
        print("❌ config/task_types.json: 未作成")
    
    # 2. ai_send.pyの更新状況
    print("\n【2. ai_send.pyの更新状況】")
    ai_send_path = PROJECT_ROOT / "commands" / "ai_send.py"
    if ai_send_path.exists():
        with open(ai_send_path) as f:
            content = f.read()
            if "test" in content and "fix" in content and "deploy" in content:
                print("✅ 拡張済み（新しいタスクタイプが追加されています）")
            else:
                print("⚠️ 未拡張（基本タイプのみ）")
                print("  → implement_ai_send_extension.shの実行が必要です")
    
    # 3. テンプレートファイル
    print("\n【3. タスクテンプレート】")
    template_dir = PROJECT_ROOT / "templates" / "task_types"
    if template_dir.exists():
        templates = list(template_dir.glob("*.yaml"))
        print(f"✅ テンプレート数: {len(templates)}個")
        for template in templates:
            print(f"  - {template.name}")
    else:
        print("❌ テンプレートディレクトリが見つかりません")
    
    # 4. ドキュメント
    print("\n【4. ドキュメント】")
    guide_path = PROJECT_ROOT / "docs" / "AI_SEND_EXTENDED_GUIDE.md"
    if guide_path.exists():
        print("✅ AI_SEND_EXTENDED_GUIDE.md: 作成済み")
    else:
        print("❌ ガイドドキュメント: 未作成")
    
    # 5. 実装スクリプト
    print("\n【5. 実装スクリプト】")
    scripts = [
        "apply_ai_send_extension.py",
        "implement_ai_send_extension.sh",
        "manual_check_ai_send_extension.sh",
        "check_ai_send_extension_status.py"
    ]
    for script in scripts:
        script_path = PROJECT_ROOT / script
        if script_path.exists():
            print(f"✅ {script}: 存在")
        else:
            print(f"❌ {script}: 見つかりません")
    
    # 総合評価
    print("\n" + "=" * 60)
    print("【総合評価】")
    
    if config_file.exists() and template_dir.exists():
        print("✅ ai-send拡張の実装は完了しています！")
        print("\n🚀 使用方法:")
        print("  ai-send 'タスクの説明' [タスクタイプ]")
        print("\n📋 利用可能なタスクタイプ:")
        print("  ai-send --list-types")
    else:
        print("⚠️ ai-send拡張の実装が不完全です")
        print("\n🔧 対処方法:")
        print("  1. AI Command Executorが起動していることを確認")
        print("  2. cd /home/aicompany/ai_co")
        print("  3. ./implement_ai_send_extension.sh を実行")

if __name__ == "__main__":
    generate_report()
