#!/usr/bin/env python3
"""
Security Audit Script for Enhanced Knowledge Sage
Performs automated security vulnerability checks
"""

import ast
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any


class SecurityAuditor:
    """Automated security auditor for Enhanced Knowledge Sage"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
            
        self.tree = ast.parse(self.source_code)
    
    def audit_sql_injection(self) -> List[Dict[str, Any]]:
        """Check for potential SQL injection vulnerabilities"""
        issues = []
        
        # Check for string formatting in SQL queries
        sql_patterns = [
            r'\.format\(',
            r'%\s*\(',
            r'f".*SELECT.*"',
            r"f'.*SELECT.*'",
        ]
        
        for i, line in enumerate(self.source_code.split('\n'), 1):
            for pattern in sql_patterns:
                if re.search(pattern, line) and ('SELECT' in line or 'INSERT' in line or 'UPDATE' in line):
                    issues.append({
                        'type': 'SQL_INJECTION_RISK',
                        'line': i,
                        'content': line.strip(),
                        'severity': 'HIGH',
                        'description': 'Potential SQL injection via string formatting'
                    })
        
        return issues
    
    def audit_input_validation(self) -> List[Dict[str, Any]]:
        """Check for insufficient input validation"""
        issues = []
        
        class InputValidationVisitor(ast.NodeVisitor):
            def __init__(self):
                self.function_params = {}
                
            def visit_FunctionDef(self, node):
                # Check if parameters have validation
                for arg in node.args.args:
                    if arg.arg not in ['self', 'cls']:
                        # Look for validation in function body
                        has_validation = False
                        for stmt in node.body:
                            if isinstance(stmt, ast.If):
                                # Check if parameter is validated
                                if self._contains_param_check(stmt, arg.arg):
                                    has_validation = True
                                    break
                        
                        if not has_validation and arg.arg in ['title', 'content', 'query', 'tags']:
                            issues.append({
                                'type': 'MISSING_INPUT_VALIDATION',
                                'line': node.lineno,
                                'function': node.name,
                                'parameter': arg.arg,
                                'severity': 'MEDIUM',
                                'description': f'Parameter "{arg.arg}" lacks validation'
                            })
                
                self.generic_visit(node)
            
            def _contains_param_check(self, node, param_name):
                """Check if node contains validation for parameter"""
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id == param_name:
                        return True
                return False
        
        visitor = InputValidationVisitor()
        visitor.visit(self.tree)
        
        return issues
    
    def audit_crypto_usage(self) -> List[Dict[str, Any]]:
        """Check for weak cryptographic practices"""
        issues = []
        
        # Check for weak hash algorithms
        weak_hashes = ['md5', 'sha1']
        
        for i, line in enumerate(self.source_code.split('\n'), 1):
            for weak_hash in weak_hashes:
                if weak_hash in line.lower() and 'hashlib' in line:
                    issues.append({
                        'type': 'WEAK_CRYPTOGRAPHY',
                        'line': i,
                        'content': line.strip(),
                        'severity': 'MEDIUM',
                        'description': f'Use of weak hash algorithm: {weak_hash}'
                    })
        
        return issues
    
    def audit_data_exposure(self) -> List[Dict[str, Any]]:
        """Check for potential data exposure"""
        issues = []
        
        # Check for export functions that might expose sensitive data
        sensitive_patterns = [
            r'export.*password',
            r'export.*secret',
            r'export.*key',
            r'\.json\.dumps\(',
            r'export_knowledge.*format.*json'
        ]
        
        for i, line in enumerate(self.source_code.split('\n'), 1):
            for pattern in sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'DATA_EXPOSURE_RISK',
                        'line': i,
                        'content': line.strip(),
                        'severity': 'MEDIUM',
                        'description': 'Potential sensitive data exposure in export'
                    })
        
        return issues
    
    def audit_access_control(self) -> List[Dict[str, Any]]:
        """Check for missing access control"""
        issues = []
        
        class AccessControlVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check for public methods without access control
                if not node.name.startswith('_'):  # Public method
                    has_auth_check = False
                    
                    for stmt in node.body:
                        if isinstance(stmt, ast.If):
                            # Look for authentication/authorization checks
                            for child in ast.walk(stmt):
                                if isinstance(child, ast.Name) and child.id in ['user', 'auth', 'permission']:
                                    has_auth_check = True
                                    break
                    
                    # Critical operations should have access control
                    critical_operations = ['store_knowledge', 'update_knowledge', 'export_knowledge']
                    if node.name in critical_operations and not has_auth_check:
                        issues.append({
                            'type': 'MISSING_ACCESS_CONTROL',
                            'line': node.lineno,
                            'function': node.name,
                            'severity': 'HIGH',
                            'description': f'Critical method "{node.name}" lacks access control'
                        })
                
                self.generic_visit(node)
        
        visitor = AccessControlVisitor()
        visitor.visit(self.tree)
        
        return issues
    
    def audit_error_handling(self) -> List[Dict[str, Any]]:
        """Check for information disclosure through error messages"""
        issues = []
        
        # Check for potential information disclosure in exceptions
        disclosure_patterns = [
            r'Exception.*f".*{.*}.*"',
            r'raise.*f".*{.*}.*"',
            r'logger\.error.*f".*{.*}.*"'
        ]
        
        for i, line in enumerate(self.source_code.split('\n'), 1):
            for pattern in disclosure_patterns:
                if re.search(pattern, line):
                    issues.append({
                        'type': 'INFORMATION_DISCLOSURE',
                        'line': i,
                        'content': line.strip(),
                        'severity': 'LOW',
                        'description': 'Potential information disclosure in error message'
                    })
        
        return issues
    
    def audit_resource_limits(self) -> List[Dict[str, Any]]:
        """Check for missing resource limits"""
        issues = []
        
        # Check for unbounded loops or operations
        unbounded_patterns = [
            r'while\s+True:',
            r'for.*in.*:(?!.*break)',
            r'\.append\(',
            r'cache\[.*\]\s*='
        ]
        
        for i, line in enumerate(self.source_code.split('\n'), 1):
            for pattern in unbounded_patterns:
                if re.search(pattern, line):
                    # Check if there's a break or limit condition
                    if 'while True:' in line:
                        issues.append({
                            'type': 'UNBOUNDED_LOOP',
                            'line': i,
                            'content': line.strip(),
                            'severity': 'MEDIUM',
                            'description': 'Potential infinite loop without proper exit condition'
                        })
                    elif '.append(' in line or 'cache[' in line:
                        issues.append({
                            'type': 'UNBOUNDED_GROWTH',
                            'line': i,
                            'content': line.strip(),
                            'severity': 'MEDIUM',
                            'description': 'Potential unbounded memory growth'
                        })
        
        return issues
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit"""
        print("🔍 Running Security Audit for Enhanced Knowledge Sage...")
        
        all_issues = []
        
        # Run all audit checks
        sql_issues = self.audit_sql_injection()
        input_issues = self.audit_input_validation()
        crypto_issues = self.audit_crypto_usage()
        exposure_issues = self.audit_data_exposure()
        access_issues = self.audit_access_control()
        error_issues = self.audit_error_handling()
        resource_issues = self.audit_resource_limits()
        
        all_issues.extend(sql_issues)
        all_issues.extend(input_issues)
        all_issues.extend(crypto_issues)
        all_issues.extend(exposure_issues)
        all_issues.extend(access_issues)
        all_issues.extend(error_issues)
        all_issues.extend(resource_issues)
        
        # Categorize by severity
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in all_issues:
            severity_counts[issue['severity']] += 1
        
        # Generate risk score (0-100)
        risk_score = (severity_counts['HIGH'] * 10 + 
                     severity_counts['MEDIUM'] * 5 + 
                     severity_counts['LOW'] * 1)
        
        return {
            'file_path': self.file_path,
            'total_issues': len(all_issues),
            'severity_breakdown': severity_counts,
            'risk_score': min(risk_score, 100),
            'issues': all_issues,
            'recommendations': self._generate_recommendations(all_issues)
        }
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on found issues"""
        recommendations = []
        
        issue_types = set(issue['type'] for issue in issues)
        
        if 'SQL_INJECTION_RISK' in issue_types:
            recommendations.append("Use parameterized queries exclusively for all database operations")
        
        if 'MISSING_INPUT_VALIDATION' in issue_types:
            recommendations.append("Implement comprehensive input validation for all user-provided data")
        
        if 'WEAK_CRYPTOGRAPHY' in issue_types:
            recommendations.append("Replace weak hash algorithms (MD5, SHA1) with SHA-256 or stronger")
        
        if 'DATA_EXPOSURE_RISK' in issue_types:
            recommendations.append("Implement access controls and data sanitization for export functions")
        
        if 'MISSING_ACCESS_CONTROL' in issue_types:
            recommendations.append("Add authentication and authorization checks to critical operations")
        
        if 'UNBOUNDED_GROWTH' in issue_types:
            recommendations.append("Implement resource limits and cleanup mechanisms for caches")
        
        if not recommendations:
            recommendations.append("No major security issues detected - continue with current practices")
        
        return recommendations


def main():
    """Run security audit on Enhanced Knowledge Sage"""
    file_path = "/home/aicompany/ai_co/libs/four_sages/knowledge/enhanced_knowledge_sage.py"
    
    auditor = SecurityAuditor(file_path)
    results = auditor.run_full_audit()
    
    print(f"\n📊 Security Audit Results")
    print(f"=" * 50)
    print(f"📁 File: {results['file_path']}")
    print(f"🔢 Total Issues: {results['total_issues']}")
    print(f"📊 Risk Score: {results['risk_score']}/100")
    print(f"\n📈 Severity Breakdown:")
    for severity, count in results['severity_breakdown'].items():
        print(f"   {severity}: {count}")
    
    print(f"\n🔍 Detailed Issues:")
    for issue in results['issues']:
        print(f"   [{issue['severity']}] Line {issue['line']}: {issue['type']}")
        print(f"       {issue['description']}")
        if 'content' in issue:
            print(f"       Code: {issue['content']}")
        print()
    
    print(f"💡 Recommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Generate security badge
    if results['risk_score'] <= 20:
        badge = "🟢 LOW RISK"
    elif results['risk_score'] <= 50:
        badge = "🟡 MEDIUM RISK"
    else:
        badge = "🔴 HIGH RISK"
    
    print(f"\n🏆 Security Rating: {badge}")
    
    return results


if __name__ == "__main__":
    main()