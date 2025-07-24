#!/usr/bin/env python3
"""
Elders Guild ProjectScope Integration
Elders GuildシステムとProjectScopeの統合
"""

import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path("/home/aicompany/ai_co")
sys.path.insert(0, str(PROJECT_ROOT))

# ProjectScopeのインポート
sys.path.insert(0, str(Path.home() / ".local/share/projectscope"))
from projectscope import ProjectScope

from core import EMOJI
from libs.slack_notifier import SlackNotifier


class AICompanyProjectScope:
    """Elders Guild専用のProjectScope拡張"""

    def __init__(self):
        """初期化メソッド"""
        self.project_root = PROJECT_ROOT
        self.ps = ProjectScope(str(self.project_root))
        self.notifier = SlackNotifier()

        # Elders Guild専用の設定を追加
        self.ps.config.update(
            {
                "project_name": "Elders Guild System",
                "custom_components": {
                    "workers": "workers/*_worker.py",
                    "managers": "libs/*_manager.py",
                    "commands": "commands/ai_*.py",
                    "core_modules": "core/*.py",
                },
                "knowledge_base": "knowledge_base/*.md",
                "web_reports": "web/*.html",
            }
        )

    def analyze_with_knowledge(self):
        """ナレッジベースを含めた分析"""
        print(f"{EMOJI['rocket']} Elders Guild ProjectScope Analysis")
        print("━" * 50)

        # 基本分析
        analysis = self.ps.analyze()

        # Elders Guild固有の分析を追加
        analysis["ai_company"] = {
            "workers": self._analyze_workers(),
            "managers": self._analyze_managers(),
            "knowledge_base": self._analyze_knowledge_base(),
            "rabbitmq_queues": self._analyze_queues(),
            "integration_points": self._analyze_integrations(),
        }

        return analysis

    def _analyze_workers(self):
        """ワーカーの詳細分析"""
        workers = {}
        workers_dir = self.project_root / "workers"

        for worker_file in workers_dir.glob("*_worker.py"):
            try:
                content = worker_file.read_text(encoding="utf-8")

                # ワーカータイプを抽出
                import re

                worker_type_match = re.search(
                    r"worker_type\s*=\s*['\"](\w+)['\"]", content
                )
                queue_match = re.search(r"queue\s*=\s*['\"](\w+)['\"]", content)

                workers[worker_file.stem] = {
                    "type": worker_type_match.group(1)
                    if worker_type_match
                    else "unknown",
                    "queue": queue_match.group(1) if queue_match else "unknown",
                    "lines": content.count("\n"),
                    "has_base_worker": "BaseWorker" in content,
                    "has_error_handling": "handle_error" in content,
                }
            except:
                pass

        return workers

    def _analyze_managers(self):
        """マネージャーの詳細分析"""
        managers = {}
        libs_dir = self.project_root / "libs"

        for manager_file in libs_dir.glob("*_manager.py"):
            try:
                content = manager_file.read_text(encoding="utf-8")

                managers[manager_file.stem] = {
                    "lines": content.count("\n"),
                    "has_base_manager": "BaseManager" in content,
                    "has_singleton": "@singleton" in content or "Singleton" in content,
                }
            except:
                pass

        return managers

    def _analyze_knowledge_base(self):
        """ナレッジベースの分析"""
        kb_info = {
            "total_documents": 0,
            "total_lines": 0,
            "documents": [],
            "consolidated_reports": 0,
            "evolution_snapshots": 0,
        }

        kb_dir = self.project_root / "knowledge_base"
        if kb_dir.exists():
            # ドキュメント分析
            for doc in kb_dir.glob("*.md"):
                lines = doc.read_text(encoding="utf-8").count("\n")
                kb_info["total_documents"] += 1
                kb_info["total_lines"] += lines
                kb_info["documents"].append(
                    {"name": doc.name, "lines": lines, "size": doc.stat().st_size}
                )

            # 統合レポート
            consolidated = kb_dir / "CONSOLIDATED_KNOWLEDGE"
            if consolidated.exists():
                kb_info["consolidated_reports"] = len(list(consolidated.glob("*.md")))

            # 進化追跡
            evolution = kb_dir / "evolution_tracking"
            if evolution.exists():
                kb_info["evolution_snapshots"] = len(
                    list(evolution.glob("snapshot_*.json"))
                )

        return kb_info

    def _analyze_queues(self):
        """RabbitMQキューの分析"""
        queues = {"defined_queues": [], "queue_usage": {}}

        # config/rabbitmq.conf から定義を読み取り
        config_file = self.project_root / "config" / "rabbitmq.conf"
        if config_file.exists():
            content = config_file.read_text()
            import re

            queue_matches = re.findall(r"queue\.declare\s*=\s*(\w+)", content)
            queues["defined_queues"] = list(set(queue_matches))

        # ワーカーのキュー使用状況
        for worker_file in (self.project_root / "workers").glob("*_worker.py"):
            try:
                content = worker_file.read_text()
                queue_match = re.search(r"consume_queue\s*=\s*['\"](\w+)['\"]", content)
                if queue_match:
                    queue_name = queue_match.group(1)
                    if queue_name not in queues["queue_usage"]:
                        queues["queue_usage"][queue_name] = []
                    queues["queue_usage"][queue_name].append(worker_file.stem)
            except:
                pass

        return queues

    def _analyze_integrations(self):
        """統合ポイントの分析"""
        integrations = {"external_services": [], "internal_apis": [], "databases": []}

        # 外部サービス検出
        patterns = {
            "claude_cli": r"claude|anthropic",
            "slack": r"slack|webhook",
            "github": r"github|git",
            "email": r"smtp|email|mail",
        }

        # 繰り返し処理
        for pattern_name, pattern in patterns.items():
            for py_file in self.project_root.rglob("*.py"):
                try:
                    if re.search(pattern, py_file.read_text(), re.IGNORECASE):
                        if not (pattern_name not in integrations["external_services"]):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if pattern_name not in integrations["external_services"]:
                            integrations["external_services"].append(pattern_name)
                        break
                except:
                    pass

        # データベース検出
        if (self.project_root / "db").exists():
            integrations["databases"].append("sqlite")

        return integrations

    def generate_ai_company_report(self, analysis):
        """Elders Guild専用レポート生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = (
            self.project_root / "web" / f"ai_company_projectscope_{timestamp}.html"
        )

        # 通常のHTMLレポートを生成
        html_report = self.ps.generate_report(analysis, "html")

        # Elders Guild固有のセクションを追加
        ai_company_section = f"""
        <div class="section">
            <h2>🤖 Elders Guild Specific Analysis</h2>

            <h3>Workers ({len(analysis['ai_company']['workers'])})</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); " \
                "gap: 10px;">
                {"".join(f'<div class="tag">{w}</div>' for w in analysis['ai_company']['workers'].keys())}
            </div>

            <h3>Managers ({len(analysis['ai_company']['managers'])})</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); " \
                "gap: 10px;">
                {"".join(f'<div class="tag">{m}</div>' for m in analysis['ai_company']['managers'].keys())}
            </div>

            <h3>Knowledge Base</h3>
            <ul>
                <li>Total Documents: {analysis['ai_company']['knowledge_base']['total_documents']}</li>
                <li>Total Lines: {analysis['ai_company']['knowledge_base']['total_lines']:,}</li>
                <li>Consolidated Reports: {analysis['ai_company']['knowledge_base']['consolidated_reports']}</li>
                <li>Evolution Snapshots: {analysis['ai_company']['knowledge_base']['evolution_snapshots']}</li>
            </ul>

            <h3>Integration Points</h3>
            <ul>
                <li>External Services: {', '.join(analysis['ai_company']['integrations']['external_services'])}</li>
                <li>Message Queues: {len(analysis['ai_company']['rabbitmq_queues']['defined_queues'])} defined</li>
                <li>Databases: {', '.join(analysis['ai_company']['integrations']['databases'])}</li>
            </ul>
        </div>
        """

        # HTMLを読み込んで追加
        html_content = Path(html_report).read_text(encoding="utf-8")
        html_content = html_content.replace(
            '</div>\n    <div class="footer">',
            ai_company_section + '</div>\n    <div class="footer">',
        )

        report_path.write_text(html_content, encoding="utf-8")

        return str(report_path)

    def notify_analysis_complete(self, analysis, report_path):
        """Slack通知"""
        message = f"""
{EMOJI['rocket']} Elders Guild ProjectScope Analysis Complete!

