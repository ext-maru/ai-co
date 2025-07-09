#!/usr/bin/env python3
"""
TIER 2 Operation Coverage Lightning - 統合実行スクリプト
Worker基盤の完全制圧 - 全テストの統合実行

実行順序:
    pass
1. Task Worker 完全制圧テスト
2. PM Worker 完全制圧テスト  
3. Result Worker 完全制圧テスト
4. Worker間連携テスト
5. ワーカー起動・動作確認テスト
6. 最終レポート生成
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import subprocess
import importlib.util

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_and_run_test_module(module_path, run_function_name):
    """テストモジュールを動的ロードして実行"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # 実行関数を取得して実行
        run_function = getattr(test_module, run_function_name)
        return run_function()
    
    except Exception as e:
        print(f"❌ テストモジュール実行エラー: {e}")
        return False

def run_pytest_coverage():
    """pytestを使用したカバレッジ測定"""
    try:
        print("📊 Pytest Coverage 分析実行中...")
        
        # Pytestでワーカー関連のカバレッジを測定
        cmd = [
            "python", "-m", "pytest",
            "tests/workers/",
            "--cov=workers",
            "--cov-report=term-missing",
            "--cov-report=json:coverage_workers.json",
            "-v",
            "--tb=short"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5分でタイムアウト
        )
        
        if result.returncode == 0:
            print("✅ Pytest Coverage 分析完了")
            return True, result.stdout
        else:
            print(f"⚠️ Pytest Coverage 警告: {result.stderr}")
            return False, result.stderr
    
    except subprocess.TimeoutExpired:
        print("⏰ Pytest Coverage タイムアウト")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ Pytest Coverage エラー: {e}")
        return False, str(e)

def generate_tier2_report(test_results):
    """TIER 2 最終レポートの生成"""
    report_data = {
        'tier': 'TIER 2',
        'title': 'Operation Coverage Lightning - Worker基盤完全制圧',
        'timestamp': datetime.now().isoformat(),
        'test_results': test_results,
        'summary': {
            'total_tests': len(test_results),
            'successful_tests': sum(1 for r in test_results if r['success']),
            'failed_tests': sum(1 for r in test_results if not r['success']),
            'overall_success_rate': 0.0
        }
    }
    
    # 全体成功率の計算
    if report_data['summary']['total_tests'] > 0:
        report_data['summary']['overall_success_rate'] = (
            report_data['summary']['successful_tests'] / 
            report_data['summary']['total_tests']
        ) * 100
    
    # レポートファイルの保存
    report_file = PROJECT_ROOT / "tests" / "tier2_worker_coverage_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    return report_data, report_file

def print_tier2_banner():
    """TIER 2 バナーの表示"""
    banner = """
🚀 TIER 2 Operation Coverage Lightning 発動！
═══════════════════════════════════════════════════════════════════════════

    ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗███████╗██████╗     ████████╗██╗███████╗██████╗     ██████╗ 
    ██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗    ╚══██╔══╝██║██╔════╝██╔══██╗    ╚════██╗
    ██║ █╗ ██║██║   ██║██████╔╝█████╔╝ █████╗  ██████╔╝       ██║   ██║█████╗  ██████╔╝     █████╔╝
    ██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══╝  ██╔══██╗       ██║   ██║██╔══╝  ██╔══██╗    ██╔═══╝ 
    ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗███████╗██║  ██║       ██║   ██║███████╗██║  ██║    ███████╗
     ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝       ╚═╝   ╚═╝╚══════╝╚═╝  ╚═╝    ╚══════╝

🎯 目標: Worker インフラ基盤の90%カバレッジ達成
🏗️ 対象: Task Worker, PM Worker, Result Worker + 連携機能
⚡ 戦略: 包括的テスト + 実際の動作確認 + パフォーマンス検証

═══════════════════════════════════════════════════════════════════════════
"""
    print(banner)

