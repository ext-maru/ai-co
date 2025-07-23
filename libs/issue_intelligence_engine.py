#!/usr/bin/env python3
"""
Issue Intelligence Engine
自然言語処理によるIssue要件抽出・理解システム
"""

import re
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional, Set, Tuple
import logging
from dataclasses import dataclass

# NLTK をオプショナルに
try:
    import nltk
    NLTK_AVAILABLE = True
    # NLTK データをダウンロード（初回のみ）
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.download('punkt_tab', quiet=True)
        except:
            pass
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            pass
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger_eng')
    except LookupError:
        try:
            nltk.download('averaged_perceptron_tagger_eng', quiet=True)
        except:
            pass
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TechnicalRequirement:
    """技術要件クラス"""
    name: str
    confidence: float
    context: str
    category: str


@dataclass
class FeatureRequirement:
    """機能要件クラス"""
    action: str
    target: str
    details: str
    priority: str


@dataclass
class IssueIntelligence:
    """Issue理解結果"""
    tech_requirements: List[TechnicalRequirement]
    feature_requirements: List[FeatureRequirement]
    complexity_indicators: Dict[str, float]
    key_entities: List[str]
    implementation_hints: List[str]
    estimated_effort: str
    primary_domain: str


class TechnicalPatternMatcher:
    """技術パターンマッチャー"""
    
    TECH_PATTERNS = {
        'aws': {
            'primary_keywords': ['aws', 'amazon', 'boto3'],
            'services': {
                's3': ['s3', 'bucket', 'object storage', 'file storage'],
                'dynamodb': ['dynamodb', 'nosql', 'document database', 'table'],
                'lambda': ['lambda', 'serverless', 'function as a service', 'faas'],
                'ec2': ['ec2', 'virtual machine', 'instance', 'compute'],
                'rds': ['rds', 'relational database', 'mysql', 'postgresql'],
                'cloudwatch': ['cloudwatch', 'monitoring', 'metrics', 'logs', 'alarm'],
                'sns': ['sns', 'notification', 'message', 'topic'],
                'sqs': ['sqs', 'queue', 'message queue'],
                'api_gateway': ['api gateway', 'rest api', 'http api'],
                'cognito': ['cognito', 'authentication', 'user pool'],
                'iam': ['iam', 'role', 'policy', 'permission', 'access'],
                'cloudformation': ['cloudformation', 'infrastructure as code', 'template'],
                'ecs': ['ecs', 'container', 'docker', 'fargate'],
                'eks': ['eks', 'kubernetes', 'k8s'],
                'elasticache': ['elasticache', 'redis', 'memcached', 'cache']
            },
            'complexity_indicators': {
                'multi_service': ['integration', 'connect', 'multiple services'],
                'security': ['security', 'encryption', 'ssl', 'tls', 'vpc'],
                'scaling': ['auto scaling', 'load balancer', 'high availability'],
                'monitoring': ['cloudwatch', 'x-ray', 'tracing', 'observability']
            }
        },
        'web': {
            'primary_keywords': ['web', 'api', 'http', 'rest', 'graphql'],
            'frameworks': {
                'fastapi': ['fastapi', 'fast api'],
                'flask': ['flask'],
                'django': ['django'],
                'tornado': ['tornado'],
                'bottle': ['bottle'],
                'starlette': ['starlette']
            },
            'features': {
                'authentication': ['auth', 'login', 'session', 'jwt', 'oauth'],
                'database': ['database', 'db', 'sql', 'orm', 'model'],
                'api': ['endpoint', 'route', 'controller', 'view'],
                'frontend': ['html', 'css', 'javascript', 'template', 'form']
            }
        },
        'data': {
            'primary_keywords': ['data', 'analysis', 'machine learning', 'ml', 'ai'],
            'libraries': {
                'pandas': ['pandas', 'dataframe', 'csv', 'excel'],
                'numpy': ['numpy', 'array', 'matrix', 'numerical'],
                'sklearn': ['scikit-learn', 'sklearn', 'classification', 'regression'],
                'matplotlib': ['matplotlib', 'plot', 'chart', 'visualization'],
                'seaborn': ['seaborn', 'statistical visualization'],
                'jupyter': ['jupyter', 'notebook', 'ipynb']
            }
        },
        'database': {
            'primary_keywords': ['database', 'db', 'data storage'],
            'types': {
                'postgresql': ['postgresql', 'postgres', 'psql'],
                'mysql': ['mysql'],
                'sqlite': ['sqlite'],
                'mongodb': ['mongodb', 'mongo', 'nosql document'],
                'redis': ['redis', 'cache', 'key-value'],
                'elasticsearch': ['elasticsearch', 'search engine', 'full-text search']
            }
        },
        'testing': {
            'primary_keywords': ['test', 'testing', 'tdd', 'bdd'],
            'frameworks': {
                'pytest': ['pytest'],
                'unittest': ['unittest', 'unit test'],
                'mock': ['mock', 'mocking', 'stub'],
                'coverage': ['coverage', 'test coverage']
            }
        }
    }
    
    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_technical_requirements(self, text: str) -> List[TechnicalRequirement]:
        """技術要件を抽出"""
        text_lower = text.lower()
        requirements = []
        
        for domain, patterns in self.TECH_PATTERNS.items():
            # ドメインの基本マッチング
            primary_matches = sum(1 for keyword in patterns['primary_keywords'] 
                                if keyword in text_lower)
            
            if primary_matches > 0:
                base_confidence = min(0.8, primary_matches * 0.3)
                
                # 詳細サービス/ライブラリの検出
                for category_name, category_patterns in patterns.items():
                    if category_name == 'primary_keywords':
                        continue
                        
                    if isinstance(category_patterns, dict):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        for service_name, service_keywords in category_patterns.items():
                            service_matches = sum(1 for keyword in service_keywords 
                                                if keyword in text_lower)
                            
                            if not (service_matches > 0):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if service_matches > 0:
                                confidence = min(0.95, base_confidence + service_matches * 0.2)
                                context = self._extract_context(text, service_keywords[0])
                                
                                requirements.append(TechnicalRequirement(
                                    name=f"{domain}_{service_name}",
                                    confidence=confidence,
                                    context=context,
                                    category=domain
                                ))
        
        return sorted(requirements, key=lambda x: x.confidence, reverse=True)
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """キーワード周辺のコンテキストを抽出"""
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        
        return text[start:end].strip()


