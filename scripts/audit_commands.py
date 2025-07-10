#!/usr/bin/env python3
"""
Elders Guild コマンド監査スクリプト
全コマンドの実装状況、使用頻度、依存関係を分析
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class CommandAuditor:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.bin_dir = self.project_root / "bin"
        self.commands_dir = self.project_root / "commands"
        self.scripts_dir = self.project_root / "scripts"
        self.logs_dir = self.project_root / "logs"
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "commands": {},
            "issues": [],
            "recommendations": []
        }
        
    def find_all_commands(self):
        """全コマンドを検出"""
        commands = set()
        
        # binディレクトリのai-*ファイル
        if self.bin_dir.exists():
            for file in self.bin_dir.glob("ai-*"):
                if file.is_file() and not file.suffix:
                    commands.add(file.name)
                    
        # scriptsディレクトリのai-*ファイル
        if self.scripts_dir.exists():
            for file in self.scripts_dir.glob("ai-*"):
                if file.is_file() and not file.suffix in ['.bak', '.pyc']:
                    commands.add(file.name)
                    
        return sorted(commands)
        
    def check_command_implementation(self, cmd_name):
        """コマンドの実装状況を確認"""
        info = {
            "name": cmd_name,
            "has_bin_wrapper": False,
            "has_script": False,
            "has_command_module": False,
            "implementation_type": None,
            "description": None,
            "dependencies": [],
            "issues": []
        }
        
        # binラッパーの確認
        bin_path = self.bin_dir / cmd_name
        if bin_path.exists():
            info["has_bin_wrapper"] = True
            
        # scriptsの確認
        script_path = self.scripts_dir / cmd_name
        if script_path.exists():
            info["has_script"] = True
            info["implementation_type"] = "script"
            
        # commandsモジュールの確認
        module_name = cmd_name.replace('-', '_') + '.py'
        command_path = self.commands_dir / module_name
        if command_path.exists():
            info["has_command_module"] = True
            info["implementation_type"] = "module"
            
            # モジュールから説明を取得
            try:
                with open(command_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # descriptionを探す
                    desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                    if desc_match:
                        info["description"] = desc_match.group(1)
                    # docstringを探す
                    elif content.strip().startswith('"""'):
                        docstring = content.split('"""')[1].strip().split('\n')[0]
                        info["description"] = docstring
            except:
                pass
                
        # 実装チェック
        if not info["has_bin_wrapper"] and not info["has_script"]:
            info["issues"].append("No implementation found")
        elif info["has_bin_wrapper"] and not info["has_command_module"] and not info["has_script"]:
            info["issues"].append("Bin wrapper exists but no backing implementation")
            
        return info
        
    def check_command_usage(self, cmd_name):
        """コマンドの使用状況を確認"""
        usage_info = {
            "referenced_in_code": [],
            "referenced_in_docs": [],
            "log_mentions": 0,
            "likely_deprecated": False
        }
        
        # コード内での参照を検索
        try:
            # Python/Shellファイルでの参照
            result = subprocess.run(
                ['grep', '-r', '--include=*.py', '--include=*.sh', cmd_name, str(self.project_root)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and '.bak' not in line and '__pycache__' not in line:
                        file_path = line.split(':')[0]
                        usage_info["referenced_in_code"].append(file_path)
        except:
            pass
            
        # ログファイルでの言及
        if self.logs_dir.exists():
            try:
                result = subprocess.run(
                    ['grep', '-c', cmd_name] + list(self.logs_dir.glob('*.log')),
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    usage_info["log_mentions"] = len(result.stdout.strip().split('\n'))
            except:
                pass
                
        # 非推奨の可能性を判定
        if (len(usage_info["referenced_in_code"]) == 0 and 
            usage_info["log_mentions"] == 0):
            usage_info["likely_deprecated"] = True
            
        return usage_info
        
    def analyze_command_relationships(self):
        """コマンド間の依存関係を分析"""
        relationships = defaultdict(list)
        
        for cmd_info in self.results["commands"].values():
            cmd_name = cmd_info["name"]
            
            # 実装ファイルを読んで他のコマンドへの参照を探す
            files_to_check = []
            
            if cmd_info["has_script"]:
                files_to_check.append(self.scripts_dir / cmd_name)
            if cmd_info["has_command_module"]:
                module_name = cmd_name.replace('-', '_') + '.py'
                files_to_check.append(self.commands_dir / module_name)
                
            for file_path in files_to_check:
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 他のai-*コマンドへの参照を探す
                            other_cmds = re.findall(r'ai-[a-z\-]+', content)
                            for other_cmd in other_cmds:
                                if other_cmd != cmd_name and other_cmd in self.results["commands"]:
                                    relationships[cmd_name].append(other_cmd)
                    except:
                        pass
                        
        return dict(relationships)
        
    def generate_recommendations(self):
        """改善提案を生成"""
        recommendations = []
        
        # 実装のないコマンド
        no_impl = [cmd for cmd, info in self.results["commands"].items() 
                   if "No implementation found" in info["issues"]]
        if no_impl:
            recommendations.append({
                "type": "missing_implementation",
                "severity": "high",
                "description": f"以下のコマンドには実装がありません: {', '.join(no_impl)}",
                "action": "削除するか実装を追加してください"
            })
            
        # 使われていないコマンド
        deprecated = [cmd for cmd, info in self.results["commands"].items() 
                     if info["usage"]["likely_deprecated"]]
        if deprecated:
            recommendations.append({
                "type": "deprecated_commands",
                "severity": "medium",
                "description": f"以下のコマンドは使われていない可能性があります: {', '.join(deprecated)}",
                "action": "削除を検討してください"
            })
            
        # 重複コマンド
        # ai-codeとai-sendの関係など
        if "ai-code" in self.results["commands"] and "ai-send" in self.results["commands"]:
            recommendations.append({
                "type": "duplicate_functionality",
                "severity": "low",
                "description": "ai-codeはai-sendのショートカットです",
                "action": "統合または明確な差別化を検討してください"
            })
            
        return recommendations
        
    def run_audit(self):
        """監査を実行"""
        print("🔍 Elders Guild コマンド監査開始...")
        
        # 全コマンド検出
        all_commands = self.find_all_commands()
        print(f"📊 検出されたコマンド数: {len(all_commands)}")
        
        # 各コマンドの詳細チェック
        for cmd in all_commands:
            print(f"  チェック中: {cmd}")
            cmd_info = self.check_command_implementation(cmd)
            cmd_info["usage"] = self.check_command_usage(cmd)
            self.results["commands"][cmd] = cmd_info
            
        # 関係性分析
        self.results["relationships"] = self.analyze_command_relationships()
        
        # 推奨事項生成
        self.results["recommendations"] = self.generate_recommendations()
        
        # サマリー生成
        self.results["summary"] = {
            "total_commands": len(all_commands),
            "implemented_commands": len([c for c, i in self.results["commands"].items() 
                                       if i["implementation_type"]]),
            "likely_deprecated": len([c for c, i in self.results["commands"].items() 
                                    if i["usage"]["likely_deprecated"]]),
            "commands_with_issues": len([c for c, i in self.results["commands"].items() 
                                       if i["issues"]])
        }
        
        return self.results
        
    def generate_report(self, output_format="markdown"):
        """レポートを生成"""
        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return json.dumps(self.results, indent=2, ensure_ascii=False)
            
    def _generate_markdown_report(self):
        """Markdownレポートを生成"""
        report = []
        report.append("# Elders Guild コマンド監査レポート")
        report.append(f"\n生成日時: {self.results['timestamp']}")
        
        # サマリー
        report.append("\n## 📊 サマリー")
        report.append(f"- 総コマンド数: {self.results['summary']['total_commands']}")
        report.append(f"- 実装済み: {self.results['summary']['implemented_commands']}")
        report.append(f"- 非推奨候補: {self.results['summary']['likely_deprecated']}")
        report.append(f"- 問題あり: {self.results['summary']['commands_with_issues']}")
        
        # カテゴリ別
        report.append("\n## 📋 カテゴリ別コマンド一覧")
        
        categories = {
            "基本操作": ["ai", "ai-start", "ai-stop", "ai-restart", "ai-status", "ai-help", "ai-version"],
            "タスク実行": ["ai-send", "ai-code", "ai-dialog", "ai-reply", "ai-run"],
            "情報表示": ["ai-logs", "ai-tasks", "ai-stats", "ai-monitor", "ai-queue"],
            "ワーカー管理": ["ai-workers", "ai-worker-restart", "ai-worker-add", "ai-worker-rm", "ai-worker-scale"],
            "タスク詳細": ["ai-task-info", "ai-task-cancel", "ai-task-retry"],
            "会話管理": ["ai-conversations", "ai-conv-info", "ai-conv-resume", "ai-conv-export"],
            "設定管理": ["ai-config", "ai-config-edit", "ai-config-reload"],
            "RAG/検索": ["ai-rag", "ai-rag-search"],
            "自己進化": ["ai-evolve", "ai-evolve-test", "ai-learn"],
            "システム管理": ["ai-backup", "ai-clean", "ai-update", "ai-queue-clear"],
            "レポート": ["ai-report", "ai-export"],
            "開発支援": ["ai-venv", "ai-debug", "ai-test", "ai-shell", "ai-simulate"],
            "新機能": ["ai-template", "ai-worker-comm", "ai-dlq", "ai-dashboard", "ai-scale"]
        }
        
        for category, cmds in categories.items():
            report.append(f"\n### {category}")
            for cmd in cmds:
                if cmd in self.results["commands"]:
                    info = self.results["commands"][cmd]
                    status = "✅" if info["implementation_type"] else "❌"
                    deprecated = "⚠️" if info["usage"]["likely_deprecated"] else ""
                    desc = info["description"] or "説明なし"
                    report.append(f"- {status} `{cmd}` {deprecated} - {desc}")
                    
        # 問題のあるコマンド
        report.append("\n## ⚠️ 問題のあるコマンド")
        
        for cmd, info in self.results["commands"].items():
            if info["issues"]:
                report.append(f"\n### {cmd}")
                for issue in info["issues"]:
                    report.append(f"- {issue}")
                    
        # 推奨事項
        report.append("\n## 💡 推奨事項")
        
        for rec in self.results["recommendations"]:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[rec["severity"]]
            report.append(f"\n### {severity_icon} {rec['type']}")
            report.append(f"- {rec['description']}")
            report.append(f"- 対応: {rec['action']}")
            
        # 削除候補
        report.append("\n## 🗑️ 削除候補コマンド")
        
        deprecated_cmds = [cmd for cmd, info in self.results["commands"].items() 
                          if info["usage"]["likely_deprecated"]]
        
        if deprecated_cmds:
            report.append("\n以下のコマンドは使われていない可能性が高いです：")
            for cmd in deprecated_cmds:
                report.append(f"- `{cmd}`")
        else:
            report.append("\n削除候補のコマンドはありません。")
            
        return "\n".join(report)

def main():
    """メイン処理"""
    auditor = CommandAuditor()
    
    # 監査実行
    results = auditor.run_audit()
    
    # レポート生成
    markdown_report = auditor.generate_report("markdown")
    
    # レポート保存
    report_path = PROJECT_ROOT / "command_audit_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
        
    print(f"\n✅ 監査完了！レポート: {report_path}")
    
    # JSON形式でも保存
    json_path = PROJECT_ROOT / "command_audit_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"📄 詳細データ: {json_path}")
    
    # サマリー表示
    print("\n📊 サマリー:")
    print(f"  - 総コマンド数: {results['summary']['total_commands']}")
    print(f"  - 非推奨候補: {results['summary']['likely_deprecated']}")
    print(f"  - 要対応: {results['summary']['commands_with_issues']}")

if __name__ == "__main__":
    main()
