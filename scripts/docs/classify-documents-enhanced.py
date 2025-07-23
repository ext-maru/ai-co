#!/usr/bin/env python3
"""
エルダーズギルド ドキュメント分類自動化スクリプト v2.0
エルダー評議会令第501号実装 - Iron Will完全準拠版

機能:
1. セキュアなドキュメント分類（パストラバーサル対策）
2. 4賢者システム完全統合
3. 堅牢なエラーハンドリング
4. 包括的テストカバレッジ対応
"""

import os
import re
import shutil
import yaml
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
import argparse
from dataclasses import dataclass
import tempfile

# セキュリティ強化
import stat
from urllib.parse import unquote

# 4賢者システム統合
try:
    import sys
    sys.path.append('/home/aicompany/ai_co')
    from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage
    from libs.four_sages.task.task_sage import TaskSage
    from libs.four_sages.incident.incident_sage import IncidentSage
    from libs.four_sages.rag.rag_sage import RAGSage
    FOUR_SAGES_AVAILABLE = True
except ImportError:
    FOUR_SAGES_AVAILABLE = False

# Iron Will遵守項目
FORBIDDEN_PATTERNS = ["TODO", "FIXME", "HACK", "XXX", "TEMP"]
SECURITY_RISK_PATTERNS = [
    r"eval\s*\(",
    r"exec\s*\(",
    r"os\.system\s*\(",
    r"subprocess\.",
    r"__import__\s*\(",
    r"getattr\s*\(",
    r"setattr\s*\(",
]

@dataclass
class DocumentInfo:
    """ドキュメント情報（セキュア版）"""
    path: Path
    category: str
    subcategory: str
    new_path: Path
    title: str
    audience: str
    difficulty: str
    status: str
    sage_assignment: Optional[str] = None
    security_score: float = 100.0
    iron_will_compliant: bool = True

@dataclass
class ClassificationResult:
    """分類結果"""
    total_files: int = 0
    processed_files: int = 0
    moved_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    security_violations: int = 0
    iron_will_violations: int = 0
    sage_assignments: Dict[str, int] = None

    def __post_init__(self):
        if self.sage_assignments is None:
            self.sage_assignments = {}

