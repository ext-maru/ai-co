#!/usr/bin/env python3
"""
"🔍" Conflict Analyzer
コンフリクト分析エンジン

機能:
- コンフリクトパターンの分類
- 自動解決可能性の判定
- リスク評価システム
- 安全性チェック
- 解決戦略の提案
"""

import logging
import re
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """コンフリクトタイプ"""
    MERGE_CONFLICT = "merge_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    VERSION_CONFLICT = "version_conflict"
    CHANGELOG_CONFLICT = "changelog_conflict"
    DOCUMENTATION_CONFLICT = "documentation_conflict"
    IMPORT_CONFLICT = "import_conflict"
    FORMATTING_CONFLICT = "formatting_conflict"
    WHITESPACE_CONFLICT = "whitespace_conflict"
    CONFIG_CONFLICT = "config_conflict"
    UNKNOWN_CONFLICT = "unknown_conflict"

class RiskLevel(Enum):
    """リスクレベル"""
    SAFE = "safe"           # 自動解決安全
    LOW = "low"             # 注意して自動解決可能
    MEDIUM = "medium"       # 慎重な検討必要
    HIGH = "high"           # 手動対応推奨
    CRITICAL = "critical"   # 絶対手動対応

class ResolutionStrategy(Enum):
    """解決戦略"""
    AUTO_MERGE_DEPENDENCIES = "auto_merge_dependencies"
    AUTO_APPEND_CHANGELOG = "auto_append_changelog"
    AUTO_FORMAT_CODE = "auto_format_code"
    AUTO_MERGE_IMPORTS = "auto_merge_imports"
    AUTO_UPDATE_VERSION = "auto_update_version"
    MANUAL_REVIEW = "manual_review"
    NO_RESOLUTION = "no_resolution"

@dataclass
class ConflictedFile:
    """コンフリクトファイル情報"""
    file_path: str
    conflict_type: ConflictType
    risk_level: RiskLevel
    conflict_markers: List[str]
    auto_resolvable: bool
    resolution_strategy: Optional[ResolutionStrategy]
    confidence_score: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "file_path": self.file_path,
            "conflict_type": self.conflict_type.value,
            "risk_level": self.risk_level.value,
            "conflict_markers": self.conflict_markers,
            "auto_resolvable": self.auto_resolvable,
            "resolution_strategy": self.resolution_strategy.value if self.resolution_strategy else None,
            "confidence_score": self.confidence_score
        }

@dataclass
class ConflictAnalysisResult:
    """コンフリクト分析結果"""
    total_conflicts: int
    conflicted_files: List[ConflictedFile]
    auto_resolvable_files: List[ConflictedFile]
    manual_required_files: List[ConflictedFile]
    overall_risk_level: RiskLevel
    estimated_resolution_time: int  # 分
    safety_score: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "total_conflicts": self.total_conflicts,
            "conflicted_files": [f.to_dict() for f in self.conflicted_files],
            "auto_resolvable_count": len(self.auto_resolvable_files),
            "manual_required_count": len(self.manual_required_files),
            "overall_risk_level": self.overall_risk_level.value,
            "estimated_resolution_time": self.estimated_resolution_time,
            "safety_score": self.safety_score
        }

