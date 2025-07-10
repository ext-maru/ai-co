#!/usr/bin/env python3
"""
Elders Guild Commit Message Generator
Conventional Commitsベストプラクティスに基づく自動生成
"""

import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

class CommitMessageGenerator:
    """Conventional Commitsに基づくコミットメッセージ生成"""
    
    # Conventional Commits タイプ定義
    COMMIT_TYPES = {
        'feat': 'A new feature',
        'fix': 'A bug fix',
        'docs': 'Documentation only changes',
        'style': 'Changes that do not affect the meaning of the code',
        'refactor': 'A code change that neither fixes a bug nor adds a feature',
        'perf': 'A code change that improves performance',
        'test': 'Adding missing tests or correcting existing tests',
        'build': 'Changes that affect the build system or external dependencies',
        'ci': 'Changes to our CI configuration files and scripts',
        'chore': 'Other changes that don\'t modify src or test files',
        'revert': 'Reverts a previous commit'
    }
    
    # ファイルパターンからコミットタイプを推測
    FILE_TYPE_PATTERNS = {
        r'test_.*\.py$|.*_test\.py$|tests/': 'test',
        r'README.*|.*\.md$|docs/': 'docs',
        r'requirements.*|setup\.py|pyproject\.toml|package.*\.json': 'build',
        r'\.github/|\.gitlab-ci\.yml|Jenkinsfile': 'ci',
        r'\.gitignore|\.editorconfig|\.pre-commit': 'chore',
        r'_worker\.py$': 'feat',
        r'_manager\.py$': 'feat',
        r'config/|.*\.conf$|.*\.json$': 'chore',
        r'scripts/': 'build'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path('/home/aicompany/ai_co')
        
    def analyze_changes(self) -> Dict[str, any]:
        """変更内容を分析"""
        try:
            # staged changes
            staged_files = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            ).stdout.strip().split('\n')
            
            # diff statistics
            diff_stat = subprocess.run(
                ['git', 'diff', '--cached', '--stat'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            ).stdout
            
            # actual changes
            diff_content = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            ).stdout
            
            return {
                'files': [f for f in staged_files if f],
                'stats': diff_stat,
                'content': diff_content
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze changes: {e}")
            return {'files': [], 'stats': '', 'content': ''}
    
    def detect_commit_type(self, files: List[str], content: str) -> str:
        """ファイルと内容からコミットタイプを推測"""
        type_votes = {}
        
        # ファイルパスから推測
        for file in files:
            for pattern, commit_type in self.FILE_TYPE_PATTERNS.items():
                if re.search(pattern, file):
                    type_votes[commit_type] = type_votes.get(commit_type, 0) + 1
                    break
        
        # コンテンツから推測
        if 'def test_' in content or 'class Test' in content:
            type_votes['test'] = type_votes.get('test', 0) + 2
        elif 'bug' in content.lower() or 'fix' in content.lower():
            type_votes['fix'] = type_votes.get('fix', 0) + 2
        elif 'feature' in content.lower() or 'add' in content.lower():
            type_votes['feat'] = type_votes.get('feat', 0) + 2
        elif 'performance' in content.lower() or 'optimize' in content.lower():
            type_votes['perf'] = type_votes.get('perf', 0) + 2
        
        # 最も可能性の高いタイプを選択
        if type_votes:
            return max(type_votes, key=type_votes.get)
        return 'chore'  # デフォルト
    
    def extract_scope(self, files: List[str]) -> Optional[str]:
        """変更スコープを抽出"""
        if not files:
            return None
            
        # ディレクトリから推測
        scopes = set()
        for file in files:
            parts = Path(file).parts
            if len(parts) > 1:
                # workers/task_worker.py → workers
                scopes.add(parts[0])
            elif file.endswith('_worker.py'):
                # task_worker.py → task
                scopes.add(file.replace('_worker.py', ''))
            elif file.endswith('_manager.py'):
                # rag_manager.py → rag
                scopes.add(file.replace('_manager.py', ''))
        
        if len(scopes) == 1:
            return list(scopes)[0]
        elif len(scopes) > 1:
            return 'multiple'
        return None
    
    def generate_subject(self, commit_type: str, scope: Optional[str], 
                        files: List[str], content: str) -> str:
        """コミット件名を生成（50文字以内）"""
        # スコープ付きプレフィックス
        prefix = f"{commit_type}({scope}): " if scope else f"{commit_type}: "
        
        # アクションを推測
        actions = []
        
        # ファイル名から推測
        for file in files[:3]:  # 最初の3ファイルのみ
            base_name = Path(file).stem
            if 'test' in file:
                actions.append(f"add tests for {base_name}")
            elif file.endswith('.md'):
                actions.append(f"update {base_name} documentation")
            elif '_worker' in file:
                actions.append(f"implement {base_name}")
            elif '_manager' in file:
                actions.append(f"add {base_name} manager")
            elif file.endswith('.sh'):
                actions.append(f"add {base_name} script")
        
        # 内容から推測
        if not actions:
            if 'class' in content:
                actions.append("implement new component")
            elif 'def ' in content:
                actions.append("add new functionality")
            elif 'import' in content:
                actions.append("update dependencies")
            else:
                actions.append("update implementation")
        
        # 50文字制限に収める
        subject = actions[0] if actions else "update code"
        if len(prefix + subject) > 50:
            subject = subject[:50 - len(prefix) - 3] + "..."
            
        return prefix + subject
    
    def generate_body(self, files: List[str], stats: str, content: str) -> List[str]:
        """コミット本文を生成（72文字改行）"""
        body_lines = []
        
        # 変更の要約
        if len(files) > 1:
            body_lines.append(f"This commit modifies {len(files)} files:")
            body_lines.append("")
            
            # ファイルリスト（最大10個）
            for file in files[:10]:
                line = f"- {file}"
                if len(line) > 72:
                    line = f"- .../{Path(file).name}"
                body_lines.append(line)
            
            if len(files) > 10:
                body_lines.append(f"- ... and {len(files) - 10} more files")
            body_lines.append("")
        
        # 主な変更内容
        changes = []
        
        # 追加された主要な要素を検出
        for match in re.finditer(r'class (\w+)', content):
            changes.append(f"Add {match.group(1)} class")
        
        for match in re.finditer(r'def (\w+)', content):
            func_name = match.group(1)
            if not func_name.startswith('_'):
                changes.append(f"Implement {func_name}() function")
        
        if changes:
            body_lines.append("Key changes:")
            for change in changes[:5]:  # 最初の5個まで
                body_lines.append(f"- {change}")
            body_lines.append("")
        
        # 統計情報
        if stats:
            lines = stats.strip().split('\n')
            if len(lines) > 1:
                # 最後の行が統計サマリー
                summary = lines[-1].strip()
                if 'changed' in summary:
                    body_lines.append(summary)
        
        return body_lines
    
    def generate_footer(self, content: str) -> List[str]:
        """コミットフッターを生成"""
        footer_lines = []
        
        # Breaking changesを検出
        if any(word in content.lower() for word in ['breaking', 'deprecated', 'removed']):
            footer_lines.append("BREAKING CHANGE: This may affect existing functionality")
            footer_lines.append("")
        
        # Issue番号を検出（仮想的に）
        task_match = re.search(r'task[_-]?(\d{8}[_-]\d{6})', content.lower())
        if task_match:
            footer_lines.append(f"Refs: #{task_match.group(1)}")
        
        return footer_lines
    
    def generate_commit_message(self) -> str:
        """完全なコミットメッセージを生成"""
        # 変更内容を分析
        changes = self.analyze_changes()
        if not changes['files']:
            return "chore: minor updates"
        
        # コミットタイプとスコープを検出
        commit_type = self.detect_commit_type(changes['files'], changes['content'])
        scope = self.extract_scope(changes['files'])
        
        # 各パートを生成
        subject = self.generate_subject(commit_type, scope, changes['files'], changes['content'])
        body = self.generate_body(changes['files'], changes['stats'], changes['content'])
        footer = self.generate_footer(changes['content'])
        
        # メッセージを組み立て
        message_parts = [subject]
        
        if body or footer:
            message_parts.append("")  # 空行
            
        if body:
            message_parts.extend(body)
            
        if footer:
            if body:
                message_parts.append("")  # 空行
            message_parts.extend(footer)
        
        return '\n'.join(message_parts)
    
    def validate_message(self, message: str) -> Tuple[bool, List[str]]:
        """コミットメッセージを検証"""
        errors = []
        lines = message.split('\n')
        
        if not lines:
            errors.append("Empty commit message")
            return False, errors
        
        # 件名の検証
        subject = lines[0]
        
        # Conventional Commits形式
        if not re.match(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+', subject):
            errors.append("Subject doesn't follow Conventional Commits format")
        
        # 50文字制限
        if len(subject) > 50:
            errors.append(f"Subject is too long ({len(subject)} > 50 characters)")
        
        # 命令形チェック
        if subject.endswith('.'):
            errors.append("Subject should not end with a period")
        
        # 本文の検証
        if len(lines) > 2:
            if lines[1] != "":
                errors.append("Missing blank line between subject and body")
            
            # 72文字制限
            for i, line in enumerate(lines[2:], start=3):
                if len(line) > 72:
                    errors.append(f"Line {i} exceeds 72 characters ({len(line)} chars)")
        
        return len(errors) == 0, errors
    
    def apply_commit(self, message: str) -> bool:
        """生成したメッセージでコミット実行"""
        try:
            # メッセージを一時ファイルに保存
            msg_file = self.project_root / '.git' / 'COMMIT_MSG_TEMP'
            msg_file.write_text(message)
            
            # コミット実行
            result = subprocess.run(
                ['git', 'commit', '-F', str(msg_file)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # 一時ファイル削除
            msg_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                self.logger.info(f"Commit successful: {message.split(chr(10))[0]}")
                return True
            else:
                self.logger.error(f"Commit failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to apply commit: {e}")
            return False


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)
    generator = CommitMessageGenerator()
    
    # コミットメッセージ生成
    message = generator.generate_commit_message()
    print("Generated commit message:")
    print("-" * 72)
    print(message)
    print("-" * 72)
    
    # 検証
    valid, errors = generator.validate_message(message)
    if valid:
        print("✅ Message is valid")
    else:
        print("❌ Message has errors:")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
