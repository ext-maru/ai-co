#!/usr/bin/env python3
"""
🏛️ エンシェントエルダー古代魔法 - PredictiveQualityEngine

予測品質分析システム
Tier 4: Predictive Quality Analysis (予測品質分析)

このモジュールは以下の予測機能を実装：
- バグ発生確率計算 (機械学習モデル)
- パフォーマンス劣化予測
- セキュリティリスク先読み
- 技術負債予測
- メンテナンス困難度予測
"""

import ast
import re
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import statistics
import time
from pathlib import Path
import pickle

# 基底クラスのインポート
try:
    from elders_guild.elder_tree.ancient_elder.base import AncientMagicBase
except ImportError:
    logging.warning("AncientMagicBase not available")
    AncientMagicBase = object

@dataclass
class PredictionResult:
    """予測結果データクラス"""

    performance_risk: float  # 性能劣化リスク 0-1
    security_risk: float  # セキュリティリスク 0-1
    technical_debt_score: float  # 技術負債スコア 0-100
    maintainability_prediction: float  # 保守性予測 0-100
    confidence: float  # 予測信頼度 0-1
    recommendations: List[str]  # 推奨アクション
    risk_factors: List[Dict[str, Any]]  # リスク要因
    prediction_time: float  # 予測実行時間