class FeatureExtractor:
    """機能要件抽出器"""
    
    ACTION_PATTERNS = {
        'create': ['create', 'add', 'implement', 'build', 'develop', 'generate'],
        'update': ['update', 'modify', 'change', 'edit', 'improve', 'enhance'],
        'delete': ['delete', 'remove', 'drop', 'clean up', 'eliminate'],
        'integrate': ['integrate', 'connect', 'link', 'combine', 'merge'],
        'optimize': ['optimize', 'improve performance', 'speed up', 'enhance'],
        'fix': ['fix', 'resolve', 'solve', 'repair', 'debug'],
        'configure': ['configure', 'setup', 'install', 'deploy', 'initialize'],
        'monitor': ['monitor', 'track', 'observe', 'watch', 'log'],
        'secure': ['secure', 'protect', 'encrypt', 'authenticate', 'authorize'],
        'test': ['test', 'verify', 'validate', 'check', 'ensure']
    }
    
    PRIORITY_INDICATORS = {
        'critical': ['critical', 'urgent', 'emergency', 'blocker', 'p0'],
        'high': ['high priority', 'important', 'asap', 'p1'],
        'medium': ['medium', 'normal', 'standard', 'p2'],
        'low': ['low priority', 'nice to have', 'enhancement', 'p3']
    }
    
    def extract_features(self, text: str) -> List[FeatureRequirement]:
        """機能要件を抽出"""
        if NLTK_AVAILABLE:
            try:
                sentences = nltk.sent_tokenize(text)
            except:
                # NLTK失敗時のフォールバック
                sentences = text.split('. ')
        else:
            # NLTK利用不可時のフォールバック
            sentences = text.split('. ')
        
        features = []
        
        for sentence in sentences:
            feature = self._analyze_sentence(sentence)
            if feature:
                features.append(feature)
        
        return features
    
    def _analyze_sentence(self, sentence: str) -> Optional[FeatureRequirement]:
        """文章から機能要件を分析"""
        sentence_lower = sentence.lower()
        
        # アクション検出
        detected_action = None
        for action, patterns in self.ACTION_PATTERNS.items():
            if any(pattern in sentence_lower for pattern in patterns):
                detected_action = action
                break
        
        if not detected_action:
            return None
        
        # 対象検出（名詞を抽出）
        if NLTK_AVAILABLE:
            try:
                tokens = nltk.word_tokenize(sentence)
                pos_tags = nltk.pos_tag(tokens)
                
                # 名詞を抽出
                nouns = [word for word, pos in pos_tags 
                        if pos.startswith('NN') and len(word) > 2]
                target = ' '.join(nouns[:3]) if nouns else "system"
                
            except:
                # NLTK失敗時のフォールバック
                words = sentence.split()
                target = ' '.join(words[1:4]) if len(words) > 1 else "system"
        else:
            # NLTK利用不可時のフォールバック
            words = sentence.split()
            target = ' '.join(words[1:4]) if len(words) > 1 else "system"
        
        # 優先度検出
        priority = 'medium'  # デフォルト
        for pri, indicators in self.PRIORITY_INDICATORS.items():
            if any(indicator in sentence_lower for indicator in indicators):
                priority = pri
                break
        
        return FeatureRequirement(
            action=detected_action,
            target=target,
            details=sentence.strip(),
            priority=priority
        )


