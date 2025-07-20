#!/usr/bin/env python3
"""
ナレッジ賢者プロセス
Knowledge Sage Process - 知識管理専門プロセス

過去の英知を蓄積し、学習による知恵の進化を担当
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from libs.elder_process_base import (
    ElderProcessBase, ElderRole, SageType, MessageType, ElderMessage
)


class KnowledgeEntry:
    """知識エントリ"""
    def __init__(self, entry_id: str, category: str, content: Dict[str, Any]):
        self.entry_id = entry_id
        self.category = category
        self.content = content
        self.created_at = datetime.now()
        self.access_count = 0
        self.relevance_score = 1.0
        self.tags: List[str] = []


class KnowledgeSageProcess(ElderProcessBase):
    """
    ナレッジ賢者 - 知識管理専門プロセス

    責務:
    - 過去の知識の蓄積と管理
    - 学習パターンの分析
    - 知識の検索と提供
    - ベストプラクティスの維持
    """

    def __init__(self):
        super().__init__(
            elder_name="knowledge_sage",
            elder_role=ElderRole.SAGE,
            sage_type=SageType.KNOWLEDGE,
            port=5002
        )

        # 知識ベース
        self.knowledge_base: Dict[str, KnowledgeEntry] = {}
        self.knowledge_index: Dict[str, List[str]] = {}  # カテゴリ別インデックス

        # 学習システム
        self.learning_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []

        # パス設定
        self.knowledge_dir = Path("knowledge_base")
        self.knowledge_dir.mkdir(exist_ok=True)

    async def initialize(self):
        """初期化処理"""
        self.logger.info("📚 Initializing Knowledge Sage...")

        # 既存の知識ベース読み込み
        await self._load_knowledge_base()

        # 学習パターンの読み込み
        await self._load_learning_patterns()

        self.logger.info(f"✅ Knowledge Sage initialized with {len(self.knowledge_base)} entries")

    async def process(self):
        """メイン処理"""
        # 知識の最適化（1時間ごと）
        if not hasattr(self, '_last_optimization') or \
           (datetime.now() - self._last_optimization).total_seconds() > 3600:
            await self._optimize_knowledge_base()
            self._last_optimization = datetime.now()

        # 学習パターンの分析（30分ごと）
        if not hasattr(self, '_last_analysis') or \
           (datetime.now() - self._last_analysis).total_seconds() > 1800:
            await self._analyze_patterns()
            self._last_analysis = datetime.now()

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {message.message_type.value} from {message.source_elder}")

        if message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
        elif message.message_type == MessageType.REPORT:
            await self._handle_report(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        # 基本ハンドラーで十分
        pass

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # 知識ベースの保存
        await self._save_knowledge_base()

        # 学習パターンの保存
        await self._save_learning_patterns()

    # プライベートメソッド

    async def _load_knowledge_base(self):
        """知識ベースの読み込み"""
        try:
            # 各カテゴリのファイルを読み込み
            for category_file in self.knowledge_dir.glob("*.json"):
                if category_file.stem.startswith("_"):
                    continue  # 内部ファイルはスキップ

                with open(category_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for entry_data in data.get('entries', []):
                        entry = KnowledgeEntry(
                            entry_id=entry_data['id'],
                            category=category_file.stem,
                            content=entry_data['content']
                        )
                        entry.tags = entry_data.get('tags', [])
                        entry.relevance_score = entry_data.get('relevance_score', 1.0)

                        self.knowledge_base[entry.entry_id] = entry

                        # インデックス更新
                        if entry.category not in self.knowledge_index:
                            self.knowledge_index[entry.category] = []
                        self.knowledge_index[entry.category].append(entry.entry_id)

            self.logger.info(f"Loaded {len(self.knowledge_base)} knowledge entries")

        except Exception as e:
            self.logger.error(f"Failed to load knowledge base: {e}")

    async def _load_learning_patterns(self):
        """学習パターンの読み込み"""
        patterns_file = self.knowledge_dir / "_learning_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learning_patterns = data.get('success_patterns', [])
                    self.failure_patterns = data.get('failure_patterns', [])

                self.logger.info(f"Loaded {len(self.learning_patterns)} learning patterns")
            except Exception as e:
                self.logger.error(f"Failed to load learning patterns: {e}")

    async def _save_knowledge_base(self):
        """知識ベースの保存"""
        try:
            # カテゴリ別に保存
            for category, entry_ids in self.knowledge_index.items():
                entries_data = []

                for entry_id in entry_ids:
                    entry = self.knowledge_base.get(entry_id)
                    if entry:
                        entries_data.append({
                            'id': entry.entry_id,
                            'content': entry.content,
                            'tags': entry.tags,
                            'relevance_score': entry.relevance_score,
                            'access_count': entry.access_count,
                            'created_at': entry.created_at.isoformat()
                        })

                category_file = self.knowledge_dir / f"{category}.json"
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump({'entries': entries_data}, f, ensure_ascii=False, indent=2)

            self.logger.info("Knowledge base saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save knowledge base: {e}")

    async def _save_learning_patterns(self):
        """学習パターンの保存"""
        patterns_file = self.knowledge_dir / "_learning_patterns.json"
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'success_patterns': self.learning_patterns,
                    'failure_patterns': self.failure_patterns,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Learning patterns saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save learning patterns: {e}")

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')

        if command == 'store_knowledge':
            # 新規知識の保存
            await self._store_knowledge(message.payload)

        elif command == 'update_knowledge':
            # 既存知識の更新
            await self._update_knowledge(message.payload)

        elif command == 'execute_task':
            # タスク実行（クロードエルダーから）
            await self._execute_task(message.payload)

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'search':
            # 知識検索
            results = await self._search_knowledge(message.payload)

            response_msg = ElderMessage(
                message_id=f"search_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'results': results},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'best_practice':
            # ベストプラクティス照会
            practice = await self._get_best_practice(message.payload)

            response_msg = ElderMessage(
                message_id=f"practice_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'best_practice': practice},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'availability':
            # 利用可能性確認
            response_msg = ElderMessage(
                message_id=f"availability_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={
                    'available': True,
                    'capacity': 0.8,
                    'knowledge_entries': len(self.knowledge_base)
                },
                priority=message.priority
            )

            await self.send_message(response_msg)

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')

        if report_type == 'learning':
            # 学習結果の記録
            await self._record_learning_result(message.payload)

        elif report_type == 'failure':
            # 失敗パターンの記録
            await self._record_failure_pattern(message.payload)

    async def _store_knowledge(self, payload: Dict[str, Any]):
        """新規知識の保存"""
        entry_id = f"knowledge_{datetime.now().timestamp()}"
        category = payload.get('category', 'general')
        content = payload.get('content', {})
        tags = payload.get('tags', [])

        entry = KnowledgeEntry(entry_id, category, content)
        entry.tags = tags

        self.knowledge_base[entry_id] = entry

        # インデックス更新
        if category not in self.knowledge_index:
            self.knowledge_index[category] = []
        self.knowledge_index[category].append(entry_id)

        self.logger.info(f"Stored new knowledge: {entry_id} in category {category}")

        # 定期的に保存
        if len(self.knowledge_base) % 10 == 0:
            await self._save_knowledge_base()

    async def _update_knowledge(self, payload: Dict[str, Any]):
        """既存知識の更新"""
        entry_id = payload.get('entry_id')
        if entry_id in self.knowledge_base:
            entry = self.knowledge_base[entry_id]

            # 内容の更新
            if 'content' in payload:
                entry.content.update(payload['content'])

            # タグの更新
            if 'tags' in payload:
                entry.tags = list(set(entry.tags + payload['tags']))

            # 関連性スコアの更新
            if 'relevance_delta' in payload:
                entry.relevance_score += payload['relevance_delta']
                entry.relevance_score = max(0.0, min(1.0, entry.relevance_score))

            self.logger.info(f"Updated knowledge: {entry_id}")

    async def _search_knowledge(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """知識検索"""
        search_terms = query.get('terms', [])
        category = query.get('category')
        limit = query.get('limit', 10)

        results = []

        # カテゴリ指定がある場合
        if category and category in self.knowledge_index:
            search_entries = [self.knowledge_base[eid] for eid in self.knowledge_index[category]]
        else:
            search_entries = list(self.knowledge_base.values())

        # 検索実行
        for entry in search_entries:
            score = 0.0

            # タグマッチング
            for term in search_terms:
                if term.lower() in [tag.lower() for tag in entry.tags]:
                    score += 2.0

                # コンテンツ内検索（簡易版）
                content_str = json.dumps(entry.content, ensure_ascii=False).lower()
                if term.lower() in content_str:
                    score += 1.0

            if score > 0:
                results.append({
                    'entry_id': entry.entry_id,
                    'category': entry.category,
                    'content': entry.content,
                    'tags': entry.tags,
                    'score': score * entry.relevance_score,
                    'access_count': entry.access_count
                })

        # スコア順にソート
        results.sort(key=lambda x: x['score'], reverse=True)

        # アクセスカウント更新
        for result in results[:limit]:
            entry_id = result['entry_id']
            if entry_id in self.knowledge_base:
                self.knowledge_base[entry_id].access_count += 1

        return results[:limit]

    async def _get_best_practice(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """ベストプラクティス取得"""
        topic = query.get('topic', 'general')

        # 成功パターンから最適なものを選択
        best_practice = None
        highest_score = 0.0

        for pattern in self.learning_patterns:
            if pattern.get('topic') == topic:
                score = pattern.get('success_rate', 0.0) * pattern.get('usage_count', 1)
                if score > highest_score:
                    highest_score = score
                    best_practice = pattern

        if best_practice:
            return {
                'topic': topic,
                'practice': best_practice.get('practice'),
                'success_rate': best_practice.get('success_rate'),
                'examples': best_practice.get('examples', [])
            }

        return {'topic': topic, 'practice': None, 'message': 'No best practice found'}

    async def _record_learning_result(self, result: Dict[str, Any]):
        """学習結果の記録"""
        pattern = {
            'timestamp': datetime.now().isoformat(),
            'topic': result.get('topic'),
            'practice': result.get('practice'),
            'success_rate': result.get('success_rate', 1.0),
            'usage_count': 1,
            'examples': [result.get('example')] if result.get('example') else []
        }

        # 既存パターンの更新または新規追加
        existing = None
        for p in self.learning_patterns:
            if p.get('topic') == pattern['topic'] and p.get('practice') == pattern['practice']:
                existing = p
                break

        if existing:
            # 既存パターンを更新
            existing['usage_count'] += 1
            existing['success_rate'] = (existing['success_rate'] * (existing['usage_count'] - 1) +
                                       pattern['success_rate']) / existing['usage_count']
            if pattern['examples'][0]:
                existing['examples'].append(pattern['examples'][0])
        else:
            # 新規パターンを追加
            self.learning_patterns.append(pattern)

        self.logger.info(f"Recorded learning result for topic: {pattern['topic']}")

    async def _record_failure_pattern(self, failure: Dict[str, Any]):
        """失敗パターンの記録"""
        pattern = {
            'timestamp': datetime.now().isoformat(),
            'category': failure.get('category'),
            'error_type': failure.get('error_type'),
            'description': failure.get('description'),
            'root_cause': failure.get('root_cause'),
            'prevention': failure.get('prevention'),
            'occurrences': 1
        }

        # 類似の失敗パターンを探す
        for p in self.failure_patterns:
            if p.get('error_type') == pattern['error_type'] and \
               p.get('category') == pattern['category']:
                p['occurrences'] += 1
                return

        # 新規失敗パターンを追加
        self.failure_patterns.append(pattern)

        self.logger.info(f"Recorded failure pattern: {pattern['error_type']}")

    async def _optimize_knowledge_base(self):
        """知識ベースの最適化"""
        self.logger.info("Optimizing knowledge base...")

        # 関連性スコアの減衰
        for entry in self.knowledge_base.values():
            # アクセスされていない知識の関連性を下げる
            if entry.access_count == 0:
                entry.relevance_score *= 0.95
            else:
                # アクセス頻度に応じて調整
                entry.relevance_score = min(1.0, entry.relevance_score + 0.01 * entry.access_count)
                entry.access_count = 0  # リセット

        # 低関連性エントリの削除候補抽出
        deletion_candidates = [
            entry_id for entry_id, entry in self.knowledge_base.items()
            if entry.relevance_score < 0.1
        ]

        if deletion_candidates:
            self.logger.info(f"Found {len(deletion_candidates)} low-relevance entries")

    async def _analyze_patterns(self):
        """パターン分析"""
        self.logger.info("Analyzing learning patterns...")

        # 成功率の高いパターンを特定
        high_success_patterns = [
            p for p in self.learning_patterns
            if p.get('success_rate', 0) > 0.8
        ]

        # 頻発する失敗パターンを特定
        frequent_failures = [
            p for p in self.failure_patterns
            if p.get('occurrences', 0) > 5
        ]

        if high_success_patterns or frequent_failures:
            # 分析結果をクロードエルダーに報告
            analysis_report = ElderMessage(
                message_id=f"pattern_analysis_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder="claude_elder",
                message_type=MessageType.REPORT,
                payload={
                    'type': 'pattern_analysis',
                    'high_success_patterns': len(high_success_patterns),
                    'frequent_failures': len(frequent_failures),
                    'recommendations': self._generate_recommendations(
                        high_success_patterns, frequent_failures
                    )
                },
                priority=5
            )

            await self.send_message(analysis_report)

    def _generate_recommendations(self, success_patterns: List[Dict],
                                failure_patterns: List[Dict]) -> List[str]:
        """推奨事項の生成"""
        recommendations = []

        # 成功パターンからの推奨
        if success_patterns:
            recommendations.append(
                f"Apply high-success patterns: {', '.join(p.get('topic', '') for p in success_patterns[:3])}"
            )

        # 失敗パターンからの推奨
        if failure_patterns:
            recommendations.append(
                f"Avoid frequent failures: {', '.join(p.get('error_type', '') for p in failure_patterns[:3])}"
            )

        return recommendations

    async def _execute_task(self, task_data: Dict[str, Any]):
        """タスク実行"""
        task_id = task_data.get('task_id')
        description = task_data.get('description', '')

        self.logger.info(f"Executing task {task_id}: {description}")

        # 知識管理タスクの実行
        if "document" in description.lower():
            # ドキュメント作成タスク
            result = await self._create_documentation(task_data)
        elif "learn" in description.lower():
            # 学習タスク
            result = await self._perform_learning(task_data)
        else:
            # 一般的な知識タスク
            result = await self._general_knowledge_task(task_data)

        # 完了報告
        completion_msg = ElderMessage(
            message_id=f"task_complete_{task_id}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'task_complete',
                'task_id': task_id,
                'result': result
            },
            priority=6
        )

        await self.send_message(completion_msg)

    async def _create_documentation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメント作成"""
        # シミュレーション
        await asyncio.sleep(2)

        return {
            'status': 'completed',
            'documentation': {
                'title': 'Generated Documentation',
                'sections': ['Overview', 'Usage', 'Examples'],
                'word_count': 1500
            }
        }

    async def _perform_learning(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """学習実行"""
        # シミュレーション
        await asyncio.sleep(3)

        return {
            'status': 'completed',
            'learning': {
                'patterns_identified': 5,
                'knowledge_gained': 12,
                'recommendations': 3
            }
        }

    async def _general_knowledge_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """一般的な知識タスク"""
        # シミュレーション
        await asyncio.sleep(1)

        return {
            'status': 'completed',
            'message': 'Knowledge task completed successfully'
        }


# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(KnowledgeSageProcess)
