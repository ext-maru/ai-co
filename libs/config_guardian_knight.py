#!/usr/bin/env python3
"""
🛡️ Configuration Guardian Knight
設定守護騎士 - 設定ファイル問題の自動検出・修復
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.unified_config_manager import config_manager
from libs.incident_knights_framework import (
    IncidentKnight, KnightType, Issue, Diagnosis, Resolution,
    IssueCategory, IssueSeverity
)

logger = logging.getLogger(__name__)

class ConfigGuardianKnight(IncidentKnight):
    """設定守護騎士 - 全設定ファイルの監視・保護"""
    
    def __init__(self, knight_id: str = "config_guardian_001"):
        super().__init__(knight_id, KnightType.DIAGNOSTIC, "config_guardian")
        
        self.watched_namespaces = ['slack', 'database', 'worker']
        self.repair_history = []
        
    async def patrol(self) -> List[Issue]:
        """設定問題の巡回検出"""
        issues = []
        
        self.logger.info("🔍 設定ファイルスキャン開始...")
        
        # 全ネームスペースの健全性チェック
        health_results = config_manager.health_check()
        
        for namespace, health in health_results.items():
            if health['status'] == 'error':
                issue = Issue(
                    id=f"config_{namespace}_{datetime.now().strftime('%H%M%S')}",
                    title=f"設定エラー: {namespace}",
                    description=f"設定取得エラー: {health['error']}",
                    category=IssueCategory.CONFIGURATION,
                    severity=IssueSeverity.HIGH,
                    source=f"config_guardian",
                    metadata={
                        'namespace': namespace,
                        'error': health['error'],
                        'available_sources': health.get('sources_found', [])
                    }
                )
                issues.append(issue)
                
        self.logger.info(f"🔍 設定問題検出完了: {len(issues)}件")
        return issues
        
    async def diagnose(self, issue: Issue) -> Diagnosis:
        """設定問題の詳細診断"""
        namespace = issue.metadata.get('namespace')
        
        diagnosis_data = {
            'namespace': namespace,
            'timestamp': datetime.now().isoformat(),
            'available_sources': [],
            'missing_sources': [],
            'backup_available': False,
            'auto_repair_possible': False
        }
        
        # 利用可能なソースを確認
        sources = config_manager.sources.get(namespace, [])
        for source in sources:
            if source.path.exists():
                diagnosis_data['available_sources'].append(str(source.path))
            else:
                diagnosis_data['missing_sources'].append(str(source.path))
                
        # バックアップの存在確認
        primary_source = config_manager._get_primary_source(namespace)
        if primary_source:
            pattern = f"{primary_source.path.name}.*.backup"
            backups = list(config_manager.backup_dir.glob(pattern))
            diagnosis_data['backup_available'] = len(backups) > 0
            diagnosis_data['backup_count'] = len(backups)
            
        # 自動修復可能性の判定
        diagnosis_data['auto_repair_possible'] = (
            len(diagnosis_data['available_sources']) > 0 or
            diagnosis_data['backup_available']
        )
        
        return Diagnosis(
            issue_id=issue.id,
            root_cause=f"設定ファイルエラー: {namespace}",
            affected_components=[namespace],
            repair_complexity="自動修復可能" if diagnosis_data['auto_repair_possible'] else "手動対応必要",
            estimated_impact="設定取得失敗による機能停止",
            data=diagnosis_data
        )
        
    async def repair(self, issue: Issue, diagnosis: Diagnosis) -> Resolution:
        """設定問題の自動修復"""
        namespace = issue.metadata.get('namespace')
        
        start_time = datetime.now()
        repair_actions = []
        success = False
        
        try:
            self.logger.info(f"🔧 設定自動修復開始: {namespace}")
            
            # 1. 自動修復を試行
            repair_actions.append("設定自動修復を実行")
            success = config_manager.auto_repair(namespace)
            
            if success:
                repair_actions.append("✅ 設定の自動修復に成功")
                
                # 2. 修復後の検証
                repair_actions.append("修復後の検証を実行")
                try:
                    repaired_config = config_manager.get_config(namespace)
                    repair_actions.append(f"✅ 設定取得成功: {len(repaired_config)}個のキー")
                    
                    # 3. 修復履歴を記録
                    self.repair_history.append({
                        'timestamp': start_time.isoformat(),
                        'namespace': namespace,
                        'success': True,
                        'actions': repair_actions.copy()
                    })
                    
                except Exception as e:
                    repair_actions.append(f"❌ 修復後検証失敗: {e}")
                    success = False
            else:
                repair_actions.append("❌ 自動修復に失敗")
                
        except Exception as e:
            repair_actions.append(f"❌ 修復中にエラー: {e}")
            success = False
            
        # 修復結果の記録
        if not success:
            self.repair_history.append({
                'timestamp': start_time.isoformat(),
                'namespace': namespace,
                'success': False,
                'actions': repair_actions.copy()
            })
            
        duration = (datetime.now() - start_time).total_seconds()
        
        return Resolution(
            issue_id=issue.id,
            status="resolved" if success else "failed",
            actions_taken=repair_actions,
            time_to_resolution=duration,
            metadata={
                'namespace': namespace,
                'repair_method': 'auto_repair',
                'success': success
            }
        )
        
    async def continuous_monitoring(self, interval: int = 300):
        """継続的な設定監視"""
        self.logger.info(f"🛡️ 設定継続監視開始 (間隔: {interval}秒)")
        
        while True:
            try:
                # 問題検出
                issues = await self.patrol()
                
                # 検出された問題を自動修復
                for issue in issues:
                    self.logger.warning(f"🚨 設定問題検出: {issue.title}")
                    
                    diagnosis = await self.diagnose(issue)
                    
                    if diagnosis.data.get('auto_repair_possible', False):
                        resolution = await self.repair(issue, diagnosis)
                        
                        if resolution.status == "resolved":
                            self.logger.info(f"✅ 自動修復成功: {issue.title}")
                        else:
                            self.logger.error(f"❌ 自動修復失敗: {issue.title}")
                            # エルダー会議にエスカレーション
                            await self._escalate_to_elder_council(issue, diagnosis, resolution)
                    else:
                        self.logger.warning(f"⚠️ 手動対応必要: {issue.title}")
                        await self._escalate_to_elder_council(issue, diagnosis)
                        
            except Exception as e:
                self.logger.error(f"監視中にエラー: {e}")
                
            await asyncio.sleep(interval)
            
    async def _escalate_to_elder_council(self, issue: Issue, diagnosis: Diagnosis, resolution: Resolution = None):
        """エルダー会議へのエスカレーション"""
        escalation_data = {
            'timestamp': datetime.now().isoformat(),
            'issue': {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'severity': issue.severity.value
            },
            'diagnosis': {
                'root_cause': diagnosis.root_cause,
                'affected_components': diagnosis.affected_components,
                'repair_complexity': diagnosis.repair_complexity
            },
            'knight_id': self.knight_id,
            'escalation_reason': '自動修復失敗' if resolution else '手動対応必要'
        }
        
        if resolution:
            escalation_data['failed_resolution'] = {
                'status': resolution.status,
                'actions_taken': resolution.actions_taken
            }
            
        # エルダー会議への報告ファイルを作成
        report_path = Path("knowledge_base/elder_council_requests") / f"config_issue_{issue.id}.md"
        report_path.parent.mkdir(exist_ok=True)
        
        report_content = f"""# 🚨 設定問題エスカレーション