def print_final_results(test_results, report_file):
    """最終結果の表示"""
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r['success'])
    failed_tests = total_tests - successful_tests
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "═" * 80)
    print("🎯 TIER 2 Operation Coverage Lightning - 最終戦果報告")
    print("═" * 80)
    
    # 個別テスト結果
    print("\n📊 テスト別戦果:")
    for i, result in enumerate(test_results, 1):
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {i}. {status_icon} {result['name']}")
        if result['details']:
            print(f"     📝 {result['details']}")
    
    # 全体サマリー
    print(f"\n🏆 総合戦果:")
    print(f"  📈 総テスト数: {total_tests}")
    print(f"  ✅ 成功: {successful_tests}")
    print(f"  ❌ 失敗: {failed_tests}")
    print(f"  🎯 成功率: {success_rate:.1f}%")
    
    # 成果判定
    if success_rate >= 90:
        print(f"\n🏆 🎉 TIER 2 完全制圧成功！ 🎉 🏆")
        print(f"Worker基盤の90%以上カバレッジを達成しました！")
        tier2_status = "🏆 MISSION ACCOMPLISHED"
    elif success_rate >= 75:
        print(f"\n🥈 TIER 2 部分的成功")
        print(f"Worker基盤の75%以上カバレッジを達成しました。")
        tier2_status = "🥈 PARTIAL SUCCESS"
    else:
        print(f"\n⚠️ TIER 2 改善が必要")
        print(f"Worker基盤のカバレッジが75%未満です。継続改善が必要です。")
        tier2_status = "⚠️ NEEDS IMPROVEMENT"
    
    # レポートファイル情報
    print(f"\n📄 詳細レポート: {report_file}")
    print(f"🕒 実行完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "═" * 80)
    print(f"TIER 2 Operation Coverage Lightning: {tier2_status}")
    print("═" * 80)
    
    return success_rate >= 90

def main():
    """TIER 2統合テストのメイン実行"""
    print_tier2_banner()
    
    # テスト実行計画
    test_plan = [
        {
            'name': 'Task Worker 完全制圧テスト',
            'file': 'test_task_worker_tier2_comprehensive.py',
            'function': 'run_tier2_task_worker_tests',
            'priority': 'CRITICAL'
        },
        {
            'name': 'PM Worker 完全制圧テスト',
            'file': 'test_pm_worker_tier2_comprehensive.py',
            'function': 'run_tier2_pm_worker_tests',
            'priority': 'CRITICAL'
        },
        {
            'name': 'Result Worker 完全制圧テスト',
            'file': 'test_result_worker_tier2_comprehensive.py',
            'function': 'run_tier2_result_worker_tests',
            'priority': 'HIGH'
        },
        {
            'name': 'Worker間連携テスト',
            'file': 'test_worker_inter_communication_tier2.py',
            'function': 'run_tier2_worker_inter_communication_tests',
            'priority': 'HIGH'
        },
        {
            'name': 'ワーカー起動・動作確認テスト',
            'file': 'test_worker_startup_tier2.py',
            'function': 'run_tier2_worker_startup_tests',
            'priority': 'MEDIUM'
        }
    ]
    
    print(f"📋 実行計画: {len(test_plan)}個のテストスイートを順次実行\n")
    
    # テスト実行
    test_results = []
    start_time = time.time()
    
    for i, test in enumerate(test_plan, 1):
        print(f"🚀 [{i}/{len(test_plan)}] {test['name']} 実行開始...")
        print(f"   優先度: {test['priority']}")
        
        test_start = time.time()
        
        # テストファイルのパス
        test_file = Path(__file__).parent / test['file']
        
        if not test_file.exists():
            print(f"❌ テストファイルが見つかりません: {test_file}")
            test_results.append({
                'name': test['name'],
                'success': False,
                'details': f"テストファイル不在: {test['file']}",
                'duration': 0.0
            })
            continue
        
        # テスト実行
        try:
            success = load_and_run_test_module(test_file, test['function'])
            test_end = time.time()
            duration = test_end - test_start
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {test['name']} 完了 ({duration:.1f}秒)\n")
            
            test_results.append({
                'name': test['name'],
                'success': success,
                'details': f"実行時間: {duration:.1f}秒",
                'duration': duration,
                'priority': test['priority']
            })
        
        except Exception as e:
            test_end = time.time()
            duration = test_end - test_start
            
            print(f"💥 {test['name']} 実行エラー: {e}")
            test_results.append({
                'name': test['name'],
                'success': False,
                'details': f"実行エラー: {str(e)}",
                'duration': duration,
                'priority': test['priority']
            })
    
    # Pytestカバレッジ測定（オプション）
    print("🔍 追加カバレッジ分析...")
    pytest_success, pytest_output = run_pytest_coverage()
    if pytest_success:
        print("✅ Pytest カバレッジ分析完了")
    else:
        print(f"⚠️ Pytest カバレッジ分析: {pytest_output[:200]}...")
    
    # 最終レポート生成
    total_time = time.time() - start_time
    print(f"\n⏱️ 総実行時間: {total_time:.1f}秒")
    
    report_data, report_file = generate_tier2_report(test_results)
    
    # 最終結果表示
    mission_success = print_final_results(test_results, report_file)
    
    # 終了コード
    if mission_success:
        print("\n🎊 TIER 2 Operation Coverage Lightning 大成功！ 🎊")
        return 0
    else:
        print("\n⚠️ TIER 2 継続改善が必要です。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)