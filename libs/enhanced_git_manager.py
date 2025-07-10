#!/usr/bin/env python3
"""
拡張Git管理マネージャー - 詳細なコミットメッセージ生成機能付き
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
from libs.task_history_db import TaskHistoryDB

class EnhancedGitManager:
    """詳細なコミットメッセージを生成する拡張Git管理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_dir = Path(__file__).parent.parent
        self.task_db = TaskHistoryDB()
        
        # ファイルタイプ別の説明テンプレート
        self.file_descriptions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON設定',
            '.sh': 'シェルスクリプト',
            '.md': 'ドキュメント',
            '.txt': 'テキスト',
            '.conf': '設定ファイル',
            '.yaml': 'YAML設定',
            '.yml': 'YAML設定'
        }
        
        # コンポーネントタイプの判定パターン
        self.component_patterns = {
            'worker': r'.*_worker\.py$',
            'manager': r'.*_manager\.py$',
            'notifier': r'.*_notifier\.py$',
            'config': r'.*\.(conf|json|yaml|yml)$',
            'script': r'.*\.sh$',
            'web': r'.*\.(html|css|js)$',
            'api': r'.*api.*\.py$',
            'test': r'.*(test_|_test).*\.(py|sh)$',
            'lib': r'libs/.*\.py$'
        }
    
    def analyze_file_content(self, file_path: str) -> Dict[str, Any]:
        """ファイル内容を分析して概要を生成"""
        analysis = {
            'type': None,
            'purpose': None,
            'key_features': [],
            'dependencies': [],
            'classes': [],
            'functions': []
        }
        
        try:
            full_path = self.project_dir / file_path
            if not full_path.exists():
                return analysis
            
            # ファイルタイプ判定
            for comp_type, pattern in self.component_patterns.items():
                if re.match(pattern, file_path):
                    analysis['type'] = comp_type
                    break
            
            # Python ファイルの詳細分析
            if file_path.endswith('.py'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # クラス抽出
                classes = re.findall(r'class\s+(\w+)', content)
                analysis['classes'] = classes
                
                # 関数抽出（メソッド除く）
                functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                analysis['functions'] = [f for f in functions if not f.startswith('_')]
                
                # import文から依存関係抽出
                imports = re.findall(r'(?:from|import)\s+([\w.]+)', content)
                analysis['dependencies'] = list(set(imports))
                
                # 目的推定（docstringから）
                docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if docstring_match:
                    purpose = docstring_match.group(1).strip().split('\n')[0]
                    analysis['purpose'] = purpose[:100]
                
                # 主要機能の抽出
                if 'BaseWorker' in content:
                    analysis['key_features'].append('RabbitMQワーカー実装')
                if 'slack' in content.lower():
                    analysis['key_features'].append('Slack通知機能')
                if 'claude' in content.lower():
                    analysis['key_features'].append('Claude API統合')
                if 'git' in content.lower():
                    analysis['key_features'].append('Git操作')
                if 'database' in content.lower() or 'db' in content.lower():
                    analysis['key_features'].append('データベース操作')
                
            # シェルスクリプトの分析
            elif file_path.endswith('.sh'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # コマンド抽出
                if 'ai-' in file_path:
                    analysis['purpose'] = 'Elders Guildコマンドスクリプト'
                
                # 主要コマンドの検出
                if 'docker' in content:
                    analysis['key_features'].append('Docker操作')
                if 'python' in content:
                    analysis['key_features'].append('Python実行')
                if 'git' in content:
                    analysis['key_features'].append('Git操作')
                
        except Exception as e:
            self.logger.error(f"ファイル分析エラー: {e}")
        
        return analysis
    
    def generate_detailed_commit_message(self, task_id: str, files: List[str]) -> str:
        """詳細なコミットメッセージを生成"""
        # タスク情報を取得
        task_info = self.task_db.get_task_by_id(task_id)
        
        # 基本情報
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # タイトル行（50文字以内）
        if task_info:
            # プロンプトから要約を生成
            prompt = task_info.get('prompt', '')
            title_summary = self._extract_title_from_prompt(prompt)
        else:
            title_summary = f"{len(files)}ファイルの追加/更新"
        
        title = f"🤖 [AI] {title_summary}"
        
        # 詳細セクション
        details = []
        
        # タスク情報セクション
        details.append(f"## 📋 タスク情報")
        details.append(f"- **タスクID**: {task_id}")
        details.append(f"- **実行時刻**: {timestamp}")
        
        if task_info:
            details.append(f"- **実行ワーカー**: {task_info.get('worker', 'unknown')}")
            details.append(f"- **使用モデル**: {task_info.get('model', 'unknown')}")
            details.append(f"- **タスクタイプ**: {task_info.get('task_type', 'general')}")
            
            # プロンプトの要約
            prompt = task_info.get('prompt', '')
            if prompt:
                details.append(f"\n### 要求内容")
                # 長いプロンプトは要約
                if len(prompt) > 200:
                    prompt_lines = prompt.split('\n')
                    details.append(f"> {prompt_lines[0][:150]}...")
                    if len(prompt_lines) > 1:
                        details.append(f"> （他{len(prompt_lines)-1}行）")
                else:
                    details.append(f"> {prompt}")
        
        # ファイル変更セクション
        details.append(f"\n## 📁 変更ファイル（{len(files)}件）")
        
        # ファイルをカテゴリ別に分類
        categorized_files = self._categorize_files(files)
        
        for category, category_files in categorized_files.items():
            if category_files:
                details.append(f"\n### {self._get_category_emoji(category)} {self._get_category_name(category)}")
                
                for file_path in category_files:
                    # ファイル分析
                    analysis = self.analyze_file_content(file_path)
                    
                    # ファイル説明
                    file_desc = f"- `{file_path}`"
                    
                    # 詳細情報があれば追加
                    if analysis['purpose']:
                        file_desc += f"\n  - 📝 {analysis['purpose']}"
                    
                    if analysis['classes']:
                        file_desc += f"\n  - 🏗️ クラス: {', '.join(analysis['classes'])}"
                    
                    if analysis['key_features']:
                        file_desc += f"\n  - ✨ 機能: {', '.join(analysis['key_features'])}"
                    
                    details.append(file_desc)
        
        # 技術的詳細セクション
        if task_info and task_info.get('response'):
            details.append(f"\n## 🔧 技術的詳細")
            
            # 応答から技術的なポイントを抽出
            response = task_info.get('response', '')
            tech_points = self._extract_technical_points(response)
            
            if tech_points:
                for point in tech_points[:5]:  # 最大5つまで
                    details.append(f"- {point}")
        
        # AI要約セクション
        if task_info and task_info.get('summary'):
            details.append(f"\n## 🧠 AI要約")
            summary_lines = task_info['summary'].split('\n')
            for line in summary_lines[:3]:  # 最大3行
                if line.strip():
                    details.append(f"> {line.strip()}")
        
        # タグセクション
        tags = self._generate_tags(files, task_info)
        if tags:
            details.append(f"\n## 🏷️ タグ")
            details.append(f"{', '.join(tags)}")
        
        # 最終的なメッセージ組み立て
        commit_message = title + "\n\n" + "\n".join(details)
        
        return commit_message
    
    def _extract_title_from_prompt(self, prompt: str) -> str:
        """プロンプトからタイトルを抽出"""
        # 最初の行や主要なキーワードを抽出
        lines = prompt.strip().split('\n')
        first_line = lines[0] if lines else prompt
        
        # 長すぎる場合は短縮
        if len(first_line) > 40:
            # 重要なキーワードを探す
            keywords = re.findall(r'\b(?:作成|実装|追加|修正|更新|生成|構築)\b.*?(?:[をのに]|$)', first_line)
            if keywords:
                return keywords[0][:40] + "..."
            else:
                return first_line[:40] + "..."
        
        return first_line
    
    def _categorize_files(self, files: List[str]) -> Dict[str, List[str]]:
        """ファイルをカテゴリ別に分類"""
        categories = {
            'workers': [],
            'managers': [],
            'configs': [],
            'scripts': [],
            'web': [],
            'libs': [],
            'tests': [],
            'docs': [],
            'others': []
        }
        
        for file_path in files:
            categorized = False
            
            # ディレクトリベースの分類
            if 'workers/' in file_path:
                categories['workers'].append(file_path)
                categorized = True
            elif 'libs/' in file_path and file_path.endswith('_manager.py'):
                categories['managers'].append(file_path)
                categorized = True
            elif 'libs/' in file_path:
                categories['libs'].append(file_path)
                categorized = True
            elif 'config/' in file_path or file_path.endswith('.conf'):
                categories['configs'].append(file_path)
                categorized = True
            elif 'scripts/' in file_path or file_path.endswith('.sh'):
                categories['scripts'].append(file_path)
                categorized = True
            elif 'web/' in file_path or file_path.endswith(('.html', '.css', '.js')):
                categories['web'].append(file_path)
                categorized = True
            elif 'test' in file_path.lower():
                categories['tests'].append(file_path)
                categorized = True
            elif file_path.endswith('.md'):
                categories['docs'].append(file_path)
                categorized = True
            
            if not categorized:
                categories['others'].append(file_path)
        
        # 空のカテゴリを削除
        return {k: v for k, v in categories.items() if v}
    
    def _get_category_emoji(self, category: str) -> str:
        """カテゴリに対応する絵文字を取得"""
        emojis = {
            'workers': '⚙️',
            'managers': '📊',
            'configs': '🔧',
            'scripts': '📜',
            'web': '🌐',
            'libs': '📚',
            'tests': '🧪',
            'docs': '📝',
            'others': '📄'
        }
        return emojis.get(category, '📄')
    
    def _get_category_name(self, category: str) -> str:
        """カテゴリの日本語名を取得"""
        names = {
            'workers': 'ワーカー',
            'managers': 'マネージャー',
            'configs': '設定ファイル',
            'scripts': 'スクリプト',
            'web': 'Web関連',
            'libs': 'ライブラリ',
            'tests': 'テスト',
            'docs': 'ドキュメント',
            'others': 'その他'
        }
        return names.get(category, 'その他')
    
    def _extract_technical_points(self, response: str) -> List[str]:
        """応答から技術的なポイントを抽出"""
        points = []
        
        # 技術的なキーワードを含む行を抽出
        tech_keywords = [
            'class', 'def', 'import', 'async', 'await',
            'API', 'データベース', 'キュー', 'ワーカー',
            '実装', '処理', '機能', '統合', '自動'
        ]
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in tech_keywords) and len(line) < 100:
                # 不要な記号を除去
                clean_line = re.sub(r'^[#\-*・]+\s*', '', line)
                if clean_line and not clean_line.startswith('```'):
                    points.append(clean_line)
        
        return points[:10]  # 最大10個
    
    def _generate_tags(self, files: List[str], task_info: Optional[Dict]) -> List[str]:
        """タグを生成"""
        tags = set()
        
        # ファイルタイプベースのタグ
        for file_path in files:
            if file_path.endswith('.py'):
                tags.add('#python')
            elif file_path.endswith('.sh'):
                tags.add('#shell')
            elif file_path.endswith(('.html', '.css', '.js')):
                tags.add('#web')
            
            # コンポーネントタイプのタグ
            if '_worker.py' in file_path:
                tags.add('#worker')
            elif '_manager.py' in file_path:
                tags.add('#manager')
        
        # タスク情報ベースのタグ
        if task_info:
            task_type = task_info.get('task_type', '')
            if task_type:
                tags.add(f'#{task_type}')
            
            # プロンプトからキーワード抽出
            prompt = task_info.get('prompt', '').lower()
            if 'api' in prompt:
                tags.add('#api')
            if 'データベース' in prompt or 'db' in prompt:
                tags.add('#database')
            if 'テスト' in prompt or 'test' in prompt:
                tags.add('#test')
        
        return sorted(list(tags))
