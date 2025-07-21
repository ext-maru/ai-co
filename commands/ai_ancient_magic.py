#!/usr/bin/env python3
"""
🏛️ Ancient Magic CLI Command
エンシェントエルダーの6つの古代魔法を実行するCLIコマンド
"""

import asyncio
import sys
from pathlib import Path
import click
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder.audit_engine import AncientElderAuditEngine
from libs.ancient_elder.integrity_auditor import AncientElderIntegrityAuditor
from libs.ancient_elder.tdd_guardian import TDDGuardian
from libs.ancient_elder.flow_compliance_auditor import FlowComplianceAuditor
from libs.ancient_elder.four_sages_overseer import FourSagesOverseer
from libs.ancient_elder.git_chronicle import GitChronicle
from libs.ancient_elder.servant_inspector import ServantInspector

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
def cli():
    """🏛️ Ancient Magic System - エンシェントエルダーの6つの古代魔法"""
    pass


@cli.command()
@click.option('--target', default='.', help='監査対象のパス')
@click.option('--comprehensive', is_flag=True, help='包括的監査を実行')
@click.option('--output', type=click.Path(), help='結果の出力ファイル')
async def audit(target: str, comprehensive: bool, output: Optional[str]):
    """🔍 古代魔法による監査を実行"""
    try:
        click.echo("🏛️ Ancient Elder Audit System starting...")
        
        # 監査エンジンを初期化
        engine = AncientElderAuditEngine()
        
        # 全ての古代魔法監査者を登録
        auditors = {
            "integrity": AncientElderIntegrityAuditor(),
            "tdd_guardian": TDDGuardian(),
            "flow_compliance": FlowComplianceAuditor(),
            "four_sages": FourSagesOverseer(),
            "git_chronicle": GitChronicle(),
            "servant_inspector": ServantInspector()
        }
        
        for key, auditor in auditors.items():
            engine.register_auditor(key, auditor)
            
        # 監査ターゲットを設定
        audit_target = {
            "type": "project",
            "path": str(Path(target).resolve()),
            "comprehensive": comprehensive
        }
        
        # 監査を実行
        click.echo(f"\n📋 Auditing target: {audit_target['path']}")
        result = await engine.run_comprehensive_audit(audit_target)
        
        # 結果を表示
        _display_audit_results(result)
        
        # ファイルに出力（指定された場合）
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {output}")
            
    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('magic_type', type=click.Choice([
    'integrity', 'tdd', 'flow', 'sages', 'git', 'servant'
]))
@click.option('--target', default='.', help='監査対象のパス')
async def single(magic_type: str, target: str):
    """🎯 特定の古代魔法を実行"""
    try:
        # 魔法タイプに応じた監査者を選択
        auditor_map = {
            'integrity': AncientElderIntegrityAuditor(),
            'tdd': TDDGuardian(),
            'flow': FlowComplianceAuditor(),
            'sages': FourSagesOverseer(),
            'git': GitChronicle(),
            'servant': ServantInspector()
        }
        
        auditor = auditor_map[magic_type]
        click.echo(f"🔮 Executing {auditor.name}...")
        
        # 監査を実行
        audit_target = {
            "type": "project",
            "path": str(Path(target).resolve())
        }
        
        result = await auditor.audit(audit_target)
        
        # 結果を表示
        click.echo(f"\n📊 {auditor.name} Results:")
        click.echo(f"Total violations: {len(result.violations)}")
        
        # 違反を重要度別に表示
        for violation in sorted(result.violations, 
                              key=lambda v: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].index(v.get('severity', 'LOW')),
                              reverse=True):
            severity = violation.get('severity', 'UNKNOWN')
            emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '📋', 'LOW': '💡'}.get(severity, '❓')
            click.echo(f"\n{emoji} [{severity}] {violation.get('title', 'Untitled')}")
            click.echo(f"   {violation.get('description', 'No description')}")
            if violation.get('location'):
                click.echo(f"   📍 Location: {violation['location']}")
            if violation.get('suggested_fix'):
                click.echo(f"   💡 Fix: {violation['suggested_fix']}")
                
    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def list():
    """📜 利用可能な古代魔法を一覧表示"""
    magics = [
        ("🛡️ Integrity Auditor", "誠実性・Iron Will遵守監査"),
        ("🔴🟢🔵 TDD Guardian", "TDDサイクル遵守監査"),
        ("🌊 Flow Compliance", "Elder Flow実行遵守監査"),
        ("🧙‍♂️ Four Sages Overseer", "4賢者協調監査"),
        ("📚 Git Chronicle", "Git履歴品質監査"),
        ("🤖 Servant Inspector", "エルダーサーバント監査")
    ]
    
    click.echo("🏛️ Ancient Elder's 6 Magic Systems:\n")
    for name, desc in magics:
        click.echo(f"  {name}")
        click.echo(f"    └─ {desc}\n")


