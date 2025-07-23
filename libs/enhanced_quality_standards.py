#!/usr/bin/env python3
"""
🏛️ Enhanced Quality Standards - Elder Guild 85+ Requirements
Strict quality standards for Elder Guild compliance

Quality Requirements:
- Minimum Score: 85/100 (raised from 70)
- Iron Will: 100% compliance (no workarounds)
- Security Risk: Level 3 maximum (reduced from 7)
- Zero Critical Issues tolerance
"""

import ast
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EnhancedQualityConfig:
    """Enhanced quality configuration for Elder Guild standards"""
    minimum_quality_score: float = 85.0  # Raised from 70
    iron_will_compliance_rate: float = 1.0  # 100% required
    maximum_security_risk_level: int = 3  # Reduced from 7
    critical_issues_limit: int = 0  # Zero tolerance
    complexity_threshold: int = 8  # Reduced from 10
    maintainability_minimum: int = 60  # Raised from 20
    test_coverage_minimum: float = 90.0  # Raised from 80
    documentation_coverage_minimum: float = 80.0

@dataclass
class QualityViolation:
    """Quality standard violation"""
    violation_type: str
    severity: str  # 'critical', 'major', 'minor'
    message: str
    file_path: str
    line_number: int
    context: str
    suggestion: str
    elder_guild_standard: str