## 問題概要
- **ID**: {issue.id}
- **タイトル**: {issue.title}
- **重要度**: {issue.severity.value}
- **発生時刻**: {escalation_data['timestamp']}

## 詳細情報
{issue.description}

## 診断結果
- **根本原因**: {diagnosis.root_cause}
- **影響コンポーネント**: {', '.join(diagnosis.affected_components)}
- **修復複雑度**: {diagnosis.repair_complexity}

## 騎士団による対応
- **担当騎士**: {self.knight_id}
- **エスカレーション理由**: {escalation_data['escalation_reason']}

{'## 失敗した修復試行' if resolution else '## 自動修復不可能'}
{'- ' + chr(10).join(f'- {action}' for action in resolution.actions_taken) if resolution else '設定の手動対応が必要です。'}

## 推奨対応
1. 設定ファイルの手動確認
2. 必要な設定値の再設定
3. システム再起動

---
*Report generated by Config Guardian Knight*
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        self.logger.info(f"📝 エルダー会議報告作成: {report_path}")
        
    def get_status_report(self) -> Dict[str, Any]:
        """ステータスレポートを生成"""
        health_results = config_manager.health_check()
        
        return {
            'knight_id': self.knight_id,
            'timestamp': datetime.now().isoformat(),
            'watched_namespaces': self.watched_namespaces,
            'health_status': health_results,
            'repair_history_count': len(self.repair_history),
            'recent_repairs': self.repair_history[-5:] if self.repair_history else []
        }

# 設定守護騎士のシングルトンインスタンス
config_guardian = ConfigGuardianKnight()

async def start_config_guardian():
    """設定守護騎士の起動"""
    await config_guardian.continuous_monitoring()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_config_guardian())