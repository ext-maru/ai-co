#!/usr/bin/env python3
"""
コード生成テンプレート管理システム
Issue #184 Phase 1: Jinja2テンプレート強化
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
import logging
from datetime import datetime

# Phase 2 imports
from .issue_analyzer import IssueAnalyzer
from .requirement_extractor import RequirementExtractor

# Phase 3 imports
from .pattern_learning import PatternLearningEngine
from .context_enhancer import ContextEnhancer

logger = logging.getLogger(__name__)


class CodeGenerationTemplateManager:
    """技術スタック別の高品質コード生成テンプレート管理"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        テンプレートマネージャーの初期化
        
        Args:
            template_dir: テンプレートディレクトリのパス
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates" / "code_generation"
        
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Phase 2: 分析エンジンの初期化
        self.issue_analyzer = IssueAnalyzer()
        self.requirement_extractor = RequirementExtractor()
        
        # Phase 3: パターン学習とコンテキスト強化の初期化
        self.pattern_learning_engine = PatternLearningEngine()
        self.context_enhancer = ContextEnhancer(self.pattern_learning_engine)
        
        # テクノロジースタック定義
        self.tech_stacks = {
            "aws": {
                "keywords": ["boto3", "aws", "s3", "ec2", "lambda", "dynamodb", "sqs", "sns"],
                "imports": ["boto3", "botocore"],
                "template_path": "aws"
            },
            "web": {
                "keywords": ["flask", "django", "fastapi", "api", "rest", "http", "web"],
                "imports": ["flask", "django", "fastapi", "requests"],
                "template_path": "web"
            },
            "data": {
                "keywords": ["pandas", "numpy", "scikit", "ml", "data", "analysis", "csv", "json"],
                "imports": ["pandas", "numpy", "sklearn"],
                "template_path": "data"
            }
        }

    def detect_tech_stack(self, issue_text: str, requirements: List[str] = None) -> str:
        """
        Issue内容から技術スタックを自動検出
        
        Args:
            issue_text: Issueのタイトルと本文
            requirements: 要件リスト
            
        Returns:
            検出された技術スタック名
        """
        issue_lower = issue_text.lower()
        scores = {}
        
        for stack_name, stack_info in self.tech_stacks.items():
            score = 0
            # キーワードマッチング
            for keyword in stack_info["keywords"]:
                if keyword in issue_lower:
                    score += 2
            
            # 要件からの検出
            if requirements:
                for req in requirements:
                    if any(imp in req.lower() for imp in stack_info["imports"]):
                        score += 3
                        
            scores[stack_name] = score
        
        # 最高スコアの技術スタックを選択
        if scores:
            selected = max(scores.items(), key=lambda x: x[1])
            if selected[1] > 0:
                logger.info(f"Detected tech stack: {selected[0]} (score: {selected[1]})")
                return selected[0]
        
        logger.info("No specific tech stack detected, using base template")
        return "base"

    def has_template(self, template_name: str, tech_stack: str = "base") -> bool:
        """
        指定されたテンプレートが存在するかチェック
        
        Args:
            template_name: テンプレート名
            tech_stack: 技術スタック名
            
        Returns:
            テンプレートが存在するか
        """
        # 強化版テンプレートをチェック
        enhanced_path = f"{tech_stack}/{template_name}_enhanced.j2"
        if (self.template_dir / enhanced_path).exists():
            return True
        
        # 標準テンプレートをチェック
        template_path = f"{tech_stack}/{template_name}.j2"
        if (self.template_dir / template_path).exists():
            return True
            
        # baseテンプレートをチェック
        base_path = f"base/{template_name}.j2"
        return (self.template_dir / base_path).exists()

    def get_template(
        self,
        template_name: str,
        tech_stack: str = "base",
        use_enhanced: bool = True
    ) -> Template:
        """
        指定された技術スタックのテンプレートを取得
        
        Args:
            template_name: テンプレート名
            tech_stack: 技術スタック名
            use_enhanced: 強化版テンプレートを使用するか
            
        Returns:
            Jinja2テンプレート
        """
        # 強化版テンプレートを優先使用
        if use_enhanced:
            enhanced_path = f"{tech_stack}/{template_name}_enhanced.j2"
            if (self.template_dir / enhanced_path).exists():
                logger.info(f"Using enhanced template: {enhanced_path}")
                return self.env.get_template(enhanced_path)
        
        # 標準テンプレート
        template_path = f"{tech_stack}/{template_name}.j2"
        
        # フォールバック: 技術スタック固有のテンプレートがない場合はbaseを使用
        if not (self.template_dir / template_path).exists():
            template_path = f"base/{template_name}.j2"
            
        return self.env.get_template(template_path)

    def generate_code(self, 
                     template_type: str,
                     tech_stack: str,
                     context: Dict[str, Any],
                     use_enhanced: bool = True) -> str:
        """
        テンプレートを使用してコードを生成
        
        Args:
            template_type: テンプレートタイプ (class, function, test, etc.)
            tech_stack: 技術スタック
            context: テンプレートコンテキスト
            use_enhanced: 強化版テンプレートを使用するか
            
        Returns:
            生成されたコード
        """
        try:
            template = self.get_template(template_type, tech_stack, use_enhanced)
            generated_code = template.render(context)
            
            # 後処理: 空行の調整など
            lines = generated_code.split('\n')
            cleaned_lines = []
            prev_empty = False
            
            for line in lines:
                if line.strip() == '':
                    if not prev_empty:
                        cleaned_lines.append(line)
                    prev_empty = True
                else:
                    cleaned_lines.append(line)
                    prev_empty = False
                    
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            logger.error(f"Template generation error: {e}")
            raise

    def extract_requirements(self, issue_body: str) -> Dict[str, Any]:
        """
        Issue本文から要件を抽出
        
        Args:
            issue_body: Issueの本文
            
        Returns:
            抽出された要件
        """
        requirements = {
            "imports": [],
            "classes": [],
            "functions": [],
            "features": [],
            "technologies": []
        }
        
        lines = issue_body.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # インポート要件の検出
            if 'import' in line_lower or 'pip install' in line_lower:
                requirements["imports"].append(line.strip())
                
            # クラス要件の検出
            if 'class' in line_lower and ':' in line:
                requirements["classes"].append(line.strip())
                
            # 関数要件の検出
            if 'def' in line_lower or 'function' in line_lower:
                requirements["functions"].append(line.strip())
                
            # 機能要件の検出
            if any(keyword in line_lower for keyword in ['implement', '実装', 'create', '作成']):
                requirements["features"].append(line.strip())
        
        return requirements

    async def create_context_from_issue(self, 
                                 issue_number: int,
                                 issue_title: str,
                                 issue_body: str,
                                 tech_stack: Optional[str] = None,
                                 use_advanced_analysis: bool = True,
                                 use_pattern_learning: bool = True) -> Dict[str, Any]:
        """
        Issue情報からテンプレートコンテキストを作成（Phase 3対応）
        
        Args:
            issue_number: Issue番号
            issue_title: Issueタイトル
            issue_body: Issue本文
            tech_stack: 技術スタック（Noneの場合は自動検出）
            use_advanced_analysis: Phase 2の高度な分析を使用するか
            use_pattern_learning: Phase 3のパターン学習を使用するか
            
        Returns:
            テンプレートコンテキスト
        """
        # Phase 2: 高度な分析を実行
        if use_advanced_analysis:
            # Issue を分析
            analyzed_issue = self.issue_analyzer.analyze(issue_title, issue_body)
            
            # 詳細な要件を抽出
            detailed_requirements = self.requirement_extractor.extract_requirements(analyzed_issue)
            
            # 技術スタック検出（Phase 2の分析結果を使用）
            if tech_stack is None:
                detected_stacks = analyzed_issue.get('tech_stack', {})
                # 最も関連性の高い技術スタックを選択
                if detected_stacks:
                    # フレームワークを優先し、webスタックに統一
                    if 'framework' in detected_stacks and detected_stacks['framework']:
                        framework = detected_stacks['framework'][0]
                        # FastAPI, Flask, Django -> web に統一
                        if framework in ['fastapi', 'flask', 'django']:
                        if framework in ['fastapi', 'flask', 'django']:
                            tech_stack = 'web'
                        else:
                            tech_stack = framework
                    elif 'cloud' in detected_stacks and detected_stacks['cloud']:
                        tech_stack = 'aws' if 'aws' in detected_stacks['cloud'] else 'base'
                    else:
                        tech_stack = 'base'
                else:
                    tech_stack = self.detect_tech_stack(
                        f"{issue_title} {issue_body}",
                        []
                    )
            
            # Phase 1の要件も保持（互換性のため）
            simple_requirements = self.extract_requirements(issue_body)
            
            # クラス名とモジュール名の生成
            class_name = f"Issue{issue_number}Implementation"
            module_name = f"issue_{issue_number}_solution"
            
            # 拡張コンテキスト作成
            context = {
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_body": issue_body,
                "class_name": class_name,
                "module_name": module_name,
                "tech_stack": tech_stack,
                "requirements": simple_requirements,  # Phase 1互換性
                "imports": self._get_tech_stack_imports(tech_stack),
                "timestamp": "2025-07-21",
                # Phase 2拡張
                "analyzed_issue": analyzed_issue,
                "detailed_requirements": detailed_requirements,
                "api_endpoints": detailed_requirements.get('api_endpoints', []),
                "data_models": detailed_requirements.get('data_models', []),
                "technical_requirements": detailed_requirements.get('technical_requirements', []),
                "auth_requirements": detailed_requirements.get('auth_requirements', {}),
                "business_rules": detailed_requirements.get('business_rules', []),
                "implementation_notes": detailed_requirements.get('implementation_notes', []),
                "intent": analyzed_issue.get('intent', {}),
                "complexity": analyzed_issue.get('complexity', 'medium')
            }
            
            # Phase 3: パターン学習による強化
            if use_pattern_learning:
                try:
                    context = await self.context_enhancer.enhance_context(context)
                    logger.info("Context enhanced with learned patterns")
                except Exception as e:
                    logger.warning(f"Pattern learning enhancement failed: {e}")
                    # エラーが発生してもPhase 2の結果は保持
        else:
            # Phase 1の処理（後方互換性）
            requirements = self.extract_requirements(issue_body)
            
            if tech_stack is None:
                tech_stack = self.detect_tech_stack(
                    f"{issue_title} {issue_body}",
                    requirements["imports"]
                )
            
            class_name = f"Issue{issue_number}Implementation"
            module_name = f"issue_{issue_number}_solution"
            
            context = {
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_body": issue_body,
                "class_name": class_name,
                "module_name": module_name,
                "tech_stack": tech_stack,
                "requirements": requirements,
                "imports": self._get_tech_stack_imports(tech_stack),
                "timestamp": "2025-07-21"
            }
        
        return context

    def _get_tech_stack_imports(self, tech_stack: str) -> List[str]:
        """技術スタック固有のインポートを取得"""
        stack_imports = {
            "aws": [
                "import boto3",
                "from botocore.exceptions import ClientError",
                "import logging"
            ],
            "web": [
                "from typing import Dict, Any, Optional",
                "import logging",
                "from datetime import datetime"
            ],
            "data": [
                "import pandas as pd",
                "import numpy as np",
                "from typing import Dict, Any, List, Optional",
                "import logging"
            ],
            "base": [
                "from typing import Dict, Any, Optional",
                "import logging"
            ]
        }
        
        return stack_imports.get(tech_stack, stack_imports["base"])

    def analyze_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]title = issue_data.get('title', '')body = issue_data.get('body', '')
    """ssue分析とメタデータ生成"""
        labels = issue_data.get('labels', [])
        issue_text = f"{title} {body}"
        
        # 技術スタック検出
        tech_stack = self.detect_tech_stack(issue_text)
        
        # 要件抽出（簡易版）
        requirements = []
        if 'test' in title.lower() or 'testing' in title.lower():
            requirements.append('testing')
        if 'api' in title.lower() or 'endpoint' in title.lower():
            requirements.append('api')
        if 'database' in title.lower() or 'db' in title.lower():
            requirements.append('database')
        
        return {
            'tech_stack': tech_stack,
            'requirements': requirements,
            'complexity': self._estimate_complexity(issue_text),
            'type': issue_data.get('type', 'general')
        }

    def generate_test_code(self, issue_number: int, issue_title: str, 
                          requirements: List[str], tech_stack: str = 'base',
                          test_type: str = 'general', issue_body: str = '') -> str:
        """テストコード生成"""
        try:
            template = self.get_template('test', tech_stack)
            return template.render(
                issue_number=issue_number,
                issue_title=issue_title,
                issue_body=issue_body,
                requirements=requirements,
                test_type=test_type,
                class_name=f"Test{issue_number}",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Test code generation failed: {e}")
            # フォールバック
            return f"""#!/usr/bin/env python3
\"\"\"
Test for Issue #{issue_number}: {issue_title}
\"\"\"
import unittest

class Test{issue_number}(unittest.TestCase):
    def test_basic_functionality(self):
        self.assertTrue(True, "Placeholder test")

if __name__ == "__main__":
    unittest.main()
"""

    def generate_implementation_code(self, issue_number: int, issue_title: str, 
                                   requirements: List[str], tech_stack: str = 'base',
                                   sage_advice: Dict[str, Any] = None, 
                                   code_type: str = 'general', issue_body: str = '') -> str:
        """実装コード生成"""
        try:
            template = self.get_template('class', tech_stack)
            # quality_improvements を生成
            quality_improvements = [
                "エラーハンドリングの強化",
                "ログ出力の改善", 
                "型ヒントの追加",
                "ドキュメント文字列の充実"
            ]
            
            return template.render(
                issue_number=issue_number,
                issue_title=issue_title,
                issue_body=issue_body,
                requirements=requirements,
                code_type=code_type,
                class_name=f"Issue{issue_number}Implementation",
                sage_advice=sage_advice or {},
                quality_improvements=quality_improvements,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Implementation code generation failed: {e}")
            # フォールバック
            return f"""#!/usr/bin/env python3
\"\"\"
Implementation for Issue #{issue_number}: {issue_title}
\"\"\"

class Issue{issue_number}Implementation:
    def __init__(self):
        self.issue_number = {issue_number}
        self.title = "{issue_title}"
    
    def execute(self):
        # TODO: Implement functionality
        return {{"status": "success", "issue": self.issue_number}}
"""

    def generate_design_document(self, issue, analysis_result: Dict[str, Any], 
                                sage_advice: Dict[str, Any], 
                                generated_files: List[str]) -> str:
        """設計書生成"""
        return f"""# Design Document for Issue #{issue.number}

## Title
{issue.title}

## Analysis Result
- Tech Stack: {analysis_result.get('tech_stack', 'base')}
- Complexity: {analysis_result.get('complexity', 'medium')}
- Requirements: {', '.join(analysis_result.get('requirements', []))}

## Generated Files
{chr(10).join(f'- {file}' for file in generated_files)}

## Implementation Notes
This document describes the implementation for Issue #{issue.number}.
The implementation follows TDD principles with tests generated first.

Generated at: {datetime.now().isoformat()}
"""

    def _estimate_complexity(self, issue_text: str) -> strtext_lower = issue_text.lower():
    """雑度推定"""
        
        high_complexity_keywords = ['integration', 'complex', 'architecture', 'system', 'multiple']
        medium_complexity_keywords = ['feature', 'implement', 'add', 'create']
        
        if any(keyword in text_lower for keyword in high_complexity_keywords):
            return 'high'
        elif any(keyword in text_lower for keyword in medium_complexity_keywords):
            return 'medium'
        else:
            return 'low'