📊 **Project Health Score**: {analysis['insights']['health_score']}/100

**Statistics:**
- Total Files: {analysis['statistics']['total_files']:,}
- Total Lines: {analysis['statistics']['total_lines']:,}
- Workers: {len(analysis['ai_company']['workers'])}
- Managers: {len(analysis['ai_company']['managers'])}

**Elders Guild Specific:**
- Knowledge Documents: {analysis['ai_company']['knowledge_base']['total_documents']}
- RabbitMQ Queues: {len(analysis['ai_company']['rabbitmq_queues']['defined_queues'])}
- External Integrations: {len(analysis['ai_company']['integrations']['external_services'])}

"📊" View Report: http://localhost:8080/{Path(report_path).name}
"""

        self.notifier.send_message(message)

    def run_full_analysis(self):
        """完全な分析を実行"""
        # 分析実行
        analysis = self.analyze_with_knowledge()

        # レポート生成
        print("\n📝 Generating Elders Guild customized report...")
        report_path = self.generate_ai_company_report(analysis)
        print(f"✅ Report generated: {report_path}")

        # Slack通知
        try:
            self.notify_analysis_complete(analysis, report_path)
            print("📢 Slack notification sent")
        except:
            print("⚠️  Slack notification failed")

        # サマリー表示
        print("\n" + "━" * 50)
        print("📊 Elders Guild ProjectScope Summary")
        print("━" * 50)
        print(f"Health Score: {analysis['insights']['health_score']}/100")
        print(f"Total Code: {analysis['statistics']['total_lines']:,} lines")
        print(f"Workers: {len(analysis['ai_company']['workers'])}")
        print(f"Managers: {len(analysis['ai_company']['managers'])}")
        print(
            f"Knowledge Docs: {analysis['ai_company']['knowledge_base']['total_documents']}"
        )

        return analysis, report_path


def main():
    """メイン実行"""
    print("◎ Elders Guild ProjectScope")
    print("╱ ╲  Specialized Analysis for Elders Guild System")
    print("━" * 50)

    # Elders Guild用ProjectScope実行
    ai_ps = AICompanyProjectScope()
    analysis, report_path = ai_ps.run_full_analysis()

    print("\n✨ Analysis complete!")
    print(f"\nView the report at:")
    print(f"   http://localhost:8080/{Path(report_path).name}")

    # コマンドとして使えるように
    print("\n💡 You can also use standard ProjectScope commands:")
    print("   pscope /home/aicompany/ai_co")
    print("   pscope --watch  # for continuous monitoring")


if __name__ == "__main__":
    main()