class RiskLevel(Enum):
    """リスクレベル"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

class PredictiveQualityEngine(AncientMagicBase):
    """🔮 予測品質分析エンジン"""
    
    def __init__(self):
        """予測エンジン初期化"""
        super().__init__()
        
        # 予測モデルの初期化

        self.performance_model = self._initialize_performance_model()
        self.security_model = self._initialize_security_model()
        
        # 学習データとパターン
        self.historical_data = self._load_historical_data()

        self.performance_patterns = self._load_performance_patterns()
        self.security_patterns = self._load_security_patterns()
        
        # 予測統計
        self.prediction_history = []
        
    def predict_quality_issues(
        self,
        code: str,
        metadata: Optional[Dict] = None
    ) -> PredictionResult:
        """品質問題の予測分析
        
        Args:
            code: 分析対象のコード
            metadata: 追加メタデータ（開発者情報、プロジェクト履歴等）
            
        Returns:
            PredictionResult: 包括的予測結果
        """
        start_time = time.time()
        
        try:
            # コード特徴量の抽出
            features = self._extract_code_features(code)
            
            # 各種予測の実行

            perf_risk = self._predict_performance_risk(features, code)
            sec_risk = self._predict_security_risk(features, code)
            debt_score = self._predict_technical_debt(features, code)
            maintain_pred = self._predict_maintainability(features, code)
            
            # 予測信頼度の計算
            confidence = self._calculate_prediction_confidence(features)
            
            # リスク要因の特定
            risk_factors = self._identify_risk_factors(code, features)
            
            # 推奨アクションの生成
            recommendations = self._generate_recommendations(

            )
            
            result = PredictionResult(

                performance_risk=perf_risk,
                security_risk=sec_risk,
                technical_debt_score=debt_score,
                maintainability_prediction=maintain_pred,
                confidence=confidence,
                recommendations=recommendations,
                risk_factors=risk_factors,
                prediction_time=time.time() - start_time
            )
            
            # 予測履歴に追加
            self.prediction_history.append(result)
            
            return result
            
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return PredictionResult(

                performance_risk=0.5,
                security_risk=0.5,
                technical_debt_score=50.0,
                maintainability_prediction=50.0,
                confidence=0.0,  # エラー時は信頼度ゼロ
                recommendations=["Error in prediction - manual review required"],
                risk_factors=[{"type": "prediction_error", "message": str(e)}],
                prediction_time=time.time() - start_time
            )
    
    def _extract_code_features(self, code: str) -> Dict[str, Any]:
        """コードから特徴量を抽出"""
        try:
            tree = ast.parse(code)
            
            features = {
                # 基本統計
                "lines_of_code": len(code.split('\n')),
                "characters": len(code),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                
                # 複雑度指標
                "cyclomatic_complexity": self._calculate_complexity(tree),
                "nesting_depth": self._calculate_nesting_depth(tree),
                "conditional_statements": len(
                    [n for n in ast.walk(tree) if isinstance(n,
                    (ast.If,
                    ast.While,
                    ast.For))]
                ),
                
                # コード品質指標
                "comments_ratio": self._calculate_comments_ratio(code),
                "docstring_ratio": self._calculate_docstring_ratio(tree),
                "magic_numbers": self._count_magic_numbers(tree),
                "long_functions": self._count_long_functions(tree, code),
                
                # リスク指標
                "exception_handling": self._count_exception_handling(tree),
                "global_variables": self._count_global_variables(tree),
                "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
                
                # パフォーマンス指標
                "loops": len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]),
                "nested_loops": self._count_nested_loops(tree),
                "list_comprehensions": len([n for n in ast.walk(tree) if isinstance(n, ast.ListComp)]),
                
                # セキュリティ指標
                "eval_usage": len(re.findall(r'\beval\s*\(', code)),
                "exec_usage": len(re.findall(r'\bexec\s*\(', code)),
                "os_system_usage": len(re.findall(r'os\.system\s*\(', code)),
                "subprocess_usage": len(re.findall(r'subprocess\s*\.', code)),
            }
            
            return features
            
        except Exception as e:
            logging.warning(f"Feature extraction error: {e}")
            return self._get_default_features()

        """バグ発生確率の予測"""
        try:
            # 簡単な重み付きスコアリングモデル

            # 複雑度による影響
            complexity = features.get("cyclomatic_complexity", 0)

            # ネスト深度による影響
            nesting = features.get("nesting_depth", 0)

            # 長い関数による影響
            long_funcs = features.get("long_functions", 0)

            # 例外処理の不足による影響
            exception_handling = features.get("exception_handling", 0)
            total_functions = features.get("functions", 1)
            if total_functions > 0 and exception_handling / total_functions < 0.3:

            # マジックナンバーによる影響
            magic_numbers = features.get("magic_numbers", 0)

            # 過去のパターンマッチング

        except Exception as e:

            return 0.5  # デフォルト値
    
    def _predict_performance_risk(self, features: Dict[str, Any], code: str) -> float:
        """パフォーマンス劣化リスクの予測"""
        try:
            perf_risk = 0.0
            
            # ネストしたループによるリスク
            nested_loops = features.get("nested_loops", 0)
            perf_risk += min(nested_loops * 0.2, 0.4)  # O(n²)以上のリスク
            
            # ループ内での非効率な操作
            loops = features.get("loops", 0)
            if loops > 0:
                # ループ内でのファイルI/Oやネットワーク処理を検出
                if re.search(r'for.*open\s*\(|while.*open\s*\(', code):
                    perf_risk += 0.3
                if re.search(r'for.*requests\.|while.*requests\.', code):
                    perf_risk += 0.3
            
            # 大量のメモリ使用パターン
            if re.search(r'range\s*\(\s*\d{6,}', code):  # 100万以上のrange
                perf_risk += 0.2
            
            # 非効率なデータ構造使用
            if 'list.append' in code and 'for' in code:
                perf_risk += 0.1  # リストappendループ
            
            # リスト内包表記の不適切な使用
            list_comps = features.get("list_comprehensions", 0)
            if list_comps > 5:  # 多数のリスト内包表記
                perf_risk += 0.1
            
            return min(perf_risk, 1.0)
            
        except Exception as e:
            logging.warning(f"Performance prediction error: {e}")
            return 0.5
    
    def _predict_security_risk(self, features: Dict[str, Any], code: str) -> float:
        """セキュリティリスクの予測"""
        try:
            sec_risk = 0.0
            
            # 危険な関数の使用
            sec_risk += features.get("eval_usage", 0) * 0.4  # eval使用
            sec_risk += features.get("exec_usage", 0) * 0.3  # exec使用
            sec_risk += features.get("os_system_usage", 0) * 0.5  # os.system使用
            sec_risk += features.get("subprocess_usage", 0) * 0.2  # subprocess使用
            
            # SQLインジェクションリスク
            if re.search(r'execute\s*\(\s*["\'].*%.*["\']', code):
                sec_risk += 0.3
            
            # ハードコードされた認証情報
            if re.search(
                r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']',
                code,
                re.IGNORECASE
            ):
                sec_risk += 0.4
            
            # ファイルパス操作のリスク
            if re.search(r'open\s*\([^)]*\+|\.\./|/etc/', code):
                sec_risk += 0.2
            
            # 入力検証の不足
            functions = features.get("functions", 0)
            if functions > 0 and not re.search(r'isinstance\s*\(|len\s*\(.*\)\s*[<>]|validate', code):
                sec_risk += 0.2
            
            return min(sec_risk, 1.0)
            
        except Exception as e:
            logging.warning(f"Security prediction error: {e}")
            return 0.5
    
    def _predict_technical_debt(self, features: Dict[str, Any], code: str) -> float:
        """技術負債の予測（0-100スコア）"""
        try:
            debt_score = 0.0

            # コメント不足による負債
            comments_ratio = features.get("comments_ratio", 0)
            if comments_ratio < 0.1:  # コメント率10%未満
                debt_score += 20
            
            # ドキュメント不足による負債
            docstring_ratio = features.get("docstring_ratio", 0)
            if docstring_ratio < 0.5:  # 関数の50%未満がドキュメント化
                debt_score += 15
            
            # 複雑度による負債
            complexity = features.get("cyclomatic_complexity", 0)
            debt_score += min(complexity * 2, 25)
            
            # 長い関数による負債
            long_funcs = features.get("long_functions", 0)
            debt_score += min(long_funcs * 8, 20)
            
            return min(debt_score, 100.0)
            
        except Exception as e:
            logging.warning(f"Technical debt prediction error: {e}")
            return 50.0
    
    def _predict_maintainability(self, features: Dict[str, Any], code: str) -> float:
        """保守性の予測（0-100スコア）"""
        try:
            maintain_score = 100.0  # 最高スコアから減算
            
            # 複雑度による保守性低下
            complexity = features.get("cyclomatic_complexity", 0)
            maintain_score -= min(complexity * 3, 40)
            
            # ネスト深度による保守性低下
            nesting = features.get("nesting_depth", 0)
            maintain_score -= min(nesting * 5, 20)
            
            # 長い関数による保守性低下
            long_funcs = features.get("long_functions", 0)
            maintain_score -= min(long_funcs * 10, 25)
            
            # グローバル変数による保守性低下
            globals_count = features.get("global_variables", 0)
            maintain_score -= min(globals_count * 8, 15)
            
            # コメント・ドキュメントによる保守性向上
            comments_ratio = features.get("comments_ratio", 0)
            docstring_ratio = features.get("docstring_ratio", 0)
            maintain_score += (comments_ratio + docstring_ratio) * 10
            
            return max(0.0, min(maintain_score, 100.0))
            
        except Exception as e:
            logging.warning(f"Maintainability prediction error: {e}")
            return 50.0
    
    def _calculate_prediction_confidence(self, features: Dict[str, Any]) -> float:
        """予測信頼度の計算"""
        try:
            confidence = 0.5  # ベース信頼度
            
            # コードサイズによる信頼度調整
            loc = features.get("lines_of_code", 0)
            if 10 <= loc <= 500:  # 適切なサイズ範囲
                confidence += 0.2
            elif loc < 10:  # 小さすぎる
                confidence -= 0.1
            elif loc > 1000:  # 大きすぎる
                confidence -= 0.2
            
            # 特徴量の完全性
            feature_completeness = len(features) / 20  # 期待特徴量数
            confidence += min(feature_completeness * 0.3, 0.3)
            
            return max(0.0, min(confidence, 1.0))
            
        except Exception:
            return 0.5
    
    def _identify_risk_factors(self, code: str, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """リスク要因の特定"""
        risk_factors = []
        
        try:
            # 高い複雑度
            complexity = features.get("cyclomatic_complexity", 0)
            if complexity > 10:
                risk_factors.append({
                    "type": "high_complexity",
                    "severity": "high" if complexity > 20 else "medium",
                    "description": f"High cyclomatic complexity: {complexity}",
                    "recommendation": "Consider refactoring into smaller functions"
                })
            
            # 深いネスト
            nesting = features.get("nesting_depth", 0)
            if nesting > 4:
                risk_factors.append({
                    "type": "deep_nesting",
                    "severity": "medium",
                    "description": f"Deep nesting level: {nesting}",
                    "recommendation": "Extract nested logic into separate functions"
                })
            
            # セキュリティリスク
            if features.get("eval_usage", 0) > 0:
                risk_factors.append({
                    "type": "security_risk",
                    "severity": "critical",
                    "description": "Use of eval() function detected",
                    "recommendation": "Replace eval() with safer alternatives"
                })
            
            # パフォーマンスリスク
            nested_loops = features.get("nested_loops", 0)
            if nested_loops > 2:
                risk_factors.append({
                    "type": "performance_risk",
                    "severity": "high",
                    "description": f"Nested loops detected: depth {nested_loops}",
                    "recommendation": "Consider algorithmic optimization"
                })
            
            return risk_factors
            
        except Exception as e:
            logging.warning(f"Risk factor identification error: {e}")
            return [{"type": "analysis_error", "description": str(e)}]

                                 sec_risk: float, debt_score: float, maintain_pred: float) -> List[str]:
        """推奨アクションの生成"""
        recommendations = []

            recommendations.append("HIGH: Implement comprehensive unit tests")
            recommendations.append("HIGH: Add extensive error handling")

            recommendations.append("MEDIUM: Review function complexity")
            recommendations.append("MEDIUM: Add input validation")
        
        if perf_risk > 0.6:
            recommendations.append("HIGH: Optimize nested loops")
            recommendations.append("HIGH: Profile memory usage")
        elif perf_risk > 0.3:
            recommendations.append("MEDIUM: Review algorithm efficiency")
        
        if sec_risk > 0.6:
            recommendations.append("CRITICAL: Address security vulnerabilities immediately")
            recommendations.append("HIGH: Implement input sanitization")
        elif sec_risk > 0.3:
            recommendations.append("MEDIUM: Review security best practices")
        
        if debt_score > 70:
            recommendations.append("HIGH: Refactor code to reduce technical debt")
            recommendations.append("MEDIUM: Add comprehensive documentation")
        
        if maintain_pred < 40:
            recommendations.append("HIGH: Simplify complex functions")
            recommendations.append("MEDIUM: Improve code organization")
        
        if not recommendations:
            recommendations.append("Code quality appears acceptable - continue monitoring")
        
        return recommendations
    
    # ヘルパーメソッド群
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """サイクロマティック複雑度計算"""
        complexity = 1  # ベース複雑度
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """ネスト深度計算"""
        max_depth = 0
        
        def get_depth(node, current_depth=0):
            """depth取得メソッド"""
            nonlocal max_depth
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                get_depth(child, current_depth)
        
        get_depth(tree)
        return max_depth
    
    def _calculate_comments_ratio(self, code: str) -> float:
        """コメント率計算"""
        lines = code.split('\n')
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        total_lines = len([line for line in lines if line.strip()])
        return comment_lines / max(total_lines, 1)
    
    def _calculate_docstring_ratio(self, tree: ast.AST) -> float:
        """ドキュメント文字列率計算"""
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if not functions:
            return 1.0  # 関数がない場合は完璧とする
        
        documented = 0
        for func in functions:
            # 複雑な条件判定
            if (func.body and isinstance(func.body[0], ast.Expr) and 
                isinstance(func.body[0].value, ast.Constant) and 
                isinstance(func.body[0].value.value, str)):
                documented += 1
        
        return documented / len(functions)
    
    def _count_magic_numbers(self, tree: ast.AST) -> int:
        """マジックナンバーのカウント"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in [0, 1, -1]:  # 一般的な値は除外
                    count += 1
        return count
    
    def _count_long_functions(self, tree: ast.AST, code: str) -> int:
        """長い関数のカウント"""
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        long_count = 0
        
        for func in functions:
            if hasattr(func, 'end_lineno') and func.end_lineno:
                func_length = func.end_lineno - func.lineno
                if func_length > 50:  # 50行以上を長い関数とする
                    long_count += 1
        
        return long_count
    
    def _count_exception_handling(self, tree: ast.AST) -> int:
        """例外処理のカウント"""
        return len([n for n in ast.walk(tree) if isinstance(n, ast.Try)])
    
    def _count_global_variables(self, tree: ast.AST) -> int:
        """グローバル変数のカウント"""
        return len([n for n in ast.walk(tree) if isinstance(n, ast.Global)])
    
    def _count_nested_loops(self, tree: ast.AST) -> int:
        """ネストしたループの最大深度"""
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            """count_depthメソッド"""
            nonlocal max_depth
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                count_depth(child, current_depth)
        
        count_depth(tree)
        return max_depth

        """過去のバグパターンとのマッチング"""
        # 簡単なパターンマッチング例
        pattern_score = 0.0
        
        # 一般的なバグパターン

            r'==\s*True',  # == True instead of is True
            r'==\s*False',  # == False instead of is False
            r'except:',  # bare except
            r'\.close\(\)',  # resource without try-finally
        ]

            matches = len(re.findall(pattern, code))
            pattern_score += matches * 0.05  # 各パターン5%のリスク
        
        return min(pattern_score, 0.3)  # 最大30%
    
    def _get_default_features(self) -> Dict[str, Any]:
        """デフォルト特徴量"""
        return {
            "lines_of_code": 0, "characters": 0, "functions": 0, "classes": 0,
            "cyclomatic_complexity": 1, "nesting_depth": 0, "conditional_statements": 0,
            "comments_ratio": 0, "docstring_ratio": 0, "magic_numbers": 0, "long_functions": 0,
            "exception_handling": 0, "global_variables": 0, "imports": 0,
            "loops": 0, "nested_loops": 0, "list_comprehensions": 0,
            "eval_usage": 0, "exec_usage": 0, "os_system_usage": 0, "subprocess_usage": 0,
        }
    
    # モデル初期化メソッド（将来の機械学習モデル用）

        """バグ予測モデル初期化"""
        return None  # 現在は重み付きスコアリング
    
    def _initialize_performance_model(self):
        """性能予測モデル初期化"""
        return None
    
    def _initialize_security_model(self):
        """セキュリティ予測モデル初期化"""
        return None
    
    def _load_historical_data(self) -> Dict[str, Any]:
        """履歴データ読み込み"""
        return {}  # 将来実装

        """バグパターン読み込み"""
        return []  # 将来実装
    
    def _load_performance_patterns(self) -> List[str]:
        """性能パターン読み込み"""
        return []
    
    def _load_security_patterns(self) -> List[str]:
        """セキュリティパターン読み込み"""
        return []
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """予測統計情報取得"""
        if not self.prediction_history:
            return {"message": "No prediction history available"}

        confidences = [p.confidence for p in self.prediction_history]
        
        return {
            "total_predictions": len(self.prediction_history),

            "average_confidence": statistics.mean(confidences),

        }

# 便利関数
def predict_quality(code: str, metadata: Optional[Dict] = None) -> PredictionResult:
    """品質予測の便利関数"""
    engine = PredictiveQualityEngine()
    return engine.predict_quality_issues(code, metadata)

if __name__ == "__main__":
    # 簡単なテスト実行
    sample_code = """
def risky_function(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if eval(f"data[{i}] > data[{j}]"):
                result.append(data[i])
    return result
"""
    
    engine = PredictiveQualityEngine()
    result = engine.predict_quality_issues(sample_code)

    print(f"Performance Risk: {result.performance_risk:0.2f}")
    print(f"Security Risk: {result.security_risk:0.2f}")
    print(f"Technical Debt: {result.technical_debt_score:0.2f}")
    print(f"Confidence: {result.confidence:0.2f}")
    print(f"Recommendations: {len(result.recommendations)}")