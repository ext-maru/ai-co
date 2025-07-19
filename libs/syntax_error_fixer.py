#!/usr/bin/env python3
"""
SyntaxError自動修正モジュール
安全性を考慮したPythonコード構文エラーの自動修正
"""

import ast
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager


class SyntaxErrorFixer(BaseManager):
    """SyntaxError自動修正クラス"""

    def __init__(self):
        super().__init__("SyntaxErrorFixer")

        # 安全に修正可能なSyntaxError パターン
        self.safe_patterns = {
            "missing_colon": {
                "regex": r"SyntaxError: invalid syntax.*line (\d+).*missing colon",
                "description": "欠落したコロンの修正",
                "auto_fix": True,
                "confidence": "high",
            },
            "missing_parenthesis": {
                "regex": r"SyntaxError: .*missing parenthes",
                "description": "欠落した括弧の修正",
                "auto_fix": True,
                "confidence": "high",
            },
            "missing_bracket": {
                "regex": r"SyntaxError: .*missing bracket",
                "description": "欠落した角括弧の修正",
                "auto_fix": True,
                "confidence": "high",
            },
            "missing_quote": {
                "regex": r"SyntaxError: .*unterminated string",
                "description": "欠落した引用符の修正",
                "auto_fix": True,
                "confidence": "medium",
            },
            "indentation_error": {
                "regex": r"IndentationError: .*",
                "description": "インデンテーションエラーの修正",
                "auto_fix": True,
                "confidence": "high",
            },
            "invalid_character": {
                "regex": r"SyntaxError: invalid character",
                "description": "無効な文字の修正",
                "auto_fix": True,
                "confidence": "medium",
            },
            "missing_comma": {
                "regex": r"SyntaxError: .*missing comma",
                "description": "欠落したカンマの修正",
                "auto_fix": True,
                "confidence": "high",
            },
        }

        # 修正不可能な危険なパターン
        self.unsafe_patterns = [
            "class definition",
            "function definition",
            "import statement",
            "lambda expression",
            "complex expression",
        ]

    def initialize(self) -> bool:
        """初期化処理"""
        return True

    def can_fix_syntax_error(self, error_text: str, code: Optional[str] = None) -> Dict:
        """SyntaxErrorが自動修正可能かを判定"""
        analysis = {
            "fixable": False,
            "pattern": None,
            "confidence": "none",
            "risk_level": "high",
            "description": "",
            "estimated_fixes": [],
        }

        try:
            # パターンマッチング
            for pattern_name, pattern_info in self.safe_patterns.items():
                if re.search(pattern_info["regex"], error_text, re.IGNORECASE):
                    analysis["fixable"] = pattern_info["auto_fix"]
                    analysis["pattern"] = pattern_name
                    analysis["confidence"] = pattern_info["confidence"]
                    analysis["description"] = pattern_info["description"]

                    # リスクレベルの評価
                    if pattern_info["confidence"] == "high":
                        analysis["risk_level"] = "low"
                    elif pattern_info["confidence"] == "medium":
                        analysis["risk_level"] = "medium"

                    # 具体的な修正候補を生成
                    if code:
                        fixes = self._generate_fix_candidates(
                            pattern_name, error_text, code
                        )
                        analysis["estimated_fixes"] = fixes

                    break

            # 危険なパターンのチェック
            if code:
                for unsafe_pattern in self.unsafe_patterns:
                    if unsafe_pattern.lower() in code.lower():
                        analysis["fixable"] = False
                        analysis["risk_level"] = "high"
                        analysis["description"] += f" (危険パターン検出: {unsafe_pattern})"
                        break

            self.logger.info(
                f"Syntax修正可能性分析: {analysis['pattern']} | "
                f"修正可能: {analysis['fixable']} | "
                f"信頼度: {analysis['confidence']}"
            )

            return analysis

        except Exception as e:
            self.handle_error(e, "Syntax修正可能性分析")
            return analysis

    def fix_syntax_error(
        self, error_text: str, code: str, context: Optional[Dict] = None
    ) -> Dict:
        """SyntaxErrorを自動修正"""
        result = {
            "success": False,
            "original_code": code,
            "fixed_code": None,
            "fixes_applied": [],
            "validation_passed": False,
            "backup_created": False,
            "error": None,
            "risk_assessment": {},
        }

        try:
            # 修正可能性の事前チェック
            analysis = self.can_fix_syntax_error(error_text, code)
            result["risk_assessment"] = analysis

            if not analysis["fixable"]:
                result["error"] = f"修正不可能なSyntaxError: {analysis['description']}"
                return result

            # バックアップ作成
            backup_code = code
            result["backup_created"] = True

            # パターン別修正実行
            pattern = analysis["pattern"]
            if pattern == "missing_colon":
                fixed_code = self._fix_missing_colon(code, error_text)
            elif pattern == "missing_parenthesis":
                fixed_code = self._fix_missing_parenthesis(code, error_text)
            elif pattern == "missing_bracket":
                fixed_code = self._fix_missing_bracket(code, error_text)
            elif pattern == "missing_quote":
                fixed_code = self._fix_missing_quote(code, error_text)
            elif pattern == "indentation_error":
                fixed_code = self._fix_indentation_error(code, error_text)
            elif pattern == "invalid_character":
                fixed_code = self._fix_invalid_character(code, error_text)
            elif pattern == "missing_comma":
                fixed_code = self._fix_missing_comma(code, error_text)
            else:
                result["error"] = f"未対応のパターン: {pattern}"
                return result

            if fixed_code and fixed_code != code:
                result["fixed_code"] = fixed_code
                result["fixes_applied"].append(pattern)

                # 修正コードの検証
                validation_result = self._validate_fixed_code(fixed_code)
                result["validation_passed"] = validation_result["valid"]

                if validation_result["valid"]:
                    result["success"] = True
                    self.logger.info(f"Syntax修正成功: {pattern}")
                else:
                    result["error"] = f"修正コード検証失敗: {validation_result['error']}"
                    result["fixed_code"] = backup_code  # ロールバック
                    self.logger.warning(f"Syntax修正検証失敗: {pattern}")
            else:
                result["error"] = "修正コードの生成に失敗"

        except Exception as e:
            result["error"] = str(e)
            self.handle_error(e, "Syntax修正実行")

        return result

    def _fix_missing_colon(self, code: str, error_text: str) -> str:
        """欠落したコロンの修正"""
        lines = code.split("\n")

        # エラー行番号を抽出
        line_match = re.search(r"line (\d+)", error_text)
        if line_match:
            error_line = int(line_match.group(1)) - 1
            if 0 <= error_line < len(lines):
                line = lines[error_line].rstrip()

                # if, elif, else, for, while, def, class文でコロンがない場合
                if re.match(
                    r"^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\b.*[^:]$",
                    line,
                ):
                    lines[error_line] = line + ":"
                    self.logger.info(f"コロン追加: 行{error_line + 1}")

        return "\n".join(lines)

    def _fix_missing_parenthesis(self, code: str, error_text: str) -> str:
        """欠落した括弧の修正"""
        lines = code.split("\n")

        # 簡単な括弧バランスチェックと修正
        for i, line in enumerate(lines):
            open_parens = line.count("(")
            close_parens = line.count(")")

            if open_parens > close_parens:
                # 行末に閉じ括弧を追加
                lines[i] = line.rstrip() + ")" * (open_parens - close_parens)
                self.logger.info(f"閉じ括弧追加: 行{i + 1}")
                break
            elif close_parens > open_parens:
                # 行頭に開き括弧を追加
                indent = len(line) - len(line.lstrip())
                lines[i] = (
                    " " * indent + "(" * (close_parens - open_parens) + line.lstrip()
                )
                self.logger.info(f"開き括弧追加: 行{i + 1}")
                break

        return "\n".join(lines)

    def _fix_missing_bracket(self, code: str, error_text: str) -> str:
        """欠落した角括弧の修正"""
        lines = code.split("\n")

        for i, line in enumerate(lines):
            open_brackets = line.count("[")
            close_brackets = line.count("]")

            if open_brackets > close_brackets:
                lines[i] = line.rstrip() + "]" * (open_brackets - close_brackets)
                self.logger.info(f"閉じ角括弧追加: 行{i + 1}")
                break
            elif close_brackets > open_brackets:
                indent = len(line) - len(line.lstrip())
                lines[i] = (
                    " " * indent
                    + "[" * (close_brackets - open_brackets)
                    + line.lstrip()
                )
                self.logger.info(f"開き角括弧追加: 行{i + 1}")
                break

        return "\n".join(lines)

    def _fix_missing_quote(self, code: str, error_text: str) -> str:
        """欠落した引用符の修正"""
        lines = code.split("\n")

        for i, line in enumerate(lines):
            # 単一引用符と二重引用符のバランスチェック
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\\"')

            if single_quotes % 2 == 1:  # 奇数個の単一引用符
                lines[i] = line.rstrip() + "'"
                self.logger.info(f"単一引用符追加: 行{i + 1}")
                break
            elif double_quotes % 2 == 1:  # 奇数個の二重引用符
                lines[i] = line.rstrip() + '"'
                self.logger.info(f"二重引用符追加: 行{i + 1}")
                break

        return "\n".join(lines)

    def _fix_indentation_error(self, code: str, error_text: str) -> str:
        """インデンテーションエラーの修正"""
        lines = code.split("\n")

        # 標準的な4スペースインデンテーションに統一
        fixed_lines = []
        current_indent_level = 0

        for line in lines:
            stripped = line.lstrip()
            if not stripped:  # 空行
                fixed_lines.append("")
                continue

            # インデントが必要な行を判定
            if stripped.startswith(
                (
                    "def ",
                    "class ",
                    "if ",
                    "elif ",
                    "else:",
                    "for ",
                    "while ",
                    "try:",
                    "except",
                    "finally:",
                    "with ",
                )
            ):
                fixed_line = "    " * current_indent_level + stripped
                fixed_lines.append(fixed_line)
                if stripped.endswith(":"):
                    current_indent_level += 1
            elif stripped in ("else:", "elif", "except:", "finally:"):
                current_indent_level = max(0, current_indent_level - 1)
                fixed_line = "    " * current_indent_level + stripped
                fixed_lines.append(fixed_line)
                current_indent_level += 1
            else:
                fixed_line = "    " * current_indent_level + stripped
                fixed_lines.append(fixed_line)

        self.logger.info("インデンテーション修正完了")
        return "\n".join(fixed_lines)

    def _fix_invalid_character(self, code: str, error_text: str) -> str:
        """無効な文字の修正"""
        # 一般的な無効文字の置換
        replacements = {
            '"': '"',  # 全角引用符
            '"': '"',
            """: "'",  # 全角アポストロフィ
            """: "'",
            "（": "(",  # 全角括弧
            "）": ")",
            "［": "[",
            "］": "]",
            "｛": "{",
            "｝": "}",
            "，": ",",  # 全角カンマ
            "；": ";",  # 全角セミコロン
            "：": ":",  # 全角コロン
        }

        fixed_code = code
        for invalid_char, valid_char in replacements.items():
            if invalid_char in fixed_code:
                fixed_code = fixed_code.replace(invalid_char, valid_char)
                self.logger.info(f"無効文字修正: '{invalid_char}' → '{valid_char}'")

        return fixed_code

    def _fix_missing_comma(self, code: str, error_text: str) -> str:
        """欠落したカンマの修正"""
        lines = code.split("\n")

        # リストや辞書、関数引数でのカンマ不足を検出・修正
        for i, line in enumerate(lines):
            # 単純なパターン: 数値や文字列が連続している場合
            if re.search(r'["\'\d]\s+["\'\d]', line):
                # スペースをカンマに置換
                fixed_line = re.sub(r'(["\'\d])\s+(["\'\d])', r"\1, \2", line)
                if fixed_line != line:
                    lines[i] = fixed_line
                    self.logger.info(f"カンマ追加: 行{i + 1}")
                    break

        return "\n".join(lines)

    def _validate_fixed_code(self, code: str) -> Dict:
        """修正されたコードの構文検証"""
        try:
            # ASTを使った構文チェック
            ast.parse(code)
            return {"valid": True, "error": None}

        except SyntaxError as e:
            return {"valid": False, "error": f"SyntaxError: {e}"}
        except Exception as e:
            return {"valid": False, "error": f"ValidationError: {e}"}

    def _generate_fix_candidates(
        self, pattern: str, error_text: str, code: str
    ) -> List[Dict]:
        """修正候補の生成"""
        candidates = []

        if pattern == "missing_colon":
            candidates.append(
                {
                    "description": "if/for/while/def文の末尾にコロンを追加",
                    "confidence": 0.9,
                    "estimated_change": "1行の修正",
                }
            )
        elif pattern == "missing_parenthesis":
            candidates.append(
                {
                    "description": "括弧のバランスを修正",
                    "confidence": 0.8,
                    "estimated_change": "括弧の追加",
                }
            )
        elif pattern == "indentation_error":
            candidates.append(
                {
                    "description": "インデンテーションを4スペースに統一",
                    "confidence": 0.85,
                    "estimated_change": "インデント修正",
                }
            )

        return candidates

    def get_syntax_fix_statistics(self) -> Dict:
        """Syntax修正統計の取得"""
        # 実装では実際の修正履歴を管理
        return {
            "total_attempts": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
            "by_pattern": {},
            "safety_record": {"no_data_loss": True, "rollback_count": 0},
        }


if __name__ == "__main__":
    # テスト実行
    fixer = SyntaxErrorFixer()

    print("=== SyntaxErrorFixer Test ===")

    # テストケース1: コロン不足
    test_code1 = """
if x > 5
    print("大きい")
"""

    error1 = "SyntaxError: invalid syntax at line 2, missing colon"
    result1 = fixer.fix_syntax_error(error1, test_code1.strip())
    print(f"テスト1結果: {result1['success']}")
    if result1["success"]:
        print(f"修正コード:\n{result1['fixed_code']}")

    # テストケース2: 括弧不足
    test_code2 = """
print("Hello World"
"""

    error2 = "SyntaxError: missing parenthesis"
    result2 = fixer.fix_syntax_error(error2, test_code2.strip())
    print(f"\nテスト2結果: {result2['success']}")
    if result2["success"]:
        print(f"修正コード:\n{result2['fixed_code']}")

    print("\n=== Statistics ===")
    stats = fixer.get_syntax_fix_statistics()
    print(f"統計: {stats}")
