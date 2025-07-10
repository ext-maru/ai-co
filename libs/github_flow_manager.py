import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))
from libs.commit_message_generator import CommitMessageGenerator

class GitHubFlowManager:
    """GitHub Flow運用を自動化するマネージャー"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_dir = Path(__file__).parent.parent
        self.setup_git()
    
    def setup_git(self):
        """Git設定の初期化"""
        try:
            # 基本設定
            self.run_git("config user.name 'Elders Guild Bot'")
            self.run_git("config user.email 'ai-company@localhost'")
            
            # GitHub Flowではmainブランチのみ使用
            self.run_git("checkout main")
        except Exception as e:
            self.logger.warning(f"Git setup warning: {e}")
    
    def run_git(self, command: str) -> subprocess.CompletedProcess:
        """Gitコマンドを実行"""
        cmd = f"git {command}"
        return subprocess.run(
            cmd.split(),
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
    
    def create_feature_branch(self, task_id: str) -> str:
        """機能ブランチを作成"""
        branch_name = f"feature/{task_id}"
        
        try:
            # mainから分岐
            self.run_git("checkout main")
            self.run_git("pull origin main")
            self.run_git(f"checkout -b {branch_name}")
            return branch_name
        except Exception as e:
            self.logger.error(f"Branch creation failed: {e}")
            return "main"
    
    def commit_changes(self, message: str = None, files: List[str] = None, use_best_practices: bool = True):
        """変更をコミット（ベストプラクティス対応）"""
        try:
            if files:
                for file in files:
                    self.run_git(f"add {file}")
            else:
                self.run_git("add -A")
            
            # ベストプラクティスモード
            if use_best_practices:
                generator = CommitMessageGenerator()
                generated_message = generator.generate_commit_message()
                
                # 検証
                valid, errors = generator.validate_message(generated_message)
                if not valid:
                    self.logger.warning(f"Generated message has issues: {errors}")
                    # フォールバック
                    if message:
                        generated_message = self._format_conventional_commit(message)
                    else:
                        generated_message = "chore: automated commit"
                
                final_message = generated_message
            else:
                # 従来のシンプルなメッセージ
                prefix = "🤖 [Auto]" if self.is_auto_branch() else "✨"
                final_message = f"{prefix} {message}" if message else f"{prefix} Update files"
            
            # 一時ファイルを使用してコミット（複数行対応）
            msg_file = self.project_dir / '.git' / 'COMMIT_MSG_TEMP'
            msg_file.write_text(final_message)
            
            result = self.run_git(f'commit -F {msg_file}')
            
            # 一時ファイル削除
            msg_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                self.logger.info(f"Committed with message: {final_message.split(chr(10))[0]}")
                return True
            else:
                self.logger.error(f"Commit failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Commit failed: {e}")
            return False
    
    def _format_conventional_commit(self, message: str) -> str:
        """簡易的なConventional Commits形式に変換"""
        # キーワードからタイプを推測
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['fix', 'bug', 'issue', 'problem']):
            commit_type = 'fix'
        elif any(word in message_lower for word in ['add', 'new', 'feature', 'implement']):
            commit_type = 'feat'
        elif any(word in message_lower for word in ['doc', 'readme', 'comment']):
            commit_type = 'docs'
        elif any(word in message_lower for word in ['test', 'spec']):
            commit_type = 'test'
        elif any(word in message_lower for word in ['refactor', 'clean', 'improve']):
            commit_type = 'refactor'
        else:
            commit_type = 'chore'
        
        # メッセージを整形（50文字制限）
        subject = message[:50].rstrip('.')
        if len(message) > 50:
            subject = subject[:47] + '...'
        
        # 完全なメッセージを生成
        commit_msg = f"{commit_type}: {subject}"
        
        if len(message) > 50:
            commit_msg += f"\n\n{message}"
        
        return commit_msg
    
    def is_auto_branch(self) -> bool:
        """現在のブランチがauto/*かチェック"""
        result = self.run_git("branch --show-current")
        return result.stdout.strip().startswith("auto/")
    
    def create_pull_request(self, branch_name: str, title: str, body: str = None) -> bool:
        """プルリクエストを作成（GitHub Flow）"""
        try:
            # ブランチをpush
            self.run_git(f"push origin {branch_name}")
            
            # GitHub CLIでPR作成
            pr_body = body or "Automated PR created by Elders Guild Bot"
            
            # GitHub CLI使用
            cmd = f"gh pr create --title '{title}' --body '{pr_body}' --base main --head {branch_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                self.logger.info(f"✅ PR created: {title}")
                return True
            else:
                self.logger.error(f"PR creation failed: {result.stderr}")
                # フォールバック: 直接mainにマージ
                return self.merge_to_main(branch_name)
        except Exception as e:
            self.logger.error(f"PR creation error: {e}")
            return self.merge_to_main(branch_name)
    
    def merge_to_main(self, branch_name: str) -> bool:
        """mainへ直接マージ（フォールバック）"""
        try:
            # mainに切り替え
            self.run_git("checkout main")
            self.run_git("pull origin main")
            
            # Conventional Commits形式のマージメッセージ
            merge_message = f"feat(auto): merge {branch_name} into main\n\nAutomated merge of AI-generated code"
            
            # マージ（--no-ffで履歴を保持）
            msg_file = self.project_dir / '.git' / 'MERGE_MSG_TEMP'
            msg_file.write_text(merge_message)
            
            result = self.run_git(f"merge --no-ff {branch_name} -F {msg_file}")
            
            msg_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                # 成功したらブランチを削除
                self.run_git(f"branch -d {branch_name}")
                self.run_git("push origin main")
                return True
            else:
                self.logger.error(f"Merge failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Merge error: {e}")
            return False
    
    def create_release(self, version: str = None) -> bool:
        """リリースを作成（develop → main）"""
        if not version:
            version = datetime.now().strftime("%Y.%m.%d")
        
        try:
            # mainに切り替え
            self.run_git("checkout main")
            
            # developをマージ
            result = self.run_git(f"merge --no-ff develop -m '🚀 Release v{version}'")
            
            if result.returncode == 0:
                # タグを作成
                self.run_git(f"tag -a v{version} -m 'Version {version}'")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Release failed: {e}")
            return False
    
    def get_status(self) -> dict:
        """Git状態を取得"""
        try:
            current_branch = self.run_git("branch --show-current").stdout.strip()
            status = self.run_git("status --porcelain").stdout
            log = self.run_git("log --oneline -n 5").stdout
            
            return {
                "current_branch": current_branch,
                "has_changes": bool(status),
                "recent_commits": log.strip().split('\n') if log else []
            }
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return {"error": str(e)}
    
    def auto_commit_task_result(self, task_id: str, files_created: List[str], summary: str):
        """タスク結果を自動コミット（GitHub Flow対応）"""
        branch_name = self.create_feature_branch(task_id)
        
        if files_created:
            # ベストプラクティスに従ってコミット
            if self.commit_changes(use_best_practices=True):
                self.logger.info(f"✅ Committed {len(files_created)} files to {branch_name} with best practices")
                
                # PRを作成またはmainへマージ
                if self.create_pull_request(branch_name, f"feat: {summary}", f"Auto-generated: {summary}"):
                    self.logger.info(f"✅ Created PR or merged {branch_name} to main")
                    return True
        
        return False
    
    def generate_changelog(self, from_tag: str = None, to_tag: str = "HEAD") -> str:
        """Conventional Commitsに基づいてCHANGELOGを生成"""
        try:
            # タグ間のコミットを取得
            if from_tag:
                cmd = f"log {from_tag}..{to_tag} --pretty=format:'%s||%b'"
            else:
                cmd = "log --pretty=format:'%s||%b' -n 50"  # 最新50件
            
            result = self.run_git(cmd)
            if result.returncode != 0:
                return "Failed to generate changelog"
            
            commits = result.stdout.strip().split('\n')
            
            # カテゴリ別に分類
            features = []
            fixes = []
            breaking = []
            others = []
            
            for commit in commits:
                if '||' in commit:
                    subject, body = commit.split('||', 1)
                else:
                    subject, body = commit, ''
                
                # Breaking changesをチェック
                if 'BREAKING CHANGE' in body or '!' in subject:
                    breaking.append(subject)
                # タイプ別に分類
                elif subject.startswith('feat'):
                    features.append(subject)
                elif subject.startswith('fix'):
                    fixes.append(subject)
                else:
                    others.append(subject)
            
            # CHANGELOG生成
            changelog = f"# Changelog\n\n"
            changelog += f"## [{to_tag}]\n\n"
            
            if breaking:
                changelog += "### ⚠️ Breaking Changes\n\n"
                for item in breaking:
                    changelog += f"- {item}\n"
                changelog += "\n"
            
            if features:
                changelog += "### ✨ Features\n\n"
                for item in features:
                    changelog += f"- {item}\n"
                changelog += "\n"
            
            if fixes:
                changelog += "### 🐛 Bug Fixes\n\n"
                for item in fixes:
                    changelog += f"- {item}\n"
                changelog += "\n"
            
            if others:
                changelog += "### 📝 Other Changes\n\n"
                for item in others:
                    changelog += f"- {item}\n"
                changelog += "\n"
            
            return changelog
            
        except Exception as e:
            self.logger.error(f"Changelog generation failed: {e}")
            return f"Error generating changelog: {e}"
