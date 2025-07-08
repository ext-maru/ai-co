#!/usr/bin/env python3
"""
Sage Propagation Engine - 4賢者反映エンジン
承認された報告を適切な賢者へ高品質に反映
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class PropagationAction:
    """反映アクション"""
    target_sage: str
    action_type: str
    content: Dict
    priority: str
    metadata: Dict


@dataclass
class PropagationResult:
    """反映結果"""
    success: bool
    actions_executed: List[PropagationAction]
    errors: List[str]
    propagation_id: str
    timestamp: str


class SagePropagationEngine:
    """4賢者反映エンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_path = "/home/aicompany/ai_co"
        
        # 各賢者の設定
        self.sage_configs = {
            "knowledge_sage": {
                "storage_path": f"{self.base_path}/knowledge_base",
                "index_file": f"{self.base_path}/knowledge_base/.elders_knowledge_index.md",
                "supported_actions": ["store_document", "update_index", "create_reference"]
            },
            "incident_sage": {
                "storage_path": f"{self.base_path}/knowledge_base/incident_management",
                "incident_tracker": f"{self.base_path}/libs/incident_manager.py",
                "supported_actions": ["create_incident", "update_incident", "escalate"]
            },
            "task_sage": {
                "storage_path": f"{self.base_path}/task_history.db",
                "task_tracker": f"{self.base_path}/libs/claude_task_tracker.py",
                "supported_actions": ["create_task", "update_task", "schedule"]
            },
            "rag_sage": {
                "index_path": f"{self.base_path}/rag_index",
                "rag_manager": f"{self.base_path}/libs/enhanced_rag_manager.py",
                "supported_actions": ["index_document", "update_embeddings", "create_relations"]
            }
        }
    
    def propagate_to_sages(self, 
                          report: Dict, 
                          propagation_targets: List[str],
                          report_id: str) -> PropagationResult:
        """4賢者への反映実行"""
        self.logger.info(f"Starting propagation for report {report_id} to {len(propagation_targets)} sages")
        
        propagation_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{report_id}"
        actions_executed = []
        errors = []
        
        # 各賢者への反映処理
        for target_sage in propagation_targets:
            try:
                actions = self._generate_sage_actions(target_sage, report, report_id)
                
                for action in actions:
                    success = self._execute_action(action)
                    if success:
                        actions_executed.append(action)
                        self.logger.info(f"Successfully executed {action.action_type} for {target_sage}")
                    else:
                        error_msg = f"Failed to execute {action.action_type} for {target_sage}"
                        errors.append(error_msg)
                        self.logger.error(error_msg)
                        
            except Exception as e:
                error_msg = f"Error propagating to {target_sage}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # 反映結果の記録
        result = PropagationResult(
            success=len(errors) == 0,
            actions_executed=actions_executed,
            errors=errors,
            propagation_id=propagation_id,
            timestamp=datetime.now().isoformat()
        )
        
        self._record_propagation_result(result, report_id)
        
        return result
    
    def _generate_sage_actions(self, 
                              target_sage: str, 
                              report: Dict, 
                              report_id: str) -> List[PropagationAction]:
        """賢者別のアクション生成"""
        actions = []
        
        if target_sage == "knowledge_sage":
            actions.extend(self._generate_knowledge_actions(report, report_id))
        elif target_sage == "incident_sage":
            actions.extend(self._generate_incident_actions(report, report_id))
        elif target_sage == "task_sage":
            actions.extend(self._generate_task_actions(report, report_id))
        elif target_sage == "rag_sage":
            actions.extend(self._generate_rag_actions(report, report_id))
        
        return actions
    
    def _generate_knowledge_actions(self, report: Dict, report_id: str) -> List[PropagationAction]:
        """ナレッジ賢者向けアクション生成"""
        actions = []
        
        # 1. 文書の保存
        document_content = self._format_for_knowledge_storage(report, report_id)
        
        store_action = PropagationAction(
            target_sage="knowledge_sage",
            action_type="store_document",
            content={
                "file_path": f"{self.sage_configs['knowledge_sage']['storage_path']}/council_reports/{report_id}_report.md",
                "content": document_content,
                "title": report.get('title', 'Untitled Report')
            },
            priority=report.get('priority', 'medium'),
            metadata={
                "category": report.get('category', 'general'),
                "tags": report.get('tags', []),
                "source": "elder_council"
            }
        )
        actions.append(store_action)
        
        # 2. インデックスの更新
        index_action = PropagationAction(
            target_sage="knowledge_sage",
            action_type="update_index",
            content={
                "index_file": self.sage_configs['knowledge_sage']['index_file'],
                "entry": f"- **[{report_id}_report.md](council_reports/{report_id}_report.md)** - {report.get('title', 'Report')}"
            },
            priority="low",
            metadata={"section": "## 🏛️ エルダー評議会報告"}
        )
        actions.append(index_action)
        
        return actions
    
    def _generate_incident_actions(self, report: Dict, report_id: str) -> List[PropagationAction]:
        """インシデント賢者向けアクション生成"""
        actions = []
        
        # エラー・障害関連キーワードの抽出
        content = report.get('content', '').lower()
        
        # 緊急度の判定
        urgency = self._assess_incident_urgency(report)
        
        # インシデント作成
        incident_action = PropagationAction(
            target_sage="incident_sage",
            action_type="create_incident",
            content={
                "title": f"[Council] {report.get('title', 'Incident')}",
                "description": report.get('content', ''),
                "category": self._categorize_incident(content),
                "urgency": urgency,
                "source_report_id": report_id,
                "affected_systems": self._extract_affected_systems(content)
            },
            priority=urgency,
            metadata={
                "auto_created": True,
                "council_report": report_id
            }
        )
        actions.append(incident_action)
        
        return actions
    
    def _generate_task_actions(self, report: Dict, report_id: str) -> List[PropagationAction]:
        """タスク賢者向けアクション生成"""
        actions = []
        
        # アクションアイテムの抽出
        action_items = self._extract_action_items(report.get('content', ''))
        
        for i, action_item in enumerate(action_items):
            task_action = PropagationAction(
                target_sage="task_sage",
                action_type="create_task",
                content={
                    "title": f"{report.get('title', 'Task')} - {action_item.get('title', f'Action {i+1}')}",
                    "description": action_item.get('description', ''),
                    "priority": self._map_priority(report.get('priority', 'medium')),
                    "category": report.get('category', 'general'),
                    "source_report_id": report_id,
                    "estimated_effort": action_item.get('effort', 'unknown'),
                    "deadline": action_item.get('deadline')
                },
                priority=report.get('priority', 'medium'),
                metadata={
                    "source": "elder_council",
                    "action_index": i
                }
            )
            actions.append(task_action)
        
        return actions
    
    def _generate_rag_actions(self, report: Dict, report_id: str) -> List[PropagationAction]:
        """RAG賢者向けアクション生成"""
        actions = []
        
        # 文書のインデックス登録
        index_action = PropagationAction(
            target_sage="rag_sage",
            action_type="index_document",
            content={
                "document_id": f"council_report_{report_id}",
                "title": report.get('title', 'Report'),
                "content": report.get('content', ''),
                "metadata": {
                    "category": report.get('category', 'general'),
                    "priority": report.get('priority', 'medium'),
                    "tags": report.get('tags', []),
                    "source": "elder_council",
                    "timestamp": datetime.now().isoformat()
                },
                "keywords": self._extract_keywords(report.get('content', ''))
            },
            priority="low",
            metadata={"vectorize": True}
        )
        actions.append(index_action)
        
        # 関連文書との関係性作成
        relations_action = PropagationAction(
            target_sage="rag_sage",
            action_type="create_relations",
            content={
                "source_doc": f"council_report_{report_id}",
                "related_keywords": self._extract_keywords(report.get('content', '')),
                "relation_type": "council_report"
            },
            priority="low",
            metadata={"auto_generated": True}
        )
        actions.append(relations_action)
        
        return actions
    
    def _execute_action(self, action: PropagationAction) -> bool:
        """アクションの実行"""
        try:
            if action.target_sage == "knowledge_sage":
                return self._execute_knowledge_action(action)
            elif action.target_sage == "incident_sage":
                return self._execute_incident_action(action)
            elif action.target_sage == "task_sage":
                return self._execute_task_action(action)
            elif action.target_sage == "rag_sage":
                return self._execute_rag_action(action)
            else:
                self.logger.error(f"Unknown target sage: {action.target_sage}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing action {action.action_type}: {str(e)}")
            return False
    
    def _execute_knowledge_action(self, action: PropagationAction) -> bool:
        """ナレッジ賢者へのアクション実行"""
        if action.action_type == "store_document":
            # ディレクトリ作成
            file_path = action.content["file_path"]
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # ファイル書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(action.content["content"])
            
            return True
            
        elif action.action_type == "update_index":
            # インデックスファイルの更新（簡易実装）
            index_file = action.content["index_file"]
            entry = action.content["entry"]
            
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # セクションの検索と追加
                section = action.metadata.get("section", "## 📚 その他の文書")
                if section in content:
                    # セクションの終わりに追加
                    content = content.replace(section, f"{section}\n{entry}")
                else:
                    # セクションを作成
                    content += f"\n\n{section}\n{entry}"
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return True
        
        return False
    
    def _execute_incident_action(self, action: PropagationAction) -> bool:
        """インシデント賢者へのアクション実行"""
        if action.action_type == "create_incident":
            # インシデント管理ディレクトリに保存
            incident_dir = self.sage_configs["incident_sage"]["storage_path"]
            os.makedirs(incident_dir, exist_ok=True)
            
            incident_file = f"{incident_dir}/incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            incident_content = f"""# {action.content['title']}

