#!/usr/bin/env python3
"""
📋 Issue Quality Bridge
イシューローダーと品質システムの連携ブリッジ

Features:
- 品質問題の自動Issue作成
- 品質改善要求の構造化
- エルダーズギルド品質標準準拠
- 4賢者連携によるIssue品質向上
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, '/home/aicompany/ai_co')

from libs.elders_code_quality_engine import EldersCodeQualityEngine
from libs.four_sages_quality_bridge import (
    get_four_sages_quality_orchestrator,
    QualityIncident,
    QualityTask
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    """品質Issue構造"""
    issue_id: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    category: str  # quality_improvement, iron_will_violation, security_fix
    affected_files: List[str]
    quality_metrics: Dict[str, Any]
    technical_details: Dict[str, Any]
    implementation_plan: List[str]
    acceptance_criteria: List[str]
    estimated_effort: str
    business_value: str
    tags: List[str]
    created_at: datetime
    sage_recommendations: Dict[str, List[str]]

class QualityIssueGenerator:
    """品質Issue生成器"""
    
    def __init__(self):
        self.issue_templates = self._load_issue_templates()
        self.elder_guild_standards = self._load_elder_guild_standards()
        
    def _load_issue_templates(self) -> Dict[str, Dict]:
        """Issueテンプレート読み込み"""
        return {
            'quality_improvement': {
                'title_template': '🔧 Quality Improvement: {file_name} (Score: {quality_score}/100)',
                'description_template': '''
## 📊 Quality Analysis Summary

**Current Quality Score:** {quality_score}/100
**Iron Will Compliance:** {'✅' if iron_will_compliance else '❌'}
**TDD Compatibility:** {'✅' if tdd_compatibility else '❌'}

## 🚨 Issues Detected

{issues_list}

## 💡 Improvement Recommendations

{suggestions_list}

## 🎯 Technical Implementation Plan

{implementation_steps}

## ✅ Acceptance Criteria

{acceptance_criteria}

## 📈 Expected Outcomes

- Quality score improvement: {quality_score} → {target_score}
- Reduced technical debt
- Enhanced maintainability
- Better test coverage

## 🏛️ Elder Guild Standards Compliance

This issue follows Elder Guild Issue Creation Standards (Tier 1-3):
- ✅ Root cause analysis completed
- ✅ Technical implementation details provided
- ✅ Phased implementation plan
- ✅ Quantitative success criteria
''',
                'tags': ['quality', 'technical-debt', 'elder-guild-standard']
            },
            'iron_will_violation': {
                'title_template': '⚔️ CRITICAL: Iron Will Violation in {file_name}',
                'description_template': '''
## 🚨 CRITICAL ISSUE: Iron Will Policy Violation

**Elder Guild Policy:** No workarounds or temporary solutions allowed
**Violation Type:** TODO/FIXME/Workaround comments detected
**Severity:** CRITICAL - Immediate action required

## 📍 Violation Details

**File:** {file_path}
**Violations Found:** {violation_count}

{violation_details}

## ⚡ IMMEDIATE ACTIONS REQUIRED

1. **Remove all TODO/FIXME comments**
2. **Complete all temporary implementations**
3. **Implement proper solutions**
4. **Add comprehensive tests**

## 🏛️ Elder Guild Iron Will Protocol

This violation requires immediate resolution under Elder Guild Iron Will Protocol:
- **Priority:** CRITICAL
- **SLA:** Must be resolved within 24 hours
- **Escalation:** Auto-escalated to Elder Council if not resolved

## ✅ Completion Criteria

- [ ] All TODO/FIXME comments removed
- [ ] All temporary code replaced with proper implementation
- [ ] Code passes Iron Will compliance check
- [ ] Quality score above 70/100
- [ ] Comprehensive tests added

## 🎯 Business Impact

**Direct Value:** Eliminates technical debt and reduces maintenance costs
**Strategic Value:** Maintains Elder Guild code quality standards
''',
                'tags': ['critical', 'iron-will', 'policy-violation', 'immediate-action']
            },
            'security_vulnerability': {
                'title_template': '🛡️ SECURITY: High-Risk Vulnerability in {file_name}',
                'description_template': '''
## 🛡️ SECURITY VULNERABILITY DETECTED

**Security Risk Level:** {max_risk_level}/10
**Vulnerability Count:** {vulnerability_count}
**Immediate Action Required:** YES

## 🚨 Security Issues

{security_details}

## 🔒 Security Remediation Plan

{security_fixes}

## 🧪 Testing Requirements

- [ ] Security vulnerability tests added
- [ ] Penetration testing performed
- [ ] Security code review completed
- [ ] Input validation verified

## 📊 Risk Assessment

**Technical Risk:** High - Security vulnerabilities present
**Business Risk:** High - Potential data breach or system compromise
**Compliance Risk:** High - May violate security standards

## ✅ Security Acceptance Criteria

- [ ] All high-risk vulnerabilities fixed
- [ ] Security scan passes clean
- [ ] Input validation implemented
- [ ] Error handling secured
- [ ] Security tests added and passing

## 🏛️ Elder Guild Security Standards

This issue addresses critical security concerns under Elder Guild Security Protocol.
''',
                'tags': ['security', 'vulnerability', 'critical', 'compliance']
            }
        }
        
    def _load_elder_guild_standards(self) -> Dict:
        """エルダーズギルド標準読み込み"""
        return {
            'minimum_quality_score': 70,
            'iron_will_required': True,
            'tdd_compatibility_required': False,  # Recommended but not required
            'security_risk_threshold': 7,
            'issue_tier_requirements': {
                'tier_1': ['root_cause_analysis', 'technical_details', 'implementation_plan', 'success_criteria'],
                'tier_2': ['effort_estimation', 'business_value', 'quality_assurance', 'risk_factors'],
                'tier_3': ['comprehensiveness', 'scalability', 'system_impact']
            }
        }
        
    async def generate_quality_issue_from_analysis(self, file_path: str, 
                                                 quality_analysis: Dict,
                                                 four_sages_analysis: Dict = None) -> QualityIssue:
        """品質分析からIssue生成"""
        analysis = quality_analysis.get('analysis', {})
        quality_score = analysis.get('quality_score', 0)
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        
        # Issue種別決定
        issue_category = self._determine_issue_category(analysis)
        
        # Issue ID生成
        issue_id = f"QI_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{issue_category}_{hash(file_path) % 10000}"
        
        # テンプレート選択
        template = self.issue_templates.get(issue_category, self.issue_templates['quality_improvement'])
        
        # Issue内容生成
        issue_content = await self._generate_issue_content(
            file_path, analysis, template, four_sages_analysis
        )
        
        # 4賢者推奨事項抽出
        sage_recommendations = self._extract_sage_recommendations(four_sages_analysis)
        
        quality_issue = QualityIssue(
            issue_id=issue_id,
            title=issue_content['title'],
            description=issue_content['description'],
            priority=issue_content['priority'],
            category=issue_category,
            affected_files=[file_path],
            quality_metrics={
                'current_score': quality_score,
                'target_score': max(70, quality_score + 20),
                'iron_will_compliance': iron_will_compliance,
                'issues_count': len(analysis.get('issues', [])),
                'security_risks_count': len(analysis.get('bug_risks', []))
            },
            technical_details=issue_content['technical_details'],
            implementation_plan=issue_content['implementation_plan'],
            acceptance_criteria=issue_content['acceptance_criteria'],
            estimated_effort=issue_content['estimated_effort'],
            business_value=issue_content['business_value'],
            tags=template['tags'] + [f'score-{int(quality_score)}'],
            created_at=datetime.now(),
            sage_recommendations=sage_recommendations
        )
        
        return quality_issue
        
    def _determine_issue_category(self, analysis: Dict) -> str:
        """Issue カテゴリ決定"""
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        bug_risks = analysis.get('bug_risks', [])
        quality_score = analysis.get('quality_score', 100)
        
        # Iron Will違反は最優先
        if not iron_will_compliance:
            return 'iron_will_violation'
            
        # 高セキュリティリスクも優先
        high_security_risks = [risk for risk in bug_risks if risk.get('risk_level', 0) > 7]
        if high_security_risks:
            return 'security_vulnerability'
            
        # それ以外は品質改善
        return 'quality_improvement'
        
    async def _generate_issue_content(self, file_path: str, analysis: Dict, 
                                    template: Dict, four_sages_analysis: Dict = None) -> Dict:
        """Issue内容生成"""
        file_name = Path(file_path).name
        quality_score = analysis.get('quality_score', 0)
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        tdd_compatibility = analysis.get('tdd_compatibility', False)
        issues = analysis.get('issues', [])
        suggestions = analysis.get('suggestions', [])
        bug_risks = analysis.get('bug_risks', [])
        
        # タイトル生成
        title = template['title_template'].format(
            file_name=file_name,
            file_path=file_path,
            quality_score=quality_score,
            max_risk_level=max([risk.get('risk_level', 0) for risk in bug_risks], default=0),
            vulnerability_count=len(bug_risks),
            violation_count=len([i for i in issues if 'TODO' in i.get('description', '')])
        )
        
        # Issues詳細生成
        issues_list = self._format_issues_list(issues)
        suggestions_list = self._format_suggestions_list(suggestions)
        security_details = self._format_security_details(bug_risks)
        violation_details = self._format_violation_details(issues)
        
        # 実装計画生成
        implementation_plan = self._generate_implementation_plan(analysis)
        
        # 受け入れ基準生成
        acceptance_criteria = self._generate_acceptance_criteria(analysis)
        
        # 説明文生成
        description = template['description_template'].format(
            file_path=file_path,
            quality_score=quality_score,
            target_score=max(70, quality_score + 20),
            iron_will_compliance=iron_will_compliance,
            tdd_compatibility=tdd_compatibility,
            issues_list=issues_list,
            suggestions_list=suggestions_list,
            security_details=security_details,
            violation_details=violation_details,
            implementation_steps='\n'.join([f"{i+1}. {step}" for i, step in enumerate(implementation_plan)]),
            acceptance_criteria='\n'.join([f"- [ ] {criteria}" for criteria in acceptance_criteria]),
            max_risk_level=max([risk.get('risk_level', 0) for risk in bug_risks], default=0),
            vulnerability_count=len(bug_risks),
            violation_count=len([i for i in issues if 'TODO' in i.get('description', '')]),
            security_fixes='\n'.join([f"- Fix: {risk.get('description', 'Unknown')}" for risk in bug_risks])
        )
        
        # 優先度決定
        priority = self._determine_priority(analysis)
        
        # 作業量見積もり
        estimated_effort = self._estimate_effort(analysis)
        
        # ビジネス価値
        business_value = self._generate_business_value(analysis)
        
        return {
            'title': title,
            'description': description,
            'priority': priority,
            'technical_details': {
                'complexity_score': analysis.get('complexity_score', 1),
                'maintainability_index': analysis.get('maintainability_index', 0),
                'issues_by_severity': self._group_issues_by_severity(issues),
                'risk_assessment': self._assess_risks(bug_risks)
            },
            'implementation_plan': implementation_plan,
            'acceptance_criteria': acceptance_criteria,
            'estimated_effort': estimated_effort,
            'business_value': business_value
        }
        
    def _format_issues_list(self, issues: List[Dict]) -> str:
        """Issue一覧フォーマット"""
        if not issues:
            return "No major issues detected."
            
        formatted_issues = []
        for i, issue in enumerate(issues[:10], 1):  # 最大10件
            severity = issue.get('severity', 0)
            severity_icon = "🔥" if severity > 7 else "⚠️" if severity > 4 else "📝"
            formatted_issues.append(
                f"{i}. {severity_icon} **{issue.get('name', 'Unknown')}** (Severity: {severity}/10)\n"
                f"   - {issue.get('description', 'No description')}"
            )
            
        return '\n\n'.join(formatted_issues)
        
    def _format_suggestions_list(self, suggestions: List[Dict]) -> str:
        """提案一覧フォーマット"""
        if not suggestions:
            return "No specific suggestions available."
            
        formatted_suggestions = []
        for i, suggestion in enumerate(suggestions[:8], 1):  # 最大8件
            priority = suggestion.get('priority', 'medium')
            priority_icon = "🔥" if priority == 'high' else "⚡" if priority == 'medium' else "💡"
            formatted_suggestions.append(
                f"{i}. {priority_icon} **{suggestion.get('title', 'Suggestion')}**\n"
                f"   - {suggestion.get('description', 'No description')}"
            )
            
        return '\n\n'.join(formatted_suggestions)
        
    def _format_security_details(self, bug_risks: List[Dict]) -> str:
        """セキュリティ詳細フォーマット"""
        if not bug_risks:
            return "No security risks detected."
            
        formatted_risks = []
        for i, risk in enumerate(bug_risks, 1):
            risk_level = risk.get('risk_level', 0)
            risk_icon = "🚨" if risk_level > 8 else "⚠️" if risk_level > 6 else "🔍"
            formatted_risks.append(
                f"{i}. {risk_icon} **{risk.get('name', 'Security Risk')}** (Level: {risk_level}/10)\n"
                f"   - Description: {risk.get('description', 'No description')}\n"
                f"   - Location: Line {risk.get('line', 'Unknown')}"
            )
            
        return '\n\n'.join(formatted_risks)
        
    def _format_violation_details(self, issues: List[Dict]) -> str:
        """違反詳細フォーマット"""
        violations = [i for i in issues if 'TODO' in i.get('description', '') or 'FIXME' in i.get('description', '')]
        
        if not violations:
            return "No Iron Will violations detected."
            
        formatted_violations = []
        for i, violation in enumerate(violations, 1):
            formatted_violations.append(
                f"{i}. **Line {violation.get('line_start', 'Unknown')}**: {violation.get('code_snippet', 'Unknown code')}\n"
                f"   - Issue: {violation.get('description', 'No description')}"
            )
            
        return '\n\n'.join(formatted_violations)
        
    def _generate_implementation_plan(self, analysis: Dict) -> List[str]:
        """実装計画生成"""
        plan = []
        quality_score = analysis.get('quality_score', 0)
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        issues = analysis.get('issues', [])
        
        # Iron Will違反がある場合
        if not iron_will_compliance:
            plan.append("Remove all TODO/FIXME comments and implement proper solutions")
            
        # 複雑度問題
        complexity = analysis.get('complexity_score', 1)
        if complexity > 10:
            plan.append("Break down complex functions into smaller, focused units")
            
        # ドキュメント不足
        has_doc_issues = any('documentation' in issue.get('description', '').lower() for issue in issues)
        if has_doc_issues:
            plan.append("Add comprehensive docstrings and type hints")
            
        # エラーハンドリング
        has_error_issues = any('error' in issue.get('description', '').lower() for issue in issues)
        if has_error_issues:
            plan.append("Implement proper error handling and validation")
            
        # テスト追加
        if not analysis.get('tdd_compatibility', False):
            plan.append("Add comprehensive unit tests and improve test coverage")
            
        # 品質スコア向上
        if quality_score < 70:
            plan.append("Refactor code to meet Elder Guild quality standards")
            
        # コードレビュー
        plan.append("Conduct thorough code review with Elder Guild standards")
        
        # 検証とテスト
        plan.append("Verify all changes pass quality gates and tests")
        
        return plan
        
    def _generate_acceptance_criteria(self, analysis: Dict) -> List[str]:
        """受け入れ基準生成"""
        criteria = []
        quality_score = analysis.get('quality_score', 0)
        
        # 基本品質基準
        criteria.append(f"Quality score improved to at least 70/100 (current: {quality_score:.1f})")
        
        # Iron Will遵守
        if not analysis.get('iron_will_compliance', True):
            criteria.append("Iron Will compliance check passes (no TODO/FIXME comments)")
            
        # セキュリティ
        bug_risks = analysis.get('bug_risks', [])
        if bug_risks:
            criteria.append("All high-risk security issues resolved")
            
        # 複雑度
        complexity = analysis.get('complexity_score', 1)
        if complexity > 10:
            criteria.append(f"Cyclomatic complexity reduced below 10 (current: {complexity})")
            
        # テスト
        criteria.append("All new code covered by unit tests")
        criteria.append("All existing tests continue to pass")
        
        # ドキュメント
        criteria.append("Code properly documented with docstrings and type hints")
        
        # 品質ゲート
        criteria.append("Passes Elder Guild quality gate checks")
        
        return criteria
        
    def _determine_priority(self, analysis: Dict) -> str:
        """優先度決定"""
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        bug_risks = analysis.get('bug_risks', [])
        quality_score = analysis.get('quality_score', 100)
        
        # Critical: Iron Will違反または高セキュリティリスク
        if not iron_will_compliance:
            return 'critical'
            
        high_security_risks = [risk for risk in bug_risks if risk.get('risk_level', 0) > 8]
        if high_security_risks:
            return 'critical'
            
        # High: 低品質スコアまたは中セキュリティリスク
        if quality_score < 50:
            return 'high'
            
        medium_security_risks = [risk for risk in bug_risks if risk.get('risk_level', 0) > 6]
        if medium_security_risks:
            return 'high'
            
        # Medium: 品質改善が必要
        if quality_score < 70:
            return 'medium'
            
        # Low: 軽微な改善
        return 'low'
        
    def _estimate_effort(self, analysis: Dict) -> str:
        """作業量見積もり"""
        base_hours = 1  # 1時間ベース
        
        quality_score = analysis.get('quality_score', 100)
        complexity = analysis.get('complexity_score', 1)
        issues_count = len(analysis.get('issues', []))
        
        # 品質スコアによる調整
        if quality_score < 50:
            base_hours += 3
        elif quality_score < 70:
            base_hours += 2
            
        # 複雑度による調整
        if complexity > 15:
            base_hours += 2
        elif complexity > 10:
            base_hours += 1
            
        # 問題数による調整
        base_hours += issues_count * 0.5
        
        # Iron Will違反は追加作業
        if not analysis.get('iron_will_compliance', True):
            base_hours += 2
            
        # 時間を適切な単位に変換
        if base_hours < 2:
            return f"{int(base_hours * 60)} minutes"
        elif base_hours < 8:
            return f"{base_hours:.1f} hours"
        else:
            return f"{base_hours/8:.1f} days"
            
    def _generate_business_value(self, analysis: Dict) -> str:
        """ビジネス価値生成"""
        quality_score = analysis.get('quality_score', 100)
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        security_risks = len(analysis.get('bug_risks', []))
        
        values = []
        
        # 品質改善の価値
        if quality_score < 70:
            values.append("**Direct Value:** Reduces technical debt and maintenance costs")
            values.append("**Strategic Value:** Improves code maintainability and developer productivity")
            
        # Iron Will遵守の価値
        if not iron_will_compliance:
            values.append("**Policy Value:** Ensures compliance with Elder Guild Iron Will standards")
            values.append("**Long-term Value:** Prevents accumulation of technical debt")
            
        # セキュリティの価値
        if security_risks > 0:
            values.append("**Security Value:** Reduces risk of security breaches and vulnerabilities")
            values.append("**Compliance Value:** Meets security and regulatory requirements")
            
        # 一般的な価値
        values.append("**Quality Value:** Enhances overall code quality and reliability")
        values.append("**Team Value:** Improves code readability and collaboration")
        
        return '\n'.join(values)
        
    def _group_issues_by_severity(self, issues: List[Dict]) -> Dict:
        """重要度別Issue分類"""
        groups = {'critical': [], 'high': [], 'medium': [], 'low': []}
        
        for issue in issues:
            severity = issue.get('severity', 0)
            if severity > 8:
                groups['critical'].append(issue)
            elif severity > 6:
                groups['high'].append(issue)
            elif severity > 3:
                groups['medium'].append(issue)
            else:
                groups['low'].append(issue)
                
        return {k: len(v) for k, v in groups.items()}
        
    def _assess_risks(self, bug_risks: List[Dict]) -> Dict:
        """リスク評価"""
        if not bug_risks:
            return {'level': 'low', 'count': 0, 'max_risk': 0}
            
        max_risk = max([risk.get('risk_level', 0) for risk in bug_risks])
        
        if max_risk > 8:
            level = 'critical'
        elif max_risk > 6:
            level = 'high'
        elif max_risk > 3:
            level = 'medium'
        else:
            level = 'low'
            
        return {
            'level': level,
            'count': len(bug_risks),
            'max_risk': max_risk
        }
        
    def _extract_sage_recommendations(self, four_sages_analysis: Dict) -> Dict[str, List[str]]:
        """4賢者推奨事項抽出"""
        if not four_sages_analysis:
            return {}
            
        recommendations = {}
        
        # Knowledge Sage
        knowledge_guidance = four_sages_analysis.get('knowledge_sage_guidance', [])
        if knowledge_guidance:
            recommendations['knowledge_sage'] = knowledge_guidance
            
        # Incident Sage
        incident_alert = four_sages_analysis.get('incident_sage_alert')
        if incident_alert:
            recommendations['incident_sage'] = incident_alert.suggested_actions
            
        # Task Sage
        task_planning = four_sages_analysis.get('task_sage_planning')
        if task_planning:
            recommendations['task_sage'] = [task_planning['description']]
            
        # RAG Sage
        rag_insights = four_sages_analysis.get('rag_sage_insights', {})
        rag_recommendations = rag_insights.get('recommendations', [])
        if rag_recommendations:
            recommendations['rag_sage'] = rag_recommendations
            
        return recommendations

class IssueQualityBridge:
    """Issue品質ブリッジメイン"""
    
    def __init__(self):
        self.quality_engine = None
        self.four_sages = None
        self.issue_generator = QualityIssueGenerator()
        self.generated_issues = []
        
    async def initialize(self):
        """初期化"""
        # 品質エンジン初期化
        db_params = {
            'host': 'localhost',
            'database': 'elders_guild_pgvector',
            'user': 'postgres',
            'password': ''
        }
        
        self.quality_engine = EldersCodeQualityEngine(db_params)
        await self.quality_engine.initialize()
        
        # 4賢者システム初期化
        self.four_sages = await get_four_sages_quality_orchestrator()
        
        logger.info("📋 Issue Quality Bridge initialized")
        
    async def shutdown(self):
        """終了処理"""
        if self.quality_engine:
            await self.quality_engine.shutdown()
        logger.info("🔒 Issue Quality Bridge shutdown")
        
    async def generate_quality_issues_for_file(self, file_path: str) -> List[QualityIssue]:
        """ファイルの品質Issue生成"""
        try:
            # 品質分析実行
            quality_analysis = await self.quality_engine.analyze_file(file_path)
            
            if 'error' in quality_analysis:
                logger.warning(f"⚠️ Could not analyze {file_path}: {quality_analysis['error']}")
                return []
                
            # 4賢者分析実行
            four_sages_analysis = await self.four_sages.comprehensive_quality_analysis(file_path)
            
            # Issue生成が必要かチェック
            if self._should_generate_issue(quality_analysis):
                quality_issue = await self.issue_generator.generate_quality_issue_from_analysis(
                    file_path, quality_analysis, four_sages_analysis
                )
                
                self.generated_issues.append(quality_issue)
                logger.info(f"📋 Generated quality issue for {file_path}: {quality_issue.issue_id}")
                return [quality_issue]
            else:
                logger.info(f"✅ No quality issues needed for {file_path}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to generate quality issue for {file_path}: {e}")
            return []
            
    def _should_generate_issue(self, quality_analysis: Dict) -> bool:
        """Issue生成要否判定"""
        analysis = quality_analysis.get('analysis', {})
        
        quality_score = analysis.get('quality_score', 100)
        iron_will_compliance = analysis.get('iron_will_compliance', True)
        bug_risks = analysis.get('bug_risks', [])
        
        # Iron Will違反は必ずIssue化
        if not iron_will_compliance:
            return True
            
        # 高セキュリティリスクは必ずIssue化
        high_security_risks = [risk for risk in bug_risks if risk.get('risk_level', 0) > 7]
        if high_security_risks:
            return True
            
        # 低品質スコアはIssue化
        if quality_score < 60:
            return True
            
        return False
        
    async def export_issues_to_json(self, output_file: str):
        """Issue JSON出力"""
        try:
            issues_data = [asdict(issue) for issue in self.generated_issues]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(issues_data, f, indent=2, default=str, ensure_ascii=False)
                
            logger.info(f"📄 Exported {len(self.generated_issues)} issues to {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to export issues: {e}")
            
    async def export_issues_to_github_format(self, output_dir: str):
        """GitHub Issue形式で出力"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for issue in self.generated_issues:
                # GitHub Issue形式のMarkdown生成
                github_issue = self._format_github_issue(issue)
                
                # ファイル名生成
                safe_title = "".join(c for c in issue.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_name = f"{issue.issue_id}_{safe_title[:50]}.md"
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(github_issue)
                    
            logger.info(f"📄 Exported {len(self.generated_issues)} GitHub issues to {output_dir}")
            
        except Exception as e:
            logger.error(f"❌ Failed to export GitHub issues: {e}")
            
    def _format_github_issue(self, issue: QualityIssue) -> str:
        """GitHub Issue形式フォーマット"""
        labels = ', '.join(issue.tags)
        
        github_issue = f"""---
title: {issue.title}
labels: {labels}
assignees: 
priority: {issue.priority}
---

{issue.description}

## 📊 Quality Metrics

- **Current Score:** {issue.quality_metrics.get('current_score', 0)}/100
- **Target Score:** {issue.quality_metrics.get('target_score', 70)}/100
- **Iron Will Compliance:** {'✅' if issue.quality_metrics.get('iron_will_compliance') else '❌'}
- **Issues Count:** {issue.quality_metrics.get('issues_count', 0)}
- **Security Risks:** {issue.quality_metrics.get('security_risks_count', 0)}

## 🏷️ Metadata

- **Issue ID:** {issue.issue_id}
- **Category:** {issue.category}
- **Estimated Effort:** {issue.estimated_effort}
- **Created:** {issue.created_at.isoformat()}
- **Affected Files:** {', '.join(issue.affected_files)}

## 🧙‍♂️ Four Sages Recommendations

"""
        
        # 4賢者推奨事項追加
        for sage, recommendations in issue.sage_recommendations.items():
            if recommendations:
                github_issue += f"\n### {sage.replace('_', ' ').title()}\n"
                for rec in recommendations:
                    github_issue += f"- {rec}\n"
                    
        github_issue += f"\n## 💼 Business Value\n\n{issue.business_value}\n"
        
        return github_issue

# 便利関数
async def generate_quality_issues_for_project(project_paths: List[str], output_dir: str = None) -> List[QualityIssue]:
    """プロジェクト全体の品質Issue生成"""
    bridge = IssueQualityBridge()
    await bridge.initialize()
    
    try:
        all_issues = []
        
        for base_path in project_paths:
            path = Path(base_path)
            if path.exists():
                for py_file in path.rglob('*.py'):
                    if '__pycache__' not in str(py_file) and not py_file.name.startswith('test_'):
                        issues = await bridge.generate_quality_issues_for_file(str(py_file))
                        all_issues.extend(issues)
                        
        if output_dir:
            await bridge.export_issues_to_github_format(output_dir)
            
        return all_issues
        
    finally:
        await bridge.shutdown()

if __name__ == "__main__":
    async def test_issue_bridge():
        """Issue ブリッジテスト"""
        bridge = IssueQualityBridge()
        await bridge.initialize()
        
        try:
            # テストファイル作成
            test_file = "/tmp/test_issue_bridge.py"
            with open(test_file, 'w') as f:
                f.write('''
def bad_function():
    # TODO: fix this later
    magic_number = 42
    try:
        result = eval("1 + 1")
    except:
        pass
    return magic_number
''')
            
            # Issue生成テスト
            issues = await bridge.generate_quality_issues_for_file(test_file)
            
            if issues:
                print("📋 Generated Quality Issue:")
                print(f"Title: {issues[0].title}")
                print(f"Priority: {issues[0].priority}")
                print(f"Category: {issues[0].category}")
                print(f"Estimated Effort: {issues[0].estimated_effort}")
                
                # GitHub形式出力
                await bridge.export_issues_to_github_format("/tmp/test_issues")
                print("✅ GitHub issues exported to /tmp/test_issues")
            else:
                print("ℹ️ No issues generated")
                
        finally:
            await bridge.shutdown()
            
    asyncio.run(test_issue_bridge())