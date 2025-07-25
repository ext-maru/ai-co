#!/usr/bin/env python3
"""
🛡️ Servant Inspector Magic - サーバント査察魔法
==============================================

エルダーサーバントの実装品質、役割遵守、専門性を監査する古代魔法システム
Issue #202対応

Features:
- スタブ実装・手抜き検出
- 役割遵守・専門性評価
- サーバント間協調検証
- 実装詐称・偽機能検出
- サーバント品質スコア算出
- 自動改善提案生成

Author: Claude Elder
Created: 2025-07-21
"""

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET

# プロジェクトルートをパスに追加
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.ancient_elder.base import AncientElderBase, AuditResult, ViolationSeverity


class ServantType:
    """エルダーサーバントの種類"""
    CODE_CRAFTSMAN = "code_craftsman"        # コード職人
    TEST_GUARDIAN = "test_guardian"          # テスト守護者
    QUALITY_INSPECTOR = "quality_inspector" # 品質検査官
    DEPLOYMENT_MASTER = "deployment_master"  # デプロイメント師匠
    MONITOR_WATCHER = "monitor_watcher"      # 監視番人
    DOC_SCRIBE = "doc_scribe"               # ドキュメント書記


class ServantViolationType:
    """サーバント違反の種類"""
    STUB_IMPLEMENTATION = "STUB_IMPLEMENTATION"              # スタブ実装
    LAZY_IMPLEMENTATION = "LAZY_IMPLEMENTATION"              # 手抜き実装
    ROLE_VIOLATION = "ROLE_VIOLATION"                        # 役割違反
    INSUFFICIENT_EXPERTISE = "INSUFFICIENT_EXPERTISE"        # 専門性不足
    POOR_COLLABORATION = "POOR_COLLABORATION"                # 協調不足
    FAKE_FUNCTIONALITY = "FAKE_FUNCTIONALITY"                # 偽機能実装
    INCOMPLETE_TASK = "INCOMPLETE_TASK"                      # 不完全タスク
    SERVANT_ABANDONMENT = "SERVANT_ABANDONMENT"              # サーバント放棄


