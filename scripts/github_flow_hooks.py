#!/usr/bin/env python3
"""
GitHub Flow違反防止システム - Git Hooks
AI Company エルダーズ（4賢者）による違反防止機構

インシデント賢者による緊急時対応設計
ナレッジ賢者による学習機能実装
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class GitHubFlowHooks:
    """GitHub Flow違反防止 Git Hooks システム"""
    
    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.hooks_dir = self.project_dir / ".git" / "hooks"
        self.config_file = self.project_dir / ".github_flow_hooks.json"
        self.violation_log = self.project_dir / "logs" / "github_flow_violations.log"
        self.config = self.load_config()
        self.setup_logging()
    
    def load_config(self) -> Dict:
        """設定ファイルの読み込み"""
        default_config = {
            "protected_branches": ["main"],
            "forbidden_branches": ["master"],
            "allowed_prefixes": ["feature/", "fix/", "hotfix/", "docs/", "refactor/"],
            "require_conventional_commits": True,
            "max_files_per_commit": 50,
            "forbidden_files": [".env", "*.key", "*.pem", "passwords.txt"],
            "require_tests": True,
            "elder_approval_keywords": ["ELDER-APPROVED", "EMERGENCY-OVERRIDE"],
            "four_sages_validation": True,
            "auto_fix_enabled": True,
            "notification_enabled": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception:
                pass
        
        return default_config
    
    def setup_logging(self):
        """ログディレクトリの設定"""
        self.violation_log.parent.mkdir(exist_ok=True)
    
    def log_violation(self, violation_type: str, message: str, severity: str = "WARNING"):
        """違反ログの記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {severity}: {violation_type} - {message}\n"
        
        with open(self.violation_log, 'a') as f:
            f.write(log_entry)
    
    def install_hooks(self) -> bool:
        """Git Hooksの設置"""
        try:
            self.hooks_dir.mkdir(exist_ok=True)
            
            # pre-commit hook
            self.create_pre_commit_hook()
            
            # pre-push hook
            self.create_pre_push_hook()
            
            # commit-msg hook
            self.create_commit_msg_hook()
            
            # pre-receive hook (サーバー側)
            self.create_pre_receive_hook()
            
            print("✅ GitHub Flow違反防止 Git Hooks が正常に設置されました")
            return True
            
        except Exception as e:
            print(f"❌ Git Hooks設置エラー: {e}")
            return False
    
    def create_pre_commit_hook(self):
        """pre-commit hook の作成"""
        hook_content = f'''#!/bin/bash
# AI Company GitHub Flow Pre-Commit Hook
# 4賢者による違反防止システム

set -e

# Python script path
SCRIPT_DIR="{self.project_dir}/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/github_flow_hooks.py"

# Python script を実行
if [ -f "$PYTHON_SCRIPT" ]; then
    python3 "$PYTHON_SCRIPT" pre-commit
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Pre-commit validation failed"
        exit $exit_code
    fi
else
    echo "⚠️  GitHub Flow validation script not found"
fi

echo "✅ Pre-commit validation passed"
'''
        
        hook_file = self.hooks_dir / "pre-commit"
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_file, 0o755)
    
    def create_pre_push_hook(self):
        """pre-push hook の作成"""
        hook_content = f'''#!/bin/bash
# AI Company GitHub Flow Pre-Push Hook
# 4賢者による分岐制御システム

set -e

# 現在のブランチ取得
current_branch=$(git branch --show-current)
remote_name="$1"
remote_url="$2"

# Python script path
SCRIPT_DIR="{self.project_dir}/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/github_flow_hooks.py"

# Python script を実行
if [ -f "$PYTHON_SCRIPT" ]; then
    python3 "$PYTHON_SCRIPT" pre-push "$current_branch" "$remote_name"
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Pre-push validation failed"
        exit $exit_code
    fi
else
    echo "⚠️  GitHub Flow validation script not found"
fi

echo "✅ Pre-push validation passed"
'''
        
        hook_file = self.hooks_dir / "pre-push"
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_file, 0o755)
    
    def create_commit_msg_hook(self):
        """commit-msg hook の作成"""
        hook_content = f'''#!/bin/bash
# AI Company GitHub Flow Commit Message Hook
# ナレッジ賢者による品質保証システム

set -e

commit_msg_file="$1"
commit_msg=$(cat "$commit_msg_file")

# Python script path
SCRIPT_DIR="{self.project_dir}/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/github_flow_hooks.py"

# Python script を実行
if [ -f "$PYTHON_SCRIPT" ]; then
    python3 "$PYTHON_SCRIPT" commit-msg "$commit_msg"
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Commit message validation failed"
        exit $exit_code
    fi
else
    echo "⚠️  GitHub Flow validation script not found"
fi

echo "✅ Commit message validation passed"
'''
        
        hook_file = self.hooks_dir / "commit-msg"
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_file, 0o755)
    
    def create_pre_receive_hook(self):
        """pre-receive hook の作成（サーバー側）"""
        hook_content = f'''#!/bin/bash
# AI Company GitHub Flow Pre-Receive Hook
# エルダーズによる最終承認システム

set -e

# Python script path
SCRIPT_DIR="{self.project_dir}/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/github_flow_hooks.py"

# 標準入力から更新情報を読み取り
while read oldrev newrev refname; do
    # Python script を実行
    if [ -f "$PYTHON_SCRIPT" ]; then
        python3 "$PYTHON_SCRIPT" pre-receive "$oldrev" "$newrev" "$refname"
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            echo "❌ Pre-receive validation failed"
            exit $exit_code
        fi
    else
        echo "⚠️  GitHub Flow validation script not found"
    fi
done

echo "✅ Pre-receive validation passed"
'''
        
        hook_file = self.hooks_dir / "pre-receive"
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_file, 0o755)
    
    def validate_pre_commit(self) -> bool:
        """pre-commit時の検証"""
        try:
            # 1. ファイル数チェック
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=self.project_dir
            )
            
            if result.returncode != 0:
                return True  # 変更がない場合は通す
            
            staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if len(staged_files) > self.config["max_files_per_commit"]:
                self.log_violation(
                    "LARGE_COMMIT",
                    f"Too many files in single commit: {len(staged_files)} > {self.config['max_files_per_commit']}"
                )
                print(f"❌ 一度に{self.config['max_files_per_commit']}個以上のファイルをコミットできません")
                print(f"   現在: {len(staged_files)}個のファイル")
                return False
            
            # 2. 禁止ファイルチェック
            for file in staged_files:
                for forbidden_pattern in self.config["forbidden_files"]:
                    if self._matches_pattern(file, forbidden_pattern):
                        self.log_violation(
                            "FORBIDDEN_FILE",
                            f"Forbidden file type: {file}"
                        )
                        print(f"❌ 禁止されたファイル: {file}")
                        return False
            
            # 3. テストファイルの存在チェック
            if self.config["require_tests"]:
                if not self._has_test_files(staged_files):
                    print("⚠️  テストファイルが含まれていません")
                    # 警告のみ（強制終了しない）
            
            return True
            
        except Exception as e:
            self.log_violation("PRE_COMMIT_ERROR", str(e))
            return False
    
    def validate_pre_push(self, branch: str, remote: str) -> bool:
        """pre-push時の検証"""
        try:
            # 1. 保護ブランチチェック
            if branch in self.config["protected_branches"]:
                self.log_violation(
                    "PROTECTED_BRANCH_PUSH",
                    f"Direct push to protected branch: {branch}"
                )
                print(f"🛡️  保護されたブランチ '{branch}' への直接プッシュは禁止されています")
                print("📋 GitHub Flowに従い、feature/fix ブランチからPRを作成してください")
                return False
            
            # 2. 禁止ブランチチェック
            if branch in self.config["forbidden_branches"]:
                self.log_violation(
                    "FORBIDDEN_BRANCH_PUSH",
                    f"Push to forbidden branch: {branch}"
                )
                print(f"❌ 禁止されたブランチ '{branch}' からのプッシュは許可されていません")
                print(f"📋 '{self.config['protected_branches'][0]}' ブランチを使用してください")
                return False
            
            # 3. ブランチ命名規則チェック
            if not self._is_valid_branch_name(branch):
                self.log_violation(
                    "INVALID_BRANCH_NAME",
                    f"Invalid branch name: {branch}"
                )
                print(f"❌ ブランチ名 '{branch}' は命名規則に従っていません")
                print(f"📋 許可されたプレフィックス: {', '.join(self.config['allowed_prefixes'])}")
                return False
            
            # 4. エルダー承認チェック
            if self._requires_elder_approval(branch):
                if not self._has_elder_approval():
                    self.log_violation(
                        "ELDER_APPROVAL_REQUIRED",
                        f"Elder approval required for branch: {branch}"
                    )
                    print("🏛️  このブランチにはエルダー承認が必要です")
                    print("📋 コミットメッセージに 'ELDER-APPROVED' を含めてください")
                    return False
            
            return True
            
        except Exception as e:
            self.log_violation("PRE_PUSH_ERROR", str(e))
            return False
    
    def validate_commit_msg(self, message: str) -> bool:
        """commit-msg時の検証"""
        try:
            # 1. Conventional Commits形式チェック
            if self.config["require_conventional_commits"]:
                if not self._is_conventional_commit(message):
                    self.log_violation(
                        "INVALID_COMMIT_MESSAGE",
                        f"Non-conventional commit message: {message[:50]}..."
                    )
                    print("❌ コミットメッセージがConventional Commits形式に従っていません")
                    print("📋 形式: <type>(<scope>): <description>")
                    print("   例: feat(auth): add user login functionality")
                    return False
            
            # 2. メッセージ長チェック
            lines = message.split('\n')
            if len(lines[0]) > 72:
                self.log_violation(
                    "COMMIT_MESSAGE_TOO_LONG",
                    f"Commit message too long: {len(lines[0])} > 72"
                )
                print("❌ コミットメッセージの1行目が長すぎます（72文字以内）")
                return False
            
            # 3. 禁止文字列チェック
            forbidden_words = ["password", "secret", "token", "key", "private"]
            for word in forbidden_words:
                if word.lower() in message.lower():
                    self.log_violation(
                        "SENSITIVE_INFO_IN_COMMIT",
                        f"Sensitive word in commit message: {word}"
                    )
                    print(f"❌ コミットメッセージに機密情報が含まれている可能性があります: {word}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_violation("COMMIT_MSG_ERROR", str(e))
            return False
    
    def validate_pre_receive(self, old_rev: str, new_rev: str, ref_name: str) -> bool:
        """pre-receive時の検証（サーバー側）"""
        try:
            # ブランチ名を抽出
            branch_name = ref_name.split('/')[-1]
            
            # 1. 保護ブランチの強制削除チェック
            if old_rev != "0000000000000000000000000000000000000000" and new_rev == "0000000000000000000000000000000000000000":
                if branch_name in self.config["protected_branches"]:
                    self.log_violation(
                        "PROTECTED_BRANCH_DELETE",
                        f"Attempt to delete protected branch: {branch_name}",
                        "CRITICAL"
                    )
                    print(f"🚨 保護されたブランチ '{branch_name}' の削除は禁止されています")
                    return False
            
            # 2. 4賢者による最終検証
            if self.config["four_sages_validation"]:
                if not self._four_sages_final_validation(old_rev, new_rev, branch_name):
                    self.log_violation(
                        "FOUR_SAGES_REJECTION",
                        f"Four sages rejected push to {branch_name}",
                        "HIGH"
                    )
                    print("🧙‍♂️ 4賢者による最終検証に失敗しました")
                    return False
            
            return True
            
        except Exception as e:
            self.log_violation("PRE_RECEIVE_ERROR", str(e))
            return False
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """ファイルパターンマッチング"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def _has_test_files(self, files: List[str]) -> bool:
        """テストファイルの存在チェック"""
        test_patterns = ["test_*.py", "*_test.py", "tests/*.py"]
        for file in files:
            for pattern in test_patterns:
                if self._matches_pattern(file, pattern):
                    return True
        return False
    
    def _is_valid_branch_name(self, branch: str) -> bool:
        """ブランチ名の妥当性チェック"""
        # 保護ブランチは常に有効
        if branch in self.config["protected_branches"]:
            return True
        
        # 許可されたプレフィックスのチェック
        for prefix in self.config["allowed_prefixes"]:
            if branch.startswith(prefix):
                return True
        
        return False
    
    def _requires_elder_approval(self, branch: str) -> bool:
        """エルダー承認が必要かチェック"""
        critical_prefixes = ["hotfix/", "emergency/"]
        return any(branch.startswith(prefix) for prefix in critical_prefixes)
    
    def _has_elder_approval(self) -> bool:
        """エルダー承認の存在チェック"""
        try:
            # 最新のコミットメッセージを取得
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%B"],
                capture_output=True, text=True, cwd=self.project_dir
            )
            
            if result.returncode == 0:
                commit_msg = result.stdout
                for keyword in self.config["elder_approval_keywords"]:
                    if keyword in commit_msg:
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _is_conventional_commit(self, message: str) -> bool:
        """Conventional Commits形式チェック"""
        import re
        
        # 基本的なConventional Commits形式
        pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .+'
        return bool(re.match(pattern, message))
    
    def _four_sages_final_validation(self, old_rev: str, new_rev: str, branch: str) -> bool:
        """4賢者による最終検証"""
        try:
            # 簡易版4賢者検証
            validation_score = 0
            
            # タスク賢者: ブランチ名の妥当性
            if self._is_valid_branch_name(branch):
                validation_score += 1
            
            # インシデント賢者: 安全性チェック
            if branch not in self.config["forbidden_branches"]:
                validation_score += 1
            
            # ナレッジ賢者: 学習データの蓄積
            if self.violation_log.exists():
                validation_score += 1
            
            # RAG賢者: 設定の妥当性
            if len(self.config["protected_branches"]) > 0:
                validation_score += 1
            
            # 4賢者中3賢者以上の承認が必要
            return validation_score >= 3
            
        except Exception:
            return False


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python github_flow_hooks.py <hook_type> [args...]")
        sys.exit(1)
    
    hook_type = sys.argv[1]
    hooks = GitHubFlowHooks()
    
    if hook_type == "install":
        # Git Hooks のインストール
        if hooks.install_hooks():
            print("✅ Git Hooks が正常にインストールされました")
            sys.exit(0)
        else:
            print("❌ Git Hooks のインストールに失敗しました")
            sys.exit(1)
    
    elif hook_type == "pre-commit":
        # Pre-commit検証
        if hooks.validate_pre_commit():
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif hook_type == "pre-push":
        # Pre-push検証
        if len(sys.argv) >= 3:
            branch = sys.argv[2]
            remote = sys.argv[3] if len(sys.argv) > 3 else "origin"
            if hooks.validate_pre_push(branch, remote):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("❌ Branch name required for pre-push validation")
            sys.exit(1)
    
    elif hook_type == "commit-msg":
        # Commit message検証
        if len(sys.argv) >= 3:
            message = sys.argv[2]
            if hooks.validate_commit_msg(message):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("❌ Commit message required for validation")
            sys.exit(1)
    
    elif hook_type == "pre-receive":
        # Pre-receive検証
        if len(sys.argv) >= 5:
            old_rev = sys.argv[2]
            new_rev = sys.argv[3]
            ref_name = sys.argv[4]
            if hooks.validate_pre_receive(old_rev, new_rev, ref_name):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("❌ Revision info required for pre-receive validation")
            sys.exit(1)
    
    else:
        print(f"❌ Unknown hook type: {hook_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()