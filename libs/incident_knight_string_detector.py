"""
インシデント騎士団の改良版文字列検出ロジック

Issue #32対応: f-string、raw string等の誤認識を防ぐ正確な文字列検出
"""

import ast
import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class StringContext:
    """文字列のコンテキスト情報"""

    def __init__(self, line: str, line_number: int, surrounding_lines: List[str]):
        self.line = line
        self.line_number = line_number
        self.surrounding_lines = surrounding_lines
        self.stripped = line.strip()

    def is_fstring(self) -> bool:
        """f-stringパターンかチェック"""
        # f"..." または f'...' パターン
        patterns = [
            r'f"[^"]*"""',  # f"text"""
            r"f'[^']*'''",  # f'text'''
        ]

        for pattern in patterns:
            if re.search(pattern, self.line):
                return True

        # 複数行f-string
        if 'f"""' in self.line or "f'''" in self.line:
            return True

        return False

    def is_raw_string(self) -> bool:
        """raw stringパターンかチェック"""
        patterns = [
            r'r"[^"]*"""',  # r"text"""
            r"r'[^']*'''",  # r'text'''
        ]

        for pattern in patterns:
            if re.search(pattern, self.line):
                return True

        # 複数行raw string
        if 'r"""' in self.line or "r'''" in self.line:
            return True

        return False

    def is_byte_string(self) -> bool:
        """byte stringパターンかチェック"""
        patterns = [
            r'b"[^"]*"""',  # b"text"""
            r"b'[^']*'''",  # b'text'''
        ]

        for pattern in patterns:
            if re.search(pattern, self.line):
                return True

        # 複数行byte string
        if 'b"""' in self.line or "b'''" in self.line:
            return True

        return False

    def is_assignment_or_expression(self) -> bool:
        """変数代入や式の一部かチェック"""
        # docstringが開始されていれば、内容に他の文字が含まれていても良い
        if self.stripped.startswith('"""') or self.stripped.startswith("'''"):
            return False

        # 代入、return、yield、関数呼び出し等
        patterns = ["=", "return", "yield", "(", "{", "["]
        return any(pattern in self.line for pattern in patterns)

    def has_previous_unclosed_docstring(self) -> bool:
        """前の行に未完了のdocstringがあるかチェック"""
        # 現在の行が単独のdocstringかチェック
        if not self.is_standalone_closing_quotes():
            return False

        # 前の数行を確認
        prev_lines = []
        current_index = -1

        # 現在の行のインデックスを特定
        for i, line in enumerate(self.surrounding_lines):
            if line.strip() == self.stripped:
                current_index = i
                break

        if current_index <= 0:
            # 単一行の場合、未完了docstringの開始として扱う
            if self.stripped.startswith('"""') and not self.stripped.endswith('"""'):
                return True
            return False

        # 前の行を遡って確認
        for i in range(max(0, current_index - 10), current_index):
            prev_lines.append(self.surrounding_lines[i])

        prev_text = "\n".join(prev_lines)

        # f-string、raw string、byte string等の特殊パターンを除外
        if any(pattern in prev_text for pattern in ['f"""', 'r"""', 'b"""']):
            return False

        # 変数代入等を除外
        if any(pattern in prev_text for pattern in ["=", "return", "yield"]):
            return False

        # docstringの開始（"""）の数をカウント
        triple_quote_count = prev_text.count('"""')

        # 奇数個の場合は未完了のdocstring
        return triple_quote_count % 2 == 1

    def is_standalone_closing_quotes(self) -> bool:
        """単独の閉じクォートかチェック"""
        return self.stripped == '"""' or self.stripped == "'''"