class ComplexityAnalyzer:
    """複雑度分析器"""
    
    COMPLEXITY_INDICATORS = {
        'integration': {
            'patterns': ['integrate', 'connect', 'api', 'service', 'multiple'],
            'weight': 0.3
        },
        'security': {
            'patterns': ['security', 'auth', 'permission', 'encrypt', 'ssl'],
            'weight': 0.4
        },
        'performance': {
            'patterns': ['performance', 'optimize', 'scale', 'load', 'cache'],
            'weight': 0.3
        },
        'data_processing': {
            'patterns': ['data', 'process', 'transform', 'analysis', 'algorithm'],
            'weight': 0.2
        },
        'real_time': {
            'patterns': ['real-time', 'streaming', 'live', 'instant', 'async'],
            'weight': 0.3
        },
        'distributed': {
            'patterns': ['distributed', 'microservice', 'cluster', 'multi'],
            'weight': 0.4
        }
    }
    
    def analyze_complexity(self, text: str, features: List[FeatureRequirement]) -> Dict[str, float]:
        """複雑度指標を分析"""
        text_lower = text.lower()
        complexity = {}
        
        # パターンベースの複雑度検出
        for indicator, config in self.COMPLEXITY_INDICATORS.items():
            matches = sum(1 for pattern in config['patterns'] 
                         if pattern in text_lower)
            complexity[indicator] = min(1.0, matches * config['weight'])
        
        # 機能数による複雑度
        feature_count = len(features)
        complexity['feature_count'] = min(1.0, feature_count * 0.1)
        
        # クリティカル機能の存在
        critical_features = sum(1 for f in features if f.priority == 'critical')
        complexity['critical_priority'] = min(1.0, critical_features * 0.5)
        
        return complexity