**作成日**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**カテゴリ**: {action.content['category']}
**緊急度**: {action.content['urgency']}
**ソース**: エルダー評議会報告 ({action.content['source_report_id']})

## 説明
{action.content['description']}

## 影響システム
{', '.join(action.content.get('affected_systems', ['未特定']))}

## ステータス
- [ ] 調査中
- [ ] 対応中
- [ ] 解決済み
"""
            
            with open(incident_file, 'w', encoding='utf-8') as f:
                f.write(incident_content)
            
            return True
        
        return False
    
    def _execute_task_action(self, action: PropagationAction) -> bool:
        """タスク賢者へのアクション実行"""
        if action.action_type == "create_task":
            # タスク管理ファイルに記録
            task_log_file = f"{self.base_path}/task_council_integration.log"
            
            task_record = {
                "timestamp": datetime.now().isoformat(),
                "task_id": f"council_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": action.content["title"],
                "description": action.content["description"],
                "priority": action.content["priority"],
                "category": action.content["category"],
                "source_report": action.content["source_report_id"],
                "status": "pending"
            }
            
            with open(task_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(task_record, ensure_ascii=False) + "\n")
            
            return True
        
        return False
    
    def _execute_rag_action(self, action: PropagationAction) -> bool:
        """RAG賢者へのアクション実行"""
        if action.action_type == "index_document":
            # RAGインデックスファイルに記録
            rag_index_dir = self.sage_configs["rag_sage"]["index_path"]
            os.makedirs(rag_index_dir, exist_ok=True)
            
            index_file = f"{rag_index_dir}/council_reports_index.jsonl"
            
            document_record = {
                "document_id": action.content["document_id"],
                "title": action.content["title"],
                "content": action.content["content"],
                "metadata": action.content["metadata"],
                "keywords": action.content["keywords"],
                "indexed_at": datetime.now().isoformat()
            }
            
            with open(index_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(document_record, ensure_ascii=False) + "\n")
            
            return True
        
        return False
    
    def _format_for_knowledge_storage(self, report: Dict, report_id: str) -> str:
        """ナレッジ保存用フォーマット"""
        content = f"""# {report.get('title', 'Report')}