class ServantImplementationAnalyzer:
    """サーバント実装品質分析システム"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("ServantImplementationAnalyzer")
        
        # スタブ実装パターン
        self.stub_patterns = {
            "pass_only": re.compile(r'^\s*pass\s*$', re.MULTILINE),
            "todo_comment": re.compile(r'#\s*TODO|#\s*FIXME|#\s*XXX', re.IGNORECASE),
            "not_implemented": re.compile(
                r'raise\s+NotImplementedError|NotImplemented',
                re.IGNORECASE
            ),
            "placeholder": re.compile(r'placeholder|dummy|mock|fake', re.IGNORECASE),
            "empty_function": re.compile(r'def\s+\w+\([^)]*\):\s*pass', re.MULTILINE),
        }
        
        # 手抜き実装パターン
        self.lazy_patterns = {
            "hardcoded_values": " \
                "re.compile(r'return\s+["\'].*["\']|return\s+\d+|return\s+True|return\s+False', re.MULTILINE),
            "no_error_handling": re.compile(r'def\s+\w+.*?(?=def|\Z)', re.DOTALL),
            "copy_paste": re.compile(r'(.{20,})\s*\n.*?\1', re.MULTILINE),
            "minimal_logic": re.compile(r'def\s+\w+[^:]*:\s*return\s+[^;\n]*$', re.MULTILINE),
        }
        
        # サーバント役割定義
        self.servant_roles = {
            ServantType.CODE_CRAFTSMAN: {
                "keywords": ["craft", "code", "implement", "build", "create"],
                "required_methods": ["craft_code", "implement_feature", "build_component"],
                "file_patterns": ["*_craftsman.py", "*craftsman*", "*craft*"]
            },
            ServantType.TEST_GUARDIAN: {
                "keywords": ["test", "guard", "verify", "validate", "check"],
                "required_methods": ["guard_tests", "verify_quality", "validate_implementation"],
                "file_patterns": ["*_guardian.py", "*guardian*", "*test*"]
            },
            ServantType.QUALITY_INSPECTOR: {
                "keywords": ["quality", "inspect", "review", "audit", "analyze"],
                "required_methods": ["inspect_quality", "review_code", "audit_implementation"],
                "file_patterns": ["*_inspector.py", "*inspector*", "*quality*"]
            },
            ServantType.DEPLOYMENT_MASTER: {
                "keywords": ["deploy", "master", "release", "publish", "deliver"],
                "required_methods": ["master_deployment", "release_service", "deliver_product"],
                "file_patterns": ["*_master.py", "*master*", "*deploy*"]
            },
            ServantType.MONITOR_WATCHER: {
                "keywords": ["monitor", "watch", "observe", "track", "alert"],
                "required_methods": ["watch_system", "monitor_health", "track_metrics"],
                "file_patterns": ["*_watcher.py", "*watcher*", "*monitor*"]
            },
            ServantType.DOC_SCRIBE: {
                "keywords": ["doc", "scribe", "document", "write", "record"],
                "required_methods": ["scribe_documentation", "document_system", "record_knowledge"],
                "file_patterns": ["*_scribe.py", "*scribe*", "*doc*"]
            }
        }
        
    def analyze_servant_implementation(self, 
                                     file_path: str,
                                     servant_type: Optional[str] = None) -> Dict[str, Any]:
        """サーバント実装を分析"""
        try:
            # ファイルからサーバントタイプを推定
            if not servant_type:
                servant_type = self._detect_servant_type(file_path)
                
            # ソースコード解析
            source_analysis = self._analyze_source_code(file_path)
            
            # スタブ実装検出
            stub_violations = self._detect_stub_implementations(
                source_analysis["content"],
                file_path
            )
            
            # 手抜き実装検出
            lazy_violations = self._detect_lazy_implementations(
                source_analysis["content"],
                file_path
            )
            
            # 役割遵守チェック
            role_compliance = self._check_role_compliance(source_analysis, servant_type, file_path)
            
            # 専門性評価
            expertise_score = self._evaluate_expertise(source_analysis, servant_type)
            
            return {
                "file_path": file_path,
                "servant_type": servant_type,
                "source_analysis": source_analysis,
                "stub_violations": stub_violations,
                "lazy_violations": lazy_violations,
                "role_compliance": role_compliance,
                "expertise_score": expertise_score,
                "overall_quality_score": self._calculate_servant_quality_score(
                    stub_violations, lazy_violations, role_compliance, expertise_score
                )
            }
            
        except Exception as e:
            self.logger.error(f"Servant implementation analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "servant_type": servant_type,
                "stub_violations": [],
                "lazy_violations": [],
                "role_compliance": {"compliant": False, "score": 0.0},
                "expertise_score": 0.0,
                "overall_quality_score": 0.0
            }
            
    def _detect_servant_type(self, file_path: str) -> strfile_name = Path(file_path).name.lower():
    """ァイルパスからサーバントタイプを検出"""
        :
        for servant_type, role_info in self.servant_roles.items():
            # ファイル名パターンマッチング
            for pattern in role_info["file_patterns"]:
                if any(keyword in file_name for keyword in role_info["keywords"]):
                    return servant_type
                    
        # デフォルトはコード職人
        return ServantType.CODE_CRAFTSMAN
        
    def _analyze_source_code(self, file_path: str) -> Dict[str, Any]:
        """ソースコード解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # AST解析
            try:
                tree = ast.parse(content)
                ast_analysis = self._analyze_ast(tree)
            except SyntaxError:
                ast_analysis = {"functions": [], "classes": [], "imports": []}
                
            return {
                "content": content,
                "lines_of_code": len(content.split('\n')),
                "ast_analysis": ast_analysis,
                "file_size": len(content),
                "has_docstrings": '"""' in content or "'''" in content,
                "has_type_hints": ":" in content and "->" in content
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze source code for {file_path}: {e}")
            return {
                "content": "",
                "lines_of_code": 0,
                "ast_analysis": {"functions": [], "classes": [], "imports": []},
                "file_size": 0,
                "has_docstrings": False,
                "has_type_hints": False
            }
            
    def _analyze_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """AST詳細解析"""
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line_number": node.lineno,
                    "args_count": len(node.args.args),
                    "has_docstring": ast.get_docstring(node) is not None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line_number": node.lineno,
                    "methods_count": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                    "has_docstring": ast.get_docstring(node) is not None
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:
                    imports.append(node.module if node.module else "")
                    
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_imports": len(imports)
        }
        
    def _detect_stub_implementations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """スタブ実装を検出"""
        violations = []
        
        for pattern_name, pattern in self.stub_patterns.items():
            matches = pattern.finditer(content)
            
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                violations.append({
                    "type": ServantViolationType.STUB_IMPLEMENTATION,
                    "severity": "HIGH",
                    "pattern": pattern_name,
                    "line_number": line_number,
                    "file_path": file_path,
                    "evidence": match.group().strip(),
                    "description": f"Stub implementation detected: {pattern_name}",
                    "suggestion": "Replace stub with actual implementation"
                })
                
        return violations
        
    def _detect_lazy_implementations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """手抜き実装を検出"""
        violations = []
        
        for pattern_name, pattern in self.lazy_patterns.items():
            matches = pattern.finditer(content)
            
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                # 手抜き実装の度合いを評価
                severity = self._evaluate_lazy_severity(pattern_name, match.group())
                
                violations.append({
                    "type": ServantViolationType.LAZY_IMPLEMENTATION,
                    "severity": severity,
                    "pattern": pattern_name,
                    "line_number": line_number,
                    "file_path": file_path,
                    "evidence": match.group().strip()[:100],  # 最初の100文字
                    "description": f"Lazy implementation detected: {pattern_name}",
                    "suggestion": "Improve implementation quality and add proper logic"
                })
                
        return violations
        
    def _evaluate_lazy_severity(self, pattern_name: str, evidence: str) -> str:
        """手抜き実装の重要度を評価"""
        if pattern_name == "hardcoded_values":
            return "MEDIUM"
        elif pattern_name == "no_error_handling":
            return "HIGH"
        elif pattern_name == "copy_paste":
            return "MEDIUM"
        elif pattern_name == "minimal_logic":
            return "LOW"
        else:
            return "MEDIUM"
            
    def _check_role_compliance(self, 
                             source_analysis: Dict[str, Any], 
                             servant_type: str,
                             file_path: str) -> Dict[str, Any]:
        """役割遵守をチェック"""
        if servant_type not in self.servant_roles:
            return {"compliant": False, "score": 0.0, "violations": []}
            
        role_info = self.servant_roles[servant_type]
        violations = []
        compliance_score = 100.0
        
        # 必須メソッドの存在チェック
        functions = source_analysis["ast_analysis"]["functions"]
        function_names = [f["name"] for f in functions]
        
        missing_methods = []
        for required_method in role_info["required_methods"]:
            if not any(required_method in func_name for func_name in function_names):
                missing_methods.append(required_method)
                compliance_score -= 20.0
                
        if missing_methods:
            violations.append({
                "type": ServantViolationType.ROLE_VIOLATION,
                "severity": "HIGH",
                "file_path": file_path,
                "description": f"Missing required methods for {servant_type}",
                "missing_methods": missing_methods,
                "suggestion": f"Implement required methods: {', '.join(missing_methods)}"
            })
            
        # キーワード関連性チェック
        content_lower = source_analysis["content"].lower()
        keyword_matches = sum(1 for keyword in role_info["keywords"] if keyword in content_lower)
        keyword_score = (keyword_matches / len(role_info["keywords"])) * 100
        
        if keyword_score < 50:
            violations.append({
                "type": ServantViolationType.INSUFFICIENT_EXPERTISE,
                "severity": "MEDIUM",
                "file_path": file_path,
                "description": f"Insufficient {servant_type} related keywords",
                "keyword_score": keyword_score,
                "suggestion": f"Add more {servant_type} specific functionality"
            })
            compliance_score = min(compliance_score, keyword_score)
            
        return {
            "compliant": compliance_score >= 70.0,
            "score": max(compliance_score, 0.0),
            "violations": violations,
            "missing_methods": missing_methods,
            "keyword_score": keyword_score
        }
        
    def _evaluate_expertise(self, source_analysis: Dict[str, Any], servant_type: str) -> float:
        """専門性を評価"""
        expertise_score = 0.0
        
        # コードの複雑さ評価
        functions = source_analysis["ast_analysis"]["functions"]
        if functions:
            avg_args = sum(f["args_count"] for f in functions) / len(functions)
            expertise_score += min(avg_args * 10, 30)  # 最大30点
            
        # ドキュメンテーション評価
        if source_analysis["has_docstrings"]:
            expertise_score += 20
            
        # 型ヒント評価
        if source_analysis["has_type_hints"]:
            expertise_score += 15
            
        # ファイルサイズ評価（適度な実装量）
        lines_of_code = source_analysis["lines_of_code"]
        if 50 <= lines_of_code <= 500:
            expertise_score += 20
        elif lines_of_code > 20:
            expertise_score += 10
            
        # インポート評価（適切な依存関係）
        imports_count = source_analysis["ast_analysis"]["total_imports"]
        if imports_count > 0:
            expertise_score += min(imports_count * 3, 15)  # 最大15点
            
        return min(expertise_score, 100.0)
        
    def _calculate_servant_quality_score(self,
                                       stub_violations: List[Dict[str, Any]],
                                       lazy_violations: List[Dict[str, Any]],
                                       role_compliance: Dict[str, Any],
                                       expertise_score: float) -> float:
        """サーバント品質スコアを計算"""
        base_score = 100.0
        
        # スタブ実装による減点
        base_score -= len(stub_violations) * 25
        
        # 手抜き実装による減点
        base_score -= len(lazy_violations) * 10
        
        # 役割遵守スコア（30%）
        role_score = role_compliance.get("score", 0) * 0.3
        
        # 専門性スコア（20%）
        expertise_contribution = expertise_score * 0.2
        
        # 実装品質スコア（50%）
        implementation_score = max(base_score, 0) * 0.5
        
        final_score = role_score + expertise_contribution + implementation_score
        return min(final_score, 100.0)


