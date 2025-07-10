#!/usr/bin/env python3
"""
インシデント管理ライブラリ
エラーや問題をインシデントとして記録・管理
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging


class IncidentManager:
    """インシデント賢者 (Crisis Sage) - 4賢者システム統合
    
    Elders Guildの4賢者システムの一翼を担う、危機対応専門の賢者。
    問題の即座感知・解決、エラー検知、自動復旧、インシデント履歴管理を行う。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.incident_file = Path('/home/aicompany/ai_co/knowledge_base/incident_history.json')
        self._ensure_incident_file()
        
        # 4賤者システム統合
        self.sage_type = "Crisis Sage"
        self.wisdom_level = "incident_response"
        self.collaboration_mode = True
        self.crisis_detection_enabled = True
        
        self.logger.info(f"😨 {self.sage_type} 初期化完了 - 危機対応システムアクティブ")
    
    def _ensure_incident_file(self):
        """インシデント履歴ファイルが存在することを確認"""
        if not self.incident_file.exists():
            self.incident_file.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "last_updated": datetime.now().isoformat(),
                    "total_incidents": 0,
                    "open_incidents": 0,
                    "resolved_incidents": 0,
                    "categories": {
                        "error": "システムエラー・例外",
                        "failure": "サービス障害・機能不全",
                        "request": "機能要求・サービス要求",
                        "change": "変更要求・設定変更",
                        "security": "セキュリティインシデント",
                        "performance": "パフォーマンス問題"
                    }
                },
                "incidents": [],
                "category_statistics": {
                    "error": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "failure": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "request": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "change": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "security": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "performance": {"count": 0, "open": 0, "avg_resolution_time": None}
                },
                "priority_statistics": {
                    "critical": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "high": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "medium": {"count": 0, "open": 0, "avg_resolution_time": None},
                    "low": {"count": 0, "open": 0, "avg_resolution_time": None}
                }
            }
            with open(self.incident_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def create_incident(self, 
                       category: str,
                       priority: str,
                       title: str,
                       description: str,
                       affected_components: List[str],
                       impact: str,
                       assignee: str = "ai_system",
                       metadata: Optional[Dict] = None) -> str:
        """新しいインシデントを作成"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            # インシデントID生成
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(data['metadata']['total_incidents'] + 1).zfill(4)}"
            
            # インシデントデータ
            incident = {
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "priority": priority,
                "title": title,
                "description": description,
                "affected_components": affected_components,
                "impact": impact,
                "status": "open",
                "assignee": assignee,
                "resolution": None,
                "timeline": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "action": "インシデント作成",
                        "details": f"カテゴリ: {category}, 優先度: {priority}"
                    }
                ],
                "metadata": metadata or {}
            }
            
            # データ更新
            data['incidents'].append(incident)
            data['metadata']['total_incidents'] += 1
            data['metadata']['open_incidents'] += 1
            data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # カテゴリ統計更新
            if category in data['category_statistics']:
                data['category_statistics'][category]['count'] += 1
                data['category_statistics'][category]['open'] += 1
            
            # 優先度統計更新
            if priority in data['priority_statistics']:
                data['priority_statistics'][priority]['count'] += 1
                data['priority_statistics'][priority]['open'] += 1
            
            # ファイル保存
            with open(self.incident_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created incident: {incident_id}")
            return incident_id
            
        except Exception as e:
            self.logger.error(f"Failed to create incident: {str(e)}")
            raise
    
    def add_action(self, incident_id: str, action: str, details: Optional[Dict] = None):
        """インシデントにアクションを追加"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            # インシデントを検索
            for incident in data['incidents']:
                if incident['incident_id'] == incident_id:
                    incident['timeline'].append({
                        "timestamp": datetime.now().isoformat(),
                        "action": action,
                        "details": details or {}
                    })
                    break
            
            # ファイル保存
            with open(self.incident_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to add action to incident {incident_id}: {str(e)}")
    
    def resolve_incident(self, 
                        incident_id: str,
                        resolution: str,
                        actions_taken: List[str],
                        root_cause: str,
                        preventive_measures: List[str]):
        """インシデントを解決"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            # インシデントを検索
            for incident in data['incidents']:
                if incident['incident_id'] == incident_id and incident['status'] == 'open':
                    # 解決情報を追加
                    incident['status'] = 'resolved'
                    incident['resolution'] = {
                        "timestamp": datetime.now().isoformat(),
                        "description": resolution,
                        "actions_taken": actions_taken,
                        "root_cause": root_cause,
                        "preventive_measures": preventive_measures
                    }
                    
                    # タイムラインに追加
                    incident['timeline'].append({
                        "timestamp": datetime.now().isoformat(),
                        "action": "インシデント解決",
                        "details": {
                            "resolution": resolution,
                            "root_cause": root_cause
                        }
                    })
                    
                    # 統計更新
                    data['metadata']['open_incidents'] -= 1
                    data['metadata']['resolved_incidents'] += 1
                    
                    # カテゴリ統計更新
                    category = incident['category']
                    if category in data['category_statistics']:
                        data['category_statistics'][category]['open'] -= 1
                    
                    # 優先度統計更新
                    priority = incident['priority']
                    if priority in data['priority_statistics']:
                        data['priority_statistics'][priority]['open'] -= 1
                    
                    break
            
            data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # ファイル保存
            with open(self.incident_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Resolved incident: {incident_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to resolve incident {incident_id}: {str(e)}")
    
    def get_open_incidents(self) -> List[Dict]:
        """オープン中のインシデントを取得"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            return [inc for inc in data['incidents'] if inc['status'] == 'open']
            
        except Exception as e:
            self.logger.error(f"Failed to get open incidents: {str(e)}")
            return []
    
    def get_incident_statistics(self) -> Dict:
        """インシデント統計を取得"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            return {
                'total': data['metadata']['total_incidents'],
                'open': data['metadata']['open_incidents'],
                'resolved': data['metadata']['resolved_incidents'],
                'by_category': data['category_statistics'],
                'by_priority': data['priority_statistics']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {}
    
    def search_similar_incidents(self, error_text: str, limit: int = 5) -> List[Dict]:
        """類似のインシデントを検索"""
        try:
            with open(self.incident_file, 'r') as f:
                data = json.load(f)
            
            # 簡易的な類似度計算（キーワードマッチング）
            error_keywords = set(error_text.lower().split())
            similar_incidents = []
            
            for incident in data['incidents']:
                if incident['status'] == 'resolved':
                    incident_text = (incident['title'] + ' ' + incident['description']).lower()
                    incident_keywords = set(incident_text.split())
                    
                    # キーワードの重複数を計算
                    common_keywords = len(error_keywords & incident_keywords)
                    if common_keywords > 2:  # 2つ以上のキーワードが一致
                        similar_incidents.append({
                            'incident': incident,
                            'similarity': common_keywords
                        })
            
            # 類似度でソート
            similar_incidents.sort(key=lambda x: x['similarity'], reverse=True)
            
            return [item['incident'] for item in similar_incidents[:limit]]
            
        except Exception as e:
            self.logger.error(f"Failed to search similar incidents: {str(e)}")
            return []
