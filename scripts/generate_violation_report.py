#!/usr/bin/env python3
"""
Elder Flow Violation Report Generator
違反レポートのみを生成（対話なし）
"""

import asyncio
import sys
sys.path.append('/home/aicompany/ai_co')

from libs.elder_flow_violation_resolver import ElderFlowViolationResolver


async def main():
    """レポート生成のみ実行"""
    resolver = ElderFlowViolationResolver()

    print("🔍 Elder Flow違反分析中...")
    violations = await resolver.analyze_violations()

    print(f"\n📊 違反サマリー:")
    print(f"- 総違反数: {violations['summary']['total']}件")
    print(f"- Critical違反: {violations['summary']['critical']}件")
    print(f"- 未解決違反: {violations['summary']['open']}件")
    print(f"\n違反タイプ別:")
    print(f"- 抽象メソッド違反: {violations['summary']['types']['abstract_methods']}件")
    print(f"- アイデンティティ違反: {violations['summary']['types']['identity']}件")
    print(f"- 品質ゲート違反: {violations['summary']['types']['quality_gates']}件")

    # レポート生成
    print("\n📄 詳細レポート生成中...")
    report = await resolver.generate_violation_report()

    # レポート保存
    from datetime import datetime
    from pathlib import Path

    report_path = f"knowledge_base/elder_flow_reports/violation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"✅ レポート生成完了: {report_path}")

    # greeting_system違反の確認
    greeting_violations = 0
    for v in violations.get("identity", []):
        if isinstance(v, dict) and v.get("file") == "greeting_system":
            greeting_violations += 1

    if greeting_violations == 0:
        print("\n🎉 greeting_system関連の違反は完全に削除されました！")
    else:
        print(f"\n⚠️ まだ{greeting_violations}件のgreeting_system違反が残っています")


if __name__ == "__main__":
    asyncio.run(main())