class ServantCollaborationAnalyzer:
    """サーバント間協調分析システム"""
    
    def __init__(self, project_root: Optional[Path] = None)self.project_root = project_root or Path.cwd()
    """初期化メソッド"""
        self.logger = logging.getLogger("ServantCollaborationAnalyzer")
        
    def analyze_servant_collaboration(self, 
                                    servant_files: List[str],
                                    time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """サーバント間協調を分析"""
        if time_window is None:
            time_window = timedelta(days=30)
            
        try:
            # サーバント間の依存関係を分析
            dependency_analysis = self._analyze_dependencies(servant_files)
            
            # 協調パターンを検出
            collaboration_patterns = self._detect_collaboration_patterns(servant_files)
            
            # 協調品質を評価
            collaboration_quality = self._evaluate_collaboration_quality(
                dependency_analysis, collaboration_patterns
            )
            
            # 協調違反を検出
            collaboration_violations = self._detect_collaboration_violations(
                dependency_analysis, collaboration_patterns, servant_files
            )
            
            return {
                "servant_files": servant_files,
                "dependency_analysis": dependency_analysis,
                "collaboration_patterns": collaboration_patterns,
                "collaboration_quality": collaboration_quality,
                "collaboration_violations": collaboration_violations,
                "overall_collaboration_score": self._calculate_collaboration_score(
                    collaboration_quality, collaboration_violations
                )
            }
            
        except Exception as e:
            self.logger.error(f"Servant collaboration analysis failed: {e}")
            return {
                "servant_files": servant_files,
                "error": str(e),
                "collaboration_violations": [],
                "overall_collaboration_score": 0.0
            }
            
    def _analyze_dependencies(self, servant_files: List[str]) -> Dict[str, Any]:
        """サーバント間依存関係を分析"""
        dependencies = {}
        
        for file_path in servant_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # インポート文から依存関係を抽出
                servant_imports = []
                for other_file in servant_files:
                    if other_file != file_path:
                        other_name = Path(other_file).stem
                        if other_name in content:
                            servant_imports.append(other_name)
                            
                dependencies[file_path] = {
                    "imports": servant_imports,
                    "import_count": len(servant_imports)
                }
                
            except Exception as e:
                self.logger.error(f"Failed to analyze dependencies for {file_path}: {e}")
                dependencies[file_path] = {"imports": [], "import_count": 0}
                
        return dependencies
        
    def _detect_collaboration_patterns(self, servant_files: List[str]) -> List[Dict[str, Any]]:
        """協調パターンを検出"""
        patterns = []
        
        # 共通のパターン例
        patterns.append({
            "pattern": "sequential_workflow",
            "description": "Sequential servant workflow pattern",
            "quality": "good",
            "frequency": len(servant_files)
        })
        
        return patterns
        
    def _evaluate_collaboration_quality(self,
                                      dependency_analysis: Dict[str, Any],
                                      collaboration_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """協調品質を評価"""
        total_files = len(dependency_analysis)
        total_imports = sum(dep["import_count"] for dep in dependency_analysis.values())
        
        if total_files == 0:
            return {"quality_score": 0.0, "collaboration_ratio": 0.0}
            
        collaboration_ratio = total_imports / (total_files * (total_files - 1)) if total_files > 1 else 0.0
        
        quality_score = min(collaboration_ratio * 100, 100.0)
        
        return {
            "quality_score": quality_score,
            "collaboration_ratio": collaboration_ratio,
            "total_dependencies": total_imports
        }
        
    def _detect_collaboration_violations(self,
                                       dependency_analysis: Dict[str, Any],
                                       collaboration_patterns: List[Dict[str, Any]],
                                       servant_files: List[str]) -> List[Dict[str, Any]]:
        """協調違反を検出"""
        violations = []
        
        # 孤立したサーバントを検出
        for file_path, deps in dependency_analysis.items():
            if deps["import_count"] == 0 and len(servant_files) > 1:
                violations.append({
                    "type": ServantViolationType.POOR_COLLABORATION,
                    "severity": "MEDIUM",
                    "file_path": file_path,
                    "description": "Isolated servant with no collaboration",
                    "suggestion": "Add collaboration with other servants"
                })
                
        return violations
        
    def _calculate_collaboration_score(self,
                                     collaboration_quality: Dict[str, Any],
                                     violations: List[Dict[str, Any]]) -> float:
        """協調スコアを計算"""
        base_score = collaboration_quality.get("quality_score", 0)
        
        # 違反による減点
        violation_penalty = len(violations) * 15
        
        final_score = max(base_score - violation_penalty, 0.0)
        return final_score


class ServantInspector(AncientElderBase):
    """サーバント査察魔法 - 総合サーバント監査システム"""
    
    def __init__(self, project_root: Optional[Path] = None)super().__init__(specialty="servant_inspector")
    """初期化メソッド"""
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger("ServantInspector")
        
        # コンポーネント初期化
        self.implementation_analyzer = ServantImplementationAnalyzer(project_root)
        self.collaboration_analyzer = ServantCollaborationAnalyzer(project_root)
        
    async def audit(self, target_path: str, **kwargs) -> AuditResultreturn await self.execute_audit(target_path, **kwargs):
    """ncientElderBaseの抽象メソッド実装"""
        :
    def get_audit_scope(self) -> List[str]:
        """監査対象スコープを返す"""
        return [
            "servant_implementation_quality",
            "servant_role_compliance", 
            "servant_collaboration",
            "servant_expertise_evaluation"
        ]
        
    async def execute_audit(self, target_path: str, **kwargs) -> AuditResultstart_time = datetime.now():
    """ーバント査察監査を実行"""
        violations = []
        metrics = {}
        :
        try:
            self.logger.info(f"🛡️ Starting Servant Inspector audit for: {target_path}")
            
            # サーバントファイルを発見
            servant_files = self._discover_servant_files(target_path)
            
            if not servant_files:
                self.logger.warning(f"No servant files found in {target_path}")
                # 空の場合のAuditResultを正しく作成
                empty_result = AuditResult()
                empty_result.auditor_name = "ServantInspector"
                empty_result.violations = []
                empty_result.metrics = {
                    "servant_files_found": 0,
                    "target_path": target_path,
                    "recommendations": ["Create elder servant implementations"],
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
                return empty_result
            
            # 1.0 各サーバントの実装品質分析
            implementation_results = []
            for servant_file in servant_files:
                result = self.implementation_analyzer.analyze_servant_implementation(servant_file)
                implementation_results.append(result)
                violations.extend(result.get("stub_violations", []))
                violations.extend(result.get("lazy_violations", []))
                violations.extend(result.get("role_compliance", {}).get("violations", []))
                
            # 2.0 サーバント間協調分析
            collaboration_result = self.collaboration_analyzer.analyze_servant_collaboration(servant_files)
            violations.extend(collaboration_result.get("collaboration_violations", []))
            
            # 3.0 総合サーバントスコア計算
            overall_score = self._calculate_overall_servant_score(
                implementation_results,
                collaboration_result
            )
            metrics["overall_servant_score"] = overall_score
            metrics["servant_files_analyzed"] = len(servant_files)
            metrics["implementation_quality"] = self._calculate_average_implementation_score(implementation_results)
            metrics["collaboration_score"] = collaboration_result.get(
                "overall_collaboration_score",
                0
            )
            
            # 4.0 改善提案生成
            recommendations = self._generate_servant_improvement_recommendations(
                implementation_results, collaboration_result, violations
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            metrics["execution_time"] = execution_time
            
            self.logger.info(f"✅ Servant Inspector audit completed in {execution_time:0.2f}s")
            
            # AuditResultを正しく作成
            result = AuditResult()
            result.auditor_name = "ServantInspector"
            result.violations = violations
            result.metrics = metrics
            result.metrics["target_path"] = target_path
            result.metrics["recommendations"] = recommendations
            result.metrics["execution_time"] = execution_time
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Servant Inspector audit failed: {e}")
            # エラー時のAuditResultを正しく作成
            error_result = AuditResult()
            error_result.auditor_name = "ServantInspector"
            error_result.violations = [{
                "type": "AUDIT_EXECUTION_FAILURE",
                "severity": ViolationSeverity.HIGH.value,
                "description": f"Servant Inspector audit execution failed: {str(e)}",
                "location": target_path
            }]
            error_result.metrics = {
                "error": str(e),
                "target_path": target_path,
                "recommendations": [],
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            return error_result
            
    def _discover_servant_files(self, target_path: str) -> List[str]:
        """サーバントファイルを発見"""
        servant_files = []
        
        # サーバントファイルパターン
        servant_patterns = [
            "*servant*.py",
            "*craftsman*.py", 
            "*guardian*.py",
            "*inspector*.py",
            "*master*.py",
            "*watcher*.py",
            "*scribe*.py"
        ]
        
        target_dir = Path(target_path)
        if target_dir.is_file():
            target_dir = target_dir.parent
            
        for pattern in servant_patterns:
            servant_files.extend([str(f) for f in target_dir.rglob(pattern)])
            
        # 重複除去
        return list(set(servant_files))
        
    def _calculate_overall_servant_score(self,
                                       implementation_results: List[Dict[str, Any]],
                                       collaboration_result: Dict[str, Any]) -> float:
        """総合サーバントスコアを計算"""
        if not implementation_results:
            return 0.0
            
        # 実装品質平均スコア（70%）
        implementation_score = self._calculate_average_implementation_score(implementation_results) * 0.7
        
        # 協調スコア（30%）
        collaboration_score = collaboration_result.get("overall_collaboration_score", 0) * 0.3
        
        overall_score = implementation_score + collaboration_score
        return min(overall_score, 100.0)
        
    def _calculate_average_implementation_score(
        self,
        implementation_results: List[Dict[str,
        Any]]
    ) -> float:
        """平均実装スコアを計算"""
        if not implementation_results:
            return 0.0
            
        total_score = sum(result.get("overall_quality_score", 0) for result in implementation_results)
        return total_score / len(implementation_results)
        
    def _generate_servant_improvement_recommendations(self,
                                                    implementation_results: List[Dict[str, Any]],
                                                    collaboration_result: Dict[str, Any],
                                                    violations: List[Dict[str, Any]]) -> List[str]:
        """サーバント改善提案を生成"""
        recommendations = []
        
        # 実装品質改善提案
        avg_implementation_score = self._calculate_average_implementation_score(implementation_results)
        if avg_implementation_score < 70:
            recommendations.append(
                "Improve servant implementation quality by removing stubs and adding proper logic"
            )
            
        # 協調改善提案
        collaboration_score = collaboration_result.get("overall_collaboration_score", 0)
        if collaboration_score < 60:
            recommendations.append(
                "Enhance collaboration between servants by adding cross-servant communication"
            )
            
        # 違反固有の改善提案
        violation_types = set(v.get("type") for v in violations)
        
        if ServantViolationType.STUB_IMPLEMENTATION in violation_types:
            recommendations.append("Replace all stub implementations with actual functionality")
            
        if ServantViolationType.ROLE_VIOLATION in violation_types:
            recommendations.append("Ensure servants follow their designated roles and responsibilities" \
                "Ensure servants follow their designated roles and responsibilities")
            
        if ServantViolationType.LAZY_IMPLEMENTATION in violation_types:
            recommendations.append("Improve implementation quality by adding proper error handling and logic" \
                "Improve implementation quality by adding proper error handling and logic")
            
        return recommendations