@cli.command()
@click.option('--days', default=7, help='分析期間（日数）')
async def health(days: int):
    """💚 エルダーズギルドの健康状態を診断"""
    try:
        click.echo("🏥 Diagnosing Elders Guild health...")
        
        # 監査エンジンを初期化
        engine = AncientElderAuditEngine()
        
        # 簡易監査を実行
        audit_target = {
            "type": "project",
            "path": str(Path.cwd()),
            "time_window_days": days
        }
        
        # Integrity Auditorのみで健康診断
        auditor = AncientElderIntegrityAuditor()
        engine.register_auditor("integrity", auditor)
        
        result = await engine.run_comprehensive_audit(audit_target)
        
        # 健康スコアを表示
        health_score = result.get('guild_health_score', 0)
        
        if health_score >= 90:
            status = "🟢 Excellent"
            emoji = "🎉"
        elif health_score >= 70:
            status = "🟡 Good"
            emoji = "👍"
        elif health_score >= 50:
            status = "🟠 Fair"
            emoji = "⚠️"
        else:
            status = "🔴 Poor"
            emoji = "🚨"
            
        click.echo(f"\n{emoji} Guild Health Score: {health_score:.1f}/100 - {status}")
        
        # 詳細統計
        stats = result.get('statistics', {})
        if stats:
            click.echo("\n📊 Statistics:")
            for key, value in stats.items():
                click.echo(f"  {key}: {value}")
                
    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        sys.exit(1)


def _display_audit_results(result: Dict[str, Any]):
    """監査結果を表示"""
    click.echo("\n" + "="*60)
    click.echo("🏛️ ANCIENT ELDER COMPREHENSIVE AUDIT RESULTS")
    click.echo("="*60)
    
    # 全体スコア
    health_score = result.get('guild_health_score', 0)
    if health_score >= 90:
        score_color = 'green'
    elif health_score >= 70:
        score_color = 'yellow'
    else:
        score_color = 'red'
        
    click.echo(f"\n🎯 Guild Health Score: ", nl=False)
    click.secho(f"{health_score:.1f}/100", fg=score_color, bold=True)
    
    # 実行時間
    execution_time = result.get('execution_time', 0)
    click.echo(f"⏱️  Execution Time: {execution_time:.2f}s")
    
    # 違反サマリー
    violations = result.get('all_violations', [])
    if violations:
        click.echo(f"\n⚠️  Total Violations: {len(violations)}")
        
        # 重要度別カウント
        severity_counts = {}
        for v in violations:
            severity = v.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in severity_counts:
                emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '📋', 'LOW': '💡'}[severity]
                click.echo(f"  {emoji} {severity}: {severity_counts[severity]}")
    else:
        click.echo("\n✅ No violations found!")
        
    # 個別監査結果
    individual_results = result.get('individual_results', {})
    if individual_results:
        click.echo("\n📋 Individual Audit Results:")
        for auditor, audit_result in individual_results.items():
            violations_count = len(audit_result.get('violations', []))
            status = "✅" if violations_count == 0 else "⚠️"
            click.echo(f"  {status} {auditor}: {violations_count} violations")
            
    # 推奨事項
    recommendations = result.get('recommendations', [])
    if recommendations:
        click.echo("\n💡 Recommendations:")
        for rec in recommendations[:5]:  # 上位5件のみ表示
            click.echo(f"  • {rec}")


def main():
    """メインエントリーポイント"""
    # 非同期コマンドを同期的に実行
    def run_async(func):
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))
        return wrapper
    
    # 非同期コマンドをラップ
    cli.command('audit')(run_async(audit))
    cli.command('single')(run_async(single))
    cli.command('health')(run_async(health))
    
    cli()


if __name__ == '__main__':
    main()