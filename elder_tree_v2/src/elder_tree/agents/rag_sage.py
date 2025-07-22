"""
RAG Sage - 情報検索・統合専門AI
TDD Green Phase: 実装フェーズ
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
from elder_tree.agents.base_agent import ElderTreeAgent
from sqlmodel import SQLModel, Field, Session, create_engine, select, text
from prometheus_client import Counter, Histogram
import structlog
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import chromadb
from openai import AsyncOpenAI


# SQLModel Document定義
class DocumentRecord(SQLModel, table=True):
    """ドキュメントレコード"""
    __tablename__ = "documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_id: str = Field(index=True, unique=True)
    title: str
    content: str
    source: str
    doc_type: str  # code, documentation, incident, knowledge
    metadata_json: str = Field(default="{}")
    embedding_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0)
    relevance_score: float = Field(default=1.0)


class RAGSage(ElderTreeAgent):
    """
    RAG Sage - 情報検索統合の専門家
    
    責務:
    - ベクトル検索
    - ドキュメント分析
    - 情報統合
    - 関連性スコアリング
    - ナレッジグラフ構築
    """
    
    def __init__(self, 
                 db_url: str = "sqlite:///rag_documents.db",
                 chroma_persist_dir: str = "./chroma_db"):
        super().__init__(
            name="rag_sage",
            domain="rag",
            port=50054
        )
        
        # データベース初期化
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        
        # OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings()
        self.openai_client = AsyncOpenAI()
        
        # Chromaベクトルストア
        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)
        self.collection_name = "elder_tree_documents"
        
        # テキストスプリッター
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False
        )
        
        # 追加メトリクス
        self.search_counter = Counter(
            'rag_sage_searches_total',
            'Total searches performed',
            ['search_type', 'status']
        )
        
        self.search_latency = Histogram(
            'rag_sage_search_latency_seconds',
            'Search latency',
            ['search_type']
        )
        
        self.doc_operations = Counter(
            'rag_sage_document_operations_total',
            'Document operations',
            ['operation', 'doc_type']
        )
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
        # Chromaコレクション初期化
        self._init_chroma_collection()
        
        self.logger.info("RAGSage initialized")
    
    def _init_chroma_collection(self):
        """ベクトルストアコレクション初期化"""
        try:
            # 既存コレクションを取得または作成
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Chroma collection '{self.collection_name}' ready")
        except Exception as e:
            self.logger.error("Failed to initialize Chroma collection", error=str(e))
    
    def _register_domain_handlers(self):
        """RAG Sage専用ハンドラー登録"""
        
        @self.on_message("search_documents")
        async def handle_search_documents(message) -> Dict[str, Any]:
            """
            ドキュメント検索（ベクトル検索）
            
            Input:
                - query: 検索クエリ
                - limit: 結果数上限
                - doc_type: ドキュメントタイプフィルタ
                - threshold: 関連性スコア闾値
            """
            with self.search_latency.labels(search_type="vector").time():
                query = message.data.get("query", "")
                limit = message.data.get("limit", 10)
                doc_type = message.data.get("doc_type")
                threshold = message.data.get("threshold", 0.7)
                
                try:
                    # クエリのエンベディング生成
                    query_embedding = await asyncio.to_thread(
                        self.embeddings.embed_query, query
                    )
                    
                    # Chromaでベクトル検索
                    where_clause = {"doc_type": doc_type} if doc_type else None
                    
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=limit,
                        where=where_clause
                    )
                    
                    # 結果の整形
                    documents = []
                    if results["ids"] and results["ids"][0]:
                        for i, doc_id in enumerate(results["ids"][0]):
                            # 関連性スコア計算（コサイン距離から）
                            distance = results["distances"][0][i] if results["distances"] else 0
                            relevance_score = 1 - distance  # コサイン距離からスコアへ
                            
                            if relevance_score >= threshold:
                                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                                documents.append({
                                    "doc_id": doc_id,
                                    "content": results["documents"][0][i] if results["documents"] else "",
                                    "metadata": metadata,
                                    "relevance_score": round(relevance_score, 3)
                                })
                        
                        # アクセスカウント更新
                        await self._update_access_counts([d["doc_id"] for d in documents])
                    
                    self.search_counter.labels(
                        search_type="vector",
                        status="success"
                    ).inc()
                    
                    return {
                        "status": "success",
                        "query": query,
                        "documents": documents,
                        "count": len(documents)
                    }
                    
                except Exception as e:
                    self.logger.error("Document search failed", error=str(e))
                    self.search_counter.labels(
                        search_type="vector",
                        status="error"
                    ).inc()
                    return {
                        "status": "error",
                        "message": f"Search failed: {str(e)}"
                    }
        
        @self.on_message("analyze_documents")
        async def handle_analyze_documents(message) -> Dict[str, Any]:
            """
            ドキュメント分析（要約・トピック抽出等）
            """
            documents = message.data.get("documents", [])
            analysis_type = message.data.get("analysis_type", "summary")
            
            if not documents:
                return {
                    "status": "error",
                    "message": "No documents provided for analysis"
                }
            
            try:
                # ドキュメントを結合
                combined_text = "\n\n".join([
                    doc.get("content", "") for doc in documents
                ])
                
                # GPT-4で分析
                analysis_prompt = self._get_analysis_prompt(analysis_type, combined_text)
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert document analyst."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                analysis_result = response.choices[0].message.content
                
                # 分析結果の構造化
                structured_result = self._structure_analysis_result(
                    analysis_type, analysis_result
                )
                
                return {
                    "status": "success",
                    "analysis_type": analysis_type,
                    "result": structured_result,
                    "documents_analyzed": len(documents)
                }
                
            except Exception as e:
                self.logger.error("Document analysis failed", error=str(e))
                return {
                    "status": "error",
                    "message": f"Analysis failed: {str(e)}"
                }
        
        @self.on_message("store_document")
        async def handle_store_document(message) -> Dict[str, Any]:
            """
            ドキュメント保存・インデックス化
            """
            document = message.data.get("document", {})
            
            if not document.get("content"):
                return {
                    "status": "error",
                    "message": "Document content is required"
                }
            
            try:
                # ドキュメントID生成
                doc_id = self._generate_doc_id(document)
                
                # テキスト分割
                chunks = self.text_splitter.split_text(document["content"])
                
                # 各チャンクのエンベディング生成
                embeddings = await asyncio.to_thread(
                    self.embeddings.embed_documents, chunks
                )
                
                # Chromaに保存
                chunk_ids = []
                metadatas = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_ids.append(chunk_id)
                    metadatas.append({
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "title": document.get("title", "Untitled"),
                        "source": document.get("source", "unknown"),
                        "doc_type": document.get("doc_type", "general"),
                        "created_at": datetime.now().isoformat()
                    })
                
                self.collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                
                # メタデータをデータベースに保存
                with Session(self.engine) as session:
                    doc_record = DocumentRecord(
                        doc_id=doc_id,
                        title=document.get("title", "Untitled"),
                        content=document["content"],
                        source=document.get("source", "unknown"),
                        doc_type=document.get("doc_type", "general"),
                        metadata_json=json.dumps(document.get("metadata", {})),
                        embedding_id=chunk_ids[0]  # 最初のチャンクIDを参照
                    )
                    
                    session.add(doc_record)
                    session.commit()
                
                self.doc_operations.labels(
                    operation="store",
                    doc_type=document.get("doc_type", "general")
                ).inc()
                
                # Knowledge Sageに新しいドキュメントを通知
                await self.collaborate_with_sage(
                    "knowledge_sage",
                    {
                        "action": "new_document_indexed",
                        "doc_id": doc_id,
                        "doc_type": document.get("doc_type", "general"),
                        "title": document.get("title", "Untitled")
                    }
                )
                
                return {
                    "status": "success",
                    "doc_id": doc_id,
                    "chunks_created": len(chunks),
                    "message": f"Document stored with {len(chunks)} chunks"
                }
                
            except Exception as e:
                self.logger.error("Document storage failed", error=str(e))
                self.doc_operations.labels(
                    operation="store",
                    doc_type="error"
                ).inc()
                return {
                    "status": "error",
                    "message": f"Storage failed: {str(e)}"
                }
        
        @self.on_message("search_similar_incidents")
        async def handle_search_similar_incidents(message) -> Dict[str, Any]:
            """
            類似インシデント検索（Incident Sage用）
            """
            keywords = message.data.get("keywords", [])
            limit = message.data.get("limit", 5)
            
            # キーワードを結合して検索
            query = " ".join(keywords)
            
            # doc_type="incident"でフィルタリング
            search_result = await handle_search_documents({
                "data": {
                    "query": query,
                    "limit": limit,
                    "doc_type": "incident",
                    "threshold": 0.6  # インシデントは闾値を下げる
                }
            })
            
            return search_result
        
        @self.on_message("update_document_relevance")
        async def handle_update_relevance(message) -> Dict[str, Any]:
            """
            ドキュメントの関連性スコア更新
            """
            doc_id = message.data.get("doc_id")
            feedback = message.data.get("feedback")  # positive/negative
            
            with Session(self.engine) as session:
                statement = select(DocumentRecord).where(DocumentRecord.doc_id == doc_id)
                doc = session.exec(statement).first()
                
                if not doc:
                    return {"status": "error", "message": "Document not found"}
                
                # フィードバックに基づいてスコア調整
                if feedback == "positive":
                    doc.relevance_score = min(doc.relevance_score * 1.1, 2.0)
                elif feedback == "negative":
                    doc.relevance_score = max(doc.relevance_score * 0.9, 0.1)
                
                doc.updated_at = datetime.now()
                session.add(doc)
                session.commit()
                
                return {
                    "status": "success",
                    "doc_id": doc_id,
                    "new_relevance_score": doc.relevance_score
                }
    
    def _generate_doc_id(self, document: Dict[str, Any]) -> str:
        """ドキュメントID生成"""
        # コンテンツのハッシュとタイムスタンプを組み合わせ
        content_hash = hashlib.md5(
            document.get("content", "").encode()
        ).hexdigest()[:8]
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        doc_type = document.get("doc_type", "general")
        
        return f"{doc_type}_{timestamp}_{content_hash}"
    
    def _get_analysis_prompt(self, analysis_type: str, text: str) -> str:
        """分析プロンプト生成"""
        prompts = {
            "summary": f"Please provide a concise summary of the following documents:\n\n{text}",
            "topics": f"Extract the main topics and themes from these documents:\n\n{text}",
            "entities": f"Identify key entities (people, organizations, technologies) mentioned:\n\n{text}",
            "sentiment": f"Analyze the overall sentiment and tone of these documents:\n\n{text}",
            "keywords": f"Extract the most important keywords and phrases:\n\n{text}"
        }
        
        return prompts.get(analysis_type, prompts["summary"])
    
    def _structure_analysis_result(self, analysis_type: str, raw_result: str) -> Dict[str, Any]:
        """分析結果の構造化"""
        # シンプルな実装で、分析タイプに応じて結果を整形
        if analysis_type == "keywords":
            # キーワードをリストに分割
            keywords = [kw.strip() for kw in raw_result.split(",") if kw.strip()]
            return {"keywords": keywords[:20]}  # 上位20個
        
        elif analysis_type == "topics":
            # トピックをリスト化
            topics = raw_result.split("\n")
            return {"topics": [t.strip() for t in topics if t.strip()][:10]}
        
        else:
            # その他はそのまま返す
            return {"content": raw_result}
    
    async def _update_access_counts(self, doc_ids: List[str]):
        """アクセスカウント更新"""
        with Session(self.engine) as session:
            for doc_id in doc_ids:
                statement = select(DocumentRecord).where(DocumentRecord.doc_id == doc_id)
                doc = session.exec(statement).first()
                if doc:
                    doc.access_count += 1
                    doc.updated_at = datetime.now()
                    session.add(doc)
            session.commit()


# 単体実行用
async def main():
    sage = RAGSage()
    await sage.start()
    print(f"RAG Sage running on port {sage.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await sage.stop()


if __name__ == "__main__":
    asyncio.run(main())