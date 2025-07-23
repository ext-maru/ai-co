#!/usr/bin/env python3
"""
🏛️ Elders Guild Code Quality Engine
エルダーズギルド最高品質コーディングシステム

Features:
- Real-time code quality analysis
- Pattern-based improvement suggestions  
- Bug prediction and prevention
- Learning from historical data
- Integration with 4 Sages wisdom
"""

import ast
import re
import hashlib
import json
import logging
import asyncio
import numpy as np
import psycopg2
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
try:
    import radon.complexity as complexity
    import radon.metrics as metrics
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    
try:
    from openai import OpenAI
    import tiktoken
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysisResult:
    """Code analysis result structure"""
    file_path: str
    quality_score: float
    complexity_score: int
    maintainability_index: float
    issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    bug_risks: List[Dict[str, Any]]
    iron_will_compliance: bool
    tdd_compatibility: bool
    timestamp: datetime

@dataclass
class QualityPattern:
    """Quality improvement pattern"""
    pattern_type: str
    pattern_name: str
    problematic_code: str
    improved_code: str
    description: str
    improvement_score: float
    language: str
    tags: List[str]

@dataclass
class BugLearningCase:
    """Bug learning case structure"""
    bug_category: str
    bug_title: str
    original_code: str
    bug_description: str
    error_message: str
    fix_solution: str
    fix_code: str
    severity_level: int
    language: str
    prevention_tips: List[str]

