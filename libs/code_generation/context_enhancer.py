#!/usr/bin/env python3
"""
コンテキスト強化システム
Issue #184 Phase 3: 学習済みパターンでテンプレートコンテキストを強化
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
import logging
from .pattern_learning import PatternLearningEngine

logger = logging.getLogger(__name__)


class SimilarImplementation:
    """類似実装データ"""
    
    def __init__(self, file_path:
        """初期化メソッド"""
    str, similarity_score: float, 
                 patterns: Dict[str, Any], code_snippet: str = "", 
                 usage_example: str = ""):
        self.file_path = file_path
        self.similarity_score = similarity_score
        self.patterns = patterns
        self.code_snippet = code_snippet
        self.usage_example = usage_example
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            "file_path": self.file_path,
            "similarity_score": self.similarity_score,
            "patterns": self.patterns,
            "code_snippet": self.code_snippet[:500],  # 最大500文字
            "usage_example": self.usage_example[:200]  # 最大200文字
        }


class ContextEnhancer:
    """学習済みパターンでコンテキストを強化"""
    
    def __init__(self, pattern_engine: Optional[PatternLearningEngine] = None):
        """
        コンテキスト強化器の初期化
        
        Args:
            pattern_engine: パターン学習エンジン
        """
        self.pattern_engine = pattern_engine or PatternLearningEngine()
        self.similarity_cache = {}
        
        # コード分析パターン
        self.implementation_patterns = [
            # API関連
            {"keywords": ["api", "endpoint", "rest", "http"], "category": "api", "tech_hints": ["fastapi", "flask"]},
            # データ処理
            {
                "keywords": ["data",
                "csv",
                "json",
                "pandas",
                "process"],
                "category": "data",
                "tech_hints": ["pandas",
                "numpy"]
            },
            # ファイル操作
            {
                "keywords": ["file",
                "read",
                "write",
                "path",
                "directory"],
                "category": "file",
                "tech_hints": ["pathlib",
                "os"]
            },
            # 非同期処理
            {
                "keywords": ["async",
                "await",
                "concurrent",
                "asyncio"],
                "category": "async",
                "tech_hints": ["asyncio",
                "aiohttp"]
            },
            # データベース
            {
                "keywords": ["database",
                "sql",
                "orm",
                "query"],
                "category": "database",
                "tech_hints": ["sqlalchemy",
                "asyncpg"]
            },
            # 認証・セキュリティ
            {
                "keywords": ["auth",
                "jwt",
                "token",
                "login",
                "security"],
                "category": "auth",
                "tech_hints": ["jwt",
                "bcrypt"]
            },
        ]
    
    async def enhance_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        学習済みパターンでコンテキストを強化
        
        Args:
            context: 元のコンテキスト
            
        Returns:
            強化されたコンテキスト
        """
        logger.info("Enhancing context with learned patterns...")
        
        enhanced_context = context.copy()
        
        # パターンベースの強化
        patterns = self.pattern_engine.get_patterns_for_context()
        
        # 1. インポートの強化
        enhanced_context["enhanced_imports"] = self._enhance_imports(context, patterns)
        
        # 2. コーディングスタイルの適用
        enhanced_context["style_guide"] = self._apply_coding_style(patterns)
        
        # 3. エラーハンドリングの強化
        enhanced_context["error_handling_guide"] = self._enhance_error_handling(context, patterns)
        
        # 4. ロギングパターンの適用
        enhanced_context["logging_guide"] = self._apply_logging_patterns(patterns)
        
        # 5. 命名規則の適用
        enhanced_context["naming_guide"] = self._apply_naming_conventions(context, patterns)
        
        # 6. プロジェクト固有のコンテキスト
        enhanced_context["project_context"] = await self._add_project_specific_context(
            context,
            patterns
        )
        
        # 7. 類似実装の提案
        enhanced_context["similar_implementations"] = await self._suggest_similar_implementations(context)
        
        # 8. 品質改善提案
        enhanced_context["quality_improvements"] = self._generate_quality_improvements(
            context,
            patterns
        )
        
        # 9. テストガイダンス（テスト生成時）
        if context.get("template_type") == "test":
            enhanced_context["test_guidance"] = self._provide_test_guidance(context, patterns)
        
        logger.info(f"Context enhanced with {len(enhanced_context) - len(context)} additional fields" \
            "Context enhanced with {len(enhanced_context) - len(context)} additional fields")
        return enhanced_context
    
    def _enhance_imports(self, context: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """インポートを強化"""
        current_imports = context.get("imports", [])
        suggested_imports = patterns.get("imports", [])
        
        # 重複除去しつつマージ
        all_imports = list(current_imports)
        
        for imp in suggested_imports:
            if imp not in all_imports:
                all_imports.append(imp)
        
        # Issue内容に基づく追加インポート
        issue_text = f"{context.get('issue_title', '')} {context.get('issue_body', '')}".lower()
        
        # 必要に応じて追加インポート
        additional_imports = []
        
        if any(word in issue_text for word in ["async", "await"]):
            additional_imports.append("import asyncio")
        
        if any(word in issue_text for word in ["json", "api", "response"]):
            additional_imports.append("import json")
        
        if any(word in issue_text for word in ["date", "time", "timestamp"]):
            additional_imports.append("from datetime import datetime")
        
        if any(word in issue_text for word in ["path", "file", "directory"]):
            additional_imports.append("from pathlib import Path")
        
        # 重複除去
        for imp in additional_imports:
            if imp not in all_imports:
                all_imports.append(imp)
        
        return all_imports
    
    def _apply_coding_style(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """コーディングスタイルガイドを適用"""
        style_prefs = patterns.get("style_preferences", {})
        
        return {
            "indentation": style_prefs.get("indentation", "4_spaces"),
            "line_length": style_prefs.get("recommended_line_length", 88),
            "docstring_style": "google",  # プロジェクト標準
            "type_hints": "enabled",
            "error_handling": "specific_exceptions"
        }
    
    def _enhance_error_handling(
        self,
        context: Dict[str,
        Any],
        patterns: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """エラーハンドリングを強化"""
        error_patterns = patterns.get("error_handling", {})
        
        # Issue内容から予想されるエラーを分析
        issue_text = f"{context.get('issue_title', '')} {context.get('issue_body', '')}".lower()
        
        suggested_exceptions = []
        
        # 一般的なエラーパターン
        if any(word in issue_text for word in ["file", "read", "write"]):
            suggested_exceptions.extend(["FileNotFoundError", "PermissionError", "IOError"])
        
        if any(word in issue_text for word in ["network", "api", "http", "request"]):
            suggested_exceptions.extend(["ConnectionError", "TimeoutError", "HTTPError"])
        
        if any(word in issue_text for word in ["json", "parse", "data"]):
            suggested_exceptions.extend(["JSONDecodeError", "ValueError"])
        
        if any(word in issue_text for word in ["database", "sql"]):
            suggested_exceptions.extend(["DatabaseError", "IntegrityError"])
        
        # プロジェクトで一般的なエラー
        common_exceptions = error_patterns.get("common_exceptions", [])
        suggested_exceptions.extend(common_exceptions[:3])  # 上位3つ
        
        return {
            "recommended_exceptions": list(set(suggested_exceptions)),
            "error_logging": "logger.error(f'Error: {e}')",
            "exception_chaining": True,
            "cleanup_pattern": "try-finally or context manager"
        }
    
    def _apply_logging_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """ロギングパターンを適用"""
        logging_patterns = patterns.get("logging", {})
        
        return {
            "logger_name": "__name__",
            "common_levels": logging_patterns.get("common_levels", ["info", "error", "warning"]),
            "format": "structured logging with context",
            "performance_logging": "log execution time for complex operations"
        }
    
    def _apply_naming_conventions(
        self,
        context: Dict[str,
        Any],
        patterns: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """命名規則を適用"""
        naming = patterns.get("naming", {})
        
        # Issue番号に基づく提案名
        issue_number = context.get("issue_number", 0)
        issue_title = context.get("issue_title", "")
        
        # クラス名の提案
        suggested_class = self._suggest_class_name(issue_title, issue_number)
        
        # 関数名の提案
        suggested_functions = self._suggest_function_names(issue_title, context)
        
        return {
            "class_naming": naming.get("class_naming", "PascalCase"),
            "function_naming": naming.get("function_naming", "snake_case"),
            "suggested_class_name": suggested_class,
            "suggested_function_names": suggested_functions,
            "constants_style": naming.get("constants_naming", "UPPER_CASE"),
            "private_prefix": naming.get("private_prefix", "_")
        }
    
    def _suggest_class_name(self, issue_title: str, issue_number: int) -> str:
        """クラス名を提案"""
        # キーワード抽出
        title_words = re.findall(r'[a-zA-Z]+', issue_title)
        meaningful_words = [w.capitalize() for w in title_words if len(w) > 2 and w.lower() not in {"the" \
            "the", "and", "for", "with"}]
        
        if meaningful_words:
            base_name = "".join(meaningful_words[:3])  # 最大3語
        else:
            base_name = f"Issue{issue_number}"
        
        # 一般的なサフィックス
        if any(word in issue_title.lower() for word in ["manage", "handler", "process"]):
            base_name += "Manager"
        elif any(word in issue_title.lower() for word in ["service", "api"]):
            base_name += "Service"
        elif any(word in issue_title.lower() for word in ["util", "helper"]):
            base_name += "Utility"
        else:
            base_name += "Implementation"
        
        return base_name
    
    def _suggest_function_names(self, issue_title: str, context: Dict[str, Any]) -> List[str]:
        """関数名を提案"""
        suggestions = []
        
        # API エンドポイントから関数名を生成
        api_endpoints = context.get("api_endpoints", [])
        for endpoint in api_endpoints:
            if hasattr(endpoint, 'method') and hasattr(endpoint, 'path'):
                func_name = self._endpoint_to_function_name(endpoint.method, endpoint.path)
                suggestions.append(func_name)
        
        # Issue タイトルから動詞を抽出
        title_lower = issue_title.lower()
        
        action_verbs = {
            "create": "create_",
            "add": "add_",
            "update": "update_",
            "delete": "delete_",
            "get": "get_",
            "fetch": "fetch_",
            "process": "process_",
            "handle": "handle_",
            "validate": "validate_",
            "generate": "generate_"
        }
        
        for verb, prefix in action_verbs.items():
            if verb in title_lower:
                suggestions.append(f"{prefix}data")
                break
        
        # 基本的な関数名
        if not suggestions:
            suggestions = ["execute", "process_request", "handle_task"]
        
        return suggestions[:5]  # 最大5つ
    
    def _endpoint_to_function_name(self, method: str, path: str) -> str:
        """エンドポイントから関数名を生成"""
        method_map = {
            "GET": "get_",
            "POST": "create_",
            "PUT": "update_",
            "DELETE": "delete_",
            "PATCH": "patch_"
        }
        
        prefix = method_map.get(method.upper(), "handle_")
        
        # パスから名詞を抽出
        path_parts = [part for part in path.split('/') if part and not part.startswith('{')]
        if path_parts:
            resource = path_parts[-1].replace('-', '_')
            return f"{prefix}{resource}"
        
        return f"{prefix}resource"
    
    async def _add_project_specific_context(
        self,
        context: Dict[str,
        Any],
        patterns: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """プロジェクト固有のコンテキストを追加"""
        vocabulary = patterns.get("vocabulary", [])
        
        # プロジェクト固有の用語を検出
        issue_text = f"{context.get('issue_title', '')} {context.get('issue_body', '')}".lower()
        
        relevant_terms = []
        for term in vocabulary:
            if term in issue_text:
                relevant_terms.append(term)
        
        return {
            "domain_terms": relevant_terms,
            "project_patterns": {
                "async_preferred": True,  # エルダーズギルドではasync推奨
                "logging_required": True,
                "type_hints_required": True,
                "documentation_required": True
            },
            "architectural_patterns": {
                "four_sages_integration": "Consider integration with 4 sages system",
                "elder_flow_compatibility": "Ensure compatibility with Elder Flow",
                "error_reporting": "Use incident sage for error reporting"
            }
        }
    
    async def _suggest_similar_implementations(
        self,
        context: Dict[str,
        Any]
    ) -> List[Dict[str, Any]]:
        """類似実装を提案"""
        issue_title = context.get("issue_title", "")
        issue_body = context.get("issue_body", "")
        tech_stack = context.get("tech_stack", "")
        
        # カテゴリを決定
        category = self._categorize_implementation(issue_title, issue_body)
        
        # 類似実装のモックデータ（実際の実装では既存コードを検索）
        similar_implementations = []
        
        if category == "api":
            similar_implementations.append({
                "file_path": "libs/integrations/github/auto_issue_processor.py",
                "similarity_score": 0.85,
                "patterns": {
                    "async_operations": True,
                    "error_handling": "comprehensive",
                    "logging": "structured",
                    "api_design": "REST-like"
                },
                "description": "GitHub API integration with async operations",
                "key_features": ["async/await", "error handling", "API calls"]
            })
        
        elif category == "data":
            similar_implementations.append({
                "file_path": "libs/code_generation/codebase_analyzer.py",
                "similarity_score": 0.78,
                "patterns": {
                    "data_processing": True,
                    "file_operations": True,
                    "analysis_methods": True
                },
                "description": "Data analysis and pattern extraction",
                "key_features": ["file processing", "data analysis", "pattern extraction"]
            })
        
        elif category == "async":
            similar_implementations.append({
                "file_path": "libs/elder_system/flow/elder_flow_engine.py",
                "similarity_score": 0.92,
                "patterns": {
                    "async_workflow": True,
                    "concurrent_processing": True,
                    "task_coordination": True
                },
                "description": "Async workflow engine with task coordination",
                "key_features": ["async workflows", "task management", "coordination"]
            })
        
        return similar_implementations
    
    def _categorize_implementation(self, title: str, body: str) -> str:
        """実装カテゴリを決定"""
        text = f"{title} {body}".lower()
        
        for pattern in self.implementation_patterns:
            if any(keyword in text for keyword in pattern["keywords"]):
                return pattern["category"]
        
        return "general"
    
    def _generate_quality_improvements(
        self,
        context: Dict[str,
        Any],
        patterns: Dict[str,
        Any]
    ) -> List[str]:
        """品質改善提案を生成"""
        improvements = []
        
        # 現在の品質要素をチェック
        tech_stack = context.get("tech_stack", "")
        complexity = context.get("complexity", "medium")
        
        # 基本的な改善提案
        improvements.extend([
            "Add comprehensive error handling with specific exceptions",
            "Include structured logging with context information",
            "Implement proper type hints for all function parameters and returns",
            "Add detailed docstrings with examples",
            "Consider async/await for I/O operations"
        ])
        
        # 技術スタック固有の提案
        if tech_stack == "web":
            improvements.extend([
                "Add input validation and sanitization",
                "Implement proper HTTP status codes",
                "Add rate limiting considerations",
                "Include CORS handling if needed"
            ])
        elif tech_stack == "data":
            improvements.extend([
                "Add data validation and type checking",
                "Implement efficient data processing with pandas",
                "Consider memory usage for large datasets",
                "Add data quality checks"
            ])
        elif tech_stack == "aws":
            improvements.extend([
                "Add boto3 session management",
                "Implement proper AWS credential handling",
                "Add retry logic for AWS API calls",
                "Consider resource cleanup"
            ])
        
        # 複雑度に応じた提案
        if complexity == "high":
            improvements.extend([
                "Break down into smaller, testable functions",
                "Consider using design patterns (Strategy, Factory, etc.)",
                "Add progress monitoring for long-running operations",
                "Implement proper resource management"
            ])
        
        return improvements[:8]  # 最大8つの提案
    
    def _provide_test_guidance(
        self,
        context: Dict[str,
        Any],
        patterns: Dict[str,
        Any]
    ) -> Dict[str, Any]:
        """テストガイダンスを提供"""
        test_patterns = patterns.get("test_patterns", {})
        
        return {
            "framework": test_patterns.get("framework", "pytest"),
            "test_types": [
                "unit_tests",
                "integration_tests",
                "edge_case_tests"
            ],
            "mocking_strategy": test_patterns.get("mocking_style", "unittest.mock"),
            "assertions": test_patterns.get("common_assertions", ["assert", "pytest.raises"]),
            "test_data": "Use fixtures for complex test data",
            "coverage_target": "Aim for 90%+ coverage",
            "async_testing": "Use pytest-asyncio for async code"
        }


# CLI実行用
async def main():
    """メイン関数（テスト用）"""
    enhancer = ContextEnhancer()
    
    # テスト用コンテキスト
    test_context = {
        "issue_number": 200,
        "issue_title": "Add JWT authentication API",
        "issue_body": "Implement JWT authentication with login and registration endpoints",
        "tech_stack": "web",
        "complexity": "medium"
    }
    
    print("🔧 Enhancing context...")
    enhanced = await enhancer.enhance_context(test_context)
    
    print(f"\n📊 Enhancement Results:")
    print(f"Original context keys: {len(test_context)}")
    print(f"Enhanced context keys: {len(enhanced)}")
    
    print(f"\n🔧 Enhanced imports: {len(enhanced.get('enhanced_imports', []))}")
    print(f"📋 Quality improvements: {len(enhanced.get('quality_improvements', []))}")
    print(f"🔍 Similar implementations: {len(enhanced.get('similar_implementations', []))}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())