class StrictIronWillValidator:
    """Advanced Iron Will violation detection system"""
    
    def __init__(self):
        """初期化メソッド"""
        self.workaround_patterns = {
            'explicit_todos': [
                r'#\s*TODO[:\s]',
                r'#\s*FIXME[:\s]', 
                r'#\s*HACK[:\s]',
                r'#\s*XXX[:\s]',
                r'#\s*KLUDGE[:\s]'
            ],
            'temporary_implementations': [
                r'(temp|temporary|quick|dirty)_\w+',
                r'def\s+(temp|quick|dirty|hack)\w*\s*\(',
                r'class\s+(Temp|Quick|Dirty|Hack)\w*\s*[\(:]'
            ],
            'japanese_workarounds': [
                r'#.*[一時的|暫定|仮|とりあえず]',
                r'def\s*[一時的|暫定|仮]\w*\s*\(',
            ],
            'suspicious_comments': [
                r'#.*[需要修正|要修改|临时|暂时]',  # Chinese
                r'#.*(temporary|quick\s*fix|dirty\s*hack)',
                r'#.*(will\s*fix|fix\s*later|remove\s*this)',
                r'#.*(TODO|TEMPORARY|TEMP|QUICK|DIRTY)',
            ],
            'workaround_code_patterns': [
                r'time\.sleep\s*\(\s*[0-9.]+\s*\)',  # Sleep hacks
                r'pass\s*#.*[temporary|temp|todo]',  # Temporary pass statements
                r'raise\s+NotImplementedError.*[temporary|temp]',  # Temp not implemented
            ]
        }
    
    def validate_iron_will_compliance(self, file_path: str) -> Dict[str, Any]:
        """Strict Iron Will compliance validation"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # 1. Pattern-based detection with context
            for category, patterns in self.workaround_patterns.items():
                for pattern in patterns:
                    matches = self._find_pattern_with_context(content, lines, pattern)
                    for match in matches:
                        violations.append(QualityViolation(
                            violation_type='iron_will_violation',
                            severity='critical',
                            message=f"Iron Will violation: {category}",
                            file_path=file_path,
                            line_number=match['line_number'],
                            context=match['line_text'],
                            suggestion="Remove workaround and implement proper solution",
                            elder_guild_standard="Iron Will: No workarounds permitted"
                        ))
            
            # 2. AST-based structural analysis
            try:
                tree = ast.parse(content)
                ast_violations = self._analyze_ast_for_workarounds(tree, file_path)
                violations.extend(ast_violations)
            except SyntaxError:
                violations.append(QualityViolation(
                    violation_type='syntax_error',
                    severity='critical',
                    message="Syntax error prevents analysis",
                    file_path=file_path,
                    line_number=1,
                    context="File has syntax errors",
                    suggestion="Fix syntax errors",
                    elder_guild_standard="Elder Guild: All code must be syntactically correct"
                ))
            
            # 3. Comment intent analysis
            comment_violations = self._analyze_comment_intent(lines, file_path)
            violations.extend(comment_violations)
            
            return {
                'compliant': len(violations) == 0,
                'violations': [asdict(v) for v in violations],
                'violation_count': len(violations),
                'severity': 'critical' if violations else 'none'
            }
            
        except Exception as e:
            return {
                'compliant': False,
                'error': str(e),
                'violations': [asdict(QualityViolation(
                    violation_type='analysis_error',
                    severity='critical',
                    message=f"Analysis failed: {e}",
                    file_path=file_path,
                    line_number=1,
                    context="Error during analysis",
                    suggestion="Check file accessibility and format",
                    elder_guild_standard="Elder Guild: All files must be analyzable"
                ))]
            }
    
    def _find_pattern_with_context(
        self,
        content: str,
        lines: List[str],
        pattern: str
    ) -> List[Dict]:
        """Find pattern matches with context analysis"""
        matches = []
        
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                # Extract context (surrounding lines)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context = lines[context_start:context_end]
                
                # Check if this is legitimate usage
                if not self._is_legitimate_usage(line, context):
                    matches.append({
                        'line_number': i + 1,
                        'line_text': line.strip(),
                        'context': context,
                        'pattern': pattern
                    })
        
        return matches
    
    def _is_legitimate_usage(self, line: str, context: List[str]) -> bool:
        """Determine if pattern usage is legitimate"""
        # Documentation or examples are legitimate
        legitimate_indicators = [
            'example', 'documentation', 'guide', 'instruction',
            'template', 'demo', 'test', 'mock',
            '例', '文書', 'ガイド', '説明', 'テスト'
        ]
        
        full_context = ' '.join(context).lower()
        for indicator in legitimate_indicators:
            if indicator.lower() in full_context:
                return True
        
        # Check if it's in a string literal or comment describing what NOT to do
        if any(phrase in full_context for phrase in ['do not', 'avoid', 'never', 'prohibited']):
            return True
        
        return False
    
    def _analyze_ast_for_workarounds(self, tree: ast.AST, file_path: str) -> List[QualityViolation]:
        """AST-based workaround detection"""
        violations = []
        
        for node in ast.walk(tree):
            # Temporary function/class names
            if isinstance(node, ast.FunctionDef):
                if self._is_temporary_identifier(node.name):
                    violations.append(QualityViolation(
                        violation_type='temporary_function',
                        severity='critical',
                        message=f"Temporary function name: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        context=f"def {node.name}(...)",
                        suggestion="Rename to permanent, descriptive function name",
                        elder_guild_standard="Iron Will: No temporary implementations"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if self._is_temporary_identifier(node.name):
                    violations.append(QualityViolation(
                        violation_type='temporary_class',
                        severity='critical',
                        message=f"Temporary class name: {node.name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        context=f"class {node.name}:",
                        suggestion="Rename to permanent, descriptive class name",
                        elder_guild_standard="Iron Will: No temporary implementations"
                    ))
            
            # Suspicious function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if (hasattr(node.func.value, 'id') and 
                        node.func.value.id == 'time' and 
                        node.func.attr == 'sleep'):
                        violations.append(QualityViolation(
                            violation_type='timing_hack',
                            severity='major',
                            message="time.sleep() may indicate timing hack",
                            file_path=file_path,
                            line_number=node.lineno,
                            context="time.sleep(...)",
                            suggestion="Use proper synchronization or async/await",
                            elder_guild_standard="Iron Will: No timing hacks"
                        ))
        
        return violations
    
    def _is_temporary_identifier(self, name: str) -> bool:
        """Check if identifier name suggests temporary implementation"""
        temp_patterns = [
            r'^(temp|tmp|temporary)_',
            r'^(quick|dirty|hack)_',
            r'_(temp|tmp|temporary)$',
            r'_(quick|dirty|hack)$',
            r'^Test\w*Temp',
            r'^(Temp|Tmp|Quick|Dirty|Hack)\w*',
        ]
        
        for pattern in temp_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        
        return False
    
    def _analyze_comment_intent(self, lines: List[str], file_path: str) -> List[QualityViolation]:
        """Analyze comment intent for workarounds"""
        violations = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                comment = stripped[1:].strip().lower()
                
                # Check for workaround intentions
                workaround_indicators = [
                    'will fix later', 'fix later', 'temporary fix',
                    'quick fix', 'dirty fix', 'hack for now',
                    'remove this', 'cleanup later', 'refactor later'
                ]
                
                for indicator in workaround_indicators:
                    if indicator in comment:
                        violations.append(QualityViolation(
                            violation_type='workaround_comment',
                            severity='major',
                            message=f"Workaround intention detected: {indicator}",
                            file_path=file_path,
                            line_number=i + 1,
                            context=stripped,
                            suggestion="Complete implementation now or create proper issue",
                            elder_guild_standard="Iron Will: No deferred fixes"
                        ))
        
        return violations

class EnhancedSecurityValidator:
    """Zero-tolerance security validation"""
    
    def __init__(self):
        """初期化メソッド"""
        self.security_patterns = {
            'critical': [
                (r'eval\s*\(', 'Code injection via eval()'),
                (r'exec\s*\(', 'Code injection via exec()'),
                (r'__import__\s*\(', 'Dynamic imports security risk'),
                (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', 'Shell injection risk'),
            ],
            'high': [
                (r'os\.system\s*\(', 'System command execution'),
                (r'subprocess\.Popen\s*\([^)]*shell\s*=\s*True', 'Shell command risk'),
                (r'pickle\.load\s*\(', 'Unsafe deserialization'),
                (r'yaml\.load\s*\((?!.*Loader)', 'Unsafe YAML loading'),
            ],
            'medium': [
                (r'requests\.get\s*\([^)]*verify\s*=\s*False', 'SSL verification disabled'),
                (r'ssl\._create_unverified_context', 'SSL verification bypassed'),
                (r'random\.random\s*\(', 'Weak randomness for security'),
            ]
        }
    
    def validate_security(self, file_path: str) -> Dict[str, Any]:
        """Validate security with zero tolerance for high risks"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            for severity, patterns in self.security_patterns.items():
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        line_text = lines[line_number - 1] if line_number <= len(lines) else ""
                        
                        # Determine if this violates Elder Guild standards
                        is_violation = severity in ['critical', 'high']
                        if severity == 'medium':
                            # Medium risks are violations if above level 3
                            is_violation = True
                        
                        if is_violation:
                            violations.append(QualityViolation(
                                violation_type='security_violation',
                                severity='critical' if severity == 'critical' else 'major',
                                message=f"Security risk: {description}",
                                file_path=file_path,
                                line_number=line_number,
                                context=line_text.strip(),
                                suggestion="Use secure alternatives or add proper validation",
                                elder_guild_standard=f"Security: Maximum risk level 3 (this " \
                                    "is level {7 if severity == 'critical' else 5 if severity == 'high' else 3})"
                            ))
            
            risk_level = 0
            if any(v.severity == 'critical' for v in violations):
                risk_level = 10
            elif any(v.severity == 'major' for v in violations):
                risk_level = 5
            
            return {
                'compliant': risk_level <= 3,
                'risk_level': risk_level,
                'violations': [asdict(v) for v in violations],
                'violation_count': len(violations)
            }
            
        except Exception as e:
            return {
                'compliant': False,
                'risk_level': 10,
                'error': str(e),
                'violations': []
            }

