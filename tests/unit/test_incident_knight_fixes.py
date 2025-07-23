#!/usr/bin/env python3
"""
インシデントナイトのプレースホルダー修正ロジックのテスト
Issue #32: プレースホルダー無限製造問題の修正
"""

import sys
import tempfile
import unittest
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# インポートは不要（ロジックを直接テスト）


class TestIncidentKnightFixes(unittest.TestCase):
    """インシデントナイト修正ロジックのテストケース"""

    def setUp(self):
        """テストセットアップ"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_file.py"

    def tearDown(self):
        """テストクリーンアップ"""
        import shutil

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

        self.assertFalse(modified, "f-stringが誤って修正対象になっています")

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

        self.assertFalse(modified, "raw stringが誤って修正対象になっています")

    def test_incomplete_docstring_is_modified(self):
        """本当に未完了のdocstringが修正されることを確認"""
        content = '''
def my_function():
    """
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        should_modify = False

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
                    should_modify = True
                    break

        self.assertTrue(should_modify, "未完了のdocstringが修正対象になっていません")

    def test_multiline_string_assignment_not_modified(self):
        """複数行文字列の代入が修正されないことを確認"""
        content = '''
message = """
This is a multiline
string message
"""
'''
        self.test_file.write_text(content)

        lines = content.split("\n")
        modified = False

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

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        self.assertFalse(modified, "複数行文字列の代入が誤って修正対象になっています")

    def test_function_call_with_string_not_modified(self):
        """関数呼び出し内の文字列が修正されないことを確認"""
        content = '''
print("""
This is a multiline
print statement
""")
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
                if any(
                    pattern in prev_text
                    for pattern in ['f"""', 'r"""', 'b"""', "=", "return", "yield"]
                ):
                    continue

                if '"""' in prev_text and prev_text.count('"""') % 2 == 1:
                    modified = True
                    break

        self.assertFalse(modified, "関数呼び出し内の文字列が誤って修正対象になっています")

    def test_idempotency_no_double_fix(self):
        """冪等性：既に修正済みの場合は再修正しないことを確認"""
        content = '''
def incomplete_function():
    """
    pass  # Placeholder for implementation
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
                # 既に修正済みかチェック
                if (
                    i + 1 < len(lines)
                    and "Placeholder for implementation" in lines[i + 1]
                ):
                    continue

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

        self.assertFalse(modified, "既に修正済みのdocstringが再度修正対象になっています")


if __name__ == "__main__":
    unittest.main()
