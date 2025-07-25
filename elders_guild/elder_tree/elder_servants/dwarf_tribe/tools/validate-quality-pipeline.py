#!/usr/bin/env python3
"""
🎯 Quality Pipeline エンドツーエンド検証スクリプト
3サーバントによる品質パイプラインの完全動作検証
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.quality.quality_pipeline_orchestrator import QualityPipelineOrchestrator

console = Console()

class QualityPipelineValidator:
    """品質パイプライン検証クラス"""
    
    def __init__(self):
        self.orchestrator = QualityPipelineOrchestrator()
        self.test_results = []
        
    async def check_servant_health(self) -> dict:
        """サーバントのヘルスチェック"""
        console.print("\n[bold cyan]🏥 サーバントヘルスチェック開始...[/bold cyan]")
        
        health_status = {
            "quality-watcher": False,
            "test-forge": False,
            "comprehensive-guardian": False
        }
        
        async with httpx.AsyncClient() as client:
            for servant_name, port in [
                ("quality-watcher", 8810),
                ("test-forge", 8811),
                ("comprehensive-guardian", 8812)
            ]:
                try:
                    response = await client.post(
                        f"http://localhost:{port}/a2a",
                        json={
                            "skill": "health_check",
                            "message": {
                                "content": {"text": "{}"},
                                "role": "USER"
                            }
                        },
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        health_data = json.loads(result["content"]["text"])
                        if health_data.get("status") == "healthy":
                            health_status[servant_name] = True
                            console.print(f"✅ {servant_name}: [green]Healthy[/green] (Port {port})")
                        else:
                            console.print(f"⚠️ {servant_name}: [yellow]Unhealthy[/yellow]")
                    else:
                        console.print(f"❌ {servant_name}: [red]HTTP {response.status_code}[/red]")
                        
                except Exception as e:
                    console.print(f"❌ {servant_name}: [red]接続エラー[/red] - {str(e)}")
                    
        return health_status
    
    async def validate_test_case(self, test_path: str, expected_result: str) -> dict:
        """テストケースの検証"""
        console.print(f"\n[bold blue]🧪 テストケース: {test_path}[/bold blue]")
        
        start_time = datetime.now()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("パイプライン実行中...", total=None)
            
            try:
                result = await self.orchestrator.execute_pipeline(test_path)
                duration = (datetime.now() - start_time).total_seconds()
                
                # 結果をテーブル形式で表示
                self._display_result(result, duration)
                
                # 期待結果との比較
                success = result.get("overall_status") == expected_result
                
                return {
                    "test_path": test_path,
                    "expected": expected_result,
                    "actual": result.get("overall_status"),
                    "success": success,
                    "duration": duration,
                    "details": result
                }
                
            except Exception as e:
                console.print(f"[red]❌ エラー発生: {str(e)}[/red]")
                return {
                    "test_path": test_path,
                    "expected": expected_result,
                    "actual": "ERROR",
                    "success": False,
                    "error": str(e)
                }
    
    def _display_result(self, result: dict, duration: float):
        """結果の表示"""
        # 全体ステータス
        status_color = "green" if result.get("success") else "red"
        console.print(f"\n📊 全体ステータス: [{status_color}]{result.get('overall_status')}[/{status_color}]")
        console.print(f"⏱️ 実行時間: {duration:.2f}秒")
        
        # 各ブロックの結果
        if "blocks" in result:
            table = Table(title="ブロック別結果")
            table.add_column("ブロック", style="cyan", width=12)
            table.add_column("サーバント", style="magenta")
            table.add_column("判定", style="green")
            table.add_column("スコア", justify="right")
            table.add_column("認定", style="yellow")
            
            for block_id, block_data in result["blocks"].items():
                verdict = block_data.get("verdict", "N/A")
                verdict_color = "green" if verdict == "APPROVED" else "red"
                
                table.add_row(
                    f"Block {block_id}",
                    block_data.get("servant", "N/A"),
                    f"[{verdict_color}]{verdict}[/{verdict_color}]",
                    str(block_data.get("quality_score", block_data.get("coverage", block_data.get("overall_score", "N/A")))),
                    block_data.get("certification", "N/A")
                )
            
            console.print(table)
        
        # 品質証明書
        if "quality_certificate" in result:
            cert = result["quality_certificate"]
            cert_panel = Panel(
                f"""[bold]🏆 品質証明書[/bold]
                
