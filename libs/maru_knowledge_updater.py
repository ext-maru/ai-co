#!/usr/bin/env python3
"""
Maru Knowledge Updater - maruさんナレッジ自動更新システム
会話中の気づきを専用ナレッジベースに自動反映
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MaruKnowledgeUpdater:
    """maruさんナレッジ自動更新システム"""
    
    def __init__(self):
        self.knowledge_file = "/home/aicompany/ai_co/knowledge_base/maru_personal_knowledge.md"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 更新可能なセクション定義
        self.updatable_sections = {
            "basic_policy": "## 🧭 maruさんの基本指針",
            "communication": "## 💬 コミュニケーションスタイル", 
            "tech_direction": "## 🏗️ 技術的志向",
            "decision_pattern": "## 🎯 意思決定パターン",
            "important_decisions": "## 📊 これまでの重要な決定事項",
            "future_focus": "## 🚀 今後の注目ポイント"
        }
    
    def add_new_insight(self, 
                       category: str, 
                       insight: str, 
                       context: str = "",
                       importance: str = "medium"):
        """新しい気づきを追加"""
        self.logger.info(f"Adding new insight to {category}: {insight}")
        
        # 現在のナレッジを読み込み
        if not os.path.exists(self.knowledge_file):
            self.logger.error(f"Knowledge file not found: {self.knowledge_file}")
            return False
        
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新履歴エントリを作成
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        update_entry = f"""
### {timestamp}
- **新しい気づき**: {insight}
- **カテゴリ**: {category}
- **重要度**: {importance}
- **コンテキスト**: {context}
"""
        
        # 更新履歴セクションに追加
        history_marker = "## 📝 更新履歴"
        if history_marker in content:
            # 既存の更新履歴の後に追加
            content = content.replace(
                history_marker,
                history_marker + update_entry
            )
        else:
            # 更新履歴セクションを新規作成
            content += f"\n\n{history_marker}{update_entry}"
        
        # ファイルに書き戻し
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Successfully added insight: {insight}")
        return True
    
    def update_section(self, section: str, new_content: str, append: bool = True):
        """特定セクションの更新"""
        if section not in self.updatable_sections:
            self.logger.error(f"Unknown section: {section}")
            return False
        
        section_header = self.updatable_sections[section]
        
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if section_header in content:
            if append:
                # 既存内容に追加
                # セクションの終わりを見つけて追加
                lines = content.split('\n')
                updated_lines = []
                in_target_section = False
                
                for line in lines:
                    updated_lines.append(line)
                    
                    if line.startswith(section_header):
                        in_target_section = True
                    elif in_target_section and line.startswith('## '):
                        # 次のセクションに到達したら、その前に新しい内容を追加
                        updated_lines.insert(-1, f"\n{new_content}")
                        in_target_section = False
                
                # ファイルの最後まで来た場合
                if in_target_section:
                    updated_lines.append(f"\n{new_content}")
                
                content = '\n'.join(updated_lines)
            else:
                # セクション全体を置き換え（実装省略）
                pass
        
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def record_preference(self, preference_type: str, value: str, context: str = ""):
        """新しい好みや価値観を記録"""
        insight = f"{preference_type}: {value}"
        return self.add_new_insight("preference", insight, context, "high")
    
    def record_decision_pattern(self, situation: str, decision: str, reasoning: str = ""):
        """意思決定パターンを記録"""
        insight = f"状況「{situation}」→判断「{decision}」"
        context = f"判断理由: {reasoning}" if reasoning else ""
        return self.add_new_insight("decision_pattern", insight, context, "high")
    
    def record_communication_style(self, style_note: str, example: str = ""):
        """コミュニケーションスタイルを記録"""
        insight = style_note
        context = f"例: {example}" if example else ""
        return self.add_new_insight("communication", insight, context, "medium")
    
    def get_recent_insights(self, days: int = 7) -> List[Dict]:
        """最近の気づきを取得"""
        # 実装省略 - 必要に応じて後で実装
        return []


# グローバルインスタンス
maru_knowledge_updater = MaruKnowledgeUpdater()


def update_maru_knowledge(category: str, insight: str, context: str = ""):
    """便利関数：maruさんナレッジの更新"""
    return maru_knowledge_updater.add_new_insight(category, insight, context)