class ConflictAnalyzer:
    """コンフリクト分析エンジン"""
    
    # 安全に自動解決可能なファイルパターン
    SAFE_AUTO_RESOLVE_PATTERNS = {
        r"package\.json$": {
            "type": ConflictType.DEPENDENCY_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_MERGE_DEPENDENCIES,
            "risk": RiskLevel.SAFE
        },
        r"package-lock\.json$": {
            "type": ConflictType.DEPENDENCY_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_MERGE_DEPENDENCIES,
            "risk": RiskLevel.LOW
        },
        r"CHANGELOG\.md$": {
            "type": ConflictType.CHANGELOG_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_APPEND_CHANGELOG,
            "risk": RiskLevel.SAFE
        },
        r"changelog\.md$": {
            "type": ConflictType.CHANGELOG_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_APPEND_CHANGELOG,
            "risk": RiskLevel.SAFE
        },
        r"\.gitignore$": {
            "type": ConflictType.CONFIG_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_MERGE_DEPENDENCIES,
            "risk": RiskLevel.LOW
        },
        r"requirements\.txt$": {
            "type": ConflictType.DEPENDENCY_CONFLICT,
            "strategy": ResolutionStrategy.AUTO_MERGE_DEPENDENCIES,
            "risk": RiskLevel.LOW
        }
    }
    
    # 手動対応必須パターン
    MANUAL_REQUIRED_PATTERNS = {
        r"\.py$": RiskLevel.MEDIUM,  # Pythonコード
        r"\.js$": RiskLevel.MEDIUM,  # JavaScriptコード
        r"\.ts$": RiskLevel.MEDIUM,  # TypeScriptコード
        r"\.sql$": RiskLevel.HIGH,   # SQLスクリプト
        r"config\.(json|yaml|yml)$": RiskLevel.HIGH,  # 重要設定ファイル
        r"\.env": RiskLevel.CRITICAL,  # 環境変数ファイル
        r"Dockerfile$": RiskLevel.HIGH,  # Docker設定
        r"docker-compose\.ya?ml$": RiskLevel.HIGH,  # Docker Compose
    }
    
    # コンフリクトマーカーパターン
    CONFLICT_MARKERS = [
        r"<{7}\s",      # <<<<<<< HEAD
        r"={7}",        # =======
        r">{7}\s",      # >>>>>>> branch
        r"\|{7}",       # |||||||
    ]
    
    def __init__(self, repo_path: str = None):
        """
        初期化
        
        Args:
            repo_path: Gitリポジトリのパス
        """
        self.repo_path = repo_path or os.getcwd()
        
    async def analyze_conflicts(
        self, 
        base_branch: str = "main",
        head_branch: str = None,
        pr_number: int = None
    ) -> ConflictAnalysisResult:
        """
        コンフリクトを分析
        
        Args:
            base_branch: ベースブランチ
            head_branch: ヘッドブランチ
            pr_number: PR番号（指定時はPRの情報を使用）
            
        Returns:
            ConflictAnalysisResult: 分析結果
        """
        try:
            # コンフリクトファイルを取得
            conflicted_files_info = await self._get_conflicted_files(
                base_branch, head_branch, pr_number
            )
            
            if not conflicted_files_info:
                # コンフリクトなし
                return ConflictAnalysisResult(
                    total_conflicts=0,
                    conflicted_files=[],
                    auto_resolvable_files=[],
                    manual_required_files=[],
                    overall_risk_level=RiskLevel.SAFE,
                    estimated_resolution_time=0,
                    safety_score=1.0
                )
            
            # 各ファイルを分析
            conflicted_files = []
            for file_info in conflicted_files_info:
                analyzed_file = await self._analyze_single_file(file_info)
                conflicted_files.append(analyzed_file)
            
            # 結果を分類
            auto_resolvable = [f for f in conflicted_files if f.auto_resolvable]
            manual_required = [f for f in conflicted_files if not f.auto_resolvable]
            
            # 全体のリスクレベルを算出
            overall_risk = self._calculate_overall_risk(conflicted_files)
            
            # 解決時間を推定
            estimated_time = self._estimate_resolution_time(conflicted_files)
            
            # 安全性スコアを算出
            safety_score = self._calculate_safety_score(conflicted_files)
            
            return ConflictAnalysisResult(
                total_conflicts=len(conflicted_files),
                conflicted_files=conflicted_files,
                auto_resolvable_files=auto_resolvable,
                manual_required_files=manual_required,
                overall_risk_level=overall_risk,
                estimated_resolution_time=estimated_time,
                safety_score=safety_score
            )
            
        except Exception as e:
            logger.error(f"Conflict analysis failed: {e}")
            # エラー時は保守的な結果を返す
            return ConflictAnalysisResult(
                total_conflicts=1,
                conflicted_files=[],
                auto_resolvable_files=[],
                manual_required_files=[],
                overall_risk_level=RiskLevel.CRITICAL,
                estimated_resolution_time=60,
                safety_score=0.0
            )
    
    async def _get_conflicted_files(
        self, 
        base_branch: str, 
        head_branch: str, 
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """コンフリクトファイル一覧を取得"""
        try:
            # Git merge-tree を使用してコンフリクトを検出
            if head_branch:
                # ブランチ指定時
                cmd = [
                    "git", "merge-tree", 
                    f"origin/{base_branch}", 
                    f"origin/{head_branch}"
                ]
            else:
                # PR番号指定時（簡略化）
                cmd = ["git", "status", "--porcelain"]
            
            result = subprocess.run(
                cmd, 
                cwd=self.repo_path,
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0 and not result.stdout:
                return []
            
            # 結果をパース（簡略化）
            conflicted_files = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    # 簡単な解析
                    if 'UU' in line or '<<<<<<< ' in line:
                        file_path = line.split()[-1] if line.split() else "unknown"
                        conflicted_files.append({
                            "file_path": file_path,
                            "status": "conflicted"
                        })
            
            return conflicted_files
            
        except Exception as e:
            logger.error(f"Failed to get conflicted files: {e}")
            return []
    
    async def _analyze_single_file(self, file_info: Dict[str, Any]) -> ConflictedFile:
        """単一ファイルのコンフリクト分析"""
        file_path = file_info["file_path"]
        
        try:
            # ファイルパターンマッチング
            conflict_type, risk_level, strategy = self._classify_file_conflict(file_path)
            
            # コンフリクトマーカーを検出
            conflict_markers = await self._detect_conflict_markers(file_path)
            
            # 自動解決可能性を判定
            auto_resolvable = self._is_auto_resolvable(file_path, conflict_type, risk_level)
            
            # 信頼度スコアを算出
            confidence = self._calculate_confidence_score(
                file_path, conflict_type, conflict_markers, auto_resolvable
            )
            
            return ConflictedFile(
                file_path=file_path,
                conflict_type=conflict_type,
                risk_level=risk_level,
                conflict_markers=conflict_markers,
                auto_resolvable=auto_resolvable,
                resolution_strategy=strategy if auto_resolvable else None,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            # エラー時は保守的な設定
            return ConflictedFile(
                file_path=file_path,
                conflict_type=ConflictType.UNKNOWN_CONFLICT,
                risk_level=RiskLevel.CRITICAL,
                conflict_markers=[],
                auto_resolvable=False,
                resolution_strategy=None,
                confidence_score=0.0
            )
    
    def _classify_file_conflict(
        self, 
        file_path: str
    ) -> Tuple[ConflictType, RiskLevel, Optional[ResolutionStrategy]]:
        """ファイルのコンフリクト分類"""
        
        # 安全な自動解決パターンをチェック
        for pattern, config in self.SAFE_AUTO_RESOLVE_PATTERNS.items():
            if re.search(pattern, file_path):
                return (
                    config["type"],
                    config["risk"],
                    config["strategy"]
                )
        
        # 手動対応必須パターンをチェック
        for pattern, risk in self.MANUAL_REQUIRED_PATTERNS.items():
            if re.search(pattern, file_path):
                return (
                    ConflictType.MERGE_CONFLICT,
                    risk,
                    ResolutionStrategy.MANUAL_REVIEW
                )
        
        # デフォルト
        return (
            ConflictType.UNKNOWN_CONFLICT,
            RiskLevel.MEDIUM,
            ResolutionStrategy.MANUAL_REVIEW
        )
    
    async def _detect_conflict_markers(self, file_path: str) -> List[str]:
        """コンフリクトマーカーの検出"""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            if not os.path.exists(full_path):
                return []
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            markers = []
            for pattern in self.CONFLICT_MARKERS:
                matches = re.findall(pattern, content)
                markers.extend(matches)
            
            return markers
            
        except Exception as e:
            logger.warning(f"Failed to detect conflict markers in {file_path}: {e}")
            return []
    
    def _is_auto_resolvable(
        self, 
        file_path: str, 
        conflict_type: ConflictType, 
        risk_level: RiskLevel
    ) -> bool:
        """自動解決可能性の判定"""
        
        # 高リスク・クリティカルは手動対応
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return False
        
        # 安全・低リスクで特定のタイプは自動解決可能
        if risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
            auto_resolvable_types = [
                ConflictType.DEPENDENCY_CONFLICT,
                ConflictType.CHANGELOG_CONFLICT,
                ConflictType.VERSION_CONFLICT,
                ConflictType.FORMATTING_CONFLICT,
                ConflictType.WHITESPACE_CONFLICT
            ]
            return conflict_type in auto_resolvable_types
        
        # 中リスクは慎重に判定
        if risk_level == RiskLevel.MEDIUM:
            # 特定の安全なファイルのみ
            safe_patterns = [r"\.md$", r"\.txt$", r"\.gitignore$"]
            return any(re.search(pattern, file_path) for pattern in safe_patterns)
        
        return False
    
    def _calculate_confidence_score(
        self, 
        file_path: str, 
        conflict_type: ConflictType, 
        conflict_markers: List[str],
        auto_resolvable: bool
    ) -> float:
        """信頼度スコアの算出"""
        score = 0.5  # ベーススコア
        
        # ファイルタイプによる調整
        if conflict_type in [ConflictType.DEPENDENCY_CONFLICT, ConflictType.CHANGELOG_CONFLICT]:
            score += 0.3
        
        # コンフリクトマーカーの数による調整
        marker_count = len(conflict_markers)
        if marker_count == 0:
            score += 0.2
        elif marker_count <= 3:
            score += 0.1
        else:
            score -= 0.1
        
        # 自動解決可能性による調整
        if auto_resolvable:
            score += 0.2
        else:
            score -= 0.2
        
        # 0.0-1.0の範囲に正規化
        return max(0.0, min(1.0, score))
    
    def _calculate_overall_risk(self, conflicted_files: List[ConflictedFile]) -> RiskLevel:
        """全体のリスクレベル算出"""
        if not conflicted_files:
            return RiskLevel.SAFE
        
        risk_levels = [f.risk_level for f in conflicted_files]
        
        # 最も高いリスクレベルを採用
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        elif RiskLevel.LOW in risk_levels:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    def _estimate_resolution_time(self, conflicted_files: List[ConflictedFile]) -> int:
        """解決時間の推定（分）"""
        total_time = 0
        
        time_estimates = {
            ConflictType.DEPENDENCY_CONFLICT: 2,
            ConflictType.CHANGELOG_CONFLICT: 1,
            ConflictType.VERSION_CONFLICT: 1,
            ConflictType.DOCUMENTATION_CONFLICT: 3,
            ConflictType.FORMATTING_CONFLICT: 1,
            ConflictType.WHITESPACE_CONFLICT: 1,
            ConflictType.CONFIG_CONFLICT: 5,
            ConflictType.MERGE_CONFLICT: 10,
            ConflictType.UNKNOWN_CONFLICT: 15
        }
        
        for file in conflicted_files:
            base_time = time_estimates.get(file.conflict_type, 10)
            
            # 自動解決可能な場合は時間短縮
            if file.auto_resolvable:
                base_time = max(1, base_time // 3)
            
            total_time += base_time
        
        return total_time
    
    def _calculate_safety_score(self, conflicted_files: List[ConflictedFile]) -> float:
        """安全性スコアの算出"""
        if not conflicted_files:
            return 1.0
        
        auto_resolvable_count = sum(1 for f in conflicted_files if f.auto_resolvable)
        safety_ratio = auto_resolvable_count / len(conflicted_files)
        
        # 信頼度スコアの平均も考慮
        avg_confidence = sum(f.confidence_score for f in conflicted_files) / len(conflicted_files)
        
        return (safety_ratio * 0.7) + (avg_confidence * 0.3)

# 使用例とテスト用関数
async def example_usage():
    """使用例"""
    analyzer = ConflictAnalyzer("/path/to/repo")
    
    # コンフリクト分析実行
    result = await analyzer.analyze_conflicts(
        base_branch="main",
        head_branch="feature/new-feature"
    )
    
    print(f"総コンフリクト数: {result.total_conflicts}")
    print(f"自動解決可能: {len(result.auto_resolvable_files)}")
    print(f"手動対応必要: {len(result.manual_required_files)}")
    print(f"全体リスク: {result.overall_risk_level.value}")
    print(f"推定解決時間: {result.estimated_resolution_time}分")
    print(f"安全性スコア: {result.safety_score:0.2f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())