class ImprovedStringDetector:
    """改良版文字列検出クラス"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def should_fix_docstring(
        self, line: str, surrounding_lines: List[str], line_number: int = 0
    ) -> bool:
        """
        docstringを修正すべきかどうかを判定

        Args:
            line: 対象の行
            surrounding_lines: 前後の行を含むコンテキスト
            line_number: 行番号

        Returns:
            修正すべきならTrue
        """
        # 基本チェック: """を含む行
        if '"""' not in line:
            return False

        context = StringContext(line, line_number, surrounding_lines)

        # f-stringパターンを除外
        if context.is_fstring():
            self.logger.debug(f"Skipping f-string: {line}")
            return False

        # raw stringパターンを除外
        if context.is_raw_string():
            self.logger.debug(f"Skipping raw string: {line}")
            return False

        # byte stringパターンを除外
        if context.is_byte_string():
            self.logger.debug(f"Skipping byte string: {line}")
            return False

        # 変数代入や式の一部を除外
        if context.is_assignment_or_expression():
            self.logger.debug(f"Skipping assignment/expression: {line}")
            return False

        # 単独行での未完了docstring検出
        stripped = line.strip()
        if len(surrounding_lines) == 1:
            # 単独行の場合、未完了docstringのパターンを検出
            if (stripped.startswith('"""') and not stripped.endswith('"""')) or (
                stripped.startswith("'''") and not stripped.endswith("'''")
            ):
                return True
            # 閉じクォートのみの場合も未完了として扱う
            if stripped in ['"""', "'''"]:
                return True
            # """で終わるが開始がない場合（典型的な未完了パターン）
            if (
                stripped.endswith('"""')
                and stripped.count('"""') == 1
                and not stripped.startswith('"""')
            ):
                return True

        # 複数行コンテキストでの判定
        if context.is_standalone_closing_quotes():
            # 前に未完了のdocstringがあるかチェック
            if context.has_previous_unclosed_docstring():
                self.logger.debug(f"Found incomplete docstring: {line}")
                return True

        return False

    def detect_incomplete_docstrings_in_file(
        self, content: str
    ) -> List[Tuple[int, str]]:
        """
        ファイル全体から未完了docstringを検出

        Args:
            content: ファイル内容

        Returns:
            (行番号, 行内容) のタプルリスト
        """
        lines = content.split("\n")
        incomplete_docstrings = []

        for i, line in enumerate(lines):
            if self.should_fix_docstring(line, lines, i):
                incomplete_docstrings.append((i, line))

        return incomplete_docstrings

    def fix_line(
        self, line: str, surrounding_lines: List[str], line_number: int = 0
    ) -> str:
        """
        行を修正する

        Args:
            line: 対象の行
            surrounding_lines: 前後の行を含むコンテキスト
            line_number: 行番号

        Returns:
            修正後の行
        """
        # 既に修正済みかチェック
        if "pass  # Placeholder for implementation" in line:
            return line

        if self.should_fix_docstring(line, surrounding_lines, line_number):
            return line + "\n    pass  # Placeholder for implementation"
        return line

    def fix_file_content(self, content: str) -> Tuple[str, List[str]]:
        """
        ファイル内容を修正する

        Args:
            content: ファイル内容

        Returns:
            (修正後内容, 修正箇所のリスト)
        """
        lines = content.split("\n")
        modified_lines = []
        fixes_applied = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 既に修正済みかチェック（冪等性確保）
            if (
                i + 1 < len(lines)
                and "pass  # Placeholder for implementation" in lines[i + 1]
            ):
                # 既に修正済みの行をそのまま保持
                modified_lines.append(line)
                i += 1
                continue

            if self.should_fix_docstring(line, lines, i):
                # 未完了docstringを修正
                modified_lines.append(line)
                modified_lines.append("    pass  # Placeholder for implementation")
                fixes_applied.append(
                    f"Line {i+1}: Added placeholder for incomplete docstring"
                )
                self.logger.info(f"Fixed incomplete docstring at line {i+1}")
            else:
                modified_lines.append(line)

            i += 1

        return "\n".join(modified_lines), fixes_applied


def is_incomplete_docstring(line: str, surrounding_lines: List[str] = None) -> bool:
    """
    エントリーポイント関数: 未完了docstringかどうかを判定

    Args:
        line: 対象の行
        surrounding_lines: 前後の行を含むコンテキスト（オプション）

    Returns:
        未完了docstringならTrue
    """
    if surrounding_lines is None:
        surrounding_lines = [line]

    detector = ImprovedStringDetector()
    return detector.should_fix_docstring(line, surrounding_lines)


# 後方互換性のための関数
def should_add_placeholder(line: str, context_lines: List[str] = None) -> bool:
    """後方互換性のための関数"""
    return is_incomplete_docstring(line, context_lines)
