#!/usr/bin/env python3
"""
Elder Flow Pre-commit Handler
pre-commitエラーを自動的に検出・修復する機能
"""

import subprocess
import re
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
from dataclasses import dataclass


@dataclass
class PreCommitError:
    """pre-commitエラー情報"""
    hook_id: str
    exit_code: int
    modified_files: List[str]
    error_message: str


class ElderFlowPreCommitHandler:
    """Elder Flow Pre-commit自動修復ハンドラー"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def handle_pre_commit_errors(self, stderr: str) -> Tuple[bool, List[PreCommitError], str]:
        """
        pre-commitエラーを解析して自動修復を試みる

        Returns:
            Tuple[修復成功フラグ, エラーリスト, 修復メッセージ]
        """
        errors = self._parse_pre_commit_output(stderr)

        if not errors:
            return True, [], "No pre-commit errors detected"

        self.logger.info(f"Detected {len(errors)} pre-commit errors")

        # エラータイプごとに処理
        fixed_all = True
        fix_messages = []

        for error in errors:
            if error.hook_id == "trailing-whitespace":
                fixed = self._fix_trailing_whitespace(error.modified_files)
                fix_messages.append(f"Fixed trailing whitespace in {len(error.modified_files)} files")
                fixed_all = fixed_all and fixed

            elif error.hook_id == "end-of-file-fixer":
                fixed = self._fix_end_of_file(error.modified_files)
                fix_messages.append(f"Fixed end of file in {len(error.modified_files)} files")
                fixed_all = fixed_all and fixed

            elif error.hook_id == "check-ast":
                fixed = self._fix_syntax_errors(error.modified_files)
                fix_messages.append(f"Attempted to fix syntax errors in {len(error.modified_files)} files")
                fixed_all = fixed_all and fixed

            else:
                self.logger.warning(f"Unknown pre-commit hook: {error.hook_id}")
                fixed_all = False

        return fixed_all, errors, "\n".join(fix_messages)

    def _parse_pre_commit_output(self, output: str) -> List[PreCommitError]:
        """pre-commit出力を解析してエラー情報を抽出"""
        errors = []
        lines = output.split('\n')

        current_hook = None
        current_files = []
        current_exit_code = 0

        for line in lines:
            # Hook失敗の検出
            failed_match = re.match(r'^([\w-]+)\.+Failed$', line)
            if failed_match:
                if current_hook and current_files:
                    errors.append(PreCommitError(
                        hook_id=current_hook,
                        exit_code=current_exit_code,
                        modified_files=current_files,
                        error_message=""
                    ))

                current_hook = failed_match.group(1)
                current_files = []
                continue

            # Hook IDとexit codeの検出
            hook_info_match = re.match(r'- hook id: ([\w-]+)', line)
            if hook_info_match:
                current_hook = hook_info_match.group(1)
                continue

            exit_code_match = re.match(r'- exit code: (\d+)', line)
            if exit_code_match:
                current_exit_code = int(exit_code_match.group(1))
                continue

            # 修正されたファイルの検出
            fixing_match = re.match(r'Fixing (.+)$', line)
            if fixing_match and current_hook:
                current_files.append(fixing_match.group(1))

        # 最後のエラーを追加
        if current_hook and current_files:
            errors.append(PreCommitError(
                hook_id=current_hook,
                exit_code=current_exit_code,
                modified_files=current_files,
                error_message=""
            ))

        return errors

    def _fix_trailing_whitespace(self, files: List[str]) -> bool:
        """末尾の空白を修正"""
        try:
            for file_path in files:
                full_path = self.repo_path / file_path
                if not full_path.exists():
                    continue

                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 各行の末尾の空白を削除
                lines = content.split('\n')
                fixed_lines = [line.rstrip() for line in lines]
                fixed_content = '\n'.join(fixed_lines)

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

            return True
        except Exception as e:
            self.logger.error(f"Failed to fix trailing whitespace: {e}")
            return False

    def _fix_end_of_file(self, files: List[str]) -> bool:
        """ファイル末尾の改行を修正"""
        try:
            for file_path in files:
                full_path = self.repo_path / file_path
                if not full_path.exists():
                    continue

                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 末尾に改行がない場合は追加
                if content and not content.endswith('\n'):
                    content += '\n'

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return True
        except Exception as e:
            self.logger.error(f"Failed to fix end of file: {e}")
            return False

    def _fix_syntax_errors(self, files: List[str]) -> bool:
        """構文エラーの自動修復を試みる（限定的）"""
        try:
            for file_path in files:
                if not file_path.endswith('.py'):
                    continue

                full_path = self.repo_path / file_path
                if not full_path.exists():
                    continue

                # 基本的な構文エラーの修正を試みる
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 閉じられていない括弧の検出と修正
                # これは非常に単純な実装で、より複雑な修正は手動で行う必要がある
                open_parens = content.count('(') - content.count(')')
                if open_parens > 0:
                    content += ')' * open_parens

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return True
        except Exception as e:
            self.logger.error(f"Failed to fix syntax errors: {e}")
            return False

    def run_with_auto_fix(self, command: List[str], max_retries: Optional[int] = None) -> Tuple[bool, str, str]:
        """
        コマンドを実行し、pre-commitエラーを自動修復してリトライ

        Returns:
            Tuple[成功フラグ, stdout, stderr]
        """
        if max_retries is None:
            max_retries = self.max_retries

        for attempt in range(max_retries + 1):
            try:
                result = subprocess.run(
                    command,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    return True, result.stdout, result.stderr

                # pre-commitエラーの場合
                if "Failed" in result.stderr and attempt < max_retries:
                    self.logger.info(f"Pre-commit failed on attempt {attempt + 1}, attempting auto-fix...")

                    fixed, errors, fix_message = self.handle_pre_commit_errors(result.stderr)

                    if fixed:
                        self.logger.info(f"Auto-fix successful: {fix_message}")
                        # 修正されたファイルを再度add
                        for error in errors:
                            for file in error.modified_files:
                                subprocess.run(
                                    ["git", "add", file],
                                    cwd=self.repo_path,
                                    capture_output=True
                                )

                        # リトライ前に少し待つ
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.logger.warning("Auto-fix failed, manual intervention required")
                        return False, result.stdout, result.stderr
                else:
                    # pre-commit以外のエラー
                    return False, result.stdout, result.stderr

            except Exception as e:
                self.logger.error(f"Command execution failed: {e}")
                return False, "", str(e)

        return False, "", f"Failed after {max_retries} retries"


def integrate_with_elder_flow():
    """Elder Flowとの統合設定"""
    return {
        "handler": ElderFlowPreCommitHandler,
        "config": {
            "max_retries": 3,
            "retry_delay": 2,
            "auto_fix_enabled": True,
            "fix_types": [
                "trailing-whitespace",
                "end-of-file-fixer",
                "check-ast"
            ]
        }
    }
