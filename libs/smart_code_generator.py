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
        
        # Phase 2: Issue理解エンジン統合
        try:
            from libs.issue_intelligence_engine import IssueIntelligenceEngine
            self.intelligence_engine = IssueIntelligenceEngine()
            self.use_intelligence = True
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.info("Issue Intelligence Engine enabled")
        except ImportError as e:
            self.intelligence_engine = None
            self.use_intelligence = False
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.warning(f"Issue Intelligence Engine not available: {e}")
        
        # Phase 3: コードベース解析エンジン統合
        try:
            from libs.codebase_analysis_engine import CodebaseAnalysisEngine
            self.codebase_engine = CodebaseAnalysisEngine()
            self.use_codebase_analysis = True
            self.logger.info("Codebase Analysis Engine enabled")
        except ImportError as e:
            self.codebase_engine = None
            self.use_codebase_analysis = False
            self.logger.warning(f"Codebase Analysis Engine not available: {e}")
        
        # Phase 4: インテリジェントテスト生成統合
        try:
            from libs.intelligent_test_generator import IntelligentTestGenerator
            self.test_generator = IntelligentTestGenerator()
            self.use_test_generation = True
            self.logger.info("Intelligent Test Generator enabled")
        except ImportError as e:
            self.test_generator = None
            self.use_test_generation = False
            self.logger.warning(f"Intelligent Test Generator not available: {e}")
    
    def generate_implementation(
        self, 
        issue_number: int, 
        issue_title: str, 
        issue_body: str = ""
    ) -> Dict[str, Any]:
        """
        Issue情報から実装コードを生成 (Phase 2: 高度理解対応)
        
        Args:
            issue_number: Issue番号
            issue_title: Issueタイトル
            issue_body: Issue本文
            
        Returns:
            生成されたコード情報
        """
        full_text = f"{issue_title} {issue_body}"
        
        # Phase 2: Issue理解エンジンによる詳細分析
        if self.use_intelligence:
            try:
                intelligence = self.intelligence_engine.analyze_issue(issue_title, issue_body)
                self.logger.info(f"Issue intelligence analysis completed:")
                self.logger.info(f"  Primary domain: {intelligence.primary_domain}")
                self.logger.info(f"  Tech requirements: {len(intelligence.tech_requirements)}")
                self.logger.info(f"  Feature requirements: {len(intelligence.feature_requirements)}")
                self.logger.info(f"  Estimated effort: {intelligence.estimated_effort}")
            except Exception as e:
                self.logger.warning(f"Issue intelligence analysis failed: {e}")
                intelligence = None
        else:
            intelligence = None
        
        # Phase 3: コードベース解析による学習強化
        codebase_intelligence = None
        if self.use_codebase_analysis and intelligence:
            try:
                # 技術スタックに基づいてコードベース分析
                enhanced_tech_stack = {
                    'primary_stack': intelligence.primary_domain,
                    'services': [req.name.split('_', 1)[1] for req in intelligence.tech_requirements 
                               if req.category == intelligence.primary_domain and '_' in req.name][:5]
                }
                
                codebase_intelligence = self.codebase_engine.analyze_codebase(enhanced_tech_stack)
                self.logger.info(f"Codebase analysis completed:")
                self.logger.info(f"  Import patterns: {len(codebase_intelligence.import_patterns)}")
                self.logger.info(f"  Class patterns: {len(codebase_intelligence.class_patterns)}")
                self.logger.info(f"  Similar implementations found")
                
            except Exception as e:
                self.logger.warning(f"Codebase analysis failed: {e}")
                codebase_intelligence = None
        
        # 1. 技術スタック検出 (従来方式 + Intelligence統合)
        tech_stack = self.tech_detector.detect_tech_stack(full_text)
        
        # Intelligence結果で技術スタックを強化
        if intelligence and intelligence.tech_requirements:
            primary_tech = intelligence.primary_domain
            if primary_tech != 'general':
                tech_stack['primary_stack'] = primary_tech
                tech_stack['intelligence_confidence'] = max(
                    req.confidence for req in intelligence.tech_requirements
                )
                
                # AWS サービスの詳細検出
                if primary_tech == 'aws':
                    aws_services = []
                    for req in intelligence.tech_requirements:
                        if req.category == 'aws' and '_' in req.name:
                            service = req.name.split('_', 1)[1]
                            aws_services.append(service)
                    if aws_services:
                        tech_stack['services'] = list(set(aws_services))
        
        self.logger.info(f"Enhanced tech stack: {tech_stack}")
        
        # 2. テンプレート選択
        impl_template_path, test_template_path = self.template_selector.select_templates(tech_stack)
        
        # 3. 強化されたコンテキスト生成 (Phase 3統合)
        context = self._generate_enhanced_context(
            issue_number, issue_title, issue_body, tech_stack, intelligence, codebase_intelligence
        )
        
        # 4. コード生成
        try:
            implementation_code = self._render_template(impl_template_path, context)
            test_code = self._render_template(test_template_path, context)
            
            # Phase 4: インテリジェントテスト生成
            intelligent_tests = None
            if self.use_test_generation and implementation_code:
                try:
                    # Intelligence オブジェクトを辞書形式に変換
                    intelligence_dict = None
                    if intelligence:
                        intelligence_dict = {
                            'primary_domain': intelligence.primary_domain,
                            'tech_requirements': intelligence.tech_requirements,
                            'implementation_hints': intelligence.implementation_hints,
                            'estimated_effort': intelligence.estimated_effort
                        }
                    
                    intelligent_tests = self.test_generator.generate_comprehensive_tests(
                        implementation_code, intelligence_dict, codebase_intelligence
                    )
                    self.logger.info(f"Intelligent tests generated: {len(intelligent_tests.unit_tests)} unit, "
                                   f"{len(intelligent_tests.integration_tests)} integration, "
                                   f"{len(intelligent_tests.property_tests)} property")
                except Exception as e:
                    self.logger.warning(f"Intelligent test generation failed: {e}")
                    intelligent_tests = None
            
            return {
                "success": True,
                "implementation_code": implementation_code,
                "test_code": test_code,
                "tech_stack": tech_stack,
                "context": context,
                "intelligence": {
                    "primary_domain": intelligence.primary_domain if intelligence else "unknown",
                    "estimated_effort": intelligence.estimated_effort if intelligence else "medium",
                    "implementation_hints": intelligence.implementation_hints if intelligence else [],
                    "complexity_score": sum(intelligence.complexity_indicators.values()) / max(1, len(intelligence.complexity_indicators)) if intelligence else 0.5
                },
                "codebase_learning": {
                    "import_patterns_found": len(codebase_intelligence.import_patterns) if codebase_intelligence else 0,
                    "class_patterns_found": len(codebase_intelligence.class_patterns) if codebase_intelligence else 0,
                    "similar_implementations": len(context.get('similar_implementations', [])),
                    "learned_error_patterns": len(context.get('learned_error_patterns', []))
                },
                "intelligent_tests": {
                    "unit_tests": len(intelligent_tests.unit_tests) if intelligent_tests else 0,
                    "integration_tests": len(intelligent_tests.integration_tests) if intelligent_tests else 0,
                    "property_tests": len(intelligent_tests.property_tests) if intelligent_tests else 0,
                    "mock_configurations": len(intelligent_tests.mock_configurations) if intelligent_tests else 0,
                    "fixtures": len(intelligent_tests.fixtures) if intelligent_tests else 0,
                    "test_suite": intelligent_tests
                },
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
                "tech_stack": tech_stack,
                "intelligence": intelligence.primary_domain if intelligence else "unknown"
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
    
    def _generate_enhanced_context(
        self, 
        issue_number: int, 
        issue_title: str, 
        issue_body: str, 
        tech_stack: Dict[str, Any],
        intelligence,
        codebase_intelligence=None
    ) -> Dict[str, Any]:
        """強化されたコンテキスト生成 (Phase 2対応)"""
        
        # 基本コンテキスト
        context = self._generate_context(issue_number, issue_title, issue_body, tech_stack)
        
        # Intelligence による強化
        if intelligence:
            # 実装ヒントを追加
            context['implementation_hints'] = intelligence.implementation_hints
            
            # 機能要件から詳細メソッド生成
            context['feature_methods'] = []
            for feature in intelligence.feature_requirements[:5]:  # 最大5個
                method_name = f"{feature.action}_{feature.target.replace(' ', '_').lower()}"
                method_name = re.sub(r'[^a-zA-Z0-9_]', '', method_name)  # 無効文字除去
                context['feature_methods'].append({
                    'name': method_name,
                    'action': feature.action,
                    'target': feature.target,
                    'priority': feature.priority,
                    'details': feature.details
                })
            
            # 複雑度に基づく設定調整
            complexity_score = sum(intelligence.complexity_indicators.values()) / max(1, len(intelligence.complexity_indicators))
            context['complexity_level'] = 'high' if complexity_score > 0.6 else 'medium' if complexity_score > 0.3 else 'low'
            context['include_monitoring'] = complexity_score > 0.4
            context['include_caching'] = 'performance' in intelligence.complexity_indicators and intelligence.complexity_indicators['performance'] > 0.3
            context['include_async'] = 'real_time' in intelligence.complexity_indicators and intelligence.complexity_indicators['real_time'] > 0.3
            
            # キーエンティティの活用
            context['key_entities'] = intelligence.key_entities
            
            # 工数見積もりに基づくコメント詳細度
            context['detailed_comments'] = intelligence.estimated_effort in ['large', 'extra_large']
        
        # Phase 3: コードベース学習による強化
        if codebase_intelligence:
            # 学習したインポートパターンを追加
            context['learned_imports'] = []
            for pattern in codebase_intelligence.import_patterns[:5]:  # 上位5つ
                context['learned_imports'].append({
                    'module': pattern.module,
                    'alias': pattern.alias,
                    'frequency': pattern.frequency,
                    'context': pattern.context
                })
            
            # 学習したクラスパターンを追加
            context['learned_class_patterns'] = []
            for pattern in codebase_intelligence.class_patterns:
                if pattern.tech_domain == tech_stack.get('primary_stack', 'general'):
                    context['learned_class_patterns'].append({
                        'name': pattern.name,
                        'base_classes': pattern.base_classes,
                        'common_methods': pattern.methods[:5],  # 上位5メソッド
                        'attributes': pattern.attributes[:3]   # 上位3属性
                    })
            
            # エラーハンドリングパターンを追加
            context['learned_error_patterns'] = codebase_intelligence.common_error_handling[:3]
            
            # 命名規則を追加
            context['naming_conventions'] = codebase_intelligence.naming_conventions
            
            # 類似実装からの学習
            similar_files = []
            if hasattr(self, 'codebase_engine'):
                similar_files = self.codebase_engine.find_similar_implementations(tech_stack)
            context['similar_implementations'] = similar_files[:3]  # 最大3ファイル
        
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