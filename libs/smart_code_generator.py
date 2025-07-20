#!/usr/bin/env python3
"""
Smart Code Generator
OSS組み合わせによる高品質コード生成システム
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import jinja2
import logging

logger = logging.getLogger(__name__)


class TechStackDetector:
    """技術スタック検出エンジン"""
    
    TECH_PATTERNS = {
        'aws': {
            'keywords': ['aws', 'boto3', 's3', 'dynamodb', 'lambda', 'ec2', 'cloudwatch', 'rds'],
            'services': {
                'boto3': ['s3', 'dynamodb', 'cloudwatch', 'lambda', 'ec2', 'rds'],
                's3': ['s3', 'bucket', 'object', 'storage'],
                'dynamodb': ['dynamodb', 'nosql', 'table', 'item'],
                'cloudwatch': ['cloudwatch', 'metrics', 'logs', 'monitoring'],
                'lambda': ['lambda', 'serverless', 'function'],
                'ec2': ['ec2', 'instance', 'compute'],
                'rds': ['rds', 'database', 'sql', 'mysql', 'postgresql']
            }
        },
        'web': {
            'keywords': ['flask', 'django', 'fastapi', 'rest', 'api', 'http', 'web'],
            'frameworks': ['flask', 'django', 'fastapi', 'tornado', 'bottle']
        },
        'data': {
            'keywords': ['pandas', 'numpy', 'sklearn', 'tensorflow', 'pytorch', 'data', 'ml'],
            'libraries': ['pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch']
        },
        'database': {
            'keywords': ['sql', 'postgresql', 'mysql', 'sqlite', 'database', 'db'],
            'types': ['postgresql', 'mysql', 'sqlite', 'mongodb', 'redis']
        }
    }
    
    def detect_tech_stack(self, text: str) -> Dict[str, Any]:
        """
        テキストから技術スタックを検出
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            検出された技術スタック情報
        """
        text_lower = text.lower()
        detected = {
            'primary_stack': None,
            'technologies': [],
            'services': [],
            'confidence': 0.0
        }
        
        stack_scores = {}
        
        for stack_name, stack_info in self.TECH_PATTERNS.items():
            score = 0
            found_keywords = []
            
            # キーワードマッチング
            for keyword in stack_info['keywords']:
                if keyword in text_lower:
                    score += 1
                    found_keywords.append(keyword)
            
            if score > 0:
                stack_scores[stack_name] = {
                    'score': score,
                    'keywords': found_keywords,
                    'confidence': score / len(stack_info['keywords'])
                }
        
        if stack_scores:
            # 最高スコアのスタックを主要技術として選択
            primary = max(stack_scores.items(), key=lambda x: x[1]['score'])
            detected['primary_stack'] = primary[0]
            detected['confidence'] = primary[1]['confidence']
            detected['technologies'] = primary[1]['keywords']
            
            # AWS特有のサービス検出
            if detected['primary_stack'] == 'aws':
                detected['services'] = self._detect_aws_services(text_lower)
        
        return detected
    
    def _detect_aws_services(self, text: str) -> List[str]:
        """AWS サービスを検出"""
        services = []
        aws_services = self.TECH_PATTERNS['aws']['services']
        
        for service, keywords in aws_services.items():
            if any(keyword in text for keyword in keywords):
                services.append(service)
        
        return services


class SmartTemplateSelector:
    """スマートテンプレート選択エンジン"""
    
    def __init__(self, template_dir: str = "templates/smart_generation"):
        self.template_dir = Path(template_dir)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def select_templates(self, tech_stack: Dict[str, Any]) -> Tuple[str, str]:
        """
        技術スタックに基づいてテンプレートを選択
        
        Args:
            tech_stack: 技術スタック情報
            
        Returns:
            (実装テンプレートパス, テストテンプレートパス)
        """
        primary = tech_stack.get('primary_stack', 'general')
        
        if primary == 'aws':
            return ('aws/boto3_implementation.py.j2', 'aws/boto3_test.py.j2')
        elif primary == 'web':
            return ('web/api_implementation.py.j2', 'web/api_test.py.j2')
        elif primary == 'data':
            return ('data/data_implementation.py.j2', 'data/data_test.py.j2')
        else:
            return ('general/implementation.py.j2', 'general/test.py.j2')


class SmartCodeGenerator:
    """スマートコード生成エンジン"""
    
    def __init__(self, template_dir: str = "templates/smart_generation"):
        self.tech_detector = TechStackDetector()
        self.template_selector = SmartTemplateSelector(template_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_implementation(
        self, 
        issue_number: int, 
        issue_title: str, 
        issue_body: str = ""
    ) -> Dict[str, Any]:
        """
        Issue情報から実装コードを生成
        
        Args:
            issue_number: Issue番号
            issue_title: Issueタイトル
            issue_body: Issue本文
            
        Returns:
            生成されたコード情報
        """
        # 1. 技術スタック検出
        full_text = f"{issue_title} {issue_body}"
        tech_stack = self.tech_detector.detect_tech_stack(full_text)
        
        self.logger.info(f"Detected tech stack: {tech_stack}")
        
        # 2. テンプレート選択
        impl_template_path, test_template_path = self.template_selector.select_templates(tech_stack)
        
        # 3. コンテキスト生成
        context = self._generate_context(issue_number, issue_title, issue_body, tech_stack)
        
        # 4. コード生成
        try:
            implementation_code = self._render_template(impl_template_path, context)
            test_code = self._render_template(test_template_path, context)
            
            return {
                "success": True,
                "implementation_code": implementation_code,
                "test_code": test_code,
                "tech_stack": tech_stack,
                "context": context,
                "templates_used": {
                    "implementation": impl_template_path,
                    "test": test_template_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tech_stack": tech_stack
            }
    
    def _generate_context(
        self, 
        issue_number: int, 
        issue_title: str, 
        issue_body: str, 
        tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テンプレート用コンテキストを生成"""
        
        # 基本情報
        class_name = f"Issue{issue_number}Implementation"
        module_name = f"issue_{issue_number}_implementation"
        description = f"Implementation for {issue_title}"
        
        # 技術固有の設定
        context = {
            "issue_number": issue_number,
            "issue_title": issue_title,
            "issue_body": issue_body,
            "class_name": class_name,
            "module_name": module_name,
            "description": description,
            "tech_stack": tech_stack
        }
        
        # AWS固有の設定
        if tech_stack.get('primary_stack') == 'aws':
            aws_services = tech_stack.get('services', ['s3'])  # デフォルトでS3
            if not aws_services:  # サービスが検出されない場合の安全策
                aws_services = ['s3', 'dynamodb', 'cloudwatch']
            
            context.update({
                "aws_services": aws_services,
                "use_asyncio": 'async' in issue_title.lower() or 'async' in issue_body.lower()
            })
        
        # Web固有の設定
        elif tech_stack.get('primary_stack') == 'web':
            context.update({
                "web_framework": self._detect_web_framework(tech_stack),
                "api_endpoints": self._extract_api_endpoints(issue_body),
                "use_async": 'fastapi' in tech_stack.get('technologies', [])
            })
        
        # データ処理固有の設定
        elif tech_stack.get('primary_stack') == 'data':
            context.update({
                "data_libraries": tech_stack.get('technologies', ['pandas']),
                "ml_framework": self._detect_ml_framework(tech_stack)
            })
        
        return context
    
    def _render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """テンプレートをレンダリング"""
        try:
            template = self.template_selector.jinja_env.get_template(template_path)
            return template.render(**context)
        except jinja2.TemplateNotFound:
            self.logger.warning(f"Template not found: {template_path}, using fallback")
            return self._generate_fallback_code(context)
    
    def _generate_fallback_code(self, context: Dict[str, Any]) -> str:
        """フォールバック用の基本コード生成"""
        return f'''"""
{context['description']}

Generated by Smart Code Generator (Fallback)
"""

class {context['class_name']}:
    """Basic implementation for {context['issue_title']}"""
    
    def __init__(self):
        self.initialized = True
    
    def execute(self, invalid_input=False):
        if invalid_input:
            raise ValueError("Invalid input provided")
        return "success"
    
    def __str__(self):
        return f"{context['class_name']} instance"
'''
    
    def _detect_web_framework(self, tech_stack: Dict[str, Any]) -> str:
        """Webフレームワークを検出"""
        technologies = tech_stack.get('technologies', [])
        frameworks = ['fastapi', 'flask', 'django']
        
        for framework in frameworks:
            if framework in technologies:
                return framework
        return 'flask'  # デフォルト
    
    def _extract_api_endpoints(self, text: str) -> List[str]:
        """API エンドポイントを抽出"""
        # 簡単な正規表現でエンドポイントらしきものを検出
        endpoints = re.findall(r'/[a-zA-Z0-9/_-]+', text)
        return endpoints[:5]  # 最大5個まで
    
    def _detect_ml_framework(self, tech_stack: Dict[str, Any]) -> str:
        """MLフレームワークを検出"""
        technologies = tech_stack.get('technologies', [])
        ml_frameworks = ['tensorflow', 'pytorch', 'sklearn']
        
        for framework in ml_frameworks:
            if framework in technologies:
                return framework
        return 'sklearn'  # デフォルト