#!/usr/bin/env python3
"""
RAG賢者プロセス - 情報検索と理解の専門家
Elder Soul - A2A Architecture
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.append(str(Path(__file__).parent.parent))

from libs.elder_process_base import (
    ElderProcessBase,
    ElderRole,
    SageType,
    ElderMessage,
    MessageType
)


@dataclass
class SearchResult:
    """検索結果"""
    doc_id: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


@dataclass
class DocumentIndex:
    """ドキュメントインデックス"""
    doc_id: str
    title: str
    content: str
    embedding: Optional[List[float]] = None
    tags: List[str] = None
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0


class RAGSageProcess(ElderProcessBase):
    """
    RAG賢者 - 情報検索と理解の専門プロセス

    責務:
    - 情報の検索と取得
    - コンテキストの理解と要約
    - 関連情報の推論
    - 検索結果の最適化
    """

    def __init__(self):
        super().__init__(
            elder_name="rag_sage",
            elder_role=ElderRole.SAGE,
            sage_type=SageType.RAG,
            port=5004
        )

        # ドキュメントインデックス
        self.document_index: Dict[str, DocumentIndex] = {}
        self.embeddings_cache: Dict[str, List[float]] = {}

        # 検索設定
        self.search_config = {
            "max_results": 10,
            "min_score": 0.5,
            "use_semantic": True,
            "use_keyword": True
        }

        # パス設定
        self.data_dir = Path("data/rag_sage")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初期化処理"""
        self.logger.info("🔍 Initializing RAG Sage...")

        # インデックスの読み込み
        await self._load_document_index()

        # 埋め込みモデルの初期化（シミュレーション）
        await self._initialize_embedding_model()

        self.logger.info(f"✅ RAG Sage initialized with {len(self.document_index)} documents")

    async def process(self):
        """メイン処理"""
        # インデックスの最適化（1時間ごと）
        if not hasattr(self, '_last_optimization') or \
           (datetime.now() - self._last_optimization).total_seconds() > 3600:
            await self._optimize_index()
            self._last_optimization = datetime.now()

        # 検索履歴の分析（30分ごと）
        if not hasattr(self, '_last_analysis') or \
           (datetime.now() - self._last_analysis).total_seconds() > 1800:
            await self._analyze_search_patterns()
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
        # インデックスの保存
        await self._save_document_index()

        # 検索統計の保存
        await self._save_search_statistics()

    # プライベートメソッド

    async def _load_document_index(self):
        """ドキュメントインデックスの読み込み"""
        index_file = self.data_dir / "document_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for doc_data in data.get('documents', []):
                        doc = DocumentIndex(
                            doc_id=doc_data['id'],
                            title=doc_data['title'],
                            content=doc_data['content']
                        )
                        doc.tags = doc_data.get('tags', [])
                        doc.access_count = doc_data.get('access_count', 0)

                        if doc_data.get('embedding'):
                            doc.embedding = doc_data['embedding']
                            self.embeddings_cache[doc.doc_id] = doc.embedding

                        self.document_index[doc.doc_id] = doc

                self.logger.info(f"Loaded {len(self.document_index)} documents")

            except Exception as e:
                self.logger.error(f"Failed to load document index: {e}")

    async def _initialize_embedding_model(self):
        """埋め込みモデルの初期化"""
        # 実際のモデル読み込みの代わりにシミュレーション
        self.logger.info("Initializing embedding model...")
        await asyncio.sleep(1)
        self.embedding_dim = 384  # 仮の次元数

    async def _save_document_index(self):
        """ドキュメントインデックスの保存"""
        try:
            documents_data = []
            for doc in self.document_index.values():
                doc_data = {
                    'id': doc.doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'tags': doc.tags,
                    'access_count': doc.access_count,
                    'created_at': doc.created_at.isoformat() if doc.created_at else None
                }

                # 埋め込みがあれば保存
                if doc.doc_id in self.embeddings_cache:
                    doc_data['embedding'] = self.embeddings_cache[doc.doc_id]

                documents_data.append(doc_data)

            index_file = self.data_dir / "document_index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'documents': documents_data,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Document index saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save document index: {e}")

    async def _save_search_statistics(self):
        """検索統計の保存"""
        stats_file = self.data_dir / "search_statistics.json"
        try:
            # 統計情報の収集
            total_docs = len(self.document_index)
            total_accesses = sum(doc.access_count for doc in self.document_index.values())

            stats = {
                'total_documents': total_docs,
                'total_accesses': total_accesses,
                'average_access_per_doc': total_accesses / total_docs if total_docs > 0 else 0,
                'last_updated': datetime.now().isoformat()
            }

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save search statistics: {e}")

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')

        if command == 'index_document':
            # ドキュメントのインデックス化
            await self._index_document(message.payload)

        elif command == 'update_index':
            # インデックスの更新
            await self._update_document_index(message.payload)

        elif command == 'execute_task':
            # タスク実行（クロードエルダーから）
            await self._execute_rag_task(message.payload)

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'search':
            # 検索実行
            results = await self._perform_search(message.payload)

            response_msg = ElderMessage(
                message_id=f"search_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'search_results': results},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'summarize':
            # 要約生成
            summary = await self._generate_summary(message.payload)

            response_msg = ElderMessage(
                message_id=f"summary_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'summary': summary},
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
                    'capacity': 0.85,
                    'indexed_documents': len(self.document_index),
                    'cache_hit_rate': 0.75
                },
                priority=message.priority
            )

            await self.send_message(response_msg)

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')

        if report_type == 'search_feedback':
            # 検索フィードバックの処理
            await self._process_search_feedback(message.payload)

        elif report_type == 'document_update':
            # ドキュメント更新通知
            await self._handle_document_update(message.payload)

    async def _index_document(self, payload: Dict[str, Any]):
        """ドキュメントのインデックス化"""
        doc_id = f"doc_{datetime.now().timestamp()}"
        title = payload.get('title', 'Untitled')
        content = payload.get('content', '')
        tags = payload.get('tags', [])

        # ドキュメントインデックス作成
        doc = DocumentIndex(
            doc_id=doc_id,
            title=title,
            content=content,
            tags=tags,
            created_at=datetime.now()
        )

        # 埋め込み生成（シミュレーション）
        embedding = await self._generate_embedding(content)
        doc.embedding = embedding
        self.embeddings_cache[doc_id] = embedding

        self.document_index[doc_id] = doc

        self.logger.info(f"Indexed document: {title} ({doc_id})")

        # インデックス完了通知
        await self.report_to_superior({
            'type': 'document_indexed',
            'doc_id': doc_id,
            'title': title
        })

    async def _generate_embedding(self, text: str) -> List[float]:
        """埋め込みベクトル生成（シミュレーション）"""
        # 実際のモデル推論の代わりにランダムベクトル生成
        await asyncio.sleep(0.1)  # 推論時間のシミュレーション

        # テキストベースのシード値でランダム性を固定
        seed = sum(ord(c) for c in text[:100])
        np.random.seed(seed % 2**32)

        return np.random.randn(self.embedding_dim).tolist()

    async def _perform_search(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """検索実行"""
        query_text = query_data.get('query', '')
        filters = query_data.get('filters', {})
        max_results = query_data.get('max_results', self.search_config['max_results'])

        self.logger.info(f"Performing search: {query_text[:50]}...")

        results = []

        # セマンティック検索
        if self.search_config['use_semantic']:
            semantic_results = await self._semantic_search(query_text, filters)
            results.extend(semantic_results)

        # キーワード検索
        if self.search_config['use_keyword']:
            keyword_results = await self._keyword_search(query_text, filters)
            results.extend(keyword_results)

        # 重複除去とスコアでソート
        unique_results = {}
        for result in results:
            doc_id = result['doc_id']
            if doc_id not in unique_results or result['score'] > unique_results[doc_id]['score']:
                unique_results[doc_id] = result

        # 上位N件を返す
        sorted_results = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)
        final_results = sorted_results[:max_results]

        # アクセスカウント更新
        for result in final_results:
            doc_id = result['doc_id']
            if doc_id in self.document_index:
                self.document_index[doc_id].access_count += 1
                self.document_index[doc_id].last_accessed = datetime.now()

        return final_results

    async def _semantic_search(self, query: str, filters: Dict) -> List[Dict[str, Any]]:
        """セマンティック検索"""
        # クエリの埋め込み生成
        query_embedding = await self._generate_embedding(query)

        results = []

        for doc_id, doc in self.document_index.items():
            # フィルタチェック
            if filters.get('tags'):
                if not any(tag in doc.tags for tag in filters['tags']):
                    continue

            # 埋め込みがある場合のみ
            if doc_id in self.embeddings_cache:
                doc_embedding = self.embeddings_cache[doc_id]

                # コサイン類似度計算
                similarity = cosine_similarity(
                    [query_embedding],
                    [doc_embedding]
                )[0][0]

                if similarity >= self.search_config['min_score']:
                    results.append({
                        'doc_id': doc_id,
                        'title': doc.title,
                        'content': doc.content[:200] + "...",
                        'score': float(similarity),
                        'type': 'semantic',
                        'tags': doc.tags
                    })

        return results

    async def _keyword_search(self, query: str, filters: Dict) -> List[Dict[str, Any]]:
        """キーワード検索"""
        query_terms = query.lower().split()
        results = []

        for doc_id, doc in self.document_index.items():
            # フィルタチェック
            if filters.get('tags'):
                if not any(tag in doc.tags for tag in filters['tags']):
                    continue

            # キーワードマッチング
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()

            score = 0.0
            for term in query_terms:
                # タイトルでの出現（高スコア）
                if term in title_lower:
                    score += 3.0

                # コンテンツでの出現
                score += content_lower.count(term) * 0.5

            if score > 0:
                # 正規化
                normalized_score = min(1.0, score / (len(query_terms) * 3))

                if normalized_score >= self.search_config['min_score']:
                    results.append({
                        'doc_id': doc_id,
                        'title': doc.title,
                        'content': doc.content[:200] + "...",
                        'score': float(normalized_score),
                        'type': 'keyword',
                        'tags': doc.tags
                    })

        return results

    async def _generate_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """要約生成"""
        doc_ids = payload.get('doc_ids', [])
        summary_type = payload.get('type', 'extractive')

        # ドキュメント収集
        documents = []
        for doc_id in doc_ids:
            if doc_id in self.document_index:
                documents.append(self.document_index[doc_id])

        if not documents:
            return {'error': 'No documents found'}

        # 要約生成（シミュレーション）
        if summary_type == 'extractive':
            # 抽出型要約
            summary = await self._extractive_summary(documents)
        else:
            # 生成型要約
            summary = await self._abstractive_summary(documents)

        return {
            'summary': summary,
            'document_count': len(documents),
            'type': summary_type
        }

    async def _extractive_summary(self, documents: List[DocumentIndex]) -> str:
        """抽出型要約（シミュレーション）"""
        # 各ドキュメントから重要な文を抽出
        important_sentences = []

        for doc in documents[:3]:  # 最大3ドキュメント
            sentences = doc.content.split('.')[:2]  # 最初の2文
            important_sentences.extend(sentences)

        summary = '. '.join(important_sentences)
        return summary[:500] + "..."

    async def _abstractive_summary(self, documents: List[DocumentIndex]) -> str:
        """生成型要約（シミュレーション）"""
        # 実際のLLM呼び出しの代わりにテンプレート生成
        titles = [doc.title for doc in documents[:5]]

        summary = f"Summary of {len(documents)} documents: "
        summary += f"The documents cover topics including {', '.join(titles)}. "
        summary += "Key insights include various aspects of the discussed subjects."

        return summary

    async def _optimize_index(self):
        """インデックスの最適化"""
        self.logger.info("Optimizing document index...")

        # アクセス頻度の低いドキュメントの識別
        low_access_docs = [
            doc for doc in self.document_index.values()
            if doc.access_count < 5 and doc.created_at and
            (datetime.now() - doc.created_at).days > 30
        ]

        if low_access_docs:
            self.logger.info(f"Found {len(low_access_docs)} low-access documents")

            # メモリ最適化のため埋め込みをクリア（必要時に再生成）
            for doc in low_access_docs[:10]:
                if doc.doc_id in self.embeddings_cache:
                    del self.embeddings_cache[doc.doc_id]

    async def _analyze_search_patterns(self):
        """検索パターンの分析"""
        self.logger.info("Analyzing search patterns...")

        # アクセス頻度の高いドキュメント
        popular_docs = sorted(
            self.document_index.values(),
            key=lambda x: x.access_count,
            reverse=True
        )[:10]

        if popular_docs:
            # 分析結果をクロードエルダーに報告
            analysis_report = ElderMessage(
                message_id=f"search_analysis_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder="claude_elder",
                message_type=MessageType.REPORT,
                payload={
                    'type': 'search_analysis',
                    'popular_documents': [
                        {'title': doc.title, 'access_count': doc.access_count}
                        for doc in popular_docs
                    ],
                    'total_documents': len(self.document_index),
                    'cache_size': len(self.embeddings_cache)
                },
                priority=5
            )

            await self.send_message(analysis_report)

    async def _process_search_feedback(self, feedback: Dict[str, Any]):
        """検索フィードバックの処理"""
        doc_id = feedback.get('doc_id')
        relevance = feedback.get('relevance', 0.5)

        if doc_id in self.document_index:
            # 関連性スコアの更新（簡易版）
            doc = self.document_index[doc_id]

            # フィードバックに基づいてアクセスカウントを調整
            if relevance > 0.7:
                doc.access_count += 2
            elif relevance < 0.3:
                doc.access_count = max(0, doc.access_count - 1)

            self.logger.info(f"Processed feedback for doc {doc_id}: relevance={relevance}")

    async def _handle_document_update(self, update_data: Dict[str, Any]):
        """ドキュメント更新通知の処理"""
        doc_id = update_data.get('doc_id')

        if doc_id in self.document_index:
            doc = self.document_index[doc_id]

            # 内容更新
            if 'content' in update_data:
                doc.content = update_data['content']
                # 埋め込み再生成が必要
                embedding = await self._generate_embedding(doc.content)
                doc.embedding = embedding
                self.embeddings_cache[doc_id] = embedding

            # タグ更新
            if 'tags' in update_data:
                doc.tags = update_data['tags']

            self.logger.info(f"Updated document: {doc_id}")

    async def _execute_rag_task(self, task_data: Dict[str, Any]):
        """RAGタスクの実行"""
        task_id = task_data.get('task_id')
        description = task_data.get('description', '')

        self.logger.info(f"Executing RAG task {task_id}: {description}")

        # RAG関連タスクの実行
        if "search" in description.lower() or "find" in description.lower():
            result = await self._execute_search_task(task_data)
        elif "summarize" in description.lower():
            result = await self._execute_summary_task(task_data)
        else:
            # 一般的なRAGタスク
            result = await self._execute_general_rag_task(task_data)

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

    async def _execute_search_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """検索タスクの実行"""
        # シミュレーション
        await asyncio.sleep(2)

        return {
            'status': 'completed',
            'search_results': {
                'found': 15,
                'relevant': 8,
                'top_result': 'Relevant document found'
            }
        }

    async def _execute_summary_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """要約タスクの実行"""
        # シミュレーション
        await asyncio.sleep(3)

        return {
            'status': 'completed',
            'summary': {
                'type': 'extractive',
                'length': 500,
                'key_points': 5
            }
        }

    async def _execute_general_rag_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """一般的なRAGタスクの実行"""
        # シミュレーション
        await asyncio.sleep(1)

        return {
            'status': 'completed',
            'message': 'RAG task completed successfully'
        }


# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(RAGSageProcess)
