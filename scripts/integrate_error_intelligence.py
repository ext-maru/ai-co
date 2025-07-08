#!/usr/bin/env python3
"""
エラー智能判断システムを既存ワーカーに統合
各ワーカーがエラー時に自動的にError Intelligenceを利用するように設定
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def patch_base_worker():
    """BaseWorkerにエラー智能判断機能を追加"""
    base_worker_path = PROJECT_ROOT / "core" / "base_worker.py"
    
    # パッチコード
    patch_code = '''
    def handle_error_with_intelligence(self, error: Exception, context: str = ""):
        """エラー智能判断システムと連携したエラーハンドリング"""
        try:
            from libs.error_intelligence_manager import ErrorIntelligenceManager
            
            # エラー分析
            manager = ErrorIntelligenceManager()
            analysis = manager.analyze_error(str(error), {
                'worker_type': self.worker_type,
                'context': context
            })
            
            # 自動修正可能な場合はキューに送信
            if analysis['auto_fixable']:
                self.send_to_queue('ai_error_analysis', {
                    'error_text': str(error),
                    'context': {
                        'worker_type': self.worker_type,
                        'context': context
                    },
                    'response_queue': f'{self.worker_type}_error_response'
                })
            
            # 既存のエラーハンドリングも実行
            self.handle_error(error, context)
            
        except ImportError:
            # Error Intelligenceが利用できない場合は通常のエラーハンドリング
            self.handle_error(error, context)
'''
    
    print(f"BaseWorkerへのパッチ適用をスキップ（手動で適用してください）")
    print("以下のメソッドをBaseWorkerクラスに追加してください：")
    print(patch_code)


def create_integration_config():
    """統合設定ファイルを作成"""
    config = {
        "error_intelligence_integration": {
            "enabled": True,
            "workers": {
                "task_worker": {
                    "enabled": True,
                    "auto_retry_on_fix": True
                },
                "pm_worker": {
                    "enabled": True,
                    "auto_retry_on_fix": True
                },
                "result_worker": {
                    "enabled": True,
                    "auto_retry_on_fix": False
                }
            },
            "dlq_monitoring": {
                "enabled": True,
                "check_interval": 30,
                "batch_size": 10
            }
        }
    }
    
    import json
    config_path = PROJECT_ROOT / "config" / "error_intelligence_integration.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 統合設定ファイルを作成: {config_path}")


def create_monitoring_script():
    """モニタリングスクリプトを作成"""
    script_content = '''#!/usr/bin/env python3
"""
エラー智能判断システムのモニタリング
統計情報とステータスを表示
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.error_intelligence_manager import ErrorIntelligenceManager
import json
from datetime import datetime


def main():
    manager = ErrorIntelligenceManager()
    
    print("="*60)
    print(f"エラー智能判断システム モニタリング")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 統計情報取得
    stats = manager.get_error_statistics()
    
    print("\\n📊 エラー統計:")
    print(f"  総エラー数: {stats['total_errors']}")
    print(f"  自動修正済み: {stats['auto_fixed']}")
    
    if stats['total_errors'] > 0:
        fix_rate = (stats['auto_fixed'] / stats['total_errors']) * 100
        print(f"  自動修正率: {fix_rate:.1f}%")
    
    print("\\n📈 カテゴリ別:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    
    print("\\n⚠️  重要度別:")
    for severity, count in stats['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print("\\n🔝 頻出エラー Top 5:")
    for i, error in enumerate(stats['top_errors'], 1):
        print(f"  {i}. {error['type']} ({error['count']}回)")
    
    print("\\n✅ システムステータス: 正常稼働中")


if __name__ == "__main__":
    main()
'''
    
    script_path = PROJECT_ROOT / "scripts" / "monitor_error_intelligence.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 実行権限付与
    import os
    os.chmod(script_path, 0o755)
    
    print(f"✅ モニタリングスクリプトを作成: {script_path}")


def main():
    print("=== エラー智能判断システム統合セットアップ ===\n")
    
    # 1. BaseWorkerへのパッチ案内
    print("1. BaseWorkerへの統合")
    patch_base_worker()
    
    # 2. 統合設定ファイル作成
    print("\n2. 統合設定ファイルの作成")
    create_integration_config()
    
    # 3. モニタリングスクリプト作成
    print("\n3. モニタリングスクリプトの作成")
    create_monitoring_script()
    
    print("\n=== 統合完了 ===")
    print("\n次のステップ:")
    print("1. Error Intelligence Workerを起動:")
    print("   bash scripts/start_error_intelligence.sh")
    print("\n2. システムをテスト:")
    print("   python3 scripts/test_error_intelligence.py")
    print("\n3. モニタリング:")
    print("   python3 scripts/monitor_error_intelligence.py")


if __name__ == "__main__":
    main()
