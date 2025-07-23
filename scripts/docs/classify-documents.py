#!/usr/bin/env python3
"""
エルダーズギルド ドキュメント分類自動化スクリプト
エルダー評議会令第500号実装ツール

機能:
1. 既存ドキュメントの自動分類
2. 新ディレクトリ構造への移動
3. 命名規則適用
4. メタデータ自動生成
"""

import os
import re
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
from dataclasses import dataclass

@dataclass
class DocumentInfo:
    """ドキュメント情報"""
    path: Path
    category: str
    subcategory: str
    new_path: Path
    title: str
    audience: str
    difficulty: str
    status: str

class DocumentClassifier:
    """ドキュメント分類器"""
    
    def __init__(self, base_path: str = "/home/aicompany/ai_co"):
        self.base_path = Path(base_path)
        self.docs_path = self.base_path / "docs"
        
        # 分類ルール定義
        self.classification_rules = {
            # ガイド系
            "guides": {
                "patterns": [
                    r".*guide.*\.md$",
                    r".*quickstart.*\.md$", 
                    r".*tutorial.*\.md$",
                    r".*howto.*\.md$",
                    r".*usage.*\.md$"
                ],
                "subcategories": {
                    "user-guides": ["quickstart", "basic", "beginner", "user"],
                    "developer-guides": ["development", "developer", "coding", "contribution"],
                    "administrator-guides": ["admin", "deployment", "maintenance", "security"],
                    "workflow-guides": ["workflow", "process", "github", "git"]
                }
            },
            
            # 技術文書
            "technical": {
                "patterns": [
                    r".*architecture.*\.md$",
                    r".*design.*\.md$",
                    r".*specification.*\.md$",
                    r".*implementation.*\.md$",
                    r".*technical.*\.md$",
                    r".*system.*\.md$"
                ],
                "subcategories": {
                    "architecture": ["architecture", "system", "component", "overview"],
                    "implementation": ["implementation", "elder-tree", "four-sages", "unified"],
                    "specifications": ["spec", "requirements", "functional", "interface"],
                    "deployment": ["deployment", "infrastructure", "monitoring", "logging"]
                }
            },
            
            # レポート
            "reports": {
                "patterns": [
                    r".*report.*\.md$",
                    r".*analysis.*\.md$",
                    r".*completion.*\.md$",
                    r".*summary.*\.md$",
                    r".*audit.*\.md$",
                    r".*benchmark.*\.md$"
                ],
                "subcategories": {
                    "development": ["completion", "progress", "sprint", "milestone"],
                    "quality": ["quality", "coverage", "audit", "security"],
                    "analysis": ["analysis", "impact", "risk", "cost"],
                    "operations": ["incident", "maintenance", "usage", "capacity"]
                }
            },
            
            # ポリシー
            "policies": {
                "patterns": [
                    r".*policy.*\.md$",
                    r".*standard.*\.md$",
                    r".*rule.*\.md$",
                    r".*regulation.*\.md$",
                    r".*protocol.*\.md$"
                ],
                "subcategories": {
                    "development": ["coding", "testing", "review", "workflow"],
                    "quality": ["quality", "iron-will", "oss", "security"],
                    "operations": ["deployment", "incident", "backup", "monitoring"],
                    "governance": ["council", "decision", "escalation", "compliance"]
                }
            },
            
            # API
            "api": {
                "patterns": [
                    r".*api.*\.md$",
                    r".*reference.*\.md$",
                    r".*schema.*\.md$",
                    r".*endpoint.*\.md$"
                ],
                "subcategories": {
                    "reference": ["reference", "api", "rest", "graphql"],
                    "guides": ["getting-started", "authentication", "rate-limiting"],
                    "schemas": ["schema", "openapi", "json", "proto"],
                    "examples": ["examples", "samples", "curl", "sdk"]
                }
            }
        }
        
        # 特別な処理が必要なファイル
        self.special_files = {
            "README.md": "root",
            "CLAUDE.md": "root", 
            "CHANGELOG.md": "root",
            "CONTRIBUTING.md": "root",
            "LICENSE": "root"
        }
    
    def classify_document(self, file_path: Path) -> Optional[DocumentInfo]:
        """ドキュメントの分類"""
        if not file_path.suffix == '.md':
            return None
            
        # 特別なファイルのチェック
        if file_path.name in self.special_files:
            return None  # ルートファイルはそのまま
        
        content = self._read_file_content(file_path)
        title = self._extract_title(content)
        
        # 分類ルールの適用
        for category, rules in self.classification_rules.items():
            if self._matches_patterns(file_path.name, rules["patterns"]):
                subcategory = self._determine_subcategory(file_path, content, rules["subcategories"])
                
                # 新しいパスの生成
                new_filename = self._generate_filename(file_path.name, category, subcategory)
                new_path = self.docs_path / category / subcategory / new_filename
                
                return DocumentInfo(
                    path=file_path,
                    category=category,
                    subcategory=subcategory,
                    new_path=new_path,
                    title=title,
                    audience=self._determine_audience(content, category),
                    difficulty=self._determine_difficulty(content),
                    status="approved"  # デフォルト
                )
        
        # デフォルト分類
        return self._default_classification(file_path, content, title)
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """パターンマッチング"""
        filename_lower = filename.lower()
        for pattern in patterns:
            if re.match(pattern, filename_lower):
                return True
        return False
    
    def _determine_subcategory(self, file_path: Path, content: str, subcategories: Dict[str, List[str]]) -> str:
        """サブカテゴリの決定"""
        filename_lower = file_path.name.lower()
        content_lower = content.lower()
        
        # ファイル名とコンテンツからキーワードを検索
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                if keyword in filename_lower or keyword in content_lower:
                    return subcategory
        
        # デフォルトは最初のサブカテゴリ
        return list(subcategories.keys())[0]
    
    def _determine_audience(self, content: str, category: str) -> str:
        """対象読者の決定"""
        content_lower = content.lower()
        
        if "administrator" in content_lower or "admin" in content_lower:
            return "administrators"
        elif "developer" in content_lower or "development" in content_lower:
            return "developers"
        elif "user" in content_lower and "guide" in content_lower:
            return "users"
        elif category == "api":
            return "developers"
        elif category == "policies":
            return "all"
        else:
            return "developers"  # デフォルト
    
    def _determine_difficulty(self, content: str) -> str:
        """難易度の決定"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["quickstart", "beginner", "getting started", "basic"]):
            return "beginner"
        elif any(word in content_lower for word in ["advanced", "expert", "complex", "sophisticated"]):
            return "advanced"
        else:
            return "intermediate"
    
    def _generate_filename(self, original_name: str, category: str, subcategory: str) -> str:
        """ファイル名の生成（命名規則適用）"""
        # 既に適切な命名規則の場合はそのまま
        if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*\.md$', original_name.lower()):
            return original_name.lower()
        
        # ファイル名をクリーンアップ
        name = original_name.replace('.md', '')
        # 特殊文字を削除してハイフンに置換
        name = re.sub(r'[^a-zA-Z0-9\s_-]', '', name)
        name = re.sub(r'[\s_]+', '-', name)
        name = name.lower().strip('-')
        
        return f"{name}.md"
    
    def _extract_title(self, content: str) -> str:
        """タイトルの抽出"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled Document"
    
    def _read_file_content(self, file_path: Path) -> str:
        """ファイル内容の読み込み"""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding='cp932')
            except:
                return file_path.read_text(encoding='latin-1')
    
    def _default_classification(self, file_path: Path, content: str, title: str) -> DocumentInfo:
        """デフォルト分類"""
        # プロジェクト関連かどうかの判定
        if any(word in file_path.name.lower() for word in ["project", "issue", "plan"]):
            category = "projects"
            subcategory = "active"
        else:
            category = "technical"
            subcategory = "research"
        
        new_filename = self._generate_filename(file_path.name, category, subcategory)
        new_path = self.docs_path / category / subcategory / new_filename
        
        return DocumentInfo(
            path=file_path,
            category=category,
            subcategory=subcategory,
            new_path=new_path,
            title=title,
            audience=self._determine_audience(content, category),
            difficulty=self._determine_difficulty(content),
            status="draft"  # デフォルトはドラフト
        )
    
    def generate_metadata(self, doc_info: DocumentInfo, content: str) -> str:
        """メタデータの生成"""
        metadata = {
            'title': doc_info.title,
            'description': self._extract_description(content),
            'category': doc_info.category,
            'subcategory': doc_info.subcategory,
            'audience': doc_info.audience,
            'difficulty': doc_info.difficulty,
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'version': '1.0.0',
            'status': doc_info.status,
            'related_docs': [],
            'dependencies': [],
            'author': 'claude-elder',
            'reviewers': [],
            'tags': self._generate_tags(content, doc_info.category)
        }
        
        yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_content}---\n\n{content}"
    
    def _extract_description(self, content: str) -> str:
        """説明文の抽出"""
        lines = content.split('\n')
        description_lines = []
        in_description = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                in_description = True
                continue
            elif line.startswith('#'):
                break
            elif in_description and line and not line.startswith('**'):
                description_lines.append(line)
                if not (len(' '.join(description_lines)) > 200:  # 200文字制限):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if len(' '.join(description_lines)) > 200:  # 200文字制限
                    break
        
        description = ' '.join(description_lines)[:200]
        return description if description else "No description available"
    
    def _generate_tags(self, content: str, category: str) -> List[str]:
        """タグの生成"""
        tags = [category]
        content_lower = content.lower()
        
        # 技術タグ
        tech_tags = {
            'python': 'python',
            'docker': 'docker', 
            'postgres': 'postgresql',
            'redis': 'redis',
            'a2a': 'a2a-protocol',
            'elder tree': 'elder-tree',
            'four sages': 'four-sages',
            'tdd': 'tdd',
            'pytest': 'testing'
        }
        
        for keyword, tag in tech_tags.items():
            if keyword in content_lower:
                tags.append(tag)
        
        return list(set(tags))  # 重複除去
    
    def create_directory_structure(self):
        """新しいディレクトリ構造の作成"""
        categories = {
            'guides': ['user-guides', 'developer-guides', 'administrator-guides', 'workflow-guides'],
            'technical': ['architecture', 'implementation', 'specifications', 'deployment', 'research'],
            'reports': ['development', 'quality', 'analysis', 'operations'],
            'policies': ['development', 'quality', 'operations', 'governance'],
            'api': ['reference', 'guides', 'schemas', 'examples'],
            'projects': ['active', 'completed', 'planning']
        }
        
        for category, subcategories in categories.items():
            for subcategory in subcategories:
        # 繰り返し処理
                path = self.docs_path / category / subcategory
                path.mkdir(parents=True, exist_ok=True)
    
    def classify_and_move(self, dry_run: bool = True, add_metadata: bool = True) -> Dict[str, List[str]]:
        """ドキュメントの分類と移動"""
        results = {
            'moved': [],
            'skipped': [],
            'errors': []
        }
        
        # ディレクトリ構造作成
        if not dry_run:
            self.create_directory_structure()
        
        # 既存のMarkdownファイルを検索
        md_files = []
        for pattern in ["**/*.md", "*.md"]:
            md_files.extend(self.base_path.glob(pattern))
        
        # 既存のdocs配下は除外
        md_files = [f for f in md_files if not str(f).startswith(str(self.docs_path))]
        
        for file_path in md_files:
        # 繰り返し処理
            try:
                doc_info = self.classify_document(file_path)
                if doc_info is None:
                    results['skipped'].append(str(file_path))
                    continue
                
                # ディレクトリ作成
                if not dry_run:
                    doc_info.new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイル移動とメタデータ追加
                if not dry_run:
                    content = self._read_file_content(file_path)
                    
                    if add_metadata:
                        content = self.generate_metadata(doc_info, content)
                    
                    # 既存ファイルがある場合は番号を追加
                    final_path = doc_info.new_path
                    counter = 1
                    while final_path.exists():
                        stem = doc_info.new_path.stem
                        suffix = doc_info.new_path.suffix
                        final_path = doc_info.new_path.parent / f"{stem}-{counter}{suffix}"
                        counter += 1
                    
                    # ファイル移動
                    shutil.move(str(file_path), str(final_path))
                    
                    # 内容更新
                    if add_metadata:
                        final_path.write_text(content, encoding='utf-8')
                
                results['moved'].append(f"{file_path} -> {doc_info.new_path}")
                
            except Exception as e:
                results['errors'].append(f"Error processing {file_path}: {str(e)}")
        
        return results

def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description='エルダーズギルド ドキュメント分類ツール')
    parser.add_argument('--dry-run', action='store_true', help='実際の移動は行わない（テスト実行）')
    parser.add_argument('--no-metadata', action='store_true', help='メタデータを追加しない')
    parser.add_argument('--base-path', default='/home/aicompany/ai_co', help='ベースパス')
    
    args = parser.parse_args()
    
    classifier = DocumentClassifier(args.base_path)
    
    print("🏛️ エルダーズギルド ドキュメント分類開始")
    print(f"ベースパス: {args.base_path}")
    print(f"ドライラン: {'有効' if args.dry_run else '無効'}")
    print(f"メタデータ追加: {'無効' if args.no_metadata else '有効'}")
    print()
    
    results = classifier.classify_and_move(
        dry_run=args.dry_run,
        add_metadata=not args.no_metadata
    )
    
    print("📊 実行結果:")
    print(f"移動対象: {len(results['moved'])}ファイル")
    print(f"スキップ: {len(results['skipped'])}ファイル")
    print(f"エラー: {len(results['errors'])}ファイル")
    
    if results['moved']:
        print("\n✅ 移動されたファイル:")
        for item in results['moved'][:10]:  # 最初の10件のみ表示
            print(f"  {item}")
        if len(results['moved']) > 10:
            print(f"  ... および {len(results['moved']) - 10}ファイル")
    
    if results['errors']:
        print("\n❌ エラー:")
        for error in results['errors']:
            print(f"  {error}")
    
    print(f"\n🎯 分類完了: {'テストモード' if args.dry_run else '実際に実行'}")

if __name__ == "__main__":
    main()