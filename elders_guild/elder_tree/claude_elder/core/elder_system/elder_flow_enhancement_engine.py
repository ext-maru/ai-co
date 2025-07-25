#!/usr/bin/env python3
"""
Elder Flow Enhancement Engine
Phase 2-4統合: Issue分類と技術要件抽出を組み合わせたエンジン

主な機能:
1.0 Issue種別を自動判定
2.0 実装系の場合は技術要件を抽出
3.0 Elder Flowに渡すための構造化データを生成
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from libs.elder_system.issue_classifier_v2 import (
    IssueTypeClassifierV2, IssueCategory, IssueType
)
from libs.elder_system.technical_requirements_extractor import (
    TechnicalRequirementsExtractor, ExtractionResult
)

logger = logging.getLogger(__name__)


class ElderFlowMode(Enum):
    """Elder Flow実行モード"""
    DESIGN = "design"              # 設計・ドキュメント生成モード
    IMPLEMENTATION = "implementation"  # 実装モード（技術要件ベース）
    HYBRID = "hybrid"              # ハイブリッドモード


class ElderFlowEnhancementEngine:
    """Elder Flow強化エンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.issue_classifier = IssueTypeClassifierV2()
        self.requirements_extractor = TechnicalRequirementsExtractor()
        self.logger = logging.getLogger(__name__)
        
    def analyze_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Issueを分析してElder Flow用のデータを生成"""
        try:
            # デバッグ: issue_dataの構造を確認
            self.logger.debug(f"Issue data keys: {list(issue_data.keys())}")
            
            # bodyフィールドがない場合は空文字を設定
            if 'body' not in issue_data:
                issue_data['body'] = ''
            
            # 1.0 Issue種別を判定
            classification = self.issue_classifier.classify(issue_data)
            
            # 2.0 基本情報を構築
            result = {
                'issue_number': issue_data.get('number'),
                'issue_title': issue_data.get('title', ''),
                'issue_category': classification.category.value,
                'issue_type': classification.issue_type.value,
                'confidence': classification.confidence,
                'elder_flow_mode': self._determine_flow_mode(classification),
                'timestamp': datetime.now().isoformat()
            }
            
            # 3.0 カテゴリに応じた処理
            if classification.category == IssueCategory.IMPLEMENTATION_ORIENTED:
                # 実装系: 技術要件を抽出
                extraction_result = self.requirements_extractor.extract_requirements(issue_data)
                result['technical_analysis'] = self._format_technical_analysis(extraction_result)
                result['implementation_prompt'] = self.requirements_extractor.generate_implementation_prompt( \
                    extraction_result)
                result['recommended_approach'] = 'technical_implementation'
                
            elif classification.category == IssueCategory.DESIGN_ORIENTED:
                # 設計系: Elder Flowのデフォルト処理
                result['design_analysis'] = self._extract_design_elements(issue_data)
                result['recommended_approach'] = 'elder_flow_design'
                
            else:  # MAINTENANCE_ORIENTED or UNKNOWN
                # 保守系/不明: ハイブリッドアプローチ
                extraction_result = self.requirements_extractor.extract_requirements(issue_data)
                result['technical_analysis'] = self._format_technical_analysis(extraction_result)
                result['design_analysis'] = self._extract_design_elements(issue_data)
                result['recommended_approach'] = 'hybrid'
            
            # 4.0 Elder Flow実行のための推奨設定
            result['elder_flow_config'] = self._generate_elder_flow_config(
                classification, result.get('technical_analysis')
            )
            
            # 5.0 リスク評価
            result['risk_assessment'] = self._assess_risks(
                classification, result.get('technical_analysis')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze issue: {e}")
            return {
                'error': str(e),
                'issue_number': issue_data.get('number'),
                'elder_flow_mode': ElderFlowMode.DESIGN.value,
                'recommended_approach': 'manual_review'
            }
    
    def _determine_flow_mode(self, classification) -> str:
        """Elder Flowの実行モードを決定"""
        if classification.category == IssueCategory.IMPLEMENTATION_ORIENTED:
            return ElderFlowMode.IMPLEMENTATION.value
        elif classification.category == IssueCategory.DESIGN_ORIENTED:
            return ElderFlowMode.DESIGN.value
        else:
            return ElderFlowMode.HYBRID.value
    
    def _format_technical_analysis(self, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """技術分析結果をフォーマット"""
        return {
            'technical_stack': {
                'languages': extraction_result.technical_stack.languages,
                'frameworks': extraction_result.technical_stack.frameworks,
                'databases': extraction_result.technical_stack.databases,
                'services': extraction_result.technical_stack.services,
                'is_complex': len(extraction_result.technical_stack.languages) > 1
            },
            'requirements_summary': {
                'total': len(extraction_result.requirements),
                'by_type': self._count_requirements_by_type(extraction_result.requirements),
                'high_priority': len([r for r in extraction_result.requirements 
                                    if r.priority == 'high'])
            },
            'implementation_steps': extraction_result.implementation_steps,
            'complexity': extraction_result.estimated_complexity,
            'risks': extraction_result.risk_factors,
            'dependencies': extraction_result.dependencies
        }
    
    def _count_requirements_by_type(self, requirements) -> Dict[str, int]:
        """要件タイプ別のカウント"""
        counts = {}
        for req in requirements:
            req_type = req.requirement_type.value
            counts[req_type] = counts.get(req_type, 0) + 1
        return counts
    
    def _extract_design_elements(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """設計要素を抽出"""
        try:
            body = issue_data.get('body', '')
            if body is None:
                body = ''
            if isinstance(body, str):
                body = body.lower()
            else:
                body = str(body).lower()
            
            design_elements = {
                'has_architecture': any(keyword in body for keyword in 
                                      ['architecture', 'design', 'structure', '設計']),
                'has_documentation': any(keyword in body for keyword in 
                                       ['document', 'docs', 'readme', 'guide']),
                'has_diagrams': any(keyword in body for keyword in 
                                  ['diagram', 'chart', 'flow', 'uml']),
                'has_api_design': any(keyword in body for keyword in 
                                    ['api design', 'endpoint design', 'interface design']),
                'estimated_documents': self._estimate_document_count(body)
            }
            
            return design_elements
        except Exception as e:
            self.logger.error(f"Error in _extract_design_elements: {str(e)}")
            self.logger.error(f"Issue data type: {type(issue_data)}")
            self.logger.error(f"Issue data: {issue_data}")
            raise
    
    def _estimate_document_count(self, body: str) -> int:
        """生成すべきドキュメント数を推定"""
        count = 0
        doc_keywords = ['readme', 'guide', 'manual', 'specification', 'design doc']
        
        for keyword in doc_keywords:
            if keyword in body.lower():
                count += 1
        
        # セクション数からも推定
        if '##' in body:
            count += body.count('##')
        
        return max(1, min(count, 10))  # 1-10の範囲
    
    def _generate_elder_flow_config(
        self,
        classification,
        technical_analysis: Optional[Dict]
    ) -> Dict[str, Any]:
        """Elder Flow実行用の設定を生成"""
        config = {
            'mode': self._determine_flow_mode(classification),
            'quality_requirements': {
                'minimum_score': 85 if classification.category == IssueCategory.IMPLEMENTATION_ORIENTED else 70,
                'iron_will_compliance': True,
                'test_coverage': 90 if classification.category == IssueCategory.IMPLEMENTATION_ORIENTED else 80
            },
            'execution_phases': []
        }
        
        # 実行フェーズを決定
        if classification.category == IssueCategory.IMPLEMENTATION_ORIENTED:
            config['execution_phases'] = [
                '4_sages_consultation',
                'technical_implementation',
                'unit_test_creation',
                'integration_test',
                'quality_gate',
                'documentation'
            ]
        elif classification.category == IssueCategory.DESIGN_ORIENTED:
            config['execution_phases'] = [
                '4_sages_consultation',
                'design_generation',
                'documentation_creation',
                'diagram_generation',
                'quality_review'
            ]
        else:
            config['execution_phases'] = [
                '4_sages_consultation',
                'hybrid_analysis',
                'selective_implementation',
                'documentation',
                'quality_gate'
            ]
        
        # 技術的な複雑度に応じて調整
        if technical_analysis and technical_analysis.get('complexity') in ['high', 'very_high']:
            config['execution_phases'].insert(1, 'risk_mitigation_planning')
            config['quality_requirements']['additional_review'] = True
        
        return config
    
    def _assess_risks(self, classification, technical_analysis: Optional[Dict]) -> Dict[str, Any]:
        """リスク評価"""
        risks = {
            'overall_risk_level': 'low',
            'risk_factors': [],
            'mitigation_required': False
        }
        
        risk_score = 0
        
        # 分類の信頼度が低い場合
        if classification.confidence < 0.7:
            risks['risk_factors'].append({
                'type': 'classification_uncertainty',
                'description': 'Low confidence in issue classification',
                'severity': 'medium',
                'mitigation': 'Manual review recommended'
            })
            risk_score += 2
        
        # 技術的複雑度が高い場合
        if technical_analysis:
            complexity = technical_analysis.get('complexity', 'unknown')
            if complexity in ['high', 'very_high']:
                risks['risk_factors'].append({
                    'type': 'technical_complexity',
                    'description': f'High technical complexity detected: {complexity}',
                    'severity': 'high',
                    'mitigation': 'Phased implementation recommended'
                })
                risk_score += 3
            
            # 既存のリスク要因を追加
            for risk in technical_analysis.get('risks', []):
                risks['risk_factors'].append(risk)
                risk_score += 1
        
        # 全体的なリスクレベルを決定
        if risk_score >= 5:
            risks['overall_risk_level'] = 'high'
            risks['mitigation_required'] = True
        elif risk_score >= 3:
            risks['overall_risk_level'] = 'medium'
            risks['mitigation_required'] = True
        else:
            risks['overall_risk_level'] = 'low'
        
        return risks
    
    def generate_elder_flow_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """Elder Flow実行用の最適化されたプロンプトを生成"""
        mode = analysis_result.get('elder_flow_mode', 'design')
        
        prompt_parts = [
            f"# Elder Flow Execution - {mode.upper()} Mode",
            f"Issue: #{analysis_result.get('issue_number')} - {analysis_result.get('issue_title')}",
            f"Category: {analysis_result.get('issue_category')}",
            f"Type: {analysis_result.get('issue_type')}",
            ""
        ]
        
        # モードに応じたプロンプト生成
        if mode == ElderFlowMode.IMPLEMENTATION.value:
            prompt_parts.append("## Implementation Requirements")
            if 'implementation_prompt' in analysis_result:
                prompt_parts.append(analysis_result['implementation_prompt'])
            prompt_parts.append("\n## Quality Requirements")
            prompt_parts.append("- Follow TDD approach")
            prompt_parts.append("- Ensure 90% test coverage")
            prompt_parts.append("- No TODO/FIXME comments (Iron Will)")
            
        elif mode == ElderFlowMode.DESIGN.value:
            prompt_parts.append("## Design Requirements")
            design = analysis_result.get('design_analysis', {})
            if design.get('has_architecture'):
                prompt_parts.append("- Create comprehensive architecture documentation")
            if design.get('has_api_design'):
                prompt_parts.append("- Design RESTful API endpoints")
            prompt_parts.append(f"- Generate {design.get('estimated_documents', 1)} documentation files")
            
        else:  # HYBRID
            prompt_parts.append("## Hybrid Approach Required")
            prompt_parts.append("Combine design documentation with selective implementation:")
            prompt_parts.append("- Focus on critical components")
            prompt_parts.append("- Create both design docs and code")
        
        # リスク警告
        risk_assessment = analysis_result.get('risk_assessment', {})
        if risk_assessment.get('mitigation_required'):
            prompt_parts.append("\n## ⚠️ Risk Mitigation Required")
            for risk in risk_assessment.get('risk_factors', []):
                prompt_parts.append(f"- {risk['type']}: {risk['description']}")
        
        return "\n".join(prompt_parts)


# CLIテスト
if __name__ == "__main__":
    # テストデータ
    test_issue = {
        'number': 83,
        'title': '⚡ Performance optimization #83 - Implement caching layer',
        'body': '''## Description
We need to implement a Redis-based caching layer for our FastAPI application.

## Requirements
- Response time should be under 100ms
- Support for 10000 concurrent users
- 90% test coverage required

## Technical Details
- Python 3.11+
- FastAPI framework
- Redis for caching
''',
        'labels': ['enhancement', 'performance', 'backend']
    }
    
    engine = ElderFlowEnhancementEngine()
    result = engine.analyze_issue(test_issue)
    
    print("🔍 Analysis Result:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n📝 Elder Flow Prompt:")
    print(engine.generate_elder_flow_prompt(result))