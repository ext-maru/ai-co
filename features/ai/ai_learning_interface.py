#!/usr/bin/env python3
from typing import Dict, List

"""
AI自己学習用インターフェース
"""
import sys

sys.path.append("/root/ai_co")
import json

from features.conversation.conversation_manager import ConversationManager
from features.conversation.conversation_search import ConversationSearchEngine


class AILearningInterface:
    def __init__(self):
        self.search_engine = ConversationSearchEngine()
        self.conversation_manager = ConversationManager()

    def learn_from_similar_tasks(self, new_prompt: str) -> Dict:
        """新しいタスクに対して類似タスクから学習"""
        # 類似タスク検索
        similar = self.search_engine.find_similar_tasks(new_prompt, limit=3)

        learning_data = {
            "similar_tasks": similar,
            "patterns": [],
            "suggested_approach": None,
        }

        if similar:
            # 最も類似したタスクの会話履歴を分析
            best_match = similar[0]
            messages = self.conversation_manager.db.get_messages(
                best_match["conversation_id"]
            )

            # パターン抽出
            for msg in messages:
                if msg["message_type"] in ["worker_response", "user_question"]:
                    learning_data["patterns"].append(
                        {"type": msg["message_type"], "content": msg["content"][:100]}
                    )

            # アプローチ提案
            if best_match.get("summary"):
                learning_data["suggested_approach"] = (
                    f"類似タスク（類似度{best_match['similarity_score']:.1%}）"
                    f"の成功例: {best_match['summary']}"
                )

        return learning_data

    def get_learning_context(self, keywords: List[str]) -> str:
        """キーワードから学習コンテキストを構築"""
        # 関連する会話を検索
        related = self.search_engine.search_by_keywords(keywords, limit=5)

        if not related:
            return "関連する過去の会話が見つかりませんでした。"

        context = "【関連する過去の経験】\n"
        for conv in related:
            context += f"- {conv['task_id']}: {conv['preview']}\n"

        # パターン分析
        patterns = self.search_engine.get_conversation_patterns()
        if patterns["common_questions"]:
            context += "\n【よくある質問】\n"
            for q in patterns["common_questions"][:3]:
                context += f"- {q['question']} ({q['count']}回)\n"

        return context

    def generate_self_improvement_report(self) -> str:
        """自己改善レポート生成"""
        report = self.search_engine.generate_ai_report()

        output = "=== AI自己改善レポート ===\n\n"

        # 統計
        output += f"【統計情報】\n"
        output += f"- 平均メッセージ数: {report['patterns']['average_messages']}\n"
        output += f"- タスク完了率: {report['patterns']['completion_rate']}%\n\n"

        # タスクタイプ
        output += f"【タスクタイプ分布】\n"
        for task_type, count in report["task_types"].items():
            output += f"- {task_type}: {count}件\n"
        output += "\n"

        # 推奨事項
        output += f"【改善推奨事項】\n"
        for rec in report["recommendations"]:
            output += f"- {rec}\n"

        return output
