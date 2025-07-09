#!/usr/bin/env python3
"""
🛡️ Pre-Commit インシデント騎士団ガード
コミット前の脅威検出と自動ブロック機能

作成日: 2025年7月8日
作成者: クロードエルダー（開発実行責任者）
承認: インシデント賢者による事前相談済み
"""

import sys
import os
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import logging

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.enhanced_incident_manager import EnhancedIncidentManager, IncidentLevel

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CodeChange:
    """コード変更データ"""
    file_path: str
    lines_added: int
    lines_deleted: int
    total_changes: int
    risk_indicators: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)


@dataclass
class CommitRiskAssessment:
    """コミットリスク評価結果"""
    overall_risk: str
    risk_score: float
    creature_threat: str
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    should_block: bool = False


class PreCommitIncidentGuard:
    """Pre-Commit インシデント騎士団ガード"""
    
    # 危険パターン定義
    CRITICAL_PATTERNS = {
        # セキュリティ関連
        "hardcoded_password": [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'pwd\s*=\s*["\'][^"\']{6,}["\']',
            r'secret\s*=\s*["\'][^"\']{10,}["\']'
        ],
        "sql_injection": [
            r'execute\s*\(\s*["\'].*%.*["\']',
            r'query\s*\(\s*f["\'].*{.*}.*["\']',
            r'\.format\s*\(.*\)\s*\+.*sql'
        ],
        "api_key_exposure": [
            r'api_key\s*=\s*["\'][A-Za-z0-9]{20,}["\']',
            r'token\s*=\s*["\'][A-Za-z0-9]{30,}["\']',
            r'bearer\s+[A-Za-z0-9]{20,}'
        ],
        "dangerous_imports": [
            r'import\s+os\s*;\s*os\.system',
            r'from\s+subprocess\s+import.*shell=True',
            r'eval\s*\(',
            r'exec\s*\('
        ]
    }
    
    # 警告パターン
    WARNING_PATTERNS = {
        "performance_risk": [
            r'while\s+True\s*:(?!\s*break)',
            r'for.*in.*range\(.*\*.*\*.*\)',
            r'\.join\(.*\)\s*\+\s*\.join'
        ],
        "deprecated_usage": [
            r'\.iteritems\(',
            r'urllib2\.',
            r'md5\.',
            r'cPickle\.'
        ],
        "todo_markers": [
            r'#\s*TODO',
            r'#\s*FIXME',
            r'#\s*HACK',
            r'#\s*XXX'
        ]
    }
    
    # 重要ファイルパターン
    CRITICAL_FILES = [
        r'.*security.*\.py$',
        r'.*auth.*\.py$',
        r'.*payment.*\.py$',
        r'.*database.*\.py$',
        r'.*config.*\.py$',
        r'.*settings.*\.py$',
        r'.*\.env$',
        r'.*requirements.*\.txt$'
    ]
    
    def __init__(self):
        """初期化"""
        self.incident_manager = EnhancedIncidentManager()
        self.stats = {
            "commits_checked": 0,
            "commits_blocked": 0,
            "threats_detected": 0
        }
        
        logger.info("🛡️ Pre-Commit インシデント騎士団ガード起動")
    
    def get_staged_files(self) -> List[str]:
        """ステージングされたファイル一覧を取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return files
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git staged files取得エラー: {e}")
            return []
    
    def get_file_changes(self, file_path: str) -> Optional[CodeChange]:
        """ファイルの変更内容を分析"""
        try:
            # git diffを取得
            result = subprocess.run(
                ["git", "diff", "--cached", "--numstat", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return None
            
            # numstatから変更行数を取得
            stats = result.stdout.strip().split('\t')
            if len(stats) >= 2:
                lines_added = int(stats[0]) if stats[0] != '-' else 0
                lines_deleted = int(stats[1]) if stats[1] != '-' else 0
            else:
                lines_added = lines_deleted = 0
            
            # ファイル内容の変更を取得
            content_result = subprocess.run(
                ["git", "diff", "--cached", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            change = CodeChange(
                file_path=file_path,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                total_changes=lines_added + lines_deleted
            )
            
            # パターン分析
            change.risk_indicators = self._analyze_risk_patterns(content_result.stdout)
            change.security_issues = self._analyze_security_issues(content_result.stdout)
            
            return change
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ファイル変更分析エラー {file_path}: {e}")
            return None
    
    def _analyze_risk_patterns(self, diff_content: str) -> List[str]:
        """リスクパターンを分析"""
        risks = []
        
        for risk_type, patterns in self.WARNING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, diff_content, re.IGNORECASE | re.MULTILINE):
                    risks.append(risk_type)
                    break
        
        return risks
    
    def _analyze_security_issues(self, diff_content: str) -> List[str]:
        """セキュリティ問題を分析"""
        issues = []
        
        for issue_type, patterns in self.CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, diff_content, re.IGNORECASE | re.MULTILINE):
                    issues.append(issue_type)
                    break
        
        return issues
    
    def _is_critical_file(self, file_path: str) -> bool:
        """重要ファイルかどうか判定"""
        for pattern in self.CRITICAL_FILES:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def assess_commit_risk(self, changes: List[CodeChange]) -> CommitRiskAssessment:
        """コミットリスクを総合評価"""
        total_changes = sum(change.total_changes for change in changes)
        critical_files = sum(1 for change in changes if self._is_critical_file(change.file_path))
        all_security_issues = []
        all_risk_indicators = []
        
        for change in changes:
            all_security_issues.extend(change.security_issues)
            all_risk_indicators.extend(change.risk_indicators)
        
        # リスクスコア計算
        risk_score = 0.0
        
        # 変更量によるリスク
        risk_score += min(0.3, total_changes / 1000)
        
        # 重要ファイルによるリスク
        risk_score += critical_files * 0.2
        
        # セキュリティ問題によるリスク
        risk_score += len(set(all_security_issues)) * 0.3
        
        # その他のリスク指標
        risk_score += len(set(all_risk_indicators)) * 0.1
        
        risk_score = min(1.0, risk_score)
        
        # リスクレベル判定
        if risk_score >= 0.8:
            overall_risk = "CRITICAL"
            creature_threat = "🐉 古龍の覚醒"
        elif risk_score >= 0.6:
            overall_risk = "HIGH"
            creature_threat = "⚔️ オークの大軍"
        elif risk_score >= 0.3:
            overall_risk = "MEDIUM"
            creature_threat = "🧟‍♂️ ゾンビの侵入"
        else:
            overall_risk = "LOW"
            creature_threat = "🧚‍♀️ 妖精の悪戯"
        
        # ブロック判定
        should_block = False
        blocking_issues = []
        warnings = []
        recommendations = []
        
        # 重大なセキュリティ問題
        critical_security = ["hardcoded_password", "sql_injection", "api_key_exposure", "dangerous_imports"]
        for issue in all_security_issues:
            if issue in critical_security:
                should_block = True
                blocking_issues.append(f"🚨 重大セキュリティ問題: {issue}")
        
        # 非常に高いリスクスコア
        if risk_score > 0.9:
            should_block = True
            blocking_issues.append("🐉 リスクスコアが危険レベル (>90%)")
        
        # 警告とレコメンデーション
        if all_risk_indicators:
            warnings.extend([f"⚠️ リスク指標: {indicator}" for indicator in set(all_risk_indicators)])
        
        if overall_risk == "CRITICAL":
            recommendations.append("🏰 緊急会議招集！複数の騎士によるレビューが必要")
            recommendations.append("🔍 セキュリティ監査の実施を強く推奨")
        elif overall_risk == "HIGH":
            recommendations.append("⚔️ 上級騎士による詳細レビューを推奨")
            recommendations.append("🧪 追加テストの実施を推奨")
        elif overall_risk == "MEDIUM":
            recommendations.append("🛡️ 通常レビューで問題の確認を推奨")
        
        assessment = CommitRiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            creature_threat=creature_threat,
            blocking_issues=blocking_issues,
            warnings=warnings,
            recommendations=recommendations,
            should_block=should_block
        )
        
        return assessment
    
    def format_assessment_report(self, assessment: CommitRiskAssessment, 
                               changes: List[CodeChange]) -> str:
        """評価レポートをフォーマット"""
        report = []
        report.append("🏰" + "=" * 60)
        report.append("    インシデント騎士団 Pre-Commit 守護報告")
        report.append("=" * 64)
        report.append("")
        
        # 脅威レベル
        report.append(f"🎯 脅威レベル: {assessment.overall_risk}")
        report.append(f"🐲 検出されたクリーチャー: {assessment.creature_threat}")
        report.append(f"📊 リスクスコア: {assessment.risk_score * 100:.1f}%")
        report.append("")
        
        # 変更サマリー
        total_files = len(changes)
        total_changes = sum(c.total_changes for c in changes)
        critical_files = sum(1 for c in changes if self._is_critical_file(c.file_path))
        
        report.append(f"📝 変更サマリー:")
        report.append(f"   - ファイル数: {total_files}")
        report.append(f"   - 総変更行数: {total_changes}")
        report.append(f"   - 重要ファイル: {critical_files}")
        report.append("")
        
        # ブロック理由
        if assessment.should_block:
            report.append("🚫 コミットブロック理由:")
            for issue in assessment.blocking_issues:
                report.append(f"   {issue}")
            report.append("")
        
        # 警告
        if assessment.warnings:
            report.append("⚠️ 警告事項:")
            for warning in assessment.warnings:
                report.append(f"   {warning}")
            report.append("")
        
        # 推奨事項
        if assessment.recommendations:
            report.append("💡 推奨事項:")
            for rec in assessment.recommendations:
                report.append(f"   {rec}")
            report.append("")
        
        # ファイル別詳細
        if len(changes) <= 10:  # 詳細表示は10ファイルまで
            report.append("📋 ファイル別詳細:")
            for change in changes:
                risk_level = "🚨" if change.security_issues else "⚠️" if change.risk_indicators else "✅"
                report.append(f"   {risk_level} {change.file_path}")
                if change.security_issues:
                    report.append(f"      🔒 セキュリティ: {', '.join(change.security_issues)}")
                if change.risk_indicators:
                    report.append(f"      ⚠️ リスク: {', '.join(change.risk_indicators)}")
                report.append(f"      📊 変更: +{change.lines_added}/-{change.lines_deleted}")
        
        report.append("")
        report.append("🛡️ 騎士団の誓い: 「コードの平和を守り、バグという名の怪物を討伐せん！」")
        report.append("=" * 64)
        
        return "\n".join(report)
    
    def guard_commit(self) -> int:
        """コミットガード実行（メイン処理）"""
        logger.info("🛡️ コミット前のガード処理開始")
        
        # ステージングされたファイルを取得
        staged_files = self.get_staged_files()
        
        if not staged_files:
            logger.info("📝 ステージングされたファイルがありません")
            return 0
        
        logger.info(f"📝 ステージングファイル: {len(staged_files)}個")
        
        # 各ファイルの変更を分析
        changes = []
        for file_path in staged_files:
            # Python/設定ファイルのみを対象
            if (file_path.endswith(('.py', '.yml', '.yaml', '.json', '.env', '.txt', '.md')) 
                and not file_path.startswith('.git/')):
                
                change = self.get_file_changes(file_path)
                if change:
                    changes.append(change)
        
        if not changes:
            logger.info("✅ 分析対象ファイルがありません")
            return 0
        
        # リスク評価
        assessment = self.assess_commit_risk(changes)
        
        # レポート表示
        report = self.format_assessment_report(assessment, changes)
        print(report)
        
        # 統計更新
        self.stats["commits_checked"] += 1
        if assessment.should_block:
            self.stats["commits_blocked"] += 1
        if assessment.overall_risk in ["HIGH", "CRITICAL"]:
            self.stats["threats_detected"] += 1
        
        # インシデント記録
        if assessment.overall_risk in ["HIGH", "CRITICAL"]:
            incident_data = {
                "type": "precommit_threat",
                "severity": assessment.overall_risk.lower(),
                "description": f"Pre-commit threat detected: {assessment.creature_threat}",
                "files_affected": len(changes),
                "risk_score": assessment.risk_score
            }
            
            creature = self.incident_manager.classify_creature(incident_data)
            logger.info(f"📋 インシデント記録: {creature}")
        
        # ブロック判定
        if assessment.should_block:
            logger.error("🚫 コミットをブロックします")
            return 1
        else:
            logger.info("✅ コミットを許可します")
            return 0


def main():
    """メイン実行関数"""
    try:
        guard = PreCommitIncidentGuard()
        return guard.guard_commit()
    except Exception as e:
        logger.error(f"❌ 騎士団ガードエラー: {e}")
        print(f"""
🚨 騎士団ガードシステムエラー！
エラー: {e}

緊急対応として、手動でのコード確認を強く推奨します。
""")
        return 1


if __name__ == "__main__":
    sys.exit(main())