class IssueIntelligenceEngine:
    """Issue理解エンジン"""
    
    def __init__(self):
        """初期化メソッド"""
        self.tech_matcher = TechnicalPatternMatcher()
        self.feature_extractor = FeatureExtractor()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_issue(self, issue_title: str, issue_body: str = "") -> IssueIntelligence:
        """Issue を包括的に分析"""
        full_text = f"{issue_title} {issue_body}"
        
        try:
            # 技術要件抽出
            tech_requirements = self.tech_matcher.extract_technical_requirements(full_text)
            
            # 機能要件抽出
            feature_requirements = self.feature_extractor.extract_features(full_text)
            
            # 複雑度分析
            complexity_indicators = self.complexity_analyzer.analyze_complexity(
                full_text, feature_requirements
            )
            
            # キーエンティティ抽出
            key_entities = self._extract_key_entities(full_text)
            
            # 実装ヒント生成
            implementation_hints = self._generate_implementation_hints(
                tech_requirements, feature_requirements
            )
            
            # 工数見積もり
            estimated_effort = self._estimate_effort(complexity_indicators, feature_requirements)
            
            # 主要ドメイン特定
            primary_domain = self._determine_primary_domain(tech_requirements)
            
            return IssueIntelligence(
                tech_requirements=tech_requirements,
                feature_requirements=feature_requirements,
                complexity_indicators=complexity_indicators,
                key_entities=key_entities,
                implementation_hints=implementation_hints,
                estimated_effort=estimated_effort,
                primary_domain=primary_domain
            )
            
        except Exception as e:
            self.logger.error(f"Issue analysis failed: {e}")
            # フォールバック: 基本的な分析結果を返す
            return self._create_fallback_analysis(issue_title, issue_body)
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """キーエンティティを抽出"""
        # 技術用語、ファイル名、URLなどを抽出
        entities = []
        
        # ファイル拡張子
        file_extensions = re.findall(r'\w+\.\w{2,4}', text)
        entities.extend(file_extensions)
        
        # URL
        urls = re.findall(r'https?://[^\s]+', text)
        entities.extend([url.split('/')[2] for url in urls])  # ドメインのみ
        
        # 大文字の単語（API名など）
        capitals = re.findall(r'\b[A-Z]{2,}\b', text)
        entities.extend(capitals)
        
        # 技術用語（キャメルケース）
        camel_case = re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', text)
        entities.extend(camel_case)
        
        return list(set(entities))[:10]  # 重複除去、最大10個
    
    def _generate_implementation_hints(
        self, 
        tech_reqs: List[TechnicalRequirement],
        feature_reqs: List[FeatureRequirement]
    ) -> List[str]:
        """実装ヒントを生成"""
        hints = []
        
        # 技術要件ベースのヒント
        for tech in tech_reqs[:3]:  # 上位3つ
            if 'aws_s3' in tech.name:
                hints.append("boto3.client('s3') を使用してS3操作を実装")
            elif 'aws_dynamodb' in tech.name:
                hints.append("DynamoDBリソースでテーブル操作を実装")
            elif 'web_fastapi' in tech.name:
                hints.append("FastAPIでRESTful APIエンドポイントを実装")
            elif 'data_pandas' in tech.name:
                hints.append("pandas.DataFrameでデータ処理パイプラインを実装")
        
        # 機能要件ベースのヒント
        action_counts = Counter(f.action for f in feature_reqs)
        for action, count in action_counts.most_common(2):
            if action == 'create':
                hints.append("作成機能にはバリデーションとエラーハンドリングを追加")
            elif action == 'integrate':
                hints.append("統合処理には再試行ロジックとログ出力を実装")
            elif action == 'secure':
                hints.append("セキュリティ機能には認証・認可・暗号化を考慮")
        
        return hints[:5]  # 最大5個
    
    def _estimate_effort(
        self, 
        complexity: Dict[str, float],
        features: List[FeatureRequirement]
    ) -> str:
        """工数を見積もり"""
        # 複雑度スコアの計算
        complexity_score = sum(complexity.values()) / max(1, len(complexity))
        
        # 機能数とクリティカル度
        feature_count = len(features)
        critical_count = sum(1 for f in features if f.priority == 'critical')
        
        # 総合スコア
        total_score = (
            complexity_score * 0.5 +
            min(1.0, feature_count * 0.1) * 0.3 +
            min(1.0, critical_count * 0.3) * 0.2
        )
        
        if total_score < 0.3:
            return "small"  # 1-2日
        elif total_score < 0.6:
            return "medium"  # 3-5日
        elif total_score < 0.8:
            return "large"  # 1-2週間
        else:
            return "extra_large"  # 2週間以上
    
    def _determine_primary_domain(self, tech_reqs: List[TechnicalRequirement]) -> str:
        """主要ドメインを特定"""
        if not tech_reqs:
            return "general"
        
        # カテゴリ別の信頼度合計
        domain_scores = defaultdict(float)
        for req in tech_reqs:
            domain_scores[req.category] += req.confidence
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return "general"
    
    def _create_fallback_analysis(self, title: str, body: str) -> IssueIntelligence:
        """フォールバック分析結果"""
        return IssueIntelligence(
            tech_requirements=[],
            feature_requirements=[],
            complexity_indicators={'basic': 0.5},
            key_entities=[],
            implementation_hints=["基本的な実装パターンを使用"],
            estimated_effort="medium",
            primary_domain="general"
        )