class DatabaseManager:
    """PostgreSQL with pgvector database manager"""
    
    def __init__(self, connection_params:
        """初期化メソッド"""
    Dict[str, str]):
        self.connection_params = connection_params
        self.connection = None
        
    async def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
            
    async def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔒 Database connection closed")
            
    async def store_quality_pattern(self, pattern: QualityPattern, embedding: List[float]) -> str:
        """Store quality pattern with embedding"""
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO code_quality_patterns 
            (pattern_type, pattern_name, problematic_code, improved_code, description, 
             improvement_score, language, tags, embedding, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING uuid;
            """
            now = datetime.now()
            cursor.execute(query, (
                pattern.pattern_type, pattern.pattern_name, pattern.problematic_code,
                pattern.improved_code, pattern.description, pattern.improvement_score,
                pattern.language, pattern.tags, embedding, now, now
            ))
            uuid = cursor.fetchone()[0]
            self.connection.commit()
            cursor.close()
            logger.info(f"✅ Quality pattern stored: {uuid}")
            return str(uuid)
        except Exception as e:
            logger.error(f"❌ Failed to store quality pattern: {e}")
            self.connection.rollback()
            raise
            
    async def store_bug_case(self, bug_case: BugLearningCase, embedding: List[float]) -> str:
        """Store bug learning case with embedding"""
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO bug_learning_cases 
            (bug_category, bug_title, original_code, bug_description, error_message,
             fix_solution, fix_code, severity_level, language, prevention_tips, embedding,
             created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING uuid;
            """
            now = datetime.now()
            cursor.execute(query, (
                bug_case.bug_category, bug_case.bug_title, bug_case.original_code,
                bug_case.bug_description, bug_case.error_message, bug_case.fix_solution,
                bug_case.fix_code, bug_case.severity_level, bug_case.language,
                bug_case.prevention_tips, embedding, now, now
            ))
            uuid = cursor.fetchone()[0]
            self.connection.commit()
            cursor.close()
            logger.info(f"✅ Bug case stored: {uuid}")
            return str(uuid)
        except Exception as e:
            logger.error(f"❌ Failed to store bug case: {e}")
            self.connection.rollback()
            raise
            
    async def search_similar_patterns(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 5
    ) -> List[Dict]:
        """Search for similar quality patterns"""
        try:
            cursor = self.connection.cursor()
            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            query = """
            SELECT uuid, pattern_name, pattern_type, improved_code, description, 
                   improvement_score, 1 - (embedding <=> %s::vector) as similarity
            FROM code_quality_patterns 
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY similarity DESC
            LIMIT %s;
            """
            cursor.execute(query, (embedding_str, embedding_str, similarity_threshold, limit))
            results = cursor.fetchall()
            cursor.close()
            
            patterns = []
            for row in results:
                patterns.append({
                    'uuid': str(row[0]),
                    'pattern_name': row[1],
                    'pattern_type': row[2],
                    'improved_code': row[3],
                    'description': row[4],
                    'improvement_score': float(row[5]),
                    'similarity': float(row[6])
                })
            return patterns
        except Exception as e:
            logger.error(f"❌ Failed to search patterns: {e}")
            return []
            
    async def search_similar_bugs(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 5
    ) -> List[Dict]:
        """Search for similar bug cases"""
        try:
            cursor = self.connection.cursor()
            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            query = """
            SELECT uuid, bug_title, bug_category, fix_solution, prevention_tips,
                   severity_level, 1 - (embedding <=> %s::vector) as similarity
            FROM bug_learning_cases 
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY similarity DESC
            LIMIT %s;
            """
            cursor.execute(query, (embedding_str, embedding_str, similarity_threshold, limit))
            results = cursor.fetchall()
            cursor.close()
            
            bugs = []
            for row in results:
                bugs.append({
                    'uuid': str(row[0]),
                    'bug_title': row[1],
                    'bug_category': row[2],
                    'fix_solution': row[3],
                    'prevention_tips': row[4],
                    'severity_level': int(row[5]),
                    'similarity': float(row[6])
                })
            return bugs
        except Exception as e:
            logger.error(f"❌ Failed to search bug cases: {e}")
            return []

class EmbeddingGenerator:
    """OpenAI embedding generator for semantic search"""
    
    def __init__(self, api_key:
        """初期化メソッド"""
    Optional[str] = None):
        if OPENAI_AVAILABLE and api_key:
            self.client = OpenAI(api_key=api_key)
            self.model = "text-embedding-3-small"
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            self.client = None
            self.model = None
            self.encoding = None
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.client:
            # Return dummy embedding for testing/demo
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_hex = hash_obj.hexdigest()
            # Convert hash to float values
            dummy_embedding = []
            for i in range(0, len(hash_hex), 2):
                val = int(hash_hex[i:i+2], 16) / 255.0
                dummy_embedding.append(val)
            # Pad to 1536 dimensions
            while len(dummy_embedding) < 1536:
                dummy_embedding.extend(dummy_embedding[:min(16, 1536 - len(dummy_embedding))])
            return dummy_embedding[:1536]
            
        try:
            # Truncate text if too long
            tokens = self.encoding.encode(text)
            if len(tokens) > 8000:
                text = self.encoding.decode(tokens[:8000])
                
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

class CodeQualityAnalyzer:
    """Advanced code quality analyzer with Elder's wisdom"""
    
    def __init__(self):
        """初期化メソッド"""
        self.anti_patterns = self._load_anti_patterns()
        self.best_practices = self._load_best_practices()
        
    def _load_anti_patterns(self) -> List[Dict]:
        """Load known anti-patterns"""
        return [
            {
                'name': 'God Class',
                'pattern': r'class\s+\w+.*?(?=\n\s*class|\n\s*def|\Z)',
                'description': 'Class with too many responsibilities',
                'severity': 8,
                'suggestion': 'Break into smaller, focused classes'
            },
            {
                'name': 'Long Method',
                'pattern': r'def\s+\w+\([^)]*\):.*?(?=\n\s*def|\n\s*class|\Z)',
                'description': 'Method with too many lines',
                'severity': 6,
                'suggestion': 'Extract smaller methods'
            },
            {
                'name': 'Magic Numbers',
                'pattern': r'\b\d+\b',
                'description': 'Hardcoded numeric values',
                'severity': 4,
                'suggestion': 'Use named constants'
            },
            {
                'name': 'TODO Comments',
                'pattern': r'#.*?TODO',
                'description': 'Unfinished implementation',
                'severity': 3,
                'suggestion': 'Complete implementation or create issue'
            }
        ]
        
    def _load_best_practices(self) -> List[Dict]:
        """Load best practice patterns"""
        return [
            {
                'name': 'Type Hints',
                'pattern': r'def\s+\w+\([^)]*\)\s*->',
                'description': 'Functions with return type hints',
                'score_bonus': 5
            },
            {
                'name': 'Docstrings',
                'pattern': r'""".*?"""',
                'description': 'Functions with documentation',
                'score_bonus': 3
            },
            {
                'name': 'Error Handling',
                'pattern': r'try:.*?except',
                'description': 'Proper exception handling',
                'score_bonus': 4
            }
        ]
        
    async def analyze_code(self, code: str, file_path: str = "") -> CodeAnalysisResult:
        """Comprehensive code quality analysis"""
        try:
            # Parse AST for structure analysis
            tree = ast.parse(code)
            
            # Calculate complexity
            complexity_score = self._calculate_complexity(code)
            
            # Calculate maintainability index
            maintainability_index = self._calculate_maintainability(code)
            
            # Detect issues
            issues = self._detect_issues(code)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(code, issues)
            
            # Assess bug risks
            bug_risks = self._assess_bug_risks(code)
            
            # Check Iron Will compliance
            iron_will_compliance = self._check_iron_will_compliance(code)
            
            # Check TDD compatibility
            tdd_compatibility = self._check_tdd_compatibility(code)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                complexity_score, maintainability_index, issues, iron_will_compliance, tdd_compatibility
            )
            
            return CodeAnalysisResult(
                file_path=file_path,
                quality_score=quality_score,
                complexity_score=complexity_score,
                maintainability_index=maintainability_index,
                issues=issues,
                suggestions=suggestions,
                bug_risks=bug_risks,
                iron_will_compliance=iron_will_compliance,
                tdd_compatibility=tdd_compatibility,
                timestamp=datetime.now()
            )
            
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in code: {e}")
            return CodeAnalysisResult(
                file_path=file_path,
                quality_score=0.0,
                complexity_score=100,
                maintainability_index=0.0,
                issues=[{'type': 'syntax_error', 'message': str(e), 'severity': 10}],
                suggestions=[],
                bug_risks=[],
                iron_will_compliance=False,
                tdd_compatibility=False,
                timestamp=datetime.now()
            )
            
    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity"""
        if not RADON_AVAILABLE:
            # Simple complexity estimation based on control structures
            complexity_score = 1
            complexity_score += code.count('if ')
            complexity_score += code.count('elif ')
            complexity_score += code.count('for ')
            complexity_score += code.count('while ')
            complexity_score += code.count('except ')
            complexity_score += code.count('and ')
            complexity_score += code.count('or ')
            return complexity_score
            
        try:
            cc = complexity.cc_visit(code)
            if cc:
                return max([block.complexity for block in cc])
            return 1
        except:
            return 1
            
    def _calculate_maintainability(self, code: str) -> float:
        """Calculate maintainability index"""
        if not RADON_AVAILABLE:
            # Simple maintainability estimation
            lines = code.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            if not non_empty_lines:
                return 0.0
                
            # Basic heuristics
            score = 100.0
            
            # Penalize long functions
            avg_function_length = len(non_empty_lines) / max(1, code.count('def '))
            if avg_function_length > 20:
                score -= 20
            elif avg_function_length > 10:
                score -= 10
                
            # Reward documentation
            docstring_lines = code.count('"""') + code.count("'''")
            score += min(20, docstring_lines * 5)
            
            # Penalize complexity
            complexity_score = self._calculate_complexity(code)
            if complexity_score > 10:
                score -= 30
            elif complexity_score > 5:
                score -= 15
                
            return max(0.0, min(100.0, score))
            
        try:
            mi = metrics.mi_visit(code, True)
            return mi if mi else 0.0
        except:
            return 0.0
            
    def _detect_issues(self, code: str) -> List[Dict[str, Any]]:
        """Detect code issues and anti-patterns"""
        issues = []
        
        for pattern in self.anti_patterns:
            matches = re.finditer(pattern['pattern'], code, re.DOTALL | re.MULTILINE)
            for match in matches:
                issues.append({
                    'type': 'anti_pattern',
                    'name': pattern['name'],
                    'description': pattern['description'],
                    'severity': pattern['severity'],
                    'line_start': code[:match.start()].count('\n') + 1,
                    'line_end': code[:match.end()].count('\n') + 1,
                    'code_snippet': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0)
                })
                
        return issues
        
    def _generate_suggestions(self, code: str, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Suggestions based on detected issues
        for issue in issues:
            if issue['type'] == 'anti_pattern':
                suggestions.append({
                    'type': 'improvement',
                    'priority': 'high' if issue['severity'] > 7 else 'medium' if issue['severity'] > 4 else 'low',
                    'title': f"Fix {issue['name']}",
                    'description': issue.get('suggestion', 'Consider refactoring this code'),
                    'line_start': issue['line_start'],
                    'line_end': issue['line_end']
                })
                
        # Check for missing best practices
        for practice in self.best_practices:
            if not re.search(practice['pattern'], code, re.DOTALL):
                suggestions.append({
                    'type': 'enhancement',
                    'priority': 'medium',
                    'title': f"Add {practice['name']}",
                    'description': practice['description'],
                    'score_bonus': practice['score_bonus']
                })
                
        return suggestions
        
    def _assess_bug_risks(self, code: str) -> List[Dict[str, Any]]:
        """Assess potential bug risks"""
        risks = []
        
        # Check for common bug patterns
        bug_patterns = [
            {
                'pattern': r'if\s+\w+\s*=\s*',
                'name': 'Assignment in condition',
                'risk_level': 8,
                'description': 'Assignment used instead of comparison'
            },
            {
                'pattern': r'except:\s*pass',
                'name': 'Silent exception',
                'risk_level': 7,
                'description': 'Exception swallowed without handling'
            },
            {
                'pattern': r'eval\s*\(',
                'name': 'Code injection risk',
                'risk_level': 9,
                'description': 'eval() can execute arbitrary code'
            },
            {
                'pattern': r'os\.system\s*\(',
                'name': 'Command injection risk',
                'risk_level': 9,
                'description': 'os.system() can execute shell commands'
            }
        ]
        
        for pattern in bug_patterns:
            matches = re.finditer(pattern['pattern'], code)
            for match in matches:
                risks.append({
                    'name': pattern['name'],
                    'risk_level': pattern['risk_level'],
                    'description': pattern['description'],
                    'line': code[:match.start()].count('\n') + 1,
                    'code_snippet': match.group(0)
                })
                
        return risks
        
    def _check_iron_will_compliance(self, code: str) -> bool:
        """Check Iron Will (no workarounds) compliance"""
        workaround_patterns = [
            r'#\s*hack',
            r'#\s*workaround',
            r'#\s*temporary',
            r'#\s*quick\s*fix',
            r'#\s*dirty',
            r'#\s*TODO',
            r'#\s*todo',
            r'time\.sleep\s*\(',  # Often indicates timing hacks
        ]
        
        for pattern in workaround_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False
                
        return True
        
    def _check_tdd_compatibility(self, code: str) -> bool:
        """Check TDD compatibility"""
        # Look for test indicators
        tdd_indicators = [
            r'def\s+test_',
            r'import\s+pytest',
            r'import\s+unittest',
            r'assert\s+',
            r'@pytest\.',
            r'TestCase'
        ]
        
        for pattern in tdd_indicators:
            if re.search(pattern, code):
                return True
                
        return False
        
    def _calculate_quality_score(self, complexity: int, maintainability: float, 
                                issues: List[Dict], iron_will: bool, tdd: bool) -> float:
        """Calculate overall quality score (0-100)"""
        base_score = 100.0
        
        # Complexity penalty
        if complexity > 15:
            base_score -= 30
        elif complexity > 10:
            base_score -= 20
        elif complexity > 5:
            base_score -= 10
            
        # Maintainability bonus
        if maintainability > 80:
            base_score += 10
        elif maintainability < 40:
            base_score -= 20
            
        # Issues penalty
        for issue in issues:
            base_score -= issue.get('severity', 5)
            
        # Iron Will compliance bonus
        if iron_will:
            base_score += 15
        else:
            base_score -= 25
            
        # TDD compatibility bonus
        if tdd:
            base_score += 10
            
        return max(0.0, min(100.0, base_score))

class SmartCodingAssistant:
    """AI-powered coding assistant with learning capabilities"""
    
    def __init__(self, db_manager:
        """初期化メソッド"""
    DatabaseManager, embedding_generator: EmbeddingGenerator):
        self.db = db_manager
        self.embedder = embedding_generator
        self.analyzer = CodeQualityAnalyzer()
        
    async def analyze_and_suggest(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """Analyze code and provide intelligent suggestions"""
        # Perform quality analysis
        analysis = await self.analyzer.analyze_code(code, file_path)
        
        # Generate embedding for similarity search
        embedding = await self.embedder.generate_embedding(code)
        
        # Search for similar patterns and bugs (only if we have data)
        similar_patterns = []
        similar_bugs = []
        try:
            similar_patterns = await self.db.search_similar_patterns(embedding)
            similar_bugs = await self.db.search_similar_bugs(embedding)
        except Exception as e:
            logger.warning(f"⚠️ Could not search similar patterns/bugs: {e}")
        
        # Generate AI-powered suggestions
        ai_suggestions = await self._generate_ai_suggestions(
            code,
            analysis,
            similar_patterns,
            similar_bugs
        )
        
        return {
            'analysis': asdict(analysis),
            'similar_patterns': similar_patterns,
            'similar_bugs': similar_bugs,
            'ai_suggestions': ai_suggestions,
            'overall_recommendation': self._generate_overall_recommendation(
                analysis,
                similar_patterns,
                similar_bugs
            )
        }
        
    async def _generate_ai_suggestions(self, code: str, analysis: CodeAnalysisResult, 
                                     similar_patterns: List[Dict], similar_bugs: List[Dict]) -> List[Dict]:
        """Generate AI-powered improvement suggestions"""
        suggestions = []
        
        # High-priority issues first
        high_priority_issues = [issue for issue in analysis.issues if issue.get('severity', 0) > 7]
        for issue in high_priority_issues:
            suggestions.append({
                'type': 'critical_fix',
                'priority': 'critical',
                'title': f"Critical: {issue['name']}",
                'description': issue['description'],
                'action': 'immediate_fix_required',
                'line': issue.get('line_start', 0)
            })
            
        # Bug prevention based on similar cases
        for bug in similar_bugs:
            if bug['similarity'] > 0.85:
                suggestions.append({
                    'type': 'bug_prevention',
                    'priority': 'high',
                    'title': f"Prevent {bug['bug_category']}: {bug['bug_title']}",
                    'description': f"Similar code caused: {bug['bug_category']}",
                    'prevention_tips': bug['prevention_tips'],
                    'similarity': bug['similarity']
                })
                
        # Quality improvements based on patterns
        for pattern in similar_patterns:
            if pattern['similarity'] > 0.8:
                suggestions.append({
                    'type': 'quality_improvement',
                    'priority': 'medium',
                    'title': f"Apply {pattern['pattern_type']}: {pattern['pattern_name']}",
                    'description': pattern['description'],
                    'improved_code': pattern['improved_code'],
                    'improvement_score': pattern['improvement_score'],
                    'similarity': pattern['similarity']
                })
                
        return suggestions
        
    def _generate_overall_recommendation(self, analysis: CodeAnalysisResult, 
                                       similar_patterns: List[Dict], similar_bugs: List[Dict]) -> Dict[str, Any]:
        """Generate overall recommendation"""
        recommendation = {
            'quality_level': 'excellent' if analysis.quality_score > 85 else 
                           'good' if analysis.quality_score > 70 else
                           'needs_improvement' if analysis.quality_score > 50 else 'poor',
            'iron_will_status': 'compliant' if analysis.iron_will_compliance else 'violation',
            'tdd_status': 'compatible' if analysis.tdd_compatibility else 'needs_tests',
            'priority_actions': [],
            'estimated_improvement_time': 0
        }
        
        # Determine priority actions
        if not analysis.iron_will_compliance:
            recommendation['priority_actions'].append('Fix Iron Will violations immediately')
            recommendation['estimated_improvement_time'] += 30
            
        if not analysis.tdd_compatibility:
            recommendation['priority_actions'].append('Add comprehensive tests')
            recommendation['estimated_improvement_time'] += 60
            
        if analysis.complexity_score > 10:
            recommendation['priority_actions'].append('Reduce complexity through refactoring')
            recommendation['estimated_improvement_time'] += 45
            
        critical_bugs = [bug for bug in similar_bugs if bug['similarity'] > 0.9 and bug['severity_level'] > 7]
        if critical_bugs:
            recommendation['priority_actions'].append('Address critical bug risks')
            recommendation['estimated_improvement_time'] += 20
            
        return recommendation
        
    async def learn_from_bug(self, bug_case: BugLearningCase) -> str:
        """Learn from a new bug case"""
        # Generate embedding
        text = f"{bug_case.bug_title} {bug_case.bug_description} {bug_case.original_code}"
        embedding = await self.embedder.generate_embedding(text)
        
        # Store in database
        uuid = await self.db.store_bug_case(bug_case, embedding)
        
        logger.info(f"🧠 Learned from bug: {bug_case.bug_title}")
        return uuid
        
    async def learn_from_pattern(self, pattern: QualityPattern) -> str:
        """Learn from a new quality pattern"""
        # Generate embedding
        text = f"{pattern.pattern_name} {pattern.description} {pattern.problematic_code} {pattern.improved_code}"
        embedding = await self.embedder.generate_embedding(text)
        
        # Store in database
        uuid = await self.db.store_quality_pattern(pattern, embedding)
        
        logger.info(f"🎯 Learned quality pattern: {pattern.pattern_name}")
        return uuid

# Main API class
class EldersCodeQualityEngine:
    """Main engine class for Elders Guild Code Quality System"""
    
    def __init__(self, db_params:
        """初期化メソッド"""
    Dict[str, str], openai_api_key: Optional[str] = None):
        self.db = DatabaseManager(db_params)
        self.embedder = EmbeddingGenerator(openai_api_key)
        self.assistant = None
        
    async def initialize(self):
        """Initialize the engine"""
        await self.db.connect()
        self.assistant = SmartCodingAssistant(self.db, self.embedder)
        logger.info("🏛️ Elders Code Quality Engine initialized")
        
    async def shutdown(self):
        """Shutdown the engine"""
        await self.db.close()
        logger.info("🔒 Elders Code Quality Engine shutdown")
        
    async def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return await self.assistant.analyze_and_suggest(code, file_path)
        except Exception as e:
            logger.error(f"❌ Failed to analyze file {file_path}: {e}")
            return {'error': str(e)}
            
    async def analyze_code_snippet(self, code: str) -> Dict[str, Any]:
        """Analyze a code snippet"""
        return await self.assistant.analyze_and_suggest(code)
        
    async def learn_bug_case(self, bug_case: BugLearningCase) -> str:
        """Learn from a bug case"""
        return await self.assistant.learn_from_bug(bug_case)
        
    async def learn_quality_pattern(self, pattern: QualityPattern) -> str:
        """Learn from a quality pattern"""
        return await self.assistant.learn_from_pattern(pattern)

# Convenience functions for quick usage
async def quick_analyze(
    code: str,
    db_params: Dict[str,
    str],
    openai_key: Optional[str] = None
) -> Dict[str, Any]:
    """Quick code analysis"""
    engine = EldersCodeQualityEngine(db_params, openai_key)
    await engine.initialize()
    try:
        result = await engine.analyze_code_snippet(code)
        return result
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    # Example usage
    async def main():
        """mainメソッド"""
        # Database connection parameters
        db_params = {
            'host': 'localhost',
            'database': 'elders_guild_pgvector',
            'user': 'postgres',
            'password': ''
        }
        
        # Sample code to analyze
        sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total = total + item
    return total

def process_data(data):
    # TODO: implement proper validation
    result = []
    for i in range(len(data)):
        if data[i] != None:
            result.append(data[i] * 2)
    return result
'''
        
        # Analyze the code
        result = await quick_analyze(sample_code, db_params)
        print("🏛️ Elders Guild Code Quality Analysis:")
        print(json.dumps(result, indent=2, default=str))
        
    # Run the example
    asyncio.run(main())