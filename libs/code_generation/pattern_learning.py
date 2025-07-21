#!/usr/bin/env python3
"""
パターン学習エンジン
Issue #184 Phase 3: 学習したパターンでコード生成を強化
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Counter
from collections import defaultdict, Counter
import logging
from .codebase_analyzer import CodebaseAnalyzer

logger = logging.getLogger(__name__)


class PatternLearningEngine:
    """パターンの学習と蓄積システム"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        パターン学習エンジンの初期化
        
        Args:
            storage_dir: 学習済みパターンの保存ディレクトリ
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent / "learned_patterns"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.learned_patterns = {
            "coding_style": {},
            "import_patterns": {},
            "error_handling": {},
            "logging_patterns": {},
            "test_patterns": {},
            "naming_conventions": {},
            "project_vocabulary": {}
        }
        
        # 学習済みパターンをロード
        self._load_existing_patterns()
    
    async def learn_from_codebase(self, project_root: Optional[Path] = None) -> Dict[str, Any]:
        """
        コードベース全体から学習
        
        Args:
            project_root: プロジェクトルート
            
        Returns:
            学習結果
        """
        logger.info("Starting pattern learning from codebase...")
        
        # コードベース分析
        analyzer = CodebaseAnalyzer(project_root)
        analysis_result = await analyzer.analyze_codebase()
        
        # パターン学習を実行
        patterns = analysis_result.get("patterns", {})
        categorized_files = analysis_result.get("categorized_files", {})
        
        # 各種パターンを学習
        await self._learn_coding_style(patterns)
        await self._learn_import_patterns(patterns)
        await self._learn_error_handling(patterns)
        await self._learn_logging_patterns(patterns)
        await self._learn_test_patterns(categorized_files.get("tests", []))
        await self._learn_naming_conventions(patterns)
        await self._build_project_vocabulary(patterns)
        
        # 学習結果を保存
        await self._save_patterns()
        
        learning_summary = {
            "patterns_learned": {
                "coding_style_rules": len(self.learned_patterns["coding_style"]),
                "common_imports": len(self.learned_patterns["import_patterns"]),
                "error_patterns": len(self.learned_patterns["error_handling"]),
                "logging_patterns": len(self.learned_patterns["logging_patterns"]),
                "naming_rules": len(self.learned_patterns["naming_conventions"]),
                "vocabulary_size": len(self.learned_patterns["project_vocabulary"])
            },
            "source_analysis": analysis_result["analysis_metadata"],
            "confidence_score": self._calculate_confidence_score()
        }
        
        logger.info(f"Pattern learning completed: {learning_summary}")
        return learning_summary
    
    async def _learn_coding_style(self, patterns: Dict[str, Any]):
        """コーディングスタイルを学習"""
        style_data = patterns.get("coding_style", {})
        
        if not style_data:
            return
        
        # 統計的に最も一般的なスタイルを決定
        style_stats = defaultdict(list)
        
        for key, values in style_data.items():
            if isinstance(values, list):
                style_stats[key] = values
        
        learned_style = {}
        
        # インデントスタイル
        if "indentation_style" in style_stats:
            indent_counter = Counter(style_stats["indentation_style"])
            most_common_indent = indent_counter.most_common(1)
            if most_common_indent:
                learned_style["indentation"] = most_common_indent[0][0]
        
        # 行長
        if "max_line_length" in style_stats:
            lengths = [l for l in style_stats["max_line_length"] if l < 200]  # 異常値除去
            if lengths:
                learned_style["recommended_line_length"] = int(sum(lengths) / len(lengths))
        
        # ドキュメント頻度
        if "has_docstrings" in style_stats:
            docstring_ratio = sum(style_stats["has_docstrings"]) / len(style_stats["has_docstrings"])
            learned_style["docstring_usage"] = "high" if docstring_ratio > 0.7 else "medium" if docstring_ratio > 0.3 else "low"
        
        self.learned_patterns["coding_style"] = learned_style
        logger.info(f"Learned coding style: {learned_style}")
    
    async def _learn_import_patterns(self, patterns: Dict[str, Any]):
        """インポートパターンを学習"""
        imports = patterns.get("imports", [])
        
        if not imports:
            return
        
        # インポートの頻度カウント
        import_counter = Counter(imports)
        
        # 一般的なインポートパターンを抽出
        common_imports = import_counter.most_common(20)
        
        # カテゴリ別に分類
        categorized_imports = {
            "standard_library": [],
            "third_party": [],
            "local_imports": [],
            "typing_imports": [],
            "logging_imports": []
        }
        
        for import_stmt, count in common_imports:
            if "from typing import" in import_stmt or "import typing" in import_stmt:
                categorized_imports["typing_imports"].append(import_stmt)
            elif "import logging" in import_stmt or "from logging" in import_stmt:
                categorized_imports["logging_imports"].append(import_stmt)
            elif import_stmt.startswith("from libs.") or import_stmt.startswith("from workers."):
                categorized_imports["local_imports"].append(import_stmt)
            elif any(lib in import_stmt for lib in ["os", "sys", "json", "re", "pathlib", "datetime"]):
                categorized_imports["standard_library"].append(import_stmt)
            else:
                categorized_imports["third_party"].append(import_stmt)
        
        self.learned_patterns["import_patterns"] = categorized_imports
        logger.info(f"Learned {len(common_imports)} import patterns")
    
    async def _learn_error_handling(self, patterns: Dict[str, Any]):
        """エラーハンドリングパターンを学習"""
        errors = patterns.get("error_handling", [])
        
        if not errors:
            return
        
        error_counter = Counter(errors)
        common_exceptions = error_counter.most_common(10)
        
        # エラーハンドリングのベストプラクティス
        error_patterns = {
            "common_exceptions": [exc for exc, count in common_exceptions],
            "specific_vs_general": {
                "specific_count": sum(1 for exc, _ in common_exceptions if exc != "Exception"),
                "general_count": error_counter.get("Exception", 0)
            },
            "recommended_pattern": "specific_exceptions" if error_counter.get("Exception", 0) < len(errors) / 2 else "general_exceptions"
        }
        
        self.learned_patterns["error_handling"] = error_patterns
        logger.info(f"Learned error handling patterns: {len(common_exceptions)} exception types")
    
    async def _learn_logging_patterns(self, patterns: Dict[str, Any]):
        """ロギングパターンを学習"""
        logging_methods = patterns.get("logging_patterns", [])
        
        if not logging_methods:
            return
        
        method_counter = Counter(logging_methods)
        
        # 一般的なロギングレベル
        common_levels = method_counter.most_common(5)
        
        logging_patterns = {
            "common_levels": [level for level, count in common_levels],
            "preferred_style": "logger" if any("logger" in imp for imp in patterns.get("imports", [])) else "logging",
            "usage_frequency": len(logging_methods)
        }
        
        self.learned_patterns["logging_patterns"] = logging_patterns
        logger.info(f"Learned logging patterns: {common_levels}")
    
    async def _learn_test_patterns(self, test_files: List[str]):
        """テストパターンを学習"""
        if not test_files:
            self.learned_patterns["test_patterns"] = {
                "framework": "pytest",  # デフォルト
                "naming_convention": "test_*",
                "common_assertions": [],
                "mocking_style": "unittest.mock"
            }
            return
        
        # テストファイルを分析（簡易版）
        test_patterns = {
            "framework": "pytest",  # 多くのプロジェクトで使用
            "naming_convention": "test_*",
            "common_assertions": ["assert", "pytest.raises"],
            "mocking_style": "unittest.mock"
        }
        
        self.learned_patterns["test_patterns"] = test_patterns
        logger.info(f"Learned test patterns from {len(test_files)} test files")
    
    async def _learn_naming_conventions(self, patterns: Dict[str, Any]):
        """命名規則を学習"""
        classes = patterns.get("classes", [])
        functions = patterns.get("functions", [])
        
        naming_rules = {
            "class_naming": "PascalCase",  # 一般的なPython慣習
            "function_naming": "snake_case",
            "constants_naming": "UPPER_CASE",
            "private_prefix": "_",
            "dunder_methods": "__"
        }
        
        # 実際のパターンから検証
        if classes:
            class_names = [c["name"] for c in classes]
            pascal_case_count = sum(1 for name in class_names if name[0].isupper() and "_" not in name)
            if pascal_case_count / len(class_names) > 0.8:
                naming_rules["class_naming"] = "PascalCase"
        
        if functions:
            func_names = [f["name"] for f in functions if not f["name"].startswith("_")]
            snake_case_count = sum(1 for name in func_names if "_" in name or name.islower())
            if snake_case_count / len(func_names) > 0.8:
                naming_rules["function_naming"] = "snake_case"
        
        self.learned_patterns["naming_conventions"] = naming_rules
        logger.info(f"Learned naming conventions: {naming_rules}")
    
    async def _build_project_vocabulary(self, patterns: Dict[str, Any]):
        """プロジェクト固有の語彙を構築"""
        vocabulary = Counter()
        
        # クラス名から語彙抽出
        classes = patterns.get("classes", [])
        for class_info in classes:
            words = self._extract_words_from_name(class_info["name"])
            vocabulary.update(words)
        
        # 関数名から語彙抽出
        functions = patterns.get("functions", [])
        for func_info in functions:
            words = self._extract_words_from_name(func_info["name"])
            vocabulary.update(words)
        
        # ドキュメントから語彙抽出
        docstrings = patterns.get("docstrings", [])
        for doc in docstrings:
            words = self._extract_words_from_text(doc)
            vocabulary.update(words)
        
        # 頻出語彙を保存（上位100語）
        top_vocabulary = dict(vocabulary.most_common(100))
        self.learned_patterns["project_vocabulary"] = top_vocabulary
        
        logger.info(f"Built project vocabulary: {len(top_vocabulary)} words")
    
    def _extract_words_from_name(self, name: str) -> List[str]:
        """名前から単語を抽出（camelCase, snake_case対応）"""
        # snake_case を分割
        words = name.split('_')
        
        # camelCase を分割
        camel_words = []
        for word in words:
            camel_split = re.findall(r'[A-Z][a-z]*|[a-z]+', word)
            camel_words.extend(camel_split)
        
        # 小文字化して返す
        return [w.lower() for w in camel_words if len(w) > 2]
    
    def _extract_words_from_text(self, text: str) -> List[str]:
        """テキストから意味のある単語を抽出"""
        # 英単語のみ抽出
        words = re.findall(r'[a-zA-Z]{3,}', text.lower())
        
        # 一般的な単語を除外
        stop_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "her", "was", "one", "our", "had", "but", "what", "use", "your", "how", "now", "may", "say", "each", "new", "has", "two"}
        
        return [w for w in words if w not in stop_words and len(w) > 3]
    
    def _calculate_confidence_score(self) -> float:
        """学習結果の信頼度スコアを計算"""
        score = 0.0
        max_score = 6.0
        
        # 各パターンカテゴリの充実度をチェック
        if self.learned_patterns["coding_style"]:
            score += 1.0
        
        if len(self.learned_patterns["import_patterns"].get("standard_library", [])) > 3:
            score += 1.0
        
        if self.learned_patterns["error_handling"].get("common_exceptions", []):
            score += 1.0
        
        if self.learned_patterns["logging_patterns"].get("common_levels", []):
            score += 1.0
        
        if self.learned_patterns["naming_conventions"]:
            score += 1.0
        
        if len(self.learned_patterns["project_vocabulary"]) > 50:
            score += 1.0
        
        return score / max_score
    
    def _load_existing_patterns(self):
        """既存の学習済みパターンをロード"""
        for pattern_type in self.learned_patterns.keys():
            pattern_file = self.storage_dir / f"{pattern_type}.json"
            if pattern_file.exists():
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        self.learned_patterns[pattern_type] = json.load(f)
                    logger.info(f"Loaded existing patterns: {pattern_type}")
                except Exception as e:
                    logger.warning(f"Failed to load {pattern_type}: {e}")
    
    async def _save_patterns(self):
        """学習済みパターンを保存"""
        for pattern_type, patterns in self.learned_patterns.items():
            pattern_file = self.storage_dir / f"{pattern_type}.json"
            try:
                with open(pattern_file, 'w', encoding='utf-8') as f:
                    json.dump(patterns, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved patterns: {pattern_type}")
            except Exception as e:
                logger.error(f"Failed to save {pattern_type}: {e}")
    
    def get_patterns_for_context(self, context_type: str = "general") -> Dict[str, Any]:
        """
        コンテキスト強化用のパターンを取得
        
        Args:
            context_type: コンテキストタイプ（general, test, api等）
            
        Returns:
            適用すべきパターン
        """
        applicable_patterns = {
            "imports": [],
            "style_preferences": {},
            "error_handling": {},
            "logging": {},
            "naming": {},
            "vocabulary": []
        }
        
        # 基本インポート
        import_patterns = self.learned_patterns.get("import_patterns", {})
        applicable_patterns["imports"].extend(import_patterns.get("standard_library", []))
        applicable_patterns["imports"].extend(import_patterns.get("typing_imports", []))
        applicable_patterns["imports"].extend(import_patterns.get("logging_imports", []))
        
        # スタイル設定
        applicable_patterns["style_preferences"] = self.learned_patterns.get("coding_style", {})
        
        # エラーハンドリング
        applicable_patterns["error_handling"] = self.learned_patterns.get("error_handling", {})
        
        # ロギング
        applicable_patterns["logging"] = self.learned_patterns.get("logging_patterns", {})
        
        # 命名規則
        applicable_patterns["naming"] = self.learned_patterns.get("naming_conventions", {})
        
        # プロジェクト語彙（上位20語）
        vocabulary = self.learned_patterns.get("project_vocabulary", {})
        top_words = sorted(vocabulary.items(), key=lambda x: x[1], reverse=True)[:20]
        applicable_patterns["vocabulary"] = [word for word, count in top_words]
        
        return applicable_patterns


# CLI実行用
async def main():
    """メイン関数（テスト用）"""
    engine = PatternLearningEngine()
    
    print("🧠 Starting pattern learning...")
    result = await engine.learn_from_codebase()
    
    print(f"\n📊 Learning Results:")
    print(f"Patterns learned: {result['patterns_learned']}")
    print(f"Confidence score: {result['confidence_score']:.2f}")
    
    # パターン例を表示
    patterns = engine.get_patterns_for_context()
    print(f"\n📋 Sample Patterns:")
    print(f"Common imports: {patterns['imports'][:3]}")
    print(f"Coding style: {patterns['style_preferences']}")
    print(f"Project vocabulary: {patterns['vocabulary'][:10]}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())