class SecureDocumentClassifier:
    """セキュア・ドキュメント分類器（Iron Will準拠）"""
    
    def __init__(self, base_path: str = "/home/aicompany/ai_co"):
        self.base_path = Path(base_path).resolve()  # 絶対パス化
        self.docs_path = self.base_path / "docs"
        
        # セキュリティ設定
        self.max_file_size = 50 * 1024 * 1024  # 50MB制限
        self.allowed_extensions = {'.md', '.txt', '.rst'}
        self.forbidden_chars = {'..', '~', '$', '|', ';', '&'}
        
        # ログ設定
        self._setup_logging()
        
        # 4賢者システム初期化
        self._initialize_four_sages()
        
        # 分類ルール定義（4賢者割り当て含む）
        self.classification_rules = {
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
                },
                "sage": "knowledge_sage"
            },
            
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
                    "deployment": ["deployment", "infrastructure", "monitoring", "logging"],
                    "research": ["research", "investigation", "analysis", "study"]
                },
                "sage": "rag_sage"
            },
            
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
                },
                "sage": "task_sage"
            },
            
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
                },
                "sage": "incident_sage"
            },
            
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
                },
                "sage": "rag_sage"
            },
            
            "projects": {
                "patterns": [
                    r".*project.*\.md$",
                    r".*plan.*\.md$",
                    r".*proposal.*\.md$",
                    r".*issue.*\.md$"
                ],
                "subcategories": {
                    "active": ["active", "current", "ongoing"],
                    "completed": ["completed", "finished", "done"],
                    "planning": ["planning", "proposal", "draft", "design"]
                },
                "sage": "task_sage"
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
        
        self.logger.info("SecureDocumentClassifier初期化完了")
        self.logger.info(f"4賢者システム: {'有効' if FOUR_SAGES_AVAILABLE else '無効'}")
    
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('docs_classification.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('DocumentClassifier')
    
    def _initialize_four_sages(self):
        """4賢者システム初期化"""
        self.sages = {}
        if FOUR_SAGES_AVAILABLE:
            try:
                self.sages = {
                    'knowledge_sage': KnowledgeSage('knowledge_sage'),
                    'task_sage': TaskSage('task_sage'),
                    'incident_sage': IncidentSage('incident_sage'),
                    'rag_sage': RAGSage('rag_sage')
                }
                self.logger.info("4賢者システム初期化成功")
            except Exception as e:
                self.logger.error(f"4賢者システム初期化失敗: {e}")
                self.sages = {}
        else:
            self.logger.warning("4賢者システムモジュール未検出")
    
    def validate_security(self, file_path: Path, content: str) -> Tuple[bool, List[str], float]:
        """セキュリティ検証（Iron Will準拠）"""
        violations = []
        security_score = 100.0
        
        # 1. パス検証
        try:
            resolved_path = file_path.resolve()
            if not str(resolved_path).startswith(str(self.base_path)):
                violations.append(f"パストラバーサル検出: {file_path}")
                security_score -= 50
        except (OSError, ValueError) as e:
            violations.append(f"パス解決エラー: {e}")
            security_score -= 30
        
        # 2. ファイル名検証
        filename = file_path.name
        for forbidden_char in self.forbidden_chars:
            if forbidden_char in filename:
                violations.append(f"禁止文字検出: {forbidden_char} in {filename}")
                security_score -= 20
        
        # 3. ファイルサイズ検証
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                violations.append(f"ファイルサイズ超過: {file_size} > {self.max_file_size}")
                security_score -= 25
        except OSError:
            pass  # ファイル存在しない場合はスキップ
        
        # 4. 拡張子検証
        if file_path.suffix.lower() not in self.allowed_extensions:
            violations.append(f"許可されていない拡張子: {file_path.suffix}")
            security_score -= 15
        
        # 5. コンテンツセキュリティスキャン
        for pattern in SECURITY_RISK_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"セキュリティリスクパターン検出: {pattern}")
                security_score -= 30
        
        # 6. Iron Will基準チェック
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in content:
                violations.append(f"Iron Will違反: {pattern} found")
                security_score -= 10
        
        is_secure = len(violations) == 0 and security_score >= 70
        return is_secure, violations, max(0, security_score)
    
    def secure_path_join(self, base_path: Path, *paths: str) -> Optional[Path]:
        """セキュアなパス結合"""
        try:
            # パス正規化
            normalized_paths = []
            for path in paths:
                # URLデコード
                decoded = unquote(path)
                # 危険な文字を除去
                cleaned = re.sub(r'[<>:"|?*]', '', decoded)
                # 相対パス要素を除去
                parts = []
                for part in cleaned.split('/'):
                    if part and part not in {'..', '.', '~'}:
                        parts.append(part)
                if parts:
                    normalized_paths.extend(parts)
            
            if not normalized_paths:
                return None
            
            # パス結合
            result_path = base_path
            for part in normalized_paths:
                result_path = result_path / part
            
            # 最終検証
            resolved = result_path.resolve()
            if not str(resolved).startswith(str(base_path.resolve())):
                self.logger.warning(f"パストラバーサル試行を阻止: {result_path}")
                return None
            
            return resolved
            
        except Exception as e:
            self.logger.error(f"セキュアパス結合エラー: {e}")
            return None
    
    def classify_document(self, file_path: Path) -> Optional[DocumentInfo]:
        """セキュアなドキュメント分類"""
        try:
            # セキュリティ事前チェック
            if file_path.suffix != '.md':
                return None
            
            # 特別ファイルチェック
            if file_path.name in self.special_files:
                return None
            
            # ファイル読み込み
            try:
                content = self._read_file_content(file_path)
            except Exception as e:
                self.logger.error(f"ファイル読み込みエラー {file_path}: {e}")
                return None
            
            # セキュリティ検証
            is_secure, violations, security_score = self.validate_security(file_path, content)
            if not is_secure:
                self.logger.warning(f"セキュリティ検証失敗 {file_path}: {violations}")
                # セキュリティ違反でも分類は継続（記録目的）
            
            title = self._extract_title(content)
            
            # 分類実行
            for category, rules in self.classification_rules.items():
                if self._matches_patterns(file_path.name, rules["patterns"]):
                    subcategory = self._determine_subcategory(file_path, content, rules["subcategories"])
                    
                    # セキュアな新パス生成
                    new_filename = self._generate_secure_filename(file_path.name, category, subcategory)
                    new_path = self.secure_path_join(self.docs_path, category, subcategory, new_filename)
                    
                    if new_path is None:
                        self.logger.error(f"セキュアパス生成失敗: {file_path}")
                        return None
                    
                    return DocumentInfo(
                        path=file_path,
                        category=category,
                        subcategory=subcategory,
                        new_path=new_path,
                        title=title,
                        audience=self._determine_audience(content, category),
                        difficulty=self._determine_difficulty(content),
                        status="approved" if is_secure else "security_review",
                        sage_assignment=rules.get("sage"),
                        security_score=security_score,
                        iron_will_compliant=len([v for v in violations if "Iron Will" in v]) == 0
                    )
            
            # デフォルト分類
            return self._default_secure_classification(file_path, content, title, security_score, violations)
            
        except Exception as e:
            self.logger.error(f"ドキュメント分類エラー {file_path}: {e}")
            return None
    
    def _generate_secure_filename(self, original_name: str, category: str, subcategory: str) -> str:
        """セキュアなファイル名生成"""
        # 危険文字除去
        safe_name = re.sub(r'[<>:"|?*\\]', '', original_name)
        safe_name = safe_name.replace('..', '').replace('~', '')
        
        # 基本クリーンアップ
        name = safe_name.replace('.md', '')
        name = re.sub(r'[^a-zA-Z0-9\s_-]', '', name)
        name = re.sub(r'[\s_]+', '-', name)
        name = name.lower().strip('-')
        
        # 長さ制限
        if len(name) > 100:
            name = name[:100]
        
        # 空の場合はフォールバック
        if not name:
            name = f"document-{hashlib.md5(original_name.encode()).hexdigest()[:8]}"
        
        return f"{name}.md"
    
    def _default_secure_classification(self, file_path: Path, content: str, title: str, 
                                     security_score: float, violations: List[str]) -> DocumentInfo:
        """セキュアなデフォルト分類"""
        # プロジェクト関連判定
        if any(word in file_path.name.lower() for word in ["project", "issue", "plan"]):
            category = "projects"
            subcategory = "planning"  # セキュリティ上安全なデフォルト
            sage = "task_sage"
        else:
            category = "technical"
            subcategory = "research"
            sage = "rag_sage"
        
        new_filename = self._generate_secure_filename(file_path.name, category, subcategory)
        new_path = self.secure_path_join(self.docs_path, category, subcategory, new_filename)
        
        if new_path is None:
            # フォールバック: tempディレクトリ
            temp_dir = self.docs_path / "temp" / "security_review"
            new_path = temp_dir / new_filename
        
        return DocumentInfo(
            path=file_path,
            category=category,
            subcategory=subcategory,
            new_path=new_path,
            title=title,
            audience=self._determine_audience(content, category),
            difficulty=self._determine_difficulty(content),
            status="security_review" if violations else "draft",
            sage_assignment=sage,
            security_score=security_score,
            iron_will_compliant=len([v for v in violations if "Iron Will" in v]) == 0
        )
    
    def secure_move_file(self, source: Path, destination: Path) -> bool:
        """セキュアなファイル移動"""
        try:
            # 移動前検証
            if not source.exists():
                self.logger.error(f"移動元ファイル不存在: {source}")
                return False
            
            if not source.is_file():
                self.logger.error(f"移動元がファイルでない: {source}")
                return False
            
            # 移動先ディレクトリ作成
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # 移動先重複チェック
            final_destination = destination
            counter = 1
            while final_destination.exists():
                stem = destination.stem
                suffix = destination.suffix
                final_destination = destination.parent / f"{stem}-{counter:03d}{suffix}"
                counter += 1
                if counter > 999:  # 無限ループ防止
                    self.logger.error(f"移動先ファイル名生成失敗（重複多数）: {destination}")
                    return False
            
            # 権限チェック
            source_stat = source.stat()
            if not (source_stat.st_mode & stat.S_IREAD):
                self.logger.error(f"読み取り権限なし: {source}")
                return False
            
            # 原子的移動実行
            temp_destination = final_destination.with_suffix('.tmp')
            try:
                # 一時ファイルにコピー
                shutil.copy2(source, temp_destination)
                
                # 移動先にリネーム（原子的）
                temp_destination.rename(final_destination)
                
                # 移動元削除
                source.unlink()
                
                self.logger.info(f"ファイル移動成功: {source} -> {final_destination}")
                return True
                
            except Exception as e:
                # クリーンアップ
                if temp_destination.exists():
                    temp_destination.unlink()
                raise e
        
        except Exception as e:
            self.logger.error(f"セキュアファイル移動エラー {source} -> {destination}: {e}")
            return False
    
    def notify_four_sages(self, doc_info: DocumentInfo, operation: str) -> bool:
        """4賢者への通知"""
        if not self.sages or not doc_info.sage_assignment:
            return False
        
        try:
            sage = self.sages.get(doc_info.sage_assignment)
            if not sage:
                return False
            
            notification_data = {
                "operation": operation,
                "document_path": str(doc_info.new_path),
                "category": doc_info.category,
                "subcategory": doc_info.subcategory,
                "title": doc_info.title,
                "security_score": doc_info.security_score,
                "iron_will_compliant": doc_info.iron_will_compliant,
                "timestamp": datetime.now().isoformat()
            }
            
            # 賢者への通知実行（実装は賢者側に依存）
            if hasattr(sage, 'notify_document_change'):
                sage.notify_document_change(notification_data)
            
            self.logger.info(f"4賢者通知成功: {doc_info.sage_assignment} - {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"4賢者通知エラー: {e}")
            return False
    
    def classify_and_move_secure(self, dry_run: bool = True, add_metadata: bool = True) -> ClassificationResult:
        """セキュアな分類・移動処理"""
        result = ClassificationResult()
        
        try:
            # ディレクトリ構造作成
            if not dry_run:
                self.create_directory_structure()
            
            # Markdownファイル検索
            md_files = []
            for pattern in ["**/*.md", "*.md"]:
                found_files = list(self.base_path.glob(pattern))
                # セキュリティフィルタリング
                for f in found_files:
                    try:
                        resolved = f.resolve()
                        if str(resolved).startswith(str(self.base_path)) and not str(resolved).startswith(str(self.docs_path)):
                            md_files.append(resolved)
                    except Exception as e:
                        self.logger.warning(f"ファイルパス解決エラー {f}: {e}")
            
            result.total_files = len(md_files)
            
            # 各ファイル処理
            for file_path in md_files:
                try:
                    result.processed_files += 1
                    
                    doc_info = self.classify_document(file_path)
                    if doc_info is None:
                        result.skipped_files += 1
                        continue
                    
                    # セキュリティ違反カウント
                    if doc_info.security_score < 70:
                        result.security_violations += 1
                    
                    if not doc_info.iron_will_compliant:
                        result.iron_will_violations += 1
                    
                    # 賢者割り当てカウント
                    if doc_info.sage_assignment:
                        result.sage_assignments[doc_info.sage_assignment] = result.sage_assignments.get(doc_info.sage_assignment, 0) + 1
                    
                    if not dry_run:
                        # セキュアファイル移動
                        if self.secure_move_file(file_path, doc_info.new_path):
                            result.moved_files += 1
                            
                            # メタデータ追加
                            if add_metadata:
                                content = self._read_file_content(doc_info.new_path)
                                enhanced_content = self.generate_metadata(doc_info, content)
                                doc_info.new_path.write_text(enhanced_content, encoding='utf-8')
                            
                            # 4賢者通知
                            self.notify_four_sages(doc_info, "document_moved")
                        else:
                            result.error_files += 1
                    else:
                        result.moved_files += 1  # ドライランでは成功として扱う
                
                except Exception as e:
                    self.logger.error(f"ファイル処理エラー {file_path}: {e}")
                    result.error_files += 1
            
            self.logger.info(f"分類処理完了: {result.processed_files}/{result.total_files} files")
            
        except Exception as e:
            self.logger.error(f"分類・移動処理エラー: {e}")
        
        return result
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """パターンマッチング（セキュア版）"""
        filename_lower = filename.lower()
        for pattern in patterns:
            try:
                if re.match(pattern, filename_lower):
                    return True
            except re.error as e:
                self.logger.warning(f"正規表現エラー {pattern}: {e}")
        return False
    
    def _determine_subcategory(self, file_path: Path, content: str, subcategories: Dict[str, List[str]]) -> str:
        """サブカテゴリ決定（セキュア版）"""
        filename_lower = file_path.name.lower()
        # コンテンツサイズ制限（DoS対策）
        content_lower = content[:10000].lower()  # 最初の10KB
        
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                if keyword in filename_lower or keyword in content_lower:
                    return subcategory
        
        return list(subcategories.keys())[0]
    
    def _determine_audience(self, content: str, category: str) -> str:
        """対象読者決定"""
        content_lower = content[:5000].lower()  # サイズ制限
        
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
            return "developers"
    
    def _determine_difficulty(self, content: str) -> str:
        """難易度決定"""
        content_lower = content[:5000].lower()
        
        if any(word in content_lower for word in ["quickstart", "beginner", "getting started", "basic"]):
            return "beginner"
        elif any(word in content_lower for word in ["advanced", "expert", "complex", "sophisticated"]):
            return "advanced"
        else:
            return "intermediate"
    
    def _extract_title(self, content: str) -> str:
        """タイトル抽出"""
        lines = content.split('\n')[:10]  # 最初の10行のみ
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                title = line[2:].strip()
                # セキュリティクリーンアップ
                return re.sub(r'[<>:"|?*\\]', '', title)[:100]
        return "Untitled Document"
    
    def _read_file_content(self, file_path: Path) -> str:
        """セキュアなファイル読み込み"""
        try:
            # ファイルサイズチェック
            if file_path.stat().st_size > self.max_file_size:
                raise ValueError(f"File too large: {file_path.stat().st_size}")
            
            # エンコーディング自動判定・読み込み
            for encoding in ['utf-8', 'cp932', 'latin-1']:
                try:
                    return file_path.read_text(encoding=encoding)
                except UnicodeDecodeError:
                    continue
            
            # すべて失敗した場合はエラー
            raise UnicodeDecodeError("All encodings failed")
            
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー {file_path}: {e}")
            return ""
    
    def generate_metadata(self, doc_info: DocumentInfo, content: str) -> str:
        """強化されたメタデータ生成"""
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
            'tags': self._generate_tags(content, doc_info.category),
            # セキュリティ・品質情報
            'security_score': doc_info.security_score,
            'iron_will_compliant': doc_info.iron_will_compliant,
            'sage_assignment': doc_info.sage_assignment,
            'classification_date': datetime.now().isoformat()
        }
        
        yaml_content = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_content}---\n\n{content}"
    
    def _extract_description(self, content: str) -> str:
        """説明抽出（セキュア版）"""
        lines = content.split('\n')[:20]  # 最初の20行
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
                # セキュリティクリーンアップ
                clean_line = re.sub(r'[<>:"|?*\\]', '', line)
                description_lines.append(clean_line)
                if len(' '.join(description_lines)) > 200:
                    break
        
        description = ' '.join(description_lines)[:200]
        return description if description else "No description available"
    
    def _generate_tags(self, content: str, category: str) -> List[str]:
        """タグ生成（セキュア版）"""
        tags = [category]
        content_lower = content[:5000].lower()  # サイズ制限
        
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
        
        return list(set(tags))[:10]  # 最大10タグ
    
    def create_directory_structure(self):
        """セキュアなディレクトリ構造作成"""
        categories = {
            'guides': ['user-guides', 'developer-guides', 'administrator-guides', 'workflow-guides'],
            'technical': ['architecture', 'implementation', 'specifications', 'deployment', 'research'],
            'reports': ['development', 'quality', 'analysis', 'operations'],
            'policies': ['development', 'quality', 'operations', 'governance'],
            'api': ['reference', 'guides', 'schemas', 'examples'],
            'projects': ['active', 'completed', 'planning'],
            'temp': ['security_review', 'processing']  # 一時・セキュリティレビュー用
        }
        
        for category, subcategories in categories.items():
            for subcategory in subcategories:
                path = self.secure_path_join(self.docs_path, category, subcategory)
                if path:
                    path.mkdir(parents=True, exist_ok=True)


