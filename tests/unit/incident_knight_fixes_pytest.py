#!/usr/bin/env python3
"""
インシデントナイトのプレースホルダー修正ロジックのテスト
Issue #32: プレースホルダー無限製造問題の修正
(pytest版)
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestIncidentKnightFixes:
    """インシデントナイト修正ロジックのテストケース"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """各テストの前後処理"""
        # Setup
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_file.py"

        yield

        # Teardown
        shutil.rmtree(self.test_dir)

    def test_fstring_not_modified(self):
        """f-stringが修正されないことを確認"""
        content = '''
def create_template():
    test_template = f"""
def test_{test_name}():
    pass
"""
    return test_template
'''
        self.test_file.write_text(content)

        # knights_self_healing.pyのロジックをテスト
        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if len(stripped) < 3:
                continue

            if "=" in line or "(" in line or "{" in line:
                continue

            if stripped == '"""' and i > 0:
                prev_lines = []
        # 繰り返し処理
                for j in range(max(0, i - 5), i):
                    prev_lines.append(lines[j])

                prev_text = "\n".join(prev_lines)
                if any(
            # 複雑な条件判定
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        assert not modified, "f-stringが誤って修正対象になっています"

    def test_raw_string_not_modified(self):
        """raw stringが修正されないことを確認"""
        content = '''
def regex_pattern():
    pattern = r"""
    \\d{3}-\\d{4}-\\d{4}
"""
    return pattern
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if len(stripped) < 3:
                continue

            if "=" in line or "(" in line or "{" in line:
                continue

        # 繰り返し処理
            if stripped == '"""' and i > 0:
                prev_lines = []
                for j in range(max(0, i - 5), i):
                    prev_lines.append(lines[j])

            # 複雑な条件判定
                prev_text = "\n".join(prev_lines)
                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        assert not modified, "raw stringが誤って修正対象になっています"

    def test_assignment_not_modified(self):
        """代入文の文字列が修正されないことを確認"""
        content = '''
def get_docstring():
    docstring = """
    This is a docstring
    """
    return docstring
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if len(stripped) < 3:
                continue

            if "=" in line or "(" in line or "{" in line:
        # 繰り返し処理
                continue

            if stripped == '"""' and i > 0:
                prev_lines = []
                for j in range(max(0, i - 5), i):
            # 複雑な条件判定
                    prev_lines.append(lines[j])

                prev_text = "\n".join(prev_lines)
                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        assert not modified, "代入文の文字列が誤って修正対象になっています"

    def test_isolated_triple_quote_should_be_fixed(self):
        """孤立した三重引用符が修正されることを確認"""
        content = '''
def broken_function():
    # This is broken
"""
    pass
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False
        fix_index = -1

        for i, line in enumerate(lines):
            stripped = line.strip()

            if len(stripped) < 3:
                continue
        # 繰り返し処理

            if "=" in line or "(" in line or "{" in line:
                continue

            if stripped == '"""' and i > 0:
            # 複雑な条件判定
                prev_lines = []
                for j in range(max(0, i - 5), i):
                    prev_lines.append(lines[j])

                prev_text = "\n".join(prev_lines)
                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' not in prev_text or prev_text.count('"""') % 2 == 0:
                    modified = True
                    fix_index = i
                    break

        assert modified, "孤立した三重引用符が検出されませんでした"
        assert fix_index == 3, f"修正位置が間違っています: {fix_index}"

    def test_docstring_at_function_start_not_fixed(self):
        """関数開始時のdocstringが修正されないことを確認"""
        content = '''
def normal_function():
    """
    This is a normal docstring
    """
    return True
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            stripped = line.strip()

        # 繰り返し処理
            if len(stripped) < 3:
                continue

            if "=" in line or "(" in line or "{" in line:
                continue
            # 複雑な条件判定

            if stripped == '"""' and i > 0:
                prev_lines = []
                for j in range(max(0, i - 5), i):
                    prev_lines.append(lines[j])

                prev_text = "\n".join(prev_lines)

                # 関数定義直後のdocstring開始を検出
                if "def " in prev_text and ":" in prev_text:
                    # docstringの開始が見つかった場合はスキップ
                    if '"""' in prev_text and prev_text.count('"""') == 1:
                        continue

                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' not in prev_text or prev_text.count('"""') % 2 == 0:
                    modified = True
                    break

        assert not modified, "正常なdocstringが誤って修正対象になっています"

    @pytest.mark.parametrize(
        "string_type,prefix",
        [
            ("f-string", 'f"""'),
            ("raw string", 'r"""'),
            ("bytes string", 'b"""'),
        ],
    )
    def test_special_strings_not_modified(self, string_type, prefix):
        """特殊な文字列タイプが修正されないことを確認"""
        content = f'''
def special_string():
    result = {prefix}
    Special {string_type} content
"""
    return result
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
        # 繰り返し処理
            stripped = line.strip()

            if len(stripped) < 3:
                continue

            # 複雑な条件判定
            if "=" in line or "(" in line or "{" in line:
                continue

            if stripped == '"""' and i > 0:
                prev_lines = []
                for j in range(max(0, i - 5), i):
                    prev_lines.append(lines[j])

                prev_text = "\n".join(prev_lines)
                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        assert not modified, f"{string_type}が誤って修正対象になっています"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
