#!/usr/bin/env python3
"""
📋 プロジェクト一覧表示システム
既存プロジェクトの詳細情報を整理して表示

エルダーズギルドプロジェクト管理
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

console = Console()

class ProjectLister:
    """プロジェクト一覧管理"""
    
    def __init__(self):
        self.console = console
        self.project_root = PROJECT_ROOT
        self.projects_dir = self.project_root / "projects"
        
    def list_projects(self):
        """プロジェクト一覧表示"""
        if not self.projects_dir.exists():
            self.console.print("[yellow]プロジェクトディレクトリが存在しません[/yellow]")
            return
        
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                project_info = self.get_project_info(project_dir)
                if project_info:
                    projects.append(project_info)
        
        if not projects:
            self.console.print(Panel(
                "プロジェクトが見つかりません。\n\n"
                "新規作成: ai-project create",
                title="📋 プロジェクト一覧",
                border_style="yellow"
            ))
            return
        
        # テーブル表示
        self.display_projects_table(projects)
        
        # 詳細ツリー表示
        if len(projects) <= 5:
            self.display_projects_tree(projects)
        
        # サマリー
        self.display_summary(projects)
    
    def get_project_info(self, project_path: Path) -> Dict:
        """プロジェクト情報取得"""
        info = {
            "name": project_path.name,
            "path": project_path,
            "created_at": None,
            "last_modified": None,
            "size_mb": 0,
            "file_count": 0,
            "type": "unknown",
            "status": "unknown",
            "features": [],
            "tech_stack": {},
            "quality_metrics": {}
        }
        
        # PDCA履歴から情報取得
        pdca_file = project_path / ".pdca" / "pdca_history.json"
        if pdca_file.exists():
            try:
                with open(pdca_file, "r", encoding="utf-8") as f:
                    pdca_data = json.load(f)
                    info["created_at"] = pdca_data.get("created_at")
                    
                    # 初期設定から情報抽出
                    config = pdca_data.get("initial_config", {})
                    info["type"] = config.get("type", "unknown")
                    info["features"] = config.get("features", [])
                    info["tech_stack"] = {
                        "backend": config.get("backend"),
                        "frontend": config.get("frontend"),
                        "database": config.get("database")
                    }
                    
                    # メトリクス
                    metrics = pdca_data.get("metrics", {})
                    info["quality_metrics"] = {
                        "test_coverage": metrics.get("test_coverage", 0),
                        "quality_score": metrics.get("quality_score", 0)
                    }
                    
                    # ステータス判定
                    cycles = pdca_data.get("cycles", [])
                    if cycles:
                        last_cycle = cycles[-1]
                        last_update = datetime.fromisoformat(last_cycle["timestamp"])
                        days_ago = (datetime.now() - last_update).days
                        
                        if days_ago < 7:
                            info["status"] = "active"
                        elif days_ago < 30:
                            info["status"] = "idle"
                        else:
                            info["status"] = "stale"
                    else:
                        info["status"] = "new"
            except Exception as e:
                self.console.print(f"[red]エラー: {project_path.name} の情報読み取り失敗: {e}[/red]")
        
        # ファイル統計
        try:
            all_files = list(project_path.rglob("*"))
            info["file_count"] = len([f for f in all_files if f.is_file()])
            total_size = sum(f.stat().st_size for f in all_files if f.is_file())
            info["size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # 最終更新日時
            if all_files:
                latest_mtime = max(f.stat().st_mtime for f in all_files if f.is_file())
                info["last_modified"] = datetime.fromtimestamp(latest_mtime).isoformat()
        except:
            pass
        
        return info
    
    def display_projects_table(self, projects: List[Dict]):
        """プロジェクトテーブル表示"""
        table = Table(title="🏗️ プロジェクト一覧")
        
        table.add_column("プロジェクト名", style="cyan", no_wrap=True)
        table.add_column("タイプ", style="magenta")
        table.add_column("ステータス", style="green")
        table.add_column("技術スタック", style="yellow")
        table.add_column("品質", style="blue")
        table.add_column("サイズ", style="white")
        
        for project in projects:
            # ステータス表示
            status_emoji = {
                "active": "🟢",
                "idle": "🟡",
                "stale": "🔴",
                "new": "🆕"
            }.get(project["status"], "❓")
            
            # 技術スタック文字列
            tech_stack = []
            if project["tech_stack"].get("backend"):
                tech_stack.append(project["tech_stack"]["backend"])
            if project["tech_stack"].get("frontend"):
                tech_stack.append(project["tech_stack"]["frontend"])
            tech_stack_str = " + ".join(tech_stack) if tech_stack else "N/A"
            
            # 品質スコア
            coverage = project["quality_metrics"].get("test_coverage", 0)
            quality = project["quality_metrics"].get("quality_score", 0)
            quality_str = f"📊 {coverage:.0f}% | 🎯 {quality:.0f}"
            
            table.add_row(
                project["name"],
                project["type"],
                f"{status_emoji} {project['status']}",
                tech_stack_str,
                quality_str,
                f"{project['size_mb']} MB"
            )
        
        self.console.print(table)
    
    def display_projects_tree(self, projects: List[Dict]):
        """プロジェクト詳細ツリー表示"""
        for project in projects:
            tree = Tree(f"📁 [bold cyan]{project['name']}[/bold cyan]")
            
            # 基本情報
            info_branch = tree.add("📋 基本情報")
            info_branch.add(f"タイプ: {project['type']}")
            info_branch.add(f"作成日: {project['created_at'] or 'N/A'}")
            info_branch.add(f"ファイル数: {project['file_count']}")
            
            # 技術スタック
            if any(project["tech_stack"].values()):
                tech_branch = tree.add("💻 技術スタック")
                for key, value in project["tech_stack"].items():
                    if value:
                        tech_branch.add(f"{key}: {value}")
            
            # 機能
            if project["features"]:
                feature_branch = tree.add(f"✨ 機能 ({len(project['features'])})")
                for feature in project["features"][:5]:  # 最大5個表示
                    feature_branch.add(feature)
                if len(project["features"]) > 5:
                    feature_branch.add(f"... 他 {len(project['features']) - 5} 個")
            
            self.console.print(Panel(tree, border_style="blue"))
    
    def display_summary(self, projects: List[Dict]):
        """サマリー表示"""
        total_size = sum(p["size_mb"] for p in projects)
        active_count = len([p for p in projects if p["status"] == "active"])
        
        # 平均品質スコア
        quality_scores = [p["quality_metrics"].get("quality_score", 0) for p in projects if p["quality_metrics"].get("quality_score", 0) > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # テストカバレッジ
        coverages = [p["quality_metrics"].get("test_coverage", 0) for p in projects if p["quality_metrics"].get("test_coverage", 0) > 0]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0
        
        summary = Panel(
            f"📊 サマリー\n\n"
            f"総プロジェクト数: {len(projects)}\n"
            f"アクティブ: {active_count} 🟢\n"
            f"総容量: {total_size:.1f} MB\n"
            f"平均品質スコア: {avg_quality:.1f}/100\n"
            f"平均テストカバレッジ: {avg_coverage:.1f}%\n\n"
            f"💡 ヒント:\n"
            f"  • 新規作成: ai-project create\n"
            f"  • PDCA分析: ai-project pdca <project_name>\n"
            f"  • 品質レポート: ai-project report <project_name>",
            title="📈 統計情報",
            border_style="green"
        )
        
        self.console.print(summary)
    
    def export_project_list(self, format: str = "json"):
        """プロジェクトリストのエクスポート"""
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                project_info = self.get_project_info(project_dir)
                if project_info:
                    # パスをシリアライズ可能な形式に
                    project_info["path"] = str(project_info["path"])
                    projects.append(project_info)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            output_file = self.project_root / f"project_list_{timestamp}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({
                    "generated_at": datetime.now().isoformat(),
                    "total_projects": len(projects),
                    "projects": projects
                }, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"✅ エクスポート完了: {output_file}")
        
        elif format == "markdown":
            output_file = self.project_root / f"project_list_{timestamp}.md"
            md_content = f"# プロジェクト一覧\n\n生成日時: {datetime.now().isoformat()}\n\n"
            
            for project in projects:
                md_content += f"## {project['name']}\n\n"
                md_content += f"- **タイプ**: {project['type']}\n"
                md_content += f"- **ステータス**: {project['status']}\n"
                md_content += f"- **サイズ**: {project['size_mb']} MB\n"
                md_content += f"- **ファイル数**: {project['file_count']}\n"
                
                if project['tech_stack']:
                    md_content += f"- **技術スタック**:\n"
                    for key, value in project['tech_stack'].items():
                        if value:
                            md_content += f"  - {key}: {value}\n"
                
                md_content += "\n"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            self.console.print(f"✅ エクスポート完了: {output_file}")

def main():
    """メインエントリポイント"""
    lister = ProjectLister()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        format = sys.argv[2] if len(sys.argv) > 2 else "json"
        lister.export_project_list(format)
    else:
        lister.list_projects()

if __name__ == "__main__":
    main()