証明書ID: {cert.get('certificate_id', 'N/A')}
全体グレード: [bold yellow]{cert.get('overall_grade', 'N/A')}[/bold yellow]
発行者: {cert.get('issuer', 'N/A')}
有効期限: {cert.get('valid_until', 'N/A')}""",
                title="品質認定",
                border_style="green"
            )
            console.print(cert_panel)
    
    async def run_validation(self):
        """検証実行"""
        console.print("[bold green]🚀 Quality Pipeline エンドツーエンド検証開始[/bold green]")
        console.print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. ヘルスチェック
        health_status = await self.check_servant_health()
        
        # すべてのサーバントが健全でない場合は警告
        if not all(health_status.values()):
            console.print("\n[bold yellow]⚠️ 警告: 一部のサーバントが起動していません[/bold yellow]")
            console.print("以下のコマンドでサーバントを起動してください:")
            console.print("[cyan]./scripts/start-quality-servants.sh[/cyan]")
            
            # モックモードで続行するか確認
            console.print("\n[yellow]モックモードで続行しますか？ (実際のサーバントは使用されません)[/yellow]")
            return
        
        # 2. テストケース実行
        test_cases = [
            {
                "path": "/home/aicompany/ai_co/libs/quality/servants/quality_watcher_servant.py",
                "expected": "APPROVED",
                "description": "高品質コード（QualityWatcherサーバント自身）"
            },
            {
                "path": "/home/aicompany/ai_co/tests/unit/test_sample.py",
                "expected": "APPROVED",
                "description": "標準的なテストファイル"
            },
            {
                "path": "/home/aicompany/ai_co/libs/quality",
                "expected": "APPROVED",
                "description": "品質ライブラリディレクトリ全体"
            }
        ]
        
        for test_case in test_cases:
            result = await self.validate_test_case(
                test_case["path"],
                test_case["expected"]
            )
            self.test_results.append(result)
        
        # 3. 最終レポート
        self._generate_final_report()
    
    def _generate_final_report(self):
        """最終レポート生成"""
        console.print("\n[bold cyan]📊 === 最終検証レポート ===[/bold cyan]")
        
        # サマリーテーブル
        summary_table = Table(title="検証結果サマリー")
        summary_table.add_column("テストケース", style="cyan")
        summary_table.add_column("期待結果", style="yellow")
        summary_table.add_column("実際の結果", style="magenta")
        summary_table.add_column("判定", style="green")
        summary_table.add_column("実行時間", justify="right")
        
        success_count = 0
        total_duration = 0
        
        for result in self.test_results:
            success = result["success"]
            success_count += success
            duration = result.get("duration", 0)
            total_duration += duration
            
            summary_table.add_row(
                Path(result["test_path"]).name,
                result["expected"],
                result["actual"],
                "[green]✅ PASS[/green]" if success else "[red]❌ FAIL[/red]",
                f"{duration:.2f}s"
            )
        
        console.print(summary_table)
        
        # 統計情報
        total_tests = len(self.test_results)
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        stats_panel = Panel(
            f"""[bold]検証統計[/bold]
            
総テスト数: {total_tests}
成功: {success_count}
失敗: {total_tests - success_count}
成功率: [{'green' if success_rate >= 80 else 'yellow' if success_rate >= 60 else 'red'}]{success_rate:.1f}%[/]
総実行時間: {total_duration:.2f}秒
平均実行時間: {total_duration/total_tests if total_tests > 0 else 0:.2f}秒""",
            title="統計情報",
            border_style="blue"
        )
        console.print(stats_panel)
        
        # 推奨事項
        if success_rate < 100:
            console.print("\n[bold yellow]💡 推奨事項:[/bold yellow]")
            console.print("- 失敗したテストケースのログを確認してください")
            console.print("- サーバントのエラーログを確認: tail -f logs/quality_servants.log")
            console.print("- python-a2aの接続設定を確認してください")
        else:
            console.print("\n[bold green]🎉 すべてのテストが成功しました！[/bold green]")
            console.print("品質パイプラインは正常に動作しています。")
        
        # レポート保存
        report_path = f"data/validation_reports/quality_pipeline_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "execution_time": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "success_count": success_count,
                    "success_rate": success_rate,
                    "total_duration": total_duration
                },
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n📄 詳細レポート保存: {report_path}")


async def main():
    """メイン関数"""
    validator = QualityPipelineValidator()
    
    try:
        await validator.run_validation()
    except KeyboardInterrupt:
        console.print("\n[yellow]検証を中断しました[/yellow]")
    except Exception as e:
        console.print(f"\n[red]エラーが発生しました: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())