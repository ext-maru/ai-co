"""
RAG Wizard Servant - RAGウィザード族サーバント
調査・研究特化型サーバント
"""

from typing import Dict, Any, List
import asyncio
from elder_tree.servants.base_servant import ElderServantBase
import structlog
from datetime import datetime


class RAGWizardServant(ElderServantBase):
    """
    RAGウィザード族基底クラス
    
    特徴:
    - 情報検索・分析に特化
    - ドキュメント生成
    - 知識統合
    """
    
    def __init__(self, name: str, specialty: str, port: int):
        super().__init__(
            name=name,
            tribe="rag_wizard",
            specialty=specialty,
            port=port
        )
        
        # RAGウィザード特有の設定
        self.search_depth = "comprehensive"
        self.analysis_methods = ["semantic", "statistical", "comparative"]


class ResearchWizard(RAGWizardServant):
    """
    Research Wizard - 調査研究スペシャリスト
    
    専門:
    - 技術調査
    - ドキュメント作成
    - 競合分析
    - ベストプラクティス調査
    """
    
    def __init__(self, port: int = 60102):
        super().__init__(
            name="research_wizard",
            specialty="Technical research and documentation",
            port=port
        )
        
        # 追加ハンドラー登録
        self._register_research_handlers()
    
    def _register_research_handlers(self):
        """調査研究専用ハンドラー"""
        
        @self.on_message("conduct_research")
        async def handle_conduct_research(message) -> Dict[str, Any]:
            """
            調査研究リクエスト
            
            Input:
                - topic: 調査トピック
                - scope: 調査範囲
                - output_format: 出力形式
            """
            topic = message.data.get("topic", "")
            scope = message.data.get("scope", "comprehensive")
            output_format = message.data.get("output_format", "report")
            
            result = await self.execute_specialized_task(
                "research",
                {
                    "topic": topic,
                    "scope": scope,
                    "output_format": output_format
                },
                {}
            )
            
            return {
                "status": "success",
                "research_result": result
            }
    
    async def execute_specialized_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        consultation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        RAGウィザード特化タスク実行
        """
        if task_type == "research":
            topic = parameters.get("topic", "")
            scope = parameters.get("scope", "comprehensive")
            output_format = parameters.get("output_format", "report")
            
            # RAG Sageと連携して情報収集
            search_results = await self._search_documents(topic, scope)
            
            # 情報分析
            analysis = await self._analyze_search_results(search_results)
            
            # レポート生成
            report = await self._generate_report(
                topic, analysis, output_format
            )
            
            return {
                "topic": topic,
                "scope": scope,
                "sources_analyzed": len(search_results),
                "report": report,
                "key_findings": analysis.get("key_findings", []),
                "recommendations": analysis.get("recommendations", [])
            }
        
        elif task_type == "documentation":
            # ドキュメント作成タスク
            content = parameters.get("content", {})
            doc_type = parameters.get("doc_type", "technical")
            
            document = await self._create_documentation(content, doc_type)
            
            return {
                "document": document,
                "doc_type": doc_type,
                "sections": document.get("sections", []),
                "word_count": document.get("word_count", 0)
            }
        
        return await super().execute_specialized_task(
            task_type, parameters, consultation_result
        )
    
    async def _search_documents(self, topic: str, scope: str) -> List[Dict[str, Any]]:
        """
        RAG Sageを使ったドキュメント検索
        """
        try:
            # RAG Sageに検索依頼
            response = await self.send_message(
                target="rag_sage",
                message_type="search_documents",
                data={
                    "query": topic,
                    "limit": 20 if scope == "comprehensive" else 10,
                    "threshold": 0.7
                }
            )
            
            if response.data.get("status") == "success":
                return response.data.get("documents", [])
            else:
                self.logger.warning("Document search failed", error=response.data.get("message"))
                return []
                
        except Exception as e:
            self.logger.error("Failed to search documents", error=str(e))
            return []
    
    async def _analyze_search_results(
        self, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        検索結果の分析
        """
        if not search_results:
            return {
                "key_findings": ["No relevant documents found"],
                "recommendations": ["Expand search criteria"],
                "confidence": 0.0
            }
        
        # RAG Sageに分析依頼
        try:
            response = await self.send_message(
                target="rag_sage",
                message_type="analyze_documents",
                data={
                    "documents": search_results,
                    "analysis_type": "comprehensive"
                }
            )
            
            if response.data.get("status") == "success":
                result = response.data.get("result", {})
                
                # 主要な発見事項を抽出
                key_findings = self._extract_key_findings(result)
                
                # 推奨事項を生成
                recommendations = self._generate_recommendations(key_findings)
                
                return {
                    "key_findings": key_findings,
                    "recommendations": recommendations,
                    "confidence": self._calculate_confidence(search_results),
                    "summary": result.get("content", ""),
                    "topics": result.get("topics", [])
                }
            else:
                return {
                    "key_findings": ["Analysis failed"],
                    "recommendations": [],
                    "confidence": 0.0
                }
                
        except Exception as e:
            self.logger.error("Failed to analyze documents", error=str(e))
            return {
                "key_findings": ["Analysis error occurred"],
                "recommendations": [],
                "confidence": 0.0
            }
    
    async def _generate_report(
        self,
        topic: str,
        analysis: Dict[str, Any],
        output_format: str
    ) -> Dict[str, Any]:
        """
        調査レポート生成
        """
        timestamp = datetime.now().isoformat()
        
        if output_format == "report":
            return {
                "title": f"Research Report: {topic}",
                "generated_at": timestamp,
                "executive_summary": self._create_executive_summary(analysis),
                "sections": [
                    {
                        "title": "Key Findings",
                        "content": "\n".join(f"- {finding}" for finding in analysis.get("key_findings", []))
                    },
                    {
                        "title": "Analysis",
                        "content": analysis.get("summary", "No analysis available")
                    },
                    {
                        "title": "Recommendations",
                        "content": "\n".join(f"- {rec}" for rec in analysis.get("recommendations", []))
                    },
                    {
                        "title": "Topics Covered",
                        "content": ", ".join(analysis.get("topics", []))
                    }
                ],
                "confidence_score": analysis.get("confidence", 0.0)
            }
        
        elif output_format == "summary":
            return {
                "summary": self._create_executive_summary(analysis),
                "key_points": analysis.get("key_findings", [])[:5],
                "next_steps": analysis.get("recommendations", [])[:3]
            }
        
        else:  # raw format
            return analysis
    
    def _extract_key_findings(self, analysis_result: Dict[str, Any]) -> List[str]:
        """主要な発見事項の抽出"""
        findings = []
        
        # トピックから主要な発見を抽出
        topics = analysis_result.get("topics", [])
        if topics:
            findings.append(f"Main topics identified: {', '.join(topics[:3])}")
        
        # コンテンツから重要なポイントを抽出
        content = analysis_result.get("content", "")
        if content:
            # 簡易的な重要ポイント抽出（実際はもっと高度な処理）
            sentences = content.split(".")[:3]
            findings.extend([s.strip() for s in sentences if s.strip()])
        
        return findings[:5]  # 最大5つの発見事項
    
    def _generate_recommendations(self, key_findings: List[str]) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        # 発見事項に基づいた推奨事項生成（簡易版）
        for finding in key_findings:
            if "topics identified" in finding.lower():
                recommendations.append("Deep dive into the identified topics for comprehensive understanding")
            elif "no relevant" in finding.lower():
                recommendations.append("Broaden search criteria or explore alternative sources")
        
        # デフォルトの推奨事項
        if not recommendations:
            recommendations = [
                "Continue monitoring this topic for updates",
                "Consider practical implementation based on findings",
                "Validate findings with additional sources"
            ]
        
        return recommendations[:3]  # 最大3つの推奨事項
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """信頼度スコアの計算"""
        if not search_results:
            return 0.0
        
        # 関連性スコアの平均を計算
        relevance_scores = [
            doc.get("relevance_score", 0.0) 
            for doc in search_results
        ]
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # ドキュメント数による調整
        doc_count_factor = min(len(search_results) / 10, 1.0)
        
        return round(avg_relevance * doc_count_factor, 2)
    
    def _create_executive_summary(self, analysis: Dict[str, Any]) -> str:
        """エグゼクティブサマリーの作成"""
        key_findings = analysis.get("key_findings", [])
        confidence = analysis.get("confidence", 0.0)
        
        summary_parts = [
            f"Research analysis completed with {confidence:.0%} confidence.",
            f"Identified {len(key_findings)} key findings."
        ]
        
        if key_findings:
            summary_parts.append(f"Primary finding: {key_findings[0]}")
        
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            summary_parts.append(f"Top recommendation: {recommendations[0]}")
        
        return " ".join(summary_parts)
    
    async def _create_documentation(
        self,
        content: Dict[str, Any],
        doc_type: str
    ) -> Dict[str, Any]:
        """
        ドキュメント作成
        """
        # Knowledge Sageからテンプレートやガイドラインを取得
        guidelines = await self._get_documentation_guidelines(doc_type)
        
        # ドキュメント構造の作成
        document = {
            "type": doc_type,
            "created_at": datetime.now().isoformat(),
            "sections": [],
            "metadata": {
                "author": self.name,
                "version": "1.0.0",
                "guidelines_used": guidelines.get("name", "default")
            }
        }
        
        # セクションの生成
        if doc_type == "technical":
            document["sections"] = [
                {
                    "title": "Overview",
                    "content": content.get("overview", "")
                },
                {
                    "title": "Technical Details",
                    "content": content.get("technical_details", "")
                },
                {
                    "title": "Implementation",
                    "content": content.get("implementation", "")
                },
                {
                    "title": "Testing",
                    "content": content.get("testing", "")
                }
            ]
        elif doc_type == "user_guide":
            document["sections"] = [
                {
                    "title": "Introduction",
                    "content": content.get("introduction", "")
                },
                {
                    "title": "Getting Started",
                    "content": content.get("getting_started", "")
                },
                {
                    "title": "Features",
                    "content": content.get("features", "")
                },
                {
                    "title": "FAQ",
                    "content": content.get("faq", "")
                }
            ]
        
        # 単語数計算
        word_count = sum(
            len(section["content"].split()) 
            for section in document["sections"]
        )
        document["word_count"] = word_count
        
        return document
    
    async def _get_documentation_guidelines(self, doc_type: str) -> Dict[str, Any]:
        """
        Knowledge Sageからドキュメントガイドライン取得
        """
        try:
            response = await self.send_message(
                target="knowledge_sage",
                message_type="get_knowledge",
                data={
                    "category": "documentation_guidelines",
                    "key": doc_type
                }
            )
            
            if response.data.get("status") == "success":
                return response.data.get("knowledge", {})
            else:
                return {"name": "default", "rules": []}
                
        except Exception as e:
            self.logger.warning("Failed to get documentation guidelines", error=str(e))
            return {"name": "default", "rules": []}


# 単体実行用
async def main():
    wizard = ResearchWizard()
    await wizard.start()
    print(f"Research Wizard running on port {wizard.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await wizard.stop()


if __name__ == "__main__":
    asyncio.run(main())