def main():
    """エントリポイント"""
    parser = argparse.ArgumentParser(description='エルダーズギルド セキュアドキュメント分類ツール v2.0')
    parser.add_argument('--dry-run', action='store_true', help='実際の移動は行わない（テスト実行）')
    parser.add_argument('--no-metadata', action='store_true', help='メタデータを追加しない')
    parser.add_argument('--base-path', default='/home/aicompany/ai_co', help='ベースパス')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細ログ出力')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    classifier = SecureDocumentClassifier(args.base_path)
    
    print("🏛️ エルダーズギルド セキュアドキュメント分類 v2.0 開始")
    print(f"ベースパス: {args.base_path}")
    print(f"ドライラン: {'有効' if args.dry_run else '無効'}")
    print(f"メタデータ追加: {'無効' if args.no_metadata else '有効'}")
    print(f"4賢者システム: {'有効' if FOUR_SAGES_AVAILABLE else '無効'}")
    print()
    
    result = classifier.classify_and_move_secure(
        dry_run=args.dry_run,
        add_metadata=not args.no_metadata
    )
    
    print("📊 実行結果:")
    print(f"総ファイル数: {result.total_files}")
    print(f"処理対象: {result.processed_files}")
    print(f"移動成功: {result.moved_files}")
    print(f"スキップ: {result.skipped_files}")
    print(f"エラー: {result.error_files}")
    print(f"セキュリティ違反: {result.security_violations}")
    print(f"Iron Will違反: {result.iron_will_violations}")
    
    if result.sage_assignments:
        print("\n🧙‍♂️ 賢者別割り当て:")
        for sage, count in result.sage_assignments.items():
            print(f"  {sage}: {count}ファイル")
    
    # 品質判定
    if result.processed_files > 0:
        success_rate = (result.moved_files / result.processed_files) * 100
        security_compliance = ((result.processed_files - result.security_violations) / result.processed_files) * 100
        iron_will_compliance = ((result.processed_files - result.iron_will_violations) / result.processed_files) * 100
        
        print(f"\n📈 品質指標:")
        print(f"処理成功率: {success_rate:.1f}%")
        print(f"セキュリティ準拠率: {security_compliance:.1f}%")
        print(f"Iron Will準拠率: {iron_will_compliance:.1f}%")
        
        # 総合判定
        if success_rate >= 95 and security_compliance >= 90 and iron_will_compliance >= 95:
            print("\n✅ 品質判定: Iron Will基準完全準拠")
        elif success_rate >= 90 and security_compliance >= 80:
            print("\n⚠️ 品質判定: 基準達成（改善余地あり）")
        else:
            print("\n❌ 品質判定: 改善必要")
    
    print(f"\n🎯 分類完了: {'テストモード' if args.dry_run else '実際に実行'}")
    print("🏛️ Iron Will: No Workarounds! 🗡️")

if __name__ == "__main__":
    main()