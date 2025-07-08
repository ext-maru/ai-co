#!/usr/bin/env python3
"""
Enhanced Error Classification System
242万件のOtherエラーを詳細分類し、自動修正機能を提供
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ErrorPattern:
    """エラーパターン定義"""
    category: str
    pattern: str
    description: str
    auto_fix: Optional[str] = None
    severity: str = "medium"
    priority: int = 3

@dataclass
class ClassifiedError:
    """分類されたエラー"""
    original_error: str
    category: str
    subcategory: str
    severity: str
    confidence: float
    auto_fix_suggestion: Optional[str] = None
    timestamp: str = None

class EnhancedErrorClassifier:
    """強化エラー分類システム"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.statistics = defaultdict(int)
        self.classified_cache = {}
        
    def _initialize_patterns(self) -> List[ErrorPattern]:
        """エラーパターンを初期化"""
        return [
            # システムエラー
            ErrorPattern(
                "system", 
                r"ModuleNotFoundError.*(?:No module named|cannot import)",
                "Pythonモジュールが見つからない",
                "pip install <module_name>",
                "high", 1
            ),
            ErrorPattern(
                "system",
                r"FileNotFoundError.*(?:No such file|cannot find)",
                "ファイルが見つからない",
                "ファイルパスの確認とファイル作成",
                "medium", 2
            ),
            ErrorPattern(
                "system",
                r"PermissionError.*(?:Permission denied|Access denied)",
                "権限エラー",
                "chmod +x または sudo で権限を変更",
                "high", 1
            ),
            
            # ネットワークエラー
            ErrorPattern(
                "network",
                r"ConnectionError.*(?:connection|refused|timeout)",
                "ネットワーク接続エラー",
                "ネットワーク設定とサービス状態を確認",
                "high", 1
            ),
            ErrorPattern(
                "network",
                r"TimeoutError.*(?:timeout|timed out)",
                "タイムアウトエラー",
                "タイムアウト値の調整とリトライ実装",
                "medium", 2
            ),
            
            # データベースエラー
            ErrorPattern(
                "database",
                r"(?:sqlite3|mysql|postgres).*(?:error|exception)",
                "データベースエラー",
                "データベース接続とクエリの確認",
                "high", 1
            ),
            ErrorPattern(
                "database",
                r"(?:IntegrityError|ConstraintError)",
                "データベース整合性エラー",
                "データ制約の確認と修正",
                "medium", 2
            ),
            
            # メモリエラー
            ErrorPattern(
                "memory",
                r"MemoryError.*(?:out of memory|memory)",
                "メモリ不足エラー",
                "メモリ使用量の最適化とガベージコレクション",
                "high", 1
            ),
            ErrorPattern(
                "memory",
                r"(?:heap|stack) overflow",
                "ヒープ/スタックオーバーフロー",
                "再帰制限の調整とアルゴリズム最適化",
                "high", 1
            ),
            
            # 設定エラー
            ErrorPattern(
                "config",
                r"(?:KeyError|AttributeError).*(?:config|setting)",
                "設定エラー",
                "設定ファイルとパラメータの確認",
                "medium", 2
            ),
            ErrorPattern(
                "config",
                r"(?:Invalid|Missing).*(?:configuration|config)",
                "設定不備エラー",
                "設定ファイルの修正と検証",
                "medium", 2
            ),
            
            # API・通信エラー
            ErrorPattern(
                "api",
                r"(?:HTTPError|RequestException|API.*error)",
                "API通信エラー",
                "APIキーとエンドポイントの確認",
                "medium", 2
            ),
            ErrorPattern(
                "api",
                r"(?:401|403|404|500).*(?:Unauthorized|Forbidden|Not Found|Internal Server Error)",
                "HTTP ステータスエラー",
                "認証情報とリクエスト内容の確認",
                "medium", 2
            ),
            
            # 並行処理エラー
            ErrorPattern(
                "concurrency",
                r"(?:DeadlockError|RaceCondition|ThreadError)",
                "並行処理エラー",
                "ロック機構とスレッド安全性の見直し",
                "high", 1
            ),
            
            # JSON/パースエラー
            ErrorPattern(
                "parsing",
                r"(?:JSONDecodeError|ParseError|SyntaxError).*(?:json|parse)",
                "データ解析エラー",
                "データフォーマットと構文の確認",
                "medium", 2
            ),
            
            # 型エラー
            ErrorPattern(
                "type",
                r"TypeError.*(?:unsupported|not supported|expected)",
                "型エラー",
                "データ型の確認と変換処理の追加",
                "low", 3
            ),
            
            # ワーカーエラー
            ErrorPattern(
                "worker",
                r"(?:worker|task).*(?:failed|error|exception)",
                "ワーカー・タスクエラー",
                "ワーカー設定とタスク処理の確認",
                "medium", 2
            ),
            
            # その他のシステムエラー
            ErrorPattern(
                "system",
                r"(?:OSError|SystemError|RuntimeError)",
                "システムランタイムエラー",
                "システム状態とリソースの確認",
                "medium", 2
            )
        ]
    
    def classify_error(self, error_message: str) -> ClassifiedError:
        """エラーメッセージを分類"""
        error_message = error_message.strip()
        
        # キャッシュチェック
        if error_message in self.classified_cache:
            return self.classified_cache[error_message]
        
        best_match = None
        best_confidence = 0.0
        
        # パターンマッチング
        for pattern in self.patterns:
            match = re.search(pattern.pattern, error_message, re.IGNORECASE)
            if match:
                # 信頼度計算（マッチした文字数の割合）
                confidence = len(match.group(0)) / len(error_message)
                confidence = min(confidence * 1.2, 1.0)  # ブースト適用
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = pattern
        
        # 分類結果作成
        if best_match:
            classified = ClassifiedError(
                original_error=error_message,
                category=best_match.category,
                subcategory=best_match.description,
                severity=best_match.severity,
                confidence=best_confidence,
                auto_fix_suggestion=best_match.auto_fix,
                timestamp=datetime.now().isoformat()
            )
        else:
            # 未分類の場合はOtherとして処理
            classified = ClassifiedError(
                original_error=error_message,
                category="other",
                subcategory="未分類エラー",
                severity="unknown",
                confidence=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        # 統計更新
        self.statistics[classified.category] += 1
        
        # キャッシュ保存
        self.classified_cache[error_message] = classified
        
        return classified
    
    def bulk_classify_errors(self, error_list: List[str]) -> List[ClassifiedError]:
        """エラーリストを一括分類"""
        results = []
        
        for error in error_list:
            classified = self.classify_error(error)
            results.append(classified)
        
        return results
    
    def analyze_log_file(self, log_file_path: str) -> Dict[str, any]:
        """ログファイルからエラーを抽出・分析"""
        log_path = Path(log_file_path)
        
        if not log_path.exists():
            return {"error": f"Log file not found: {log_file_path}"}
        
        errors = []
        error_patterns_found = Counter()
        
        try:
            with open(log_path, 'r', errors='ignore') as f:
                content = f.read()
                
                # エラーライン抽出
                error_lines = re.findall(r'ERROR.*?(?=\n|$)', content, re.MULTILINE)
                
                for error_line in error_lines:
                    classified = self.classify_error(error_line)
                    errors.append(classified)
                    error_patterns_found[classified.category] += 1
        
        except Exception as e:
            return {"error": f"Failed to analyze log file: {str(e)}"}
        
        # 統計情報生成
        analysis = {
            "file": str(log_path),
            "timestamp": datetime.now().isoformat(),
            "total_errors": len(errors),
            "categories": dict(error_patterns_found),
            "classified_errors": errors[:100],  # 最初の100件のみ保存
            "suggestions": self._generate_suggestions(error_patterns_found)
        }
        
        return analysis
    
    def _generate_suggestions(self, error_counts: Counter) -> List[str]:
        """エラー統計から改善提案を生成"""
        suggestions = []
        
        # 最多エラーカテゴリの対策
        if error_counts:
            top_category = error_counts.most_common(1)[0]
            category, count = top_category
            
            if category == "system":
                suggestions.append(f"システムエラーが{count}件発生。依存関係とファイルパスを確認してください。")
            elif category == "network":
                suggestions.append(f"ネットワークエラーが{count}件発生。接続設定とタイムアウト値を確認してください。")
            elif category == "database":
                suggestions.append(f"データベースエラーが{count}件発生。DB接続とクエリを確認してください。")
            elif category == "memory":
                suggestions.append(f"メモリエラーが{count}件発生。メモリ使用量の最適化を実施してください。")
            elif category == "api":
                suggestions.append(f"API通信エラーが{count}件発生。認証情報とエンドポイントを確認してください。")
            elif category == "worker":
                suggestions.append(f"ワーカーエラーが{count}件発生。ワーカー設定とタスク処理を確認してください。")
            else:
                suggestions.append(f"{category}カテゴリで{count}件のエラーが発生しています。")
        
        # 複数カテゴリがある場合
        if len(error_counts) > 3:
            suggestions.append("複数のエラーカテゴリが検出されました。包括的なシステム点検を推奨します。")
        
        return suggestions
    
    def get_statistics(self) -> Dict[str, any]:
        """分類統計を取得"""
        total_errors = sum(self.statistics.values())
        
        return {
            "total_classified": total_errors,
            "categories": dict(self.statistics),
            "cache_size": len(self.classified_cache),
            "timestamp": datetime.now().isoformat()
        }
    
    def export_results(self, output_path: str):
        """分類結果をエクスポート"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "patterns_used": len(self.patterns),
            "classified_errors": [
                {
                    "error": error,
                    "category": classified.category,
                    "subcategory": classified.subcategory,
                    "severity": classified.severity,
                    "confidence": classified.confidence,
                    "auto_fix": classified.auto_fix_suggestion
                }
                for error, classified in self.classified_cache.items()
            ]
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Classification results exported to {output_path}")

def main():
    """メイン実行関数 - デモとテスト"""
    classifier = EnhancedErrorClassifier()
    
    # テストエラーメッセージ
    test_errors = [
        "ModuleNotFoundError: No module named 'docker'",
        "FileNotFoundError: No such file or directory: '/tmp/test.txt'",
        "PermissionError: [Errno 13] Permission denied: '/etc/config'",
        "ConnectionError: Failed to establish connection to localhost:5432",
        "TimeoutError: Connection timed out after 30 seconds",
        "JSONDecodeError: Expecting ',' delimiter: line 1 column 45",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "MemoryError: Unable to allocate memory",
        "HTTPError: 404 Client Error: Not Found",
        "worker task failed with unknown error"
    ]
    
    print("🔍 Enhanced Error Classification System テスト")
    print("=" * 60)
    
    # エラー分類テスト
    for error in test_errors:
        classified = classifier.classify_error(error)
        print(f"\n📝 元エラー: {error[:50]}...")
        print(f"   カテゴリ: {classified.category}")
        print(f"   詳細: {classified.subcategory}")
        print(f"   重要度: {classified.severity}")
        print(f"   信頼度: {classified.confidence:.2f}")
        if classified.auto_fix_suggestion:
            print(f"   修正案: {classified.auto_fix_suggestion}")
    
    # 統計表示
    print(f"\n📊 分類統計:")
    stats = classifier.get_statistics()
    for category, count in stats["categories"].items():
        print(f"   {category}: {count}件")
    
    print(f"\n✅ Enhanced Error Classification System テスト完了")

if __name__ == "__main__":
    main()