class EnhancedQualityEvaluator:
    """Enhanced quality evaluator with Elder Guild 85+ standards"""
    
    def __init__(self, config:
        """初期化メソッド"""
    Optional[EnhancedQualityConfig] = None):
        self.config = config or EnhancedQualityConfig()
        self.iron_will_validator = StrictIronWillValidator()
        self.security_validator = EnhancedSecurityValidator()
    
    def evaluate_file_quality(self, file_path: str) -> Dict[str, Any]:
        """Comprehensive quality evaluation with Elder Guild standards"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'quality_score': 0.0,
                'elder_guild_compliant': False,
                'violations': [],
                'error': f"Could not read file: {e}"
            }
        
        all_violations = []
        
        # 1. Iron Will compliance (mandatory)
        iron_will_result = self.iron_will_validator.validate_iron_will_compliance(file_path)
        if not iron_will_result['compliant']:
            all_violations.extend(iron_will_result['violations'])
        
        # 2. Security validation (mandatory)
        security_result = self.security_validator.validate_security(file_path)
        if not security_result['compliant']:
            all_violations.extend(security_result['violations'])
        
        # 3. Code quality metrics
        quality_metrics = self._evaluate_code_quality(content, file_path)
        
        # 4. Calculate overall score
        base_score = quality_metrics['base_score']
        
        # Apply Elder Guild penalties
        for violation in all_violations:
            if violation['severity'] == 'critical':
                base_score -= 25  # Severe penalty for critical violations
            elif violation['severity'] == 'major':
                base_score -= 15
            elif violation['severity'] == 'minor':
                base_score -= 5
        
        final_score = max(0.0, min(100.0, base_score))
        
        # Elder Guild compliance check
        elder_guild_compliant = (
            final_score >= self.config.minimum_quality_score and
            iron_will_result['compliant'] and
            security_result['compliant'] and
            len([v for v in all_violations if v['severity'] == 'critical']) == 0
        )
        
        return {
            'quality_score': final_score,
            'elder_guild_compliant': elder_guild_compliant,
            'violations': all_violations,
            'iron_will_compliant': iron_will_result['compliant'],
            'security_compliant': security_result['compliant'],
            'metrics': quality_metrics,
            'standards_applied': {
                'minimum_score': self.config.minimum_quality_score,
                'iron_will_required': True,
                'max_security_risk': self.config.maximum_security_risk_level,
                'zero_critical_tolerance': True
            }
        }
    
    def _evaluate_code_quality(self, content: str, file_path: str) -> Dict[str, Any]:
        """Evaluate basic code quality metrics"""
        lines = content.splitlines()
        
        # Basic metrics
        line_count = len(lines)
        empty_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        
        # Calculate base score
        base_score = 85.0  # Start with Elder Guild minimum
        
        # File length penalty (stricter)
        if line_count > 300:  # Reduced from 500
            base_score -= min(20, (line_count - 300) / 25)
        
        # Documentation bonus/penalty
        doc_ratio = comment_lines / max(1, line_count - empty_lines)
        if doc_ratio > 0.2:  # Good documentation
            base_score += 5
        elif doc_ratio < 0.05:  # Poor documentation
            base_score -= 10
        
        # Complexity estimation (stricter)
        complexity_indicators = [
            content.count('if '), content.count('elif '), content.count('for '),
            content.count('while '), content.count('except '), 
            content.count(' and '), content.count(' or ')
        ]
        complexity = sum(complexity_indicators)
        
        if complexity > self.config.complexity_threshold:
            base_score -= min(25, (complexity - self.config.complexity_threshold) * 2)
        
        # Type hints bonus
        if ' -> ' in content and ':' in content:
            base_score += 5
        
        # Error handling bonus
        if 'try:' in content and 'except' in content:
            base_score += 3
        
        # Async/await bonus (modern patterns)
        if 'async def' in content or 'await ' in content:
            base_score += 3
        
        return {
            'base_score': base_score,
            'line_count': line_count,
            'complexity_estimate': complexity,
            'documentation_ratio': doc_ratio,
            'has_type_hints': ' -> ' in content,
            'has_error_handling': 'try:' in content,
            'has_async_patterns': 'async ' in content
        }

class QualityGateEnforcer:
    """Enforce Elder Guild quality gates"""
    
    def __init__(self, config:
        """初期化メソッド"""
    Optional[EnhancedQualityConfig] = None):
        self.config = config or EnhancedQualityConfig()
        self.evaluator = EnhancedQualityEvaluator(config)
    
    def check_quality_gate(self, files: List[str]) -> Dict[str, Any]:
        """Check if files pass the Elder Guild quality gate"""
        results = []
        total_violations = []
        
        for file_path in files:
            if not file_path.endswith('.py'):
                continue
                
            result = self.evaluator.evaluate_file_quality(file_path)
            results.append({
                'file_path': file_path,
                'result': result
            })
            
            if result['violations']:
                total_violations.extend(result['violations'])
        
        # Overall gate decision
        failed_files = [r for r in results if not r['result']['elder_guild_compliant']]
        average_score = sum(r['result']['quality_score'] for r in results) / max(1, len(results))
        
        gate_passed = (
            len(failed_files) == 0 and
            average_score >= self.config.minimum_quality_score and
            len([v for v in total_violations if v['severity'] == 'critical']) == 0
        )
        
        return {
            'gate_passed': gate_passed,
            'average_quality_score': average_score,
            'files_analyzed': len(results),
            'files_failed': len(failed_files),
            'total_violations': len(total_violations),
            'critical_violations': len([v for v in total_violations if v['severity'] == 'critical']),
            'results': results,
            'enforcement_summary': {
                'minimum_score_required': self.config.minimum_quality_score,
                'iron_will_required': True,
                'zero_critical_tolerance': True,
                'max_security_risk': self.config.maximum_security_risk_level
            }
        }

# CLI interface
def main():
    """Main CLI interface for enhanced quality checking"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_quality_standards.py <file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    target_path = Path(target)
    
    if not target_path.exists():
        print(f"Error: {target} does not exist")
        sys.exit(1)
    
    # Collect files to check
    files = []
    if target_path.is_file() and target_path.suffix == '.py':
        files = [str(target_path)]
    elif target_path.is_dir():
        files = [str(f) for f in target_path.rglob('*.py')]
    else:
        print(f"Error: {target} is not a Python file or directory")
        sys.exit(1)
    
    # Run quality gate check
    enforcer = QualityGateEnforcer()
    result = enforcer.check_quality_gate(files[:20])  # Limit for demo
    
    # Output results
    print("🏛️ Elder Guild Enhanced Quality Gate Results")
    print("=" * 50)
    
    if result['gate_passed']:
        print("✅ QUALITY GATE PASSED")
    else:
        print("❌ QUALITY GATE FAILED")
    
    print(f"\n📊 Summary:")
    print(f"   Files analyzed: {result['files_analyzed']}")
    print(f"   Average score: {result['average_quality_score']:.1f}/100")
    print(f"   Files failed: {result['files_failed']}")
    print(f"   Total violations: {result['total_violations']}")
    print(f"   Critical violations: {result['critical_violations']}")
    
    print(f"\n🏛️ Elder Guild Standards:")
    print(f"   Minimum score: {result['enforcement_summary']['minimum_score_required']}")
    print(f"   Iron Will required: {result['enforcement_summary']['iron_will_required']}")
    print(f"   Zero critical tolerance: {result['enforcement_summary']['zero_critical_tolerance']}")
    
    if not result['gate_passed']:
        print(f"\n❌ Failed files:")
        for file_result in result['results']:
            if not file_result['result']['elder_guild_compliant']:
                print(f"   {file_result['file_path']}: {file_result['result']['quality_score']:.1f}/100")
        
        sys.exit(1)

if __name__ == "__main__":
    main()