**報告ID**: {report_id}
**カテゴリ**: {report.get('category', 'general')}
**優先度**: {report.get('priority', 'medium')}
**作成日**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 内容
{report.get('content', '')}

"""
        
        # メタデータの追加
        if 'tags' in report:
            content += f"\n**タグ**: {', '.join(report['tags'])}\n"
        
        if 'enhancement_log' in report:
            content += "\n## 改善履歴\n"
            for improvement in report['enhancement_log']:
                content += f"- {improvement}\n"
        
        content += f"\n---\n*エルダー評議会承認済み報告*"
        
        return content
    
    def _assess_incident_urgency(self, report: Dict) -> str:
        """インシデント緊急度の評価"""
        content = report.get('content', '').lower()
        priority = report.get('priority', 'medium').lower()
        
        # 高緊急度キーワード
        high_urgency_keywords = ['critical', 'urgent', 'down', 'failure', 'emergency', '緊急', '障害', '停止']
        
        if priority in ['high', 'critical'] or any(keyword in content for keyword in high_urgency_keywords):
            return "high"
        elif priority == "low":
            return "low"
        else:
            return "medium"
    
    def _categorize_incident(self, content: str) -> str:
        """インシデントカテゴリの判定"""
        categories = {
            'performance': ['slow', '遅い', 'timeout', 'performance'],
            'security': ['security', 'vulnerability', 'auth', 'セキュリティ'],
            'database': ['database', 'db', 'sql', 'データベース'],
            'network': ['network', 'connection', 'ネットワーク', '接続'],
            'system': ['system', 'server', 'service', 'システム', 'サーバー']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                return category
        
        return "general"
    
    def _extract_affected_systems(self, content: str) -> List[str]:
        """影響システムの抽出"""
        systems = []
        
        # システム名のパターン
        system_patterns = [
            r'(\w+Service)',
            r'(\w+Manager)',
            r'(\w+Monitor)',
            r'(\w+Worker)',
            r'(\w+Engine)'
        ]
        
        for pattern in system_patterns:
            matches = re.findall(pattern, content)
            systems.extend(matches)
        
        return list(set(systems)) if systems else ["unknown"]
    
    def _extract_action_items(self, content: str) -> List[Dict]:
        """アクションアイテムの抽出"""
        action_items = []
        
        # アクション関連のパターン
        action_patterns = [
            r'[-*]\s*(.*(実装|implement|修正|fix|調査|investigate|確認|check|作成|create|更新|update).*)',
            r'(\d+\.\s*.*(実装|implement|修正|fix|調査|investigate|確認|check|作成|create|更新|update).*)',
            r'(.*必要.*)',
            r'(.*すべき.*)',
            r'(.*する.*)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                action_item = {
                    "title": match.strip()[:50] + "..." if len(match) > 50 else match.strip(),
                    "description": match.strip(),
                    "effort": self._estimate_effort(match),
                    "deadline": self._extract_deadline(match)
                }
                action_items.append(action_item)
        
        return action_items[:5]  # 最大5個まで
    
    def _extract_keywords(self, content: str) -> List[str]:
        """キーワードの抽出"""
        # 技術キーワードの抽出
        tech_keywords = [
            'error', 'エラー', 'exception', 'failure', 'timeout',
            'performance', 'パフォーマンス', 'slow', '遅い',
            'database', 'データベース', 'sql', 'query',
            'service', 'サービス', 'api', 'endpoint',
            'monitoring', '監視', 'alert', 'アラート',
            'security', 'セキュリティ', 'auth', '認証'
        ]
        
        found_keywords = []
        content_lower = content.lower()
        
        for keyword in tech_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        # カスタムキーワードの抽出（大文字で始まる単語）
        custom_keywords = re.findall(r'\b[A-Z][a-zA-Z]+(?:Service|Manager|Monitor|Worker|Engine)\b', content)
        found_keywords.extend(custom_keywords)
        
        return list(set(found_keywords))
    
    def _estimate_effort(self, action_text: str) -> str:
        """作業量の推定"""
        action_lower = action_text.lower()
        
        if any(word in action_lower for word in ['調査', 'investigate', 'check', '確認']):
            return "small"
        elif any(word in action_lower for word in ['修正', 'fix', '更新', 'update']):
            return "medium"
        elif any(word in action_lower for word in ['実装', 'implement', '作成', 'create']):
            return "large"
        else:
            return "unknown"
    
    def _extract_deadline(self, action_text: str) -> Optional[str]:
        """期限の抽出"""
        deadline_patterns = [
            r'(\d{4}[-/]\d{2}[-/]\d{2})',
            r'(まで|by|until)',
            r'(\d+日)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, action_text)
            if match:
                return match.group(1)
        
        return None
    
    def _map_priority(self, priority: str) -> str:
        """優先度のマッピング"""
        priority_map = {
            "high": "urgent",
            "medium": "normal",
            "low": "low"
        }
        return priority_map.get(priority.lower(), "normal")
    
    def _record_propagation_result(self, result: PropagationResult, report_id: str):
        """反映結果の記録"""
        record_file = f"{self.base_path}/knowledge_base/council_reports/propagation_log.jsonl"
        
        os.makedirs(os.path.dirname(record_file), exist_ok=True)
        
        record = {
            "report_id": report_id,
            "propagation_id": result.propagation_id,
            "timestamp": result.timestamp,
            "success": result.success,
            "actions_count": len(result.actions_executed),
            "errors_count": len(result.errors),
            "actions": [asdict(action) for action in result.actions_executed],
            "errors": result.errors
        }
        
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        self.logger.info(f"Propagation result recorded: {result.propagation_id}")
    
    def get_propagation_history(self, report_id: Optional[str] = None) -> List[Dict]:
        """反映履歴の取得"""
        record_file = f"{self.base_path}/knowledge_base/council_reports/propagation_log.jsonl"
        
        if not os.path.exists(record_file):
            return []
        
        history = []
        with open(record_file, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line.strip())
                if report_id is None or record.get('report_id') == report_id:
                    history.append(record)
        
        return history