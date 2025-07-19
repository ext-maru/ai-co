#!/usr/bin/env python3
"""
Elders Guild Knowledge Consolidation System
全ての設計・ナレッジ・実装を統合管理するシステム
"""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from core import EMOJI, BaseManager, get_config
from libs.slack_notifier import SlackNotifier


class KnowledgeConsolidator(BaseManager):
    """設計・ナレッジ・実装の統合管理システム"""

    def __init__(self):
        super().__init__(manager_name="knowledge_consolidator")
        self.config = get_config()
        self.project_root = Path("/home/aicompany/ai_co")
        self.knowledge_base = self.project_root / "knowledge_base"
        self.consolidated_kb = self.knowledge_base / "CONSOLIDATED_KNOWLEDGE"
        self.ensure_directories()

    def initialize(self):
        """BaseManagerの抽象メソッドを実装"""
        self.logger.info(f"{EMOJI['rocket']} Knowledge Consolidator initialized")

    def ensure_directories(self):
        """必要なディレクトリを作成"""
        self.consolidated_kb.mkdir(parents=True, exist_ok=True)

    def scan_project_structure(self) -> Dict[str, Any]:
        """プロジェクト構造のスキャン"""
        self.logger.info(f"{EMOJI['info']} Scanning project structure...")

        structure = {
            "timestamp": datetime.now().isoformat(),
            "version": self._get_project_version(),
            "directories": {},
            "statistics": {"total_files": 0, "total_lines": 0, "file_types": {}},
        }

        # 主要ディレクトリのスキャン
        key_dirs = [
            "core",
            "workers",
            "libs",
            "scripts",
            "commands",
            "config",
            "templates",
            "knowledge_base",
            "web",
            "bin",
        ]

        for dir_name in key_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                structure["directories"][dir_name] = self._scan_directory(dir_path)

        # 統計情報の集計
        self._calculate_statistics(structure)

        return structure

    def _scan_directory(self, path: Path) -> Dict[str, Any]:
        """ディレクトリの詳細スキャン"""
        dir_info = {"files": [], "subdirs": {}, "total_files": 0, "total_size": 0}

        try:
            for item in path.iterdir():
                if item.name.startswith("."):
                    continue

                if item.is_file():
                    file_info = {
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat(),
                        "lines": self._count_lines(item),
                    }
                    dir_info["files"].append(file_info)
                    dir_info["total_files"] += 1
                    dir_info["total_size"] += file_info["size"]

                elif item.is_dir() and item.name not in ["__pycache__", "venv", ".git"]:
                    dir_info["subdirs"][item.name] = self._scan_directory(item)

        except Exception as e:
            self.logger.warning(f"Error scanning {path}: {e}")

        return dir_info

    def _count_lines(self, file_path: Path) -> int:
        """ファイルの行数をカウント"""
        if file_path.suffix not in [".py", ".sh", ".md", ".json", ".yaml", ".yml"]:
            return 0

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except:
            return 0

    def consolidate_knowledge_base(self) -> Dict[str, Any]:
        """ナレッジベースの統合"""
        self.logger.info(f"{EMOJI['template']} Consolidating knowledge base...")

        kb_files = []
        kb_content = {}

        # ナレッジベースファイルの収集
        for kb_file in self.knowledge_base.glob("*.md"):
            try:
                content = kb_file.read_text(encoding="utf-8")
                kb_info = {
                    "filename": kb_file.name,
                    "size": len(content),
                    "lines": content.count("\n"),
                    "modified": datetime.fromtimestamp(
                        kb_file.stat().st_mtime
                    ).isoformat(),
                    "hash": hashlib.md5(content.encode()).hexdigest(),
                }
                kb_files.append(kb_info)
                kb_content[kb_file.name] = content

            except Exception as e:
                self.logger.error(f"Error reading {kb_file}: {e}")

        return {"files": kb_files, "content": kb_content, "total_files": len(kb_files)}

    def analyze_implementations(self) -> Dict[str, Any]:
        """実装の分析"""
        self.logger.info(f"{EMOJI['gear']} Analyzing implementations...")

        analysis = {"workers": {}, "managers": {}, "commands": {}, "core_modules": {}}

        # ワーカーの分析
        for worker_file in (self.project_root / "workers").glob("*_worker.py"):
            analysis["workers"][worker_file.stem] = self._analyze_python_file(
                worker_file
            )

        # マネージャーの分析
        for manager_file in (self.project_root / "libs").glob("*_manager.py"):
            analysis["managers"][manager_file.stem] = self._analyze_python_file(
                manager_file
            )

        # コマンドの分析
        for cmd_file in (self.project_root / "commands").glob("ai_*.py"):
            analysis["commands"][cmd_file.stem] = self._analyze_python_file(cmd_file)

        # Coreモジュールの分析
        for core_file in (self.project_root / "core").glob("*.py"):
            if not core_file.name.startswith("__"):
                analysis["core_modules"][core_file.stem] = self._analyze_python_file(
                    core_file
                )

        return analysis

    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Pythonファイルの分析"""
        try:
            content = file_path.read_text(encoding="utf-8")

            # クラスと関数の抽出
            classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
            imports = re.findall(
                r"^(?:from|import)\s+(.+?)(?:\s+import|$)", content, re.MULTILINE
            )

            # docstringの抽出
            docstring_match = re.search(r'^"""(.+?)"""', content, re.DOTALL)
            docstring = docstring_match.group(1).strip() if docstring_match else ""

            return {
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports)),
                "docstring": docstring,
                "lines": content.count("\n"),
                "size": len(content),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return {}

    def generate_system_map(self) -> Dict[str, Any]:
        """システム全体のマップ生成"""
        self.logger.info(f"{EMOJI['network']} Generating system map...")

        system_map = {
            "architecture": self._analyze_architecture(),
            "dependencies": self._analyze_dependencies(),
            "workflow": self._analyze_workflow(),
            "integration_points": self._analyze_integrations(),
        }

        return system_map

    def _analyze_architecture(self) -> Dict[str, Any]:
        """アーキテクチャ分析"""
        return {
            "layers": {
                "presentation": ["commands", "web", "scripts"],
                "application": ["workers", "managers"],
                "domain": ["core", "libs"],
                "infrastructure": ["config", "db", "logs"],
            },
            "patterns": [
                "Message Queue (RabbitMQ)",
                "Worker Pattern",
                "Manager Pattern",
                "Command Pattern",
            ],
        }

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """依存関係の分析"""
        deps = {}

        # requirements.txtから依存関係を読み取り
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            deps["python"] = [
                line.strip()
                for line in req_file.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            ]

        # システム依存関係
        deps["system"] = ["rabbitmq-server", "claude-cli", "git", "python3.12"]

        return deps

    def _analyze_workflow(self) -> Dict[str, Any]:
        """ワークフロー分析"""
        return {
            "task_flow": [
                "User -> ai-send/ai-dialog",
                "-> RabbitMQ",
                "-> TaskWorker (Claude CLI)",
                "-> PMWorker (File placement)",
                "-> ResultWorker (Notification)",
            ],
            "command_flow": [
                "AI creates command",
                "-> AI Command Executor",
                "-> Execute",
                "-> Result notification",
            ],
        }

    def _analyze_integrations(self) -> Dict[str, Any]:
        """統合ポイントの分析"""
        return {
            "external": ["Claude CLI", "Slack", "GitHub"],
            "internal": ["RabbitMQ", "SQLite", "AI Command Executor"],
            "protocols": ["AMQP", "HTTP/HTTPS", "WebSocket"],
        }

    def generate_documentation(self) -> Path:
        """統合ドキュメントの生成"""
        self.logger.info(f"{EMOJI['file']} Generating consolidated documentation...")

        # 全情報の収集
        project_structure = self.scan_project_structure()
        knowledge_base = self.consolidate_knowledge_base()
        implementations = self.analyze_implementations()
        system_map = self.generate_system_map()

        # 統合ドキュメントの作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_path = self.consolidated_kb / f"AI_COMPANY_CONSOLIDATED_{timestamp}.md"

        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(f"# 🎯 Elders Guild 統合ナレッジベース\n\n")
            f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # エグゼクティブサマリー
            f.write("## 📊 エグゼクティブサマリー\n\n")
            f.write(f"- **プロジェクトバージョン**: {project_structure['version']}\n")
            f.write(
                f"- **総ファイル数**: {project_structure['statistics']['total_files']}\n"
            )
            f.write(f"- **総行数**: {project_structure['statistics']['total_lines']}\n")
            f.write(f"- **ワーカー数**: {len(implementations['workers'])}\n")
            f.write(f"- **マネージャー数**: {len(implementations['managers'])}\n")
            f.write(f"- **コマンド数**: {len(implementations['commands'])}\n\n")

            # システムアーキテクチャ
            f.write("## 🏗️ システムアーキテクチャ\n\n")
            f.write("### レイヤー構成\n")
            for layer, components in system_map["architecture"]["layers"].items():
                f.write(f"- **{layer.title()}**: {', '.join(components)}\n")
            f.write("\n")

            # ワークフロー
            f.write("### ワークフロー\n")
            f.write("```\n")
            for flow in system_map["workflow"]["task_flow"]:
                f.write(f"{flow}\n")
            f.write("```\n\n")

            # 実装詳細
            f.write("## 🔧 実装詳細\n\n")

            # ワーカー一覧
            f.write("### ワーカー実装\n")
            for worker_name, worker_info in implementations["workers"].items():
                f.write(f"#### {worker_name}\n")
                if worker_info.get("docstring"):
                    f.write(f"{worker_info['docstring']}\n")
                f.write(f"- クラス: {', '.join(worker_info.get('classes', []))}\n")
                f.write(f"- 関数数: {len(worker_info.get('functions', []))}\n")
                f.write(f"- 行数: {worker_info.get('lines', 0)}\n\n")

            # マネージャー一覧
            f.write("### マネージャー実装\n")
            for manager_name, manager_info in implementations["managers"].items():
                f.write(f"#### {manager_name}\n")
                if manager_info.get("docstring"):
                    f.write(f"{manager_info['docstring']}\n")
                f.write(f"- クラス: {', '.join(manager_info.get('classes', []))}\n")
                f.write(f"- 関数数: {len(manager_info.get('functions', []))}\n\n")

            # ナレッジベース統合
            f.write("## 📚 ナレッジベース\n\n")
            f.write("### 含まれるドキュメント\n")
            for kb_file in knowledge_base["files"]:
                f.write(f"- **{kb_file['filename']}** ({kb_file['lines']} lines)\n")
            f.write("\n")

            # 統計情報
            f.write("## 📈 統計情報\n\n")
            f.write("### ファイルタイプ別統計\n")
            for file_type, count in project_structure["statistics"][
                "file_types"
            ].items():
                f.write(f"- {file_type}: {count} files\n")

        self.logger.info(f"{EMOJI['success']} Documentation generated: {doc_path}")
        return doc_path

    def _calculate_statistics(self, structure: Dict[str, Any]):
        """統計情報の計算"""
        total_files = 0
        total_lines = 0
        file_types = {}

        def count_in_dir(dir_info):
            nonlocal total_files, total_lines

            for file_info in dir_info.get("files", []):
                total_files += 1
                total_lines += file_info.get("lines", 0)

                # ファイルタイプの集計
                ext = Path(file_info["name"]).suffix
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1

            for subdir in dir_info.get("subdirs", {}).values():
                count_in_dir(subdir)

        for dir_info in structure["directories"].values():
            count_in_dir(dir_info)

        structure["statistics"]["total_files"] = total_files
        structure["statistics"]["total_lines"] = total_lines
        structure["statistics"]["file_types"] = dict(sorted(file_types.items()))

    def _get_project_version(self) -> str:
        """プロジェクトバージョンの取得"""
        try:
            # Gitタグから取得を試みる
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        # デフォルトバージョン
        return "v5.3-dev"

    def create_interactive_report(self) -> Path:
        """インタラクティブなHTMLレポート生成"""
        self.logger.info(f"{EMOJI['monitor']} Creating interactive report...")

        # データ収集
        data = {
            "structure": self.scan_project_structure(),
            "knowledge": self.consolidate_knowledge_base(),
            "implementations": self.analyze_implementations(),
            "system_map": self.generate_system_map(),
        }

        # HTMLレポート生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.project_root / "web" / f"knowledge_report_{timestamp}.html"

        html_content = self._generate_html_report(data)
        report_path.write_text(html_content, encoding="utf-8")

        self.logger.info(
            f"{EMOJI['success']} Interactive report created: {report_path}"
        )
        return report_path

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """HTMLレポートの生成"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Elders Guild Knowledge Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .tree {{ font-family: monospace; white-space: pre; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Elders Guild Knowledge Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>📊 Overview</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{data['structure']['statistics']['total_files']}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['structure']['statistics']['total_lines']:,}</div>
                <div class="stat-label">Total Lines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(data['implementations']['workers'])}</div>
                <div class="stat-label">Workers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(data['implementations']['managers'])}</div>
                <div class="stat-label">Managers</div>
            </div>
        </div>

        <h2>🏗️ Architecture</h2>
        <pre>{json.dumps(data['system_map']['architecture'], indent=2)}</pre>

        <h2>📋 Implementation Details</h2>
        <h3>Workers</h3>
        <table>
            <tr><th>Worker</th><th>Classes</th><th>Functions</th><th>Lines</th></tr>
            {"".join(f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>" for name, info in data['implementations']['workers'].items())}
        </table>

        <h3>Managers</h3>
        <table>
            <tr><th>Manager</th><th>Classes</th><th>Functions</th><th>Lines</th></tr>
            {"".join(f"<tr><td>{name}</td><td>{', '.join(info.get('classes', []))}</td><td>{len(info.get('functions', []))}</td><td>{info.get('lines', 0)}</td></tr>" for name, info in data['implementations']['managers'].items())}
        </table>

        <h2>📚 Knowledge Base</h2>
        <table>
            <tr><th>Document</th><th>Lines</th><th>Modified</th></tr>
            {"".join(f"<tr><td>{f['filename']}</td><td>{f['lines']}</td><td>{f['modified']}</td></tr>" for f in data['knowledge']['files'])}
        </table>
    </div>
</body>
</html>"""

    def run_consolidation(self):
        """統合処理の実行"""
        try:
            self.logger.info(f"{EMOJI['rocket']} Starting knowledge consolidation...")

            # Markdownドキュメント生成
            doc_path = self.generate_documentation()

            # HTMLレポート生成
            report_path = self.create_interactive_report()

            # JSON形式でのエクスポート
            self.export_to_json()

            # Slack通知
            self._notify_completion(doc_path, report_path)

            self.logger.info(
                f"{EMOJI['party']} Knowledge consolidation completed successfully!"
            )

        except Exception as e:
            self.handle_error(e, "run_consolidation")
            raise

    def export_to_json(self):
        """JSON形式でのエクスポート"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.consolidated_kb / f"knowledge_export_{timestamp}.json"

        export_data = {
            "timestamp": timestamp,
            "structure": self.scan_project_structure(),
            "implementations": self.analyze_implementations(),
            "system_map": self.generate_system_map(),
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Exported to JSON: {json_path}")

    def _notify_completion(self, doc_path: Path, report_path: Path):
        """完了通知"""
        try:
            from libs.slack_notifier import SlackNotifier

            notifier = SlackNotifier()

            message = f"""
{EMOJI['party']} Elders Guild Knowledge Consolidation Complete!

📄 Documentation: {doc_path.name}
📊 Interactive Report: {report_path.name}
📁 Location: {self.consolidated_kb}

Access the report at: http://localhost:8080/{report_path.name}
"""
            notifier.send_message(message)

        except Exception as e:
            self.logger.warning(f"Failed to send Slack notification: {e}")


if __name__ == "__main__":
    consolidator = KnowledgeConsolidator()
    consolidator.run_consolidation()
