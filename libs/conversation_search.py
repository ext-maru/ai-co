#!/usr/bin/env python3
"""
AI向け会話検索・分析エンジン
"""
import json
import logging
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConversationSearchEngine:
    """ConversationSearchEngine - エンジンクラス"""
    def __init__(self, db_path="/home/aicompany/ai_co/conversations.db"):
        """初期化メソッド"""
        self.db_path = db_path

    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """キーワードで会話を検索（AI学習用）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # キーワード条件構築
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("m.content LIKE ?")
            params.append(f"%{keyword}%")

        where_clause = " OR ".join(conditions)

        query = f"""
            SELECT DISTINCT c.conversation_id, c.task_id, c.state,
                   GROUP_CONCAT(m.content, ' ') as all_content,
                   COUNT(m.message_id) as relevance_score
            FROM conversations c
            JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE {where_clause}
            GROUP BY c.conversation_id
            ORDER BY relevance_score DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "conversation_id": row["conversation_id"],
                    "task_id": row["task_id"],
                    "state": row["state"],
                    "relevance_score": row["relevance_score"],
                    "preview": row["all_content"][:200] + "...",
                }
            )

        conn.close()
        return results

    def find_similar_tasks(self, prompt: str, limit: int = 5) -> List[Dict]:
        """類似タスクを検索（AIが参考にする）"""
        # プロンプトからキーワード抽出
        keywords = self._extract_keywords(prompt)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 初期プロンプトが似ている会話を検索
        cursor.execute(
            """
            SELECT c.conversation_id, c.task_id,
                   m.content as initial_prompt,
                   (SELECT content FROM conversation_messages
                    WHERE conversation_id = c.conversation_id
                    AND message_type = 'summary'
                    LIMIT 1) as summary
            FROM conversations c
            JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE m.message_type = 'initial_prompt'
            AND c.state = 'completed'
            ORDER BY c.created_at DESC
            LIMIT ?
        """,
            (limit * 3,),
        )  # 多めに取得してフィルタリング

        # スコアリング
        similar_tasks = []
        for row in cursor.fetchall():
            score = self._calculate_similarity(prompt, row["initial_prompt"])
            if score > 0.3:  # 閾値
                similar_tasks.append(
                    {
                        "conversation_id": row["conversation_id"],
                        "task_id": row["task_id"],
                        "initial_prompt": row["initial_prompt"],
                        "summary": row["summary"],
                        "similarity_score": score,
                    }
                )

        conn.close()

        # スコア順でソート
        similar_tasks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_tasks[:limit]

    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワード抽出"""
        # 簡易実装：重要そうな単語を抽出
        important_words = []

        # 技術用語パターン
        tech_patterns = [
            r"Python|JavaScript|HTML|CSS|SQL",
            r"Web|API|データベース|DB",
            r"関数|クラス|メソッド",
            r"作成|実装|開発|構築",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            important_words.extend(matches)

        # 名詞っぽい単語（簡易）
        words = re.findall(r"[ァ-ヶー]+|[a-zA-Z]+", text)
        important_words.extend([w for w in words if len(w) > 2])

        return list(set(important_words))

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算（簡易版）"""
        words1 = set(self._extract_keywords(text1.lower()))
        words2 = set(self._extract_keywords(text2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard係数
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def get_conversation_patterns(self) -> Dict:
        """会話パターン分析（AI学習用）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        patterns = {
            "common_questions": [],
            "successful_patterns": [],
            "failure_patterns": [],
            "average_messages": 0,
            "completion_rate": 0,
        }

        # よくある質問パターン
        cursor.execute(
            """
            SELECT content, COUNT(*) as count
            FROM conversation_messages
            WHERE message_type = 'user_question'
            GROUP BY content
            ORDER BY count DESC
            LIMIT 10
        """
        )
        patterns["common_questions"] = [
            {"question": row[0], "count": row[1]} for row in cursor.fetchall()
        ]

        # 成功パターン
        cursor.execute(
            """
            SELECT c.conversation_id, COUNT(m.message_id) as msg_count
            FROM conversations c
            JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.state = 'completed'
            GROUP BY c.conversation_id
            ORDER BY msg_count ASC
            LIMIT 5
        """
        )
        patterns["successful_patterns"] = [
            {"conversation_id": row[0], "message_count": row[1]}
            for row in cursor.fetchall()
        ]

        # 統計
        cursor.execute(
            """
            SELECT AVG(msg_count) as avg_messages,
                   SUM(CASE WHEN state = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as completion_rate
            FROM (
                SELECT c.conversation_id, c.state, COUNT(m.message_id) as msg_count
                FROM conversations c
                LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
                GROUP BY c.conversation_id
            )
        """
        )
        stats = cursor.fetchone()
        patterns["average_messages"] = round(stats[0] or 0, 1)
        patterns["completion_rate"] = round(stats[1] or 0, 1)

        conn.close()
        return patterns

    def generate_ai_report(self) -> Dict:
        """AI用学習レポート生成"""
        patterns = self.get_conversation_patterns()

        # タスクタイプ分析
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                CASE
                    WHEN content LIKE '%作成%' OR content LIKE '%作って%' THEN 'creation'
                    WHEN content LIKE '%修正%' OR content LIKE '%直して%' THEN 'modification'
                    WHEN content LIKE '%分析%' OR content LIKE '%調査%' THEN 'analysis'
                    ELSE 'other'
                END as task_type,
                COUNT(*) as count
            FROM conversation_messages
            WHERE message_type = 'initial_prompt'
            GROUP BY task_type
        """
        )

        task_types = {row[0]: row[1] for row in cursor.fetchall()}

        # 時間帯分析
        cursor.execute(
            """
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM conversation_messages
            WHERE message_type = 'initial_prompt'
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 3
        """
        )

        peak_hours = [
            {"hour": int(row[0]), "count": row[1]} for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "patterns": patterns,
            "task_types": task_types,
            "peak_hours": peak_hours,
            "recommendations": self._generate_recommendations(patterns, task_types),
        }

    def _generate_recommendations(self, patterns: Dict, task_types: Dict) -> List[str]:
        """AI改善の推奨事項生成"""
        recommendations = []

        if patterns["completion_rate"] < 80:
            recommendations.append(
                "完了率が低いため、ユーザー要求の理解を改善する必要があります"
            )

        if patterns["average_messages"] > 15:
            recommendations.append(
                "平均メッセージ数が多いため、初回の要件確認を強化すべきです"
            )

        if task_types.get("creation", 0) > task_types.get("modification", 0) * 2:
            recommendations.append(
                "作成タスクが多いため、テンプレート機能を強化すると効率的です"
            )

        return recommendations
