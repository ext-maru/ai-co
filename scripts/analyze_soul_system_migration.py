#!/usr/bin/env python3
"""
🌟 魂システム統合・廃止分析スクリプト
==============================

4賢者Soul実装の詳細分析と移行計画生成

Author: Claude Elder
Created: 2025-07-23
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from dataclasses import dataclass, asdict


@dataclass
class SoulAnalysis:
    """Soul実装分析結果"""
    file_path: str
    lines_of_code: int
    class_name: str
    base_classes: List[str]
    methods: List[str]
    imports: List[str]
    soul_dependencies: List[str]
    business_logic_functions: List[str]
    a2a_functions: List[str]
    migration_priority: str  # high, medium, low


class SoulSystemAnalyzer:
    """魂システム分析ツール"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.analyses: Dict[str, SoulAnalysis] = {}
        
        # 4賢者システム
        self.sages = ["incident_sage", "knowledge_sage", "task_sage", "rag_sage"]
        
        # Soul関連キーワード
        self.soul_keywords = [
            "BaseSoul", "soul_base", "SoulContext", "soul_", 
            "a2a_", "Soul", "agent_to_agent"
        ]
        
        # ビジネスロジック関連キーワード
        self.business_logic_keywords = [
            "process", "analyze", "handle", "manage", "execute",
            "create", "update", "delete", "search", "query"
        ]
        
        # A2A通信関連キーワード
        self.a2a_keywords = [
            "send_message", "receive_message", "communicate",
            "a2a_", "agent_to_agent", "notify", "broadcast"
        ]
    
    def analyze_python_file(self, file_path: Path) -> SoulAnalysis:
        """Pythonファイルの詳細分析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本情報
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # パースエラーの場合は基本分析のみ
            return self._basic_analysis(file_path, content, lines_of_code)
        
        # AST分析
        class_name = ""
        base_classes = []
        methods = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                base_classes = [base.id if isinstance(base, ast.Name) else str(base) 
                              for base in node.bases]
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
            
            elif isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
        
        # Soul依存関係分析
        soul_dependencies = [imp for imp in imports 
                           if any(keyword in imp for keyword in self.soul_keywords)]
        
        # 機能分類
        business_logic_functions = [method for method in methods
                                  if any(keyword in method.lower() 
                                       for keyword in self.business_logic_keywords)]
        
        a2a_functions = [method for method in methods
                        if any(keyword in method.lower() 
                             for keyword in self.a2a_keywords)]
        
        # 移行優先度判定
        migration_priority = self._determine_migration_priority(
            lines_of_code, len(business_logic_functions), len(a2a_functions)
        )
        
        return SoulAnalysis(
            file_path=str(file_path.relative_to(self.project_root)),
            lines_of_code=lines_of_code,
            class_name=class_name,
            base_classes=base_classes,
            methods=methods,
            imports=imports,
            soul_dependencies=soul_dependencies,
            business_logic_functions=business_logic_functions,
            a2a_functions=a2a_functions,
            migration_priority=migration_priority
        )
    
    def _basic_analysis(self, file_path: Path, content: str, lines_of_code: int) -> SoulAnalysis:
        """パースエラー時の基本分析"""
        # 正規表現による基本分析
        class_pattern = r'class\s+(\w+)\s*\([^)]*BaseSoul[^)]*\):'
        class_match = re.search(class_pattern, content)
        class_name = class_match.group(1) if class_match else "Unknown"
        
        method_pattern = r'def\s+(\w+)\s*\('
        methods = re.findall(method_pattern, content)
        
        return SoulAnalysis(
            file_path=str(file_path.relative_to(self.project_root)),
            lines_of_code=lines_of_code,
            class_name=class_name,
            base_classes=["BaseSoul"] if "BaseSoul" in content else [],
            methods=methods,
            imports=[],
            soul_dependencies=["BaseSoul"] if "BaseSoul" in content else [],
            business_logic_functions=[],
            a2a_functions=[],
            migration_priority="medium"
        )
    
    def _determine_migration_priority(self, loc: int, business_functions: int, a2a_functions: int) -> str:
        """移行優先度の判定"""
        if loc > 1000 or business_functions > 10:
            return "high"
        elif loc > 500 or business_functions > 5:
            return "medium"
        else:
            return "low"
    
    def analyze_all_souls(self) -> Dict[str, Any]:
        """全Soul実装の分析"""
        print("🔍 魂システム分析開始...")
        
        total_analysis = {
            "timestamp": "2025-07-23",
            "summary": {},
            "sage_analyses": {},
            "migration_plan": {},
            "files_to_deprecate": []
        }
        
        # 4賢者Soul分析
        for sage in self.sages:
            soul_file = self.project_root / sage / "soul.py"
            if soul_file.exists():
                print(f"  📊 {sage} soul.py 分析中...")
                analysis = self.analyze_python_file(soul_file)
                self.analyses[sage] = analysis
                total_analysis["sage_analyses"][sage] = asdict(analysis)
        
        # サマリー生成
        total_loc = sum(analysis.lines_of_code for analysis in self.analyses.values())
        total_business_functions = sum(len(analysis.business_logic_functions) 
                                     for analysis in self.analyses.values())
        total_a2a_functions = sum(len(analysis.a2a_functions) 
                                for analysis in self.analyses.values())
        
        total_analysis["summary"] = {
            "total_soul_files": len(self.analyses),
            "total_lines_of_code": total_loc,
            "total_business_functions": total_business_functions,
            "total_a2a_functions": total_a2a_functions,
            "migration_complexity": "high" if total_loc > 2000 else "medium"
        }
        
        # 移行計画生成
        total_analysis["migration_plan"] = self._generate_migration_plan()
        
        # 廃止対象ファイル特定
        total_analysis["files_to_deprecate"] = self._identify_deprecation_targets()
        
        return total_analysis
    
    def _generate_migration_plan(self) -> Dict[str, Any]:
        """移行計画の生成"""
        plan = {
            "phase_1_analysis": {
                "description": "機能抽出・分析フェーズ",
                "tasks": []
            },
            "phase_2_integration": {
                "description": "4賢者システム統合フェーズ",
                "tasks": []
            },
            "phase_3_deprecation": {
                "description": "Soul系ファイル廃止フェーズ",
                "tasks": []
            }
        }
        
        # Phase 1: 分析タスク
        for sage, analysis in self.analyses.items():
            plan["phase_1_analysis"]["tasks"].append({
                "task": f"{sage} Soul機能抽出",
                "priority": analysis.migration_priority,
                "business_functions": len(analysis.business_logic_functions),
                "a2a_functions": len(analysis.a2a_functions)
            })
        
        # Phase 2: 統合タスク
        for sage in self.analyses.keys():
            plan["phase_2_integration"]["tasks"].append({
                "task": f"{sage}/business_logic.py への機能統合",
                "description": f"Soul実装をbusiness_logic.pyに移行"
            })
            plan["phase_2_integration"]["tasks"].append({
                "task": f"{sage}/a2a_agent.py への通信機能統合",
                "description": f"A2A通信をa2a_agent.pyに移行"
            })
        
        # Phase 3: 廃止タスク  
        plan["phase_3_deprecation"]["tasks"] = [
            {"task": "実験的Soul実装削除", "files": ["elder_flow_soul_integration.py"]},
            {"task": "プロトタイプSoul実装削除", "files": ["google_a2a_soul_integration.py"]},
            {"task": "バックアップSoul実装削除", "files": ["elders_guild/*/soul.py"]},
            {"task": "4賢者Soul実装削除", "files": [f"{sage}/soul.py" for sage in self.sages]},
            {"task": "Soul基底クラス削除", "files": ["shared_libs/soul_base.py", "libs/base_soul.py"]}
        ]
        
        return plan
    
    def _identify_deprecation_targets(self) -> List[str]:
        """廃止対象ファイルの特定"""
        deprecation_targets = []
        
        # Soul関連ファイル検索
        soul_patterns = [
            "**/soul.py",
            "**/base_soul.py", 
            "**/soul_base.py",
            "**/*soul*.py"
        ]
        
        for pattern in soul_patterns:
            for file_path in self.project_root.glob(pattern):
                if "venv" not in str(file_path) and "__pycache__" not in str(file_path):
                    rel_path = str(file_path.relative_to(self.project_root))
                    deprecation_targets.append(rel_path)
        
        return sorted(set(deprecation_targets))
    
    def generate_report(self) -> None:
        """分析レポートの生成・保存"""
        analysis_result = self.analyze_all_souls()
        
        # レポート保存
        report_file = self.project_root / "docs/analysis/soul_migration_detailed_analysis.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        # 概要出力
        print("\n" + "="*60)
        print("🌟 魂システム分析完了")
        print("="*60)
        
        summary = analysis_result["summary"]
        print(f"📊 Soul実装ファイル数: {summary['total_soul_files']}")
        print(f"📝 総行数: {summary['total_lines_of_code']:,}")
        print(f"🔧 ビジネス機能数: {summary['total_business_functions']}")
        print(f"📡 A2A機能数: {summary['total_a2a_functions']}")
        print(f"🎯 移行複雑度: {summary['migration_complexity']}")
        
        print(f"\n📄 詳細レポート保存: {report_file}")
        print(f"🗑️ 廃止対象ファイル数: {len(analysis_result['files_to_deprecate'])}")
        
        # 次のステップ提案
        print("\n🚀 推奨次ステップ:")
        print("1. 詳細分析レポート確認")
        print("2. 機能抽出・統合スクリプト実行")
        print("3. 段階的廃止スクリプト実行")
        
        print("="*60)


def main():
    """メイン実行"""
    analyzer = SoulSystemAnalyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()