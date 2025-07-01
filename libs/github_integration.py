#!/usr/bin/env python3
"""
GitHub連携強化マネージャー
"""
import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubIntegrationManager:
    def __init__(self, repo_url: str = None, token: str = None):
        self.repo_url = repo_url or self._get_repo_url()
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.api_base = "https://api.github.com"
        
        # リポジトリ情報を解析
        if self.repo_url:
            self._parse_repo_info()
    
    def _get_repo_url(self) -> Optional[str]:
        """現在のリポジトリURLを取得"""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _parse_repo_info(self):
        """リポジトリ情報を解析"""
        # SSH URL: git@github.com:owner/repo.git
        # HTTPS URL: https://github.com/owner/repo.git
        if 'github.com' in self.repo_url:
            if self.repo_url.startswith('git@'):
                parts = self.repo_url.split(':')[1].replace('.git', '').split('/')
            else:
                parts = self.repo_url.split('github.com/')[1].replace('.git', '').split('/')
            
            self.owner = parts[0]
            self.repo = parts[1]
            self.api_repo_url = f"{self.api_base}/repos/{self.owner}/{self.repo}"
        else:
            self.owner = None
            self.repo = None
            self.api_repo_url = None
    
    def get_repository_structure(self, path: str = "") -> List[Dict]:
        """リポジトリの構造を取得"""
        if not self.api_repo_url:
            logger.error("リポジトリ情報が設定されていません")
            return []
        
        url = f"{self.api_repo_url}/contents/{path}"
        headers = {'Authorization': f'token {self.token}'} if self.token else {}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GitHub API エラー: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"リポジトリ構造取得エラー: {e}")
            return []
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """ファイルの内容を取得"""
        url = f"{self.api_repo_url}/contents/{file_path}"
        headers = {'Authorization': f'token {self.token}'} if self.token else {}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get('content'):
                    import base64
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
        except Exception as e:
            logger.error(f"ファイル内容取得エラー: {e}")
        
        return None
    
    def analyze_codebase(self, target_dirs: List[str] = ['libs', 'workers']) -> Dict:
        """コードベースを分析"""
        analysis = {
            'total_files': 0,
            'file_types': {},
            'key_modules': [],
            'dependencies': set(),
            'structure': {}
        }
        
        for target_dir in target_dirs:
            files = self.get_repository_structure(target_dir)
            
            for file_info in files:
                if file_info['type'] == 'file':
                    analysis['total_files'] += 1
                    
                    # ファイルタイプ統計
                    ext = Path(file_info['name']).suffix
                    analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                    
                    # Pythonファイルの場合、内容を分析
                    if ext == '.py':
                        content = self.get_file_content(file_info['path'])
                        if content:
                            # インポート分析
                            imports = self._extract_imports(content)
                            analysis['dependencies'].update(imports)
                            
                            # 主要モジュール
                            if any(keyword in content for keyword in ['class', 'def']):
                                analysis['key_modules'].append({
                                    'path': file_info['path'],
                                    'name': file_info['name'],
                                    'size': file_info['size']
                                })
        
        analysis['dependencies'] = list(analysis['dependencies'])
        return analysis
    
    def _extract_imports(self, content: str) -> set:
        """コードからインポートを抽出"""
        imports = set()
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                module = line.split()[1].split('.')[0]
                imports.add(module)
            elif line.startswith('from '):
                parts = line.split()
                if len(parts) > 1:
                    module = parts[1].split('.')[0]
                    imports.add(module)
        
        return imports
    
    def create_enhanced_commit(self, task_id: str, files_changed: List[str], 
                             task_summary: str) -> bool:
        """強化されたコミット（詳細な情報付き）"""
        # 変更ファイルの分析
        change_summary = self._analyze_changes(files_changed)
        
        # コミットメッセージ生成
        commit_message = f"🤖 AI Task #{task_id}: {task_summary}\n\n"
        commit_message += "📝 Changes:\n"
        for category, files in change_summary.items():
            if files:
                commit_message += f"- {category}: {', '.join(files)}\n"
        
        commit_message += f"\n🔧 Task ID: {task_id}\n"
        commit_message += f"⏰ Timestamp: {datetime.now().isoformat()}\n"
        
        try:
            # Git add
            subprocess.run(['git', 'add'] + files_changed, check=True)
            
            # Git commit
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            logger.info("強化コミット成功")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"コミットエラー: {e}")
            return False
    
    def _analyze_changes(self, files: List[str]) -> Dict[str, List[str]]:
        """変更ファイルを分類"""
        categories = {
            'workers': [],
            'libs': [],
            'scripts': [],
            'config': [],
            'other': []
        }
        
        for file in files:
            if 'workers/' in file:
                categories['workers'].append(Path(file).name)
            elif 'libs/' in file:
                categories['libs'].append(Path(file).name)
            elif 'scripts/' in file:
                categories['scripts'].append(Path(file).name)
            elif 'config/' in file:
                categories['config'].append(Path(file).name)
            else:
                categories['other'].append(Path(file).name)
        
        return categories
    
    def create_pull_request(self, title: str, body: str, 
                          base: str = 'main', head: str = None) -> Optional[Dict]:
        """プルリクエストを作成"""
        if not all([self.api_repo_url, self.token]):
            logger.error("GitHub API認証情報が不足")
            return None
        
        # 現在のブランチ名を取得
        if not head:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True
            )
            head = result.stdout.strip() if result.returncode == 0 else None
        
        if not head or head == base:
            logger.error("PRを作成するには別ブランチが必要です")
            return None
        
        url = f"{self.api_repo_url}/pulls"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                pr_data = response.json()
                logger.info(f"PR作成成功: #{pr_data['number']}")
                return pr_data
            else:
                logger.error(f"PR作成失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"PR作成エラー: {e}")
            return None
    
    def get_code_context_for_ai(self, relevant_paths: List[str]) -> str:
        """AIが理解しやすい形式でコードコンテキストを取得"""
        context = "【関連コード情報】\n\n"
        
        for path in relevant_paths:
            content = self.get_file_content(path)
            if content:
                # 重要な部分を抽出（クラス定義、関数定義など）
                important_parts = self._extract_important_parts(content)
                
                context += f"📄 {path}:\n"
                context += f"```python\n{important_parts}\n```\n\n"
        
        # コードベース全体の分析情報も追加
        analysis = self.analyze_codebase()
        context += f"\n【コードベース概要】\n"
        context += f"- 総ファイル数: {analysis['total_files']}\n"
        context += f"- 主要モジュール: {len(analysis['key_modules'])}個\n"
        context += f"- 依存関係: {', '.join(analysis['dependencies'][:10])}\n"
        
        return context
    
    def _extract_important_parts(self, content: str, max_lines: int = 50) -> str:
        """コードから重要な部分を抽出"""
        lines = content.split('\n')
        important_lines = []
        
        in_class = False
        in_function = False
        
        for i, line in enumerate(lines):
            # クラス定義
            if line.strip().startswith('class '):
                in_class = True
                important_lines.append(line)
            # 関数定義
            elif line.strip().startswith('def '):
                in_function = True
                important_lines.append(line)
                # docstringも含める
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    j = i + 1
                    while j < len(lines) and j < i + 10:
                        important_lines.append(lines[j])
                        if lines[j].strip().endswith('"""') and j > i + 1:
                            break
                        j += 1
            
            if len(important_lines) >= max_lines:
                break
        
        return '\n'.join(important_lines[:max_lines])
    
    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """最近のコミットを取得"""
        if not self.api_repo_url:
            return []
        
        url = f"{self.api_repo_url}/commits"
        headers = {'Authorization': f'token {self.token}'} if self.token else {}
        params = {'per_page': limit}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                commits = response.json()
                return [{
                    'sha': c['sha'][:7],
                    'message': c['commit']['message'].split('\n')[0],
                    'author': c['commit']['author']['name'],
                    'date': c['commit']['author']['date']
                } for c in commits]
        except Exception as e:
            logger.error(f"コミット取得エラー: {e}")
        
        return []
