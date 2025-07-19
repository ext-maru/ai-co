#!/usr/bin/env python3
"""
RAG管理 - Claude CLI連携・要約生成クラス（修正版）
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from features.database.task_history_db import TaskHistoryDB

logger = logging.getLogger(__name__)


class RAGManager:
    def __init__(self, model="claude-sonnet-4-20250514"):
        self.model = model
        self.db = TaskHistoryDB()

    def generate_summary(self, prompt, response):
        """Claude CLIで要約生成"""
        summary_prompt = f"""以下のタスクと応答を簡潔に要約してください（100文字以内）：

【タスク】
{prompt[:500]}

【応答】
{response[:1000]}

要約:"""

        try:
            cmd = ["claude", "--model", self.model, "--print"]
            result = subprocess.run(
                cmd, input=summary_prompt, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                summary = result.stdout.strip()
                # 改行を除去して1行にまとめる
                summary = summary.replace("\n", " ").strip()
                logger.info(f"要約生成成功: {len(summary)}文字")
                return summary[:100]  # 100文字制限
            else:
                logger.error(f"要約生成失敗: {result.stderr}")
                return f"要約生成失敗 - {prompt[:30]}の実行"

        except Exception as e:
            logger.error(f"要約生成例外: {e}")
            return f"要約生成エラー - {prompt[:30]}の実行"

    def save_task_with_summary(
        self, task_id, worker, prompt, response, status="completed", task_type="general"
    ):
        """タスク保存＋要約生成"""
        # 1. まず基本情報を保存
        success = self.db.save_task(
            task_id=task_id,
            worker=worker,
            model=self.model,
            prompt=prompt,
            response=response,
            status=status,
            task_type=task_type,
        )

        if not success:
            return False

        # 2. 要約生成（エラー回避のため常に実行）
        try:
            if len(response) > 50:  # 短い応答でも要約生成
                summary = self.generate_summary(prompt, response)
                self.db.update_summary(task_id, summary)
                logger.info(f"要約保存完了: {task_id} -> {summary[:50]}...")
        except Exception as e:
            logger.error(f"要約処理エラー: {e}")
            # 要約生成に失敗してもタスク保存は成功とする

        return True

    def get_related_history(self, current_prompt, limit=5):
        """関連履歴検索"""
        keywords = self._extract_keywords(current_prompt)

        related_tasks = []
        for keyword in keywords[:3]:
            tasks = self.db.search_tasks(keyword=keyword, limit=limit)
            related_tasks.extend(tasks)

        # 重複除去
        unique_tasks = {}
        for task in related_tasks:
            if task["task_id"] not in unique_tasks:
                unique_tasks[task["task_id"]] = task

        return list(unique_tasks.values())[:limit]

    def _extract_keywords(self, text):
        """簡易キーワード抽出"""
        import re
        from collections import Counter

        words = re.findall(r"[ぁ-んァ-ヶー一-龠a-zA-Z]{2,}", text)

        stopwords = {
            "こと",
            "もの",
            "ため",
            "です",
            "ます",
            "する",
            "ある",
            "いる",
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
        }

        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 2]
        word_counts = Counter(keywords)

        return [word for word, count in word_counts.most_common(10)]

    def build_context_prompt(self, current_prompt, include_history=True):
        """過去の履歴を含めたプロンプト構築"""
        if not include_history:
            return current_prompt

        related_tasks = self.get_related_history(current_prompt, limit=3)

        if not related_tasks:
            return current_prompt

        context_prompt = f"""過去の関連タスク履歴:
"""

        for i, task in enumerate(related_tasks, 1):
            summary = task.get("summary") or f"タスク: {task['prompt'][:50]}..."
            context_prompt += f"""
【履歴{i}】{summary}
"""

        context_prompt += f"""

上記の履歴を参考に、以下の新しいタスクを実行してください:

{current_prompt}"""

        return context_prompt

    def get_performance_stats(self):
        """パフォーマンス統計"""
        stats = self.db.get_stats()

        total = stats.get("total_tasks", 0)
        completed = stats.get("completed_tasks", 0)
        success_rate = (completed / total * 100) if total > 0 else 0

        return {**stats, "success_rate": round(success_rate, 1)}
