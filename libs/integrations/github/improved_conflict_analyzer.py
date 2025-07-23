#!/usr/bin/env python3
"""
🔍 Improved Conflict Analyzer
実証済みPythonライブラリを活用したコンフリクト分析エンジン

使用ライブラリ:
- GitPython: Git操作 (既存)
- three-merge: 3-wayマージ処理
- unidiff: diff解析
- merge3: 高度なマージアルゴリズム
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import git
from pathlib import Path

logger = logging.getLogger(__name__)

# 外部ライブラリの動的インポート
try:
    from unidiff import PatchSet
    UNIDIFF_AVAILABLE = True
except ImportError:
    UNIDIFF_AVAILABLE = False
    logger.warning("unidiff not available. Install with: pip install unidiff")

try:
    from three_merge import merge as three_way_merge
    THREE_MERGE_AVAILABLE = True
except ImportError:
    THREE_MERGE_AVAILABLE = False
    logger.warning("three-merge not available. Install with: pip install three-merge")

try:
    import merge3
    MERGE3_AVAILABLE = True
except ImportError:
    MERGE3_AVAILABLE = False
    logger.warning("merge3 not available. Install with: pip install merge3")


class ConflictType(Enum):
    """コンフリクトタイプ"""
    DEPENDENCY_CONFLICT = "dependency_conflict"
    CHANGELOG_CONFLICT = "changelog_conflict"
    DOCUMENTATION_CONFLICT = "documentation_conflict"
    CODE_CONFLICT = "code_conflict"
    CONFIG_CONFLICT = "config_conflict"
    BINARY_CONFLICT = "binary_conflict"
    DELETED_BY_US = "deleted_by_us"
    DELETED_BY_THEM = "deleted_by_them"
    ADDED_BY_US = "added_by_us"
    ADDED_BY_THEM = "added_by_them"
    BOTH_MODIFIED = "both_modified"


class ResolutionStrategy(Enum):
    """解決戦略"""
    THREE_WAY_MERGE = "three_way_merge"
    TAKE_OURS = "take_ours"
    TAKE_THEIRS = "take_theirs"
    MERGE_DEPENDENCIES = "merge_dependencies"
    APPEND_CHANGELOG = "append_changelog"
    MANUAL_REVIEW = "manual_review"
    SKIP_BINARY = "skip_binary"


@dataclass
class ConflictInfo:
    """コンフリクト情報"""
    file_path: str
    conflict_type: ConflictType
    stage_info: Dict[int, str]  # {stage: blob_hash}
    auto_resolvable: bool
    resolution_strategy: Optional[ResolutionStrategy]
    confidence: float
    file_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            "file_path": self.file_path,
            "conflict_type": self.conflict_type.value,
            "stage_info": self.stage_info,
            "auto_resolvable": self.auto_resolvable,
            "resolution_strategy": self.resolution_strategy.value if self.resolution_strategy else None,
            "confidence": self.confidence,
            "file_size": self.file_size
        }


class ImprovedConflictAnalyzer:
    """改良版コンフリクト分析エンジン"""
    
    # 安全に自動解決可能なファイルパターン
    SAFE_PATTERNS = {
        'package.json': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.MERGE_DEPENDENCIES),
        'package-lock.json': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.TAKE_THEIRS),
        'yarn.lock': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.TAKE_THEIRS),
        'CHANGELOG.md': (ConflictType.CHANGELOG_CONFLICT, ResolutionStrategy.APPEND_CHANGELOG),
        'changelog.md': (ConflictType.CHANGELOG_CONFLICT, ResolutionStrategy.APPEND_CHANGELOG),
        'HISTORY.md': (ConflictType.CHANGELOG_CONFLICT, ResolutionStrategy.APPEND_CHANGELOG),
        'requirements.txt': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.MERGE_DEPENDENCIES),
        'poetry.lock': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.TAKE_THEIRS),
        'Pipfile.lock': (ConflictType.DEPENDENCY_CONFLICT, ResolutionStrategy.TAKE_THEIRS),
    }
    
    # ドキュメントファイルパターン（安全度中）
    DOC_PATTERNS = ['.md', '.txt', '.rst', '.adoc']
    
    # 危険なファイルパターン
    DANGEROUS_PATTERNS = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
    
    def __init__(self, repo_path: str):
        """
        初期化
        
        Args:
            repo_path: Gitリポジトリのパス
        """
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
    def analyze_merge_conflicts(
        self, 
        base_branch: str = "main",
        head_branch: str = None
    ) -> Dict[str, Any]:
        """
        GitPythonを使用してマージコンフリクトを分析
        
        Args:
            base_branch: ベースブランチ
            head_branch: ヘッドブランチ（None時は現在のブランチ）
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # インデックスからunmerged blobsを取得
            unmerged_blobs = self.repo.index.unmerged_blobs()
            
            if not unmerged_blobs:
                return {
                    "conflicts_found": False,
                    "total_conflicts": 0,
                    "conflicts": [],
                    "auto_resolvable_count": 0,
                    "manual_required_count": 0
                }
            
            conflicts = []
            auto_resolvable_count = 0
            
            for file_path, stages in unmerged_blobs.items():
                conflict_info = self._analyze_single_conflict(file_path, stages)
                conflicts.append(conflict_info)
                
                if conflict_info.auto_resolvable:
                    auto_resolvable_count += 1
            
            return {
                "conflicts_found": True,
                "total_conflicts": len(conflicts),
                "conflicts": [c.to_dict() for c in conflicts],
                "auto_resolvable_count": auto_resolvable_count,
                "manual_required_count": len(conflicts) - auto_resolvable_count,
                "overall_safety_score": auto_resolvable_count / len(conflicts) if conflicts else 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze merge conflicts: {e}")
            return {
                "conflicts_found": False,
                "error": str(e),
                "total_conflicts": 0,
                "conflicts": []
            }
    
    def _analyze_single_conflict(
        self,
        file_path: str,
        stages: List[Tuple[int,
        Any]]
    ) -> ConflictInfo:
        """単一ファイルのコンフリクトを分析"""
        
        # ステージ情報を整理
        stage_info = {}
        for stage, blob in stages:
            stage_info[stage] = blob.hexsha
        
        # ファイルタイプとコンフリクトタイプを判定
        conflict_type = self._determine_conflict_type(file_path, stage_info)
        
        # 解決戦略を決定
        resolution_strategy = self._determine_resolution_strategy(
            file_path,
            conflict_type,
            stage_info
        )
        
        # 自動解決可能性を判定
        auto_resolvable = self._is_auto_resolvable(file_path, conflict_type, stage_info)
        
        # 信頼度を算出
        confidence = self._calculate_confidence(file_path, conflict_type, auto_resolvable)
        
        # ファイルサイズを取得
        file_size = self._get_file_size(file_path)
        
        return ConflictInfo(
            file_path=file_path,
            conflict_type=conflict_type,
            stage_info=stage_info,
            auto_resolvable=auto_resolvable,
            resolution_strategy=resolution_strategy if auto_resolvable else ResolutionStrategy.MANUAL_REVIEW,
            confidence=confidence,
            file_size=file_size
        )
    
    def _determine_conflict_type(self, file_path: str, stage_info: Dict[int, str]) -> ConflictType:
        """コンフリクトタイプの判定"""
        
        # ファイル名での判定
        basename = os.path.basename(file_path)
        if basename in self.SAFE_PATTERNS:
            return self.SAFE_PATTERNS[basename][0]
        
        # 拡張子での判定
        _, ext = os.path.splitext(file_path)
        
        if ext in self.DOC_PATTERNS:
            return ConflictType.DOCUMENTATION_CONFLICT
        elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini']:
            return ConflictType.CONFIG_CONFLICT
        elif ext in self.DANGEROUS_PATTERNS:
            return ConflictType.CODE_CONFLICT
        
        # ステージ情報での判定
        if 1 not in stage_info and 3 in stage_info:
            return ConflictType.ADDED_BY_THEM
        elif 3 not in stage_info and 1 in stage_info:
            return ConflictType.ADDED_BY_US
        elif 1 in stage_info and 3 in stage_info:
            return ConflictType.BOTH_MODIFIED
        
        return ConflictType.BOTH_MODIFIED
    
    def _determine_resolution_strategy(
        self, 
        file_path: str, 
        conflict_type: ConflictType, 
        stage_info: Dict[int, str]
    ) -> ResolutionStrategy:
        """解決戦略の決定"""
        
        # 安全パターンの直接マッピング
        basename = os.path.basename(file_path)
        if basename in self.SAFE_PATTERNS:
            return self.SAFE_PATTERNS[basename][1]
        
        # コンフリクトタイプ別の戦略
        if conflict_type == ConflictType.DEPENDENCY_CONFLICT:
            return ResolutionStrategy.MERGE_DEPENDENCIES
        elif conflict_type == ConflictType.CHANGELOG_CONFLICT:
            return ResolutionStrategy.APPEND_CHANGELOG
        elif conflict_type == ConflictType.DOCUMENTATION_CONFLICT:
            return ResolutionStrategy.THREE_WAY_MERGE
        elif conflict_type in [ConflictType.ADDED_BY_US, ConflictType.ADDED_BY_THEM]:
            # 追加系は慎重に
            return ResolutionStrategy.MANUAL_REVIEW
        
        return ResolutionStrategy.MANUAL_REVIEW
    
    def _is_auto_resolvable(
        self, 
        file_path: str, 
        conflict_type: ConflictType, 
        stage_info: Dict[int, str]
    ) -> bool:
        """自動解決可能性の判定"""
        
        # ファイル名での安全リスト
        basename = os.path.basename(file_path)
        if basename in self.SAFE_PATTERNS:
            return True
        
        # ドキュメントファイルは限定的に自動解決
        _, ext = os.path.splitext(file_path)
        if ext in self.DOC_PATTERNS:
            # サイズが小さく、テキストファイルの場合のみ
            file_size = self._get_file_size(file_path)
            return file_size < 10000  # 10KB未満
        
        # 危険なファイルは手動対応
        if ext in self.DANGEROUS_PATTERNS:
            return False
        
        # バイナリファイルは手動対応
        if self._is_binary_file(file_path):
            return False
        
        return False
    
    def _calculate_confidence(
        self, 
        file_path: str, 
        conflict_type: ConflictType, 
        auto_resolvable: bool
    ) -> float:
        """信頼度の算出"""
        
        confidence = 0.5  # ベース
        
        # ファイル名での加点
        basename = os.path.basename(file_path)
        if basename in self.SAFE_PATTERNS:
            confidence += 0.4
        
        # ファイルタイプでの調整
        if conflict_type in [ConflictType.DEPENDENCY_CONFLICT, ConflictType.CHANGELOG_CONFLICT]:
            confidence += 0.3
        elif conflict_type == ConflictType.DOCUMENTATION_CONFLICT:
            confidence += 0.1
        elif conflict_type == ConflictType.CODE_CONFLICT:
            confidence -= 0.2
        
        # 自動解決可能性での調整
        if auto_resolvable:
            confidence += 0.2
        else:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _get_file_size(self, file_path: str) -> int:
        """ファイルサイズを取得"""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            if os.path.exists(full_path):
                return os.path.getsize(full_path)
        except Exception:
            pass
        return 0
    
    def _is_binary_file(self, file_path: str) -> bool:
        """バイナリファイルかどうか判定"""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    chunk = f.read(8000)
                    return b'\0' in chunk
        except Exception:
            pass
        return False
    
    def auto_resolve_safe_conflicts(self, conflicts: List[ConflictInfo]) -> Dict[str, Any]:
        """安全なコンフリクトの自動解決"""
        
        if not any([THREE_MERGE_AVAILABLE, MERGE3_AVAILABLE]):
            return {
                "success": False,
                "error": "Required merge libraries not available",
                "resolved_files": []
            }
        
        resolved_files = []
        failed_files = []
        
        for conflict in conflicts:
            if not conflict.auto_resolvable:
                continue
            
            try:
                success = self._resolve_single_conflict(conflict)
                if success:
                    resolved_files.append(conflict.file_path)
                else:
                    failed_files.append(conflict.file_path)
            except Exception as e:
                logger.error(f"Failed to resolve {conflict.file_path}: {e}")
                failed_files.append(conflict.file_path)
        
        return {
            "success": len(failed_files) == 0,
            "resolved_files": resolved_files,
            "failed_files": failed_files,
            "total_attempted": len([c for c in conflicts if c.auto_resolvable])
        }
    
    def _resolve_single_conflict(self, conflict: ConflictInfo) -> bool:
        """単一コンフリクトの解決"""
        
        try:
            if conflict.resolution_strategy == ResolutionStrategy.THREE_WAY_MERGE:
                return self._three_way_merge_resolve(conflict)
            elif conflict.resolution_strategy == ResolutionStrategy.MERGE_DEPENDENCIES:
                return self._merge_dependencies_resolve(conflict)
            elif conflict.resolution_strategy == ResolutionStrategy.APPEND_CHANGELOG:
                return self._append_changelog_resolve(conflict)
            elif conflict.resolution_strategy == ResolutionStrategy.TAKE_OURS:
                return self._take_ours_resolve(conflict)
            elif conflict.resolution_strategy == ResolutionStrategy.TAKE_THEIRS:
                return self._take_theirs_resolve(conflict)
        except Exception as e:
            logger.error(f"Resolution failed for {conflict.file_path}: {e}")
            return False
        
        return False
    
    def _three_way_merge_resolve(self, conflict: ConflictInfo) -> bool:
        """3-wayマージでの解決"""
        
        if not THREE_MERGE_AVAILABLE and not MERGE3_AVAILABLE:
            return False
        
        try:
            # 各ステージのファイル内容を取得
            base_content = self._get_blob_content(conflict.stage_info.get(1, ""))
            our_content = self._get_blob_content(conflict.stage_info.get(2, ""))
            their_content = self._get_blob_content(conflict.stage_info.get(3, ""))
            
            if THREE_MERGE_AVAILABLE:
                # three-mergeを使用
                result = three_way_merge(our_content, their_content, base_content)
                
                # コンフリクトマーカーが残っていないかチェック
                if '<<<<<<' in result or '======' in result or '>>>>>>' in result:
                    return False
                
            elif MERGE3_AVAILABLE:
                # merge3を使用
                m3 = merge3.Merge3(
                    base_content.splitlines(True),
                    our_content.splitlines(True),
                    their_content.splitlines(True)
                )
                
                result_lines = list(m3.merge_lines())
                result = ''.join(result_lines)
            
            # ファイルに書き込み
            file_path = os.path.join(self.repo_path, conflict.file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            # インデックスに追加
            self.repo.index.add([conflict.file_path])
            
            return True
            
        except Exception as e:
            logger.error(f"Three-way merge failed for {conflict.file_path}: {e}")
            return False
    
    def _merge_dependencies_resolve(self, conflict: ConflictInfo) -> bool:
        """依存関係ファイルのマージ解決"""
        # 簡単な実装: theirs側を採用（通常は最新の依存関係）
        return self._take_theirs_resolve(conflict)
    
    def _append_changelog_resolve(self, conflict: ConflictInfo) -> bool:
        """CHANGELOGの追記解決"""
        try:
            # 各バージョンの内容を取得
            our_content = self._get_blob_content(conflict.stage_info.get(2, ""))
            their_content = self._get_blob_content(conflict.stage_info.get(3, ""))
            
            # 簡単な追記マージ（時系列順）
            our_lines = our_content.splitlines()
            their_lines = their_content.splitlines()
            
            # 共通部分を見つけて、新しい部分を追記
            # 実装は簡略化
            merged_content = our_content + "\n" + their_content
            
            # ファイルに書き込み
            file_path = os.path.join(self.repo_path, conflict.file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            # インデックスに追加
            self.repo.index.add([conflict.file_path])
            
            return True
            
        except Exception as e:
            logger.error(f"Changelog merge failed for {conflict.file_path}: {e}")
            return False
    
    def _take_ours_resolve(self, conflict: ConflictInfo) -> bool:
        """自分側を採用"""
        try:
            if 2 in conflict.stage_info:
                content = self._get_blob_content(conflict.stage_info[2])
                file_path = os.path.join(self.repo_path, conflict.file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.repo.index.add([conflict.file_path])
                return True
        except Exception as e:
            logger.error(f"Take ours failed for {conflict.file_path}: {e}")
        return False
    
    def _take_theirs_resolve(self, conflict: ConflictInfo) -> bool:
        """相手側を採用"""
        try:
            if 3 in conflict.stage_info:
                content = self._get_blob_content(conflict.stage_info[3])
                file_path = os.path.join(self.repo_path, conflict.file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.repo.index.add([conflict.file_path])
                return True
        except Exception as e:
            logger.error(f"Take theirs failed for {conflict.file_path}: {e}")
        return False
    
    def _get_blob_content(self, blob_sha: str) -> str:
        """Blobの内容を取得"""
        try:
            if blob_sha:
                blob = self.repo.odb.stream(blob_sha).read().decode('utf-8')
                return blob
        except Exception as e:
            logger.warning(f"Failed to get blob content {blob_sha}: {e}")
        return ""


# 使用例
async def example_usage():
    """使用例"""
    analyzer = ImprovedConflictAnalyzer("/path/to/repo")
    
    # コンフリクト分析
    result = analyzer.analyze_merge_conflicts("main", "feature/branch")
    
    if result["conflicts_found"]:
        print(f"Total conflicts: {result['total_conflicts']}")
        print(f"Auto-resolvable: {result['auto_resolvable_count']}")
        
        # 自動解決実行
        conflicts = [ConflictInfo(**c) for c in result["conflicts"]]
        resolution_result = analyzer.auto_resolve_safe_conflicts(conflicts)
        
        print(f"Resolved files: {len(resolution_result['resolved_files'])}")
        print(f"Failed files: {len(resolution_result['failed_files'])}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())