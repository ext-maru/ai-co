#!/usr/bin/env python3
"""
AI Git Assistant - AIを活用したGitワークフロー支援ライブラリ
"""

import os
import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests

class AIGitAssistant:
    """AI-powered Git workflow assistant"""
    
    def __init__(self, project_path: str = "/root/ai_co"):
        self.project_path = project_path
        self.git_config = self._load_git_config()
        
    def _load_git_config(self) -> Dict:
        """Git設定を読み込む"""
        config_path = os.path.join(self.project_path, "config", "github.conf")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _run_git_command(self, command: List[str], cwd: str = None) -> Tuple[bool, str]:
        """Gitコマンドを実行"""
        if cwd is None:
            cwd = self.project_path
            
        try:
            result = subprocess.run(
                command, 
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
    
    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        success, output = self._run_git_command(['git', 'branch', '--show-current'])
        return output if success else "unknown"
    
    def get_branch_status(self) -> Dict:
        """ブランチの状態を取得"""
        current_branch = self.get_current_branch()
        
        # 変更ファイル取得
        success, modified_files = self._run_git_command(['git', 'diff', '--name-only'])
        modified_list = modified_files.split('\n') if modified_files else []
        
        # ステージングファイル取得
        success, staged_files = self._run_git_command(['git', 'diff', '--cached', '--name-only'])
        staged_list = staged_files.split('\n') if staged_files else []
        
        # コミット数取得
        success, ahead_behind = self._run_git_command(['git', 'rev-list', '--count', '--left-right', 'HEAD...origin/' + current_branch])
        ahead, behind = '0', '0'
        if success and ahead_behind:
            parts = ahead_behind.split('\t')
            if len(parts) == 2:
                behind, ahead = parts
        
        return {
            'current_branch': current_branch,
            'modified_files': [f for f in modified_list if f],
            'staged_files': [f for f in staged_list if f],
            'commits_ahead': int(ahead),
            'commits_behind': int(behind)
        }
    
    def analyze_changes(self) -> Dict:
        """変更内容を分析"""
        # 差分取得
        success, diff = self._run_git_command(['git', 'diff', '--unified=3'])
        
        if not success or not diff:
            return {'summary': 'No changes detected', 'files': []}
        
        # ファイルごとの変更を分析
        files_changed = []
        current_file = None
        additions = 0
        deletions = 0
        
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    files_changed.append(current_file)
                # ファイルパス抽出
                match = re.search(r'b/(.+)$', line)
                file_path = match.group(1) if match else 'unknown'
                current_file = {
                    'path': file_path,
                    'additions': 0,
                    'deletions': 0,
                    'type': self._get_file_type(file_path)
                }
            elif line.startswith('+') and not line.startswith('+++'):
                additions += 1
                if current_file:
                    current_file['additions'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
                if current_file:
                    current_file['deletions'] += 1
        
        if current_file:
            files_changed.append(current_file)
        
        return {
            'summary': f'{len(files_changed)} files changed, {additions} additions, {deletions} deletions',
            'files': files_changed,
            'total_additions': additions,
            'total_deletions': deletions
        }
    
    def _get_file_type(self, file_path: str) -> str:
        """ファイルタイプを判定"""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.sh': 'shell',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
        }
        return type_map.get(ext, 'other')
    
    def generate_commit_message(self, changes: Dict) -> str:
        """変更内容に基づいてコミットメッセージを生成"""
        if not changes['files']:
            return "Update files"
        
        # ファイルタイプ別に分類
        file_types = {}
        for file_info in changes['files']:
            file_type = file_info['type']
            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append(file_info)
        
        # メッセージ生成
        if len(file_types) == 1:
            file_type = list(file_types.keys())[0]
            if file_type == 'python':
                return "🐍 Python機能の更新"
            elif file_type == 'javascript':
                return "🟨 JavaScript機能の更新"
            elif file_type == 'shell':
                return "🐚 シェルスクリプト更新"
            elif file_type == 'markdown':
                return "📝 ドキュメント更新"
            else:
                return f"🔧 {file_type}ファイル更新"
        else:
            return f"🔄 複数ファイル更新 ({len(changes['files'])}個)"
    
    def create_intelligent_branch(self, branch_type: str, description: str) -> str:
        """AI支援によるブランチ作成"""
        # ブランチ名を自動生成
        clean_desc = re.sub(r'[^a-zA-Z0-9\s-]', '', description.lower())
        clean_desc = re.sub(r'\s+', '-', clean_desc.strip())
        
        timestamp = datetime.now().strftime("%Y%m%d")
        branch_name = f"{branch_type}/{clean_desc}-{timestamp}"
        
        # ブランチ作成
        success, output = self._run_git_command(['git', 'checkout', '-b', branch_name])
        
        if success:
            return branch_name
        else:
            raise Exception(f"ブランチ作成エラー: {output}")
    
    def suggest_pr_description(self, branch_name: str, changes: Dict) -> str:
        """プルリクエストの説明を提案"""
        template = f"""## 概要
{self._generate_pr_summary(branch_name, changes)}

## 変更内容
{self._generate_change_details(changes)}

## テスト
- [ ] 機能テスト完了
- [ ] 回帰テスト完了

## チェックリスト
- [ ] コードレビュー完了
- [ ] ドキュメント更新完了
- [ ] テストケース追加完了

## 関連Issue
関連するIssue番号があれば記載

---
🤖 AI自動生成 with ai-git
"""
        return template
    
    def _generate_pr_summary(self, branch_name: str, changes: Dict) -> str:
        """PRの概要を生成"""
        if 'feature/' in branch_name:
            return f"新機能の追加: {branch_name.replace('feature/', '')}"
        elif 'fix/' in branch_name:
            return f"バグ修正: {branch_name.replace('fix/', '')}"
        elif 'hotfix/' in branch_name:
            return f"緊急修正: {branch_name.replace('hotfix/', '')}"
        else:
            return f"変更内容: {changes['summary']}"
    
    def _generate_change_details(self, changes: Dict) -> str:
        """変更詳細を生成"""
        if not changes['files']:
            return "変更なし"
        
        details = []
        for file_info in changes['files']:
            path = file_info['path']
            adds = file_info['additions']
            dels = file_info['deletions']
            details.append(f"- `{path}`: +{adds} -{dels}")
        
        return '\n'.join(details)
    
    def intelligent_merge_check(self, target_branch: str) -> Dict:
        """インテリジェントマージチェック"""
        current_branch = self.get_current_branch()
        
        # コンフリクトチェック
        success, merge_base = self._run_git_command(['git', 'merge-base', current_branch, target_branch])
        
        if not success:
            return {'can_merge': False, 'reason': 'マージベースが見つかりません'}
        
        # 差分確認
        success, conflicts = self._run_git_command(['git', 'merge-tree', merge_base, current_branch, target_branch])
        
        has_conflicts = '<<<<<<<' in conflicts
        
        return {
            'can_merge': not has_conflicts,
            'reason': 'コンフリクトが検出されました' if has_conflicts else 'マージ可能',
            'conflicts': conflicts if has_conflicts else None
        }
    
    def auto_commit_with_ai(self, message: str = None) -> bool:
        """AI支援による自動コミット"""
        # 変更分析
        changes = self.analyze_changes()
        
        if not changes['files']:
            print("コミットする変更がありません")
            return False
        
        # メッセージ生成
        if not message:
            message = self.generate_commit_message(changes)
        
        # ステージング
        success, output = self._run_git_command(['git', 'add', '.'])
        if not success:
            print(f"ステージングエラー: {output}")
            return False
        
        # コミット
        success, output = self._run_git_command(['git', 'commit', '-m', message])
        if success:
            print(f"✅ コミット完了: {message}")
            return True
        else:
            print(f"コミットエラー: {output}")
            return False
    
    def create_release_notes(self, from_tag: str, to_tag: str = "HEAD") -> str:
        """リリースノートを生成"""
        # コミット履歴取得
        success, log = self._run_git_command(['git', 'log', f'{from_tag}..{to_tag}', '--pretty=format:%h %s'])
        
        if not success:
            return "リリースノートを生成できませんでした"
        
        commits = log.split('\n') if log else []
        
        # カテゴリー分類
        features = []
        fixes = []
        others = []
        
        for commit in commits:
            if not commit.strip():
                continue
                
            if any(keyword in commit.lower() for keyword in ['feat', 'add', '新機能', '追加']):
                features.append(commit)
            elif any(keyword in commit.lower() for keyword in ['fix', 'bug', '修正', 'バグ']):
                fixes.append(commit)
            else:
                others.append(commit)
        
        # リリースノート作成
        notes = f"# Release Notes ({to_tag})\n\n"
        
        if features:
            notes += "## 🚀 新機能\n"
            for feature in features:
                notes += f"- {feature}\n"
            notes += "\n"
        
        if fixes:
            notes += "## 🐛 バグ修正\n"
            for fix in fixes:
                notes += f"- {fix}\n"
            notes += "\n"
        
        if others:
            notes += "## 🔧 その他の変更\n"
            for other in others:
                notes += f"- {other}\n"
            notes += "\n"
        
        notes += "---\n🤖 AI自動生成 with ai-git\n"
        
        return notes

def main():
    """CLIエントリーポイント"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python ai_git_assistant.py <command> [args]")
        return
    
    assistant = AIGitAssistant()
    command = sys.argv[1]
    
    if command == "status":
        status = assistant.get_branch_status()
        print(f"ブランチ: {status['current_branch']}")
        print(f"変更ファイル: {len(status['modified_files'])}")
        print(f"ステージングファイル: {len(status['staged_files'])}")
        
    elif command == "analyze":
        changes = assistant.analyze_changes()
        print(changes['summary'])
        
    elif command == "commit":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        success = assistant.auto_commit_with_ai(message)
        
    elif command == "pr-desc":
        branch = assistant.get_current_branch()
        changes = assistant.analyze_changes()
        desc = assistant.suggest_pr_description(branch, changes)
        print(desc)
        
    else:
        print(f"不明なコマンド: {command}")

if __name__ == "__main__":
    main()