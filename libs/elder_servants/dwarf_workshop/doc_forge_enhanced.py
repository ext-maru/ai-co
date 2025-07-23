"""
DocForge Enhanced (D03E) - Elder Flow統合版ドキュメント生成専門エルダーサーバント

Enhanced Requirement Analyzerと統合し、完成度の高い設計書を自動生成する。
ユーザーの簡単な要件から、詳細で実用的な設計書を一気に完成まで作成。

Issue #301: Elder Flow設計書作成能力の強化対応
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from libs.elder_servants.dwarf_workshop.doc_forge import DocForge, DocumentationConfig
from libs.design_generation.requirement_analyzer import (
    EnhancedRequirementAnalyzer,
    BusinessEntity,
    BusinessRelationship, 
    BusinessRule,
    ImplicitNeed
)


class DocForgeEnhanced(DocForge):
    """
    Enhanced Requirement Analyzerと統合された設計書生成専門エルダーサーバント
    
    簡単な要件から完成度の高い設計書を自動生成し、
    Elder Flowが最後まで完成品を提供する仕組みを実現。
    """
    
    def __init__(self):
        super().__init__()
        self.servant_id = "D03E"
        self.servant_name = "DocForgeEnhanced"
        self.logger = logging.getLogger(f"elder_servant.DocForgeEnhanced")
        
        # Enhanced Requirement Analyzerの初期化
        self.requirement_analyzer = EnhancedRequirementAnalyzer()
        
        # 拡張サポート
        self.supported_doc_types.add("design_document")
        self.supported_doc_types.add("system_architecture")
        self.supported_doc_types.add("business_requirements")
    
    async def craft_artifact(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        製作品作成（拡張版）
        要件分析から完成された設計書まで一気通貫で生成
        """
        try:
            self.logger.info("Starting enhanced documentation generation...")
            
            # 要件テキストを取得
            requirements_text = specification.get("requirements", "")
            source_code = specification.get("source_code", "")
            doc_type = specification.get("doc_type", "design_document")
            
            if not requirements_text and not source_code:
                # Complex condition - consider breaking down
                return {
                    "success": False,
                    "error": "Either requirements or source_code must be provided",
                    "quality_score": 0.0
                }
            
            # Phase 1: 要件分析（Enhanced Requirement Analyzer使用）
            analyzed_requirements = None
            if requirements_text:
                self.logger.info("Phase 1: Analyzing business requirements...")
                analyzed_requirements = self.requirement_analyzer.analyze_business_requirements(
                    requirements_text,
                    language=specification.get("language", "ja")
                )
            
            # Phase 2: 設計書生成（分析結果を活用）
            self.logger.info("Phase 2: Generating comprehensive design document...")
            if doc_type == "design_document" and analyzed_requirements:
                # Complex condition - consider breaking down
                documentation = await self._generate_comprehensive_design_document(
                    analyzed_requirements, specification
                )
            elif doc_type == "system_architecture" and analyzed_requirements:
                # Complex condition - consider breaking down
                documentation = await self._generate_system_architecture_document(
                    analyzed_requirements, specification
                )
            elif doc_type == "business_requirements" and analyzed_requirements:
                # Complex condition - consider breaking down
                documentation = await self._generate_business_requirements_document(
                    analyzed_requirements, specification
                )
            elif source_code:
                # 従来のソースコードベース生成にフォールバック
                result = await super().craft_artifact(specification)
                return result
            else:
                return {
                    "success": False,
                    "error": f"Unsupported document type: {doc_type}",
                    "quality_score": 0.0
                }
            
            # Phase 3: 品質評価と最終調整
            self.logger.info("Phase 3: Quality assessment and final adjustments...")
            quality_score = await self._assess_enhanced_documentation_quality(
                documentation, analyzed_requirements
            )
            
            # 品質が不十分な場合は自動改善
            if quality_score < 80.0:
                self.logger.info("Quality below threshold, applying improvements...")
                documentation = await self._apply_quality_improvements(
                    documentation, analyzed_requirements, quality_score
                )
                quality_score = await self._assess_enhanced_documentation_quality(
                    documentation, analyzed_requirements
                )
            
            # メタデータ生成
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "doc_type": doc_type,
                "analyzer_used": "EnhancedRequirementAnalyzer",
                "analysis_results": analyzed_requirements,
                "quality_score": quality_score,
                "word_count": len(documentation.split()),
                "iron_will_compliance": quality_score >= 95.0,
                "elder_flow_enhanced": True
            }
            
            self.logger.info(f"Documentation generation completed. Quality score: {quality_score}")
            
            return {
                "success": True,
                "documentation": documentation,
                "metadata": metadata,
                "analysis_results": analyzed_requirements,
                "quality_score": quality_score
            }
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Enhanced documentation generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "quality_score": 0.0
            }
    
    async def _generate_comprehensive_design_document(
        self, 
        analysis_results: Dict[str, Any],
        specification: Dict[str, Any]
    ) -> str:
        """
        分析結果から包括的な設計書を生成
        完成度の高い実用的な設計書を作成
        """
        project_name = specification.get("project_name", "システム")
        
        doc_parts = []
        
        # ヘッダー
        doc_parts.append(f"# {project_name} 設計書")
        doc_parts.append(f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        doc_parts.append(f"**生成者**: Elder Flow Enhanced (DocForge D03E)")
        doc_parts.append("")
        
        # 目次
        doc_parts.append("## 📋 目次")
        doc_parts.append("1. [概要](#概要)")
        doc_parts.append("2. [ビジネス要件](#ビジネス要件)")
        doc_parts.append("3. [システム構成要素](#システム構成要素)")
        doc_parts.append("4. [エンティティ関係図](#エンティティ関係図)")
        doc_parts.append("5. [ビジネスルール](#ビジネスルール)")
        doc_parts.append("6. [技術的考慮事項](#技術的考慮事項)")
        doc_parts.append("7. [実装ガイドライン](#実装ガイドライン)")
        doc_parts.append("8. [品質保証計画](#品質保証計画)")
        doc_parts.append("9. [リスク分析と対策](#リスク分析と対策)")
        doc_parts.append("")
        
        # 1. 概要
        doc_parts.append("## 概要")
        entities = analysis_results.get("entities", [])
        main_entities = [e.name for e in entities[:5]]  # 主要な5つのエンティティ
        
        doc_parts.append(f"{project_name}は、{', '.join(main_entities)}を中心とした包括的なシステムです。")
        doc_parts.append("本設計書では、ビジネス要件から技術実装まで、システム開発に必要なすべての要素を定義します。")
        doc_parts.append("")
        
        # 2. ビジネス要件
        doc_parts.append("## ビジネス要件")
        
        # 2.1 主要エンティティ
        doc_parts.append("### 2.1 主要エンティティ")
        for entity in entities:
            doc_parts.append(f"#### {entity.name}")
            doc_parts.append(f"- **種別**: {self._translate_entity_type(entity.type)}")
            doc_parts.append(f"- **説明**: {self._generate_entity_description(entity)}")
            if entity.attributes:
                doc_parts.append(f"- **属性**: {', '.join(entity.attributes)}")
            doc_parts.append(f"- **信頼度**: {entity.confidence:.1%}")
            doc_parts.append("")
        
        # 2.2 ステークホルダー要件
        actors = [e for e in entities if e.type == "actor"]
        if actors:
            doc_parts.append("### 2.2 ステークホルダー要件")
            for actor in actors:
                # Process each item in collection
                doc_parts.append(f"#### {actor.name}")
                doc_parts.append(f"- システムを通じて{self._generate_actor_goals(actor.name)}")
                doc_parts.append("")
        
        # 3. システム構成要素
        doc_parts.append("## システム構成要素")
        
        # 3.1 アーキテクチャ概要
        doc_parts.append("### 3.1 アーキテクチャ概要")
        doc_parts.append("```")
        doc_parts.append(self._generate_architecture_diagram(entities))
        doc_parts.append("```")
        doc_parts.append("")
        
        # 4. エンティティ関係図
        doc_parts.append("## エンティティ関係図")
        relationships = analysis_results.get("relationships", [])
        
        doc_parts.append("### 4.1 エンティティ関係")
        doc_parts.append("| From | Relationship | To | Cardinality |")
        doc_parts.append("|------|-------------|----|-----------:|")
        
        for rel in relationships:
            # Process each item in collection
            doc_parts.append(f"| {rel.from_entity} | {rel.relationship_type} | {rel.to_entity} | {rel." \
                "| {rel.from_entity} | {rel.relationship_type} | {rel.to_entity} | {rel." \
                "| {rel.from_entity} | {rel.relationship_type} | {rel.to_entity} | {rel." \
                "cardinality} |")
        doc_parts.append("")
        
        # データモデル図
        doc_parts.append("### 4.2 データモデル")
        doc_parts.append("```mermaid")
        doc_parts.append("erDiagram")
        
        # エンティティ定義
        for entity in entities:
            doc_parts.append(f"    {entity.name} {{")
            doc_parts.append(f"        string id PK")
            doc_parts.append(f"        string name")
            if entity.attributes:
                for attr in entity.attributes[:3]:  # 最大3つの属性
                    doc_parts.append(f"        string {attr}")
            doc_parts.append(f"        datetime created_at")
            doc_parts.append(f"    }}")
        
        # リレーション定義
        for rel in relationships:
            if rel.cardinality == "1:N":
                doc_parts.append(f"    {rel.from_entity} ||--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--o{{ {rel.to_entity} : {rel.relationship_type}")
            elif rel.cardinality == "N:M":
                doc_parts.append(f"    {rel.from_entity} }}o--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} }}o--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} }}o--o{{ {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} }}o--o{{ {rel.to_entity} : {rel.relationship_type}")
            else:  # 1:1
                doc_parts.append(f"    {rel.from_entity} ||--|| {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--|| {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--|| {rel.to_entity} : {rel.relationship_type}" \
                    "    {rel.from_entity} ||--|| {rel.to_entity} : {rel.relationship_type}")
        
        doc_parts.append("```")
        doc_parts.append("")
        
        # 5. ビジネスルール
        doc_parts.append("## ビジネスルール")
        business_rules = analysis_results.get("business_rules", [])
        
        for i, rule in enumerate(business_rules, 1):
            # Process each item in collection
            doc_parts.append(f"### 5.{i} {rule.entity}関連ルール")
            doc_parts.append(f"**条件**: {rule.condition}")
            doc_parts.append(f"**アクション**: {rule.action}")
            doc_parts.append(f"**優先度**: {rule.priority}")
            doc_parts.append(f"**実装要件**: {self._generate_rule_implementation(rule)}")
            doc_parts.append("")
        
        # 6. 技術的考慮事項
        doc_parts.append("## 技術的考慮事項")
        implicit_needs = analysis_results.get("implicit_needs", [])
        
        # カテゴリ別にグループ化
        needs_by_category = {}
        for need in implicit_needs:
            if need.category not in needs_by_category:
                needs_by_category[need.category] = []
            needs_by_category[need.category].append(need)
        
        for category, needs in needs_by_category.items():
            # Process each item in collection
            doc_parts.append(f"### 6.{len(needs_by_category)} {self._translate_category(category)}")
            for need in needs:
                # Process each item in collection
                doc_parts.append(f"#### {need.description}")
                doc_parts.append(f"- **根拠**: {need.rationale}")
                doc_parts.append(f"- **重要度**: {need.importance}")
                doc_parts.append(f"- **実装指針**: {self._generate_implementation_guidance(need)}")
                doc_parts.append("")
        
        # 7. 実装ガイドライン
        doc_parts.append("## 実装ガイドライン")
        
        doc_parts.append("### 7.1 開発フェーズ")
        doc_parts.append("1. **フェーズ1: 基盤構築**")
        doc_parts.append("   - データモデルの実装")
        doc_parts.append("   - 基本的なCRUD操作")
        doc_parts.append("   - 認証・認可システム")
        doc_parts.append("")
        
        doc_parts.append("2. **フェーズ2: コア機能**")
        for rule in business_rules[:3]:
            # Process each item in collection
            doc_parts.append(f"   - {rule.action}の実装")
        doc_parts.append("")
        
        doc_parts.append("3. **フェーズ3: 統合・最適化**")
        for need in implicit_needs[:3]:
            # Process each item in collection
            doc_parts.append(f"   - {need.description}の実装")
        doc_parts.append("")
        
        # 技術スタック推奨
        doc_parts.append("### 7.2 推奨技術スタック")
        tech_stack = self._recommend_tech_stack(implicit_needs)
        for layer, technologies in tech_stack.items():
            # Process each item in collection
            doc_parts.append(f"- **{layer}**: {', '.join(technologies)}")
        doc_parts.append("")
        
        # 8. 品質保証計画
        doc_parts.append("## 品質保証計画")
        doc_parts.append("### 8.1 テスト戦略")
        doc_parts.append("- **単体テスト**: 各エンティティの基本操作（カバレッジ95%以上）")
        doc_parts.append("- **統合テスト**: エンティティ間の関係性検証")
        doc_parts.append("- **エンドツーエンドテスト**: ユーザーシナリオベース")
        doc_parts.append("")
        
        doc_parts.append("### 8.2 品質メトリクス")
        doc_parts.append("- **コードカバレッジ**: 95%以上")
        doc_parts.append("- **サイクロマティック複雑度**: 10以下")
        doc_parts.append("- **応答時間**: 95%のリクエストが2秒以内")
        doc_parts.append("")
        
        # 9. リスク分析と対策
        doc_parts.append("## リスク分析と対策")
        doc_parts.append("| リスク | 影響度 | 発生確率 | 対策 |")
        doc_parts.append("|--------|--------|----------|------|")
        
        risks = self._analyze_project_risks(implicit_needs, business_rules)
        for risk in risks:
            # Process each item in collection
            doc_parts.append(f"| {risk['description']} | {risk['impact']} | {risk['probability']} | {risk['mitigation']} |")
        doc_parts.append("")
        
        # 付録
        doc_parts.append("## 付録")
        doc_parts.append("### A. 用語集")
        for entity in entities[:10]:  # 主要エンティティの用語説明
            doc_parts.append(f"- **{entity.name}**: {self._generate_entity_glossary(entity)}")
        doc_parts.append("")
        
        metadata = analysis_results.get("metadata", {})
        doc_parts.append("### B. 分析メタデータ")
        doc_parts.append(f"- **分析信頼度**: {metadata.get('confidence', 0):.1%}")
        doc_parts.append(f"- **検出エンティティ数**: {len(entities)}")
        doc_parts.append(f"- **検出関係性数**: {len(relationships)}")
        doc_parts.append(f"- **検出ビジネスルール数**: {len(business_rules)}")
        doc_parts.append(f"- **検出潜在ニーズ数**: {len(implicit_needs)}")
        
        return "\n".join(doc_parts)
    
    async def _generate_system_architecture_document(
        self,
        analysis_results: Dict[str, Any],
        specification: Dict[str, Any]
    ) -> str:
        """システムアーキテクチャ文書を生成"""
        project_name = specification.get("project_name", "システム")
        
        doc_parts = []
        doc_parts.append(f"# {project_name} システムアーキテクチャ仕様書")
        doc_parts.append("")
        
        # アーキテクチャ概要
        doc_parts.append("## 1. アーキテクチャ概要")
        implicit_needs = analysis_results.get("implicit_needs", [])
        
        # マイクロサービス vs モノリス判定
        scalability_needs = [n for n in implicit_needs if n.category == "scalability"]
        if scalability_needs:
            doc_parts.append("### 1.1 マイクロサービスアーキテクチャ")
            doc_parts.append("スケーラビリティ要件に基づき、マイクロサービス構成を採用します。")
        else:
            doc_parts.append("### 1.1 モノリシックアーキテクチャ") 
            doc_parts.append("シンプルな構成でメンテナンス性を重視します。")
        
        # システム構成図
        doc_parts.append("```mermaid")
        doc_parts.append("graph TB")
        doc_parts.append("    subgraph \"プレゼンテーション層\"")
        doc_parts.append("        Web[Webアプリケーション]")
        doc_parts.append("        Mobile[モバイルアプリ]")
        doc_parts.append("        API[APIゲートウェイ]")
        doc_parts.append("    end")
        doc_parts.append("    ")
        doc_parts.append("    subgraph \"アプリケーション層\"")
        
        entities = analysis_results.get("entities", [])
        for entity in entities[:5]:  # 主要エンティティをサービス化
            doc_parts.append(f"        {entity.name}Service[{entity.name}サービス]")
        
        doc_parts.append("    end")
        doc_parts.append("    ")
        doc_parts.append("    subgraph \"データ層\"")
        doc_parts.append("        DB[(データベース)]")
        doc_parts.append("        Cache[(キャッシュ)]")
        doc_parts.append("    end")
        
        # 接続関係
        doc_parts.append("    Web --> API")
        doc_parts.append("    Mobile --> API")
        for entity in entities[:3]:
            # Process each item in collection
            doc_parts.append(f"    API --> {entity.name}Service")
            doc_parts.append(f"    {entity.name}Service --> DB")
        doc_parts.append("```")
        doc_parts.append("")
        
        return "\n".join(doc_parts)
    
    async def _generate_business_requirements_document(
        self,
        analysis_results: Dict[str, Any], 
        specification: Dict[str, Any]
    ) -> str:
        """ビジネス要件書を生成"""
        project_name = specification.get("project_name", "プロジェクト")
        
        doc_parts = []
        doc_parts.append(f"# {project_name} ビジネス要件定義書")
        doc_parts.append("")
        
        # エグゼクティブサマリー
        doc_parts.append("## エグゼクティブサマリー")
        entities = analysis_results.get("entities", [])
        main_purpose = self._infer_business_purpose(entities, analysis_results.get("business_rules" \
            "business_rules" \
            "business_rules" \
            "business_rules", []))
        doc_parts.append(f"本システムは{main_purpose}を目的とした統合システムです。")
        doc_parts.append("")
        
        # 機能要件
        doc_parts.append("## 機能要件")
        business_rules = analysis_results.get("business_rules", [])
        for i, rule in enumerate(business_rules, 1):
            # Process each item in collection
            doc_parts.append(f"### FR{i:02d}: {rule.entity}{rule.action}")
            doc_parts.append(f"**説明**: {rule.condition}の場合、{rule.action}を実行する")
            doc_parts.append(f"**優先度**: {rule.priority}")
            doc_parts.append(f"**受け入れ基準**: {self._generate_acceptance_criteria(rule)}")
            doc_parts.append("")
        
        return "\n".join(doc_parts)
    
    def _translate_entity_type(self, entity_type: str) -> str:
        """エンティティタイプを日本語に翻訳"""
        translations = {
            "actor": "アクター（システム利用者）",
            "object": "オブジェクト（データ・機能）", 
            "concept": "コンセプト（概念・ルール）"
        }
        return translations.get(entity_type, entity_type)
    
    def _translate_category(self, category: str) -> str:
        """カテゴリを日本語に翻訳"""
        translations = {
            "security": "セキュリティ要件",
            "performance": "パフォーマンス要件",
            "scalability": "スケーラビリティ要件",
            "usability": "ユーザビリティ要件",
            "integration": "システム統合要件",
            "compliance": "コンプライアンス要件",
            "analytics": "分析・レポート要件"
        }
        return translations.get(category, category)
    
    def _generate_entity_description(self, entity: BusinessEntity) -> str:
        """エンティティの説明を生成"""
        if entity.type == "actor":
            return f"システムを利用して各種操作を行う{entity.name}"
        elif entity.type == "object":
            return f"システム内で管理される{entity.name}データ・機能"
        else:
            return f"システム内の{entity.name}に関する概念・ルール"
    
    def _generate_actor_goals(self, actor_name: str) -> str:
        """アクターの目標を推論生成"""
        actor_goals = {
            "ユーザー": "効率的にタスクを完了し、価値を得たい",
            "顧客": "商品・サービスを購入し、満足のいく体験を得たい", 
            "管理者": "システムを効率的に運用・管理したい",
            "オペレーター": "日常業務を効率的に処理したい"
        }
        return actor_goals.get(actor_name, "システムを通じて目標を達成したい")
    
    def _generate_architecture_diagram(self, entities: List[BusinessEntity]) -> str:
        """アーキテクチャ図のテキスト表現を生成"""
        layers = []
        layers.append("┌─────────────────────────────────┐")
        layers.append("│        プレゼンテーション層        │")
        layers.append("├─────────────────────────────────┤")
        layers.append("│        アプリケーション層         │")
        
        for entity in entities[:4]:  # 主要4エンティティ
            layers.append(f"│  {entity.name}Service                │")
        
        layers.append("├─────────────────────────────────┤")
        layers.append("│           データ層              │")
        layers.append("└─────────────────────────────────┘")
        
        return "\n".join(layers)
    
    def _generate_rule_implementation(self, rule: BusinessRule) -> str:
        """ルールの実装要件を生成"""
        implementations = {
            "high": "リアルタイム実行、例外処理必須、ログ出力",
            "medium": "バッチ処理可、基本的な例外処理",
            "low": "非同期処理可、エラー時は記録のみ"
        }
        return implementations.get(rule.priority, "基本的な実装")
    
    def _generate_implementation_guidance(self, need: ImplicitNeed) -> str:
        """実装指針を生成"""
        guidances = {
            "security": "OAuth2.0、JWT、HTTPS通信、データ暗号化を実装",
            "performance": "キャッシング、CDN、データベースインデックス最適化",
            "scalability": "ロードバランサー、マイクロサービス、オートスケーリング",
            "integration": "REST API、WebHook、メッセージキューの活用",
            "analytics": "データウェアハウス、機械学習パイプライン構築"
        }
        return guidances.get(need.category, "要件に応じた適切な実装")
    
    def _recommend_tech_stack(self, implicit_needs: List[ImplicitNeed]) -> Dict[str, List[str]]:
        """技術スタックを推奨"""
        needs_categories = set(need.category for need in implicit_needs)
        
        stack = {
            "フロントエンド": ["React", "Vue.js"],
            "バックエンド": ["Python/Django", "Node.js"],
            "データベース": ["PostgreSQL", "Redis"]
        }
        
        if "scalability" in needs_categories:
            stack["クラウド"] = ["AWS", "Docker", "Kubernetes"]
        
        if "security" in needs_categories:
            stack["セキュリティ"] = ["OAuth2.0", "JWT", "SSL/TLS"]
        
        if "analytics" in needs_categories:
            stack["分析"] = ["Apache Spark", "Elasticsearch", "Grafana"]
        
        return stack
    
    def _analyze_project_risks(
        self,
        implicit_needs: List[ImplicitNeed],
        business_rules: List[BusinessRule]
    ) -> List[Dict[str, str]]:
        """プロジェクトリスクを分析"""
        risks = []
        
        # セキュリティリスク
        security_needs = [n for n in implicit_needs if n.category == "security"]
        if security_needs:
            risks.append({
                "description": "データ漏洩・不正アクセス",
                "impact": "高",
                "probability": "中", 
                "mitigation": "多要素認証、暗号化、定期的なセキュリティ監査"
            })
        
        # パフォーマンスリスク
        performance_needs = [n for n in implicit_needs if n.category == "performance"]
        if performance_needs:
            risks.append({
                "description": "システム応答遅延",
                "impact": "中",
                "probability": "中",
                "mitigation": "キャッシング戦略、データベース最適化、CDN導入"
            })
        
        # スケーラビリティリスク
        if len(business_rules) > 5:
            risks.append({
                "description": "ビジネスロジック複雑化",
                "impact": "中",
                "probability": "高",
                "mitigation": "マイクロサービス分割、ルールエンジン導入"
            })
        
        return risks
    
    def _generate_entity_glossary(self, entity: BusinessEntity) -> str:
        """エンティティの用語集説明を生成"""
        return f"{entity.type}として機能し、システム内で重要な役割を果たす"
    
    def _infer_business_purpose(
        self,
        entities: List[BusinessEntity],
        rules: List[BusinessRule]
    ) -> str:
        """ビジネス目的を推論"""
        if any("顧客" in e.name for e in entities):
            # Complex condition - consider breaking down
            return "顧客管理・サービス提供"
        elif any("商品" in e.name for e in entities):
            # Complex condition - consider breaking down
            return "商品管理・販売"
        elif any("データ" in e.name for e in entities):
            # Complex condition - consider breaking down
            return "データ管理・分析"
        else:
            return "業務効率化・自動化"
    
    def _generate_acceptance_criteria(self, rule: BusinessRule) -> str:
        """受け入れ基準を生成"""
        return f"{rule.condition}が満たされた時、{rule.action}が正しく実行されること"
    
    async def _assess_enhanced_documentation_quality(
        self, 
        documentation: str, 
        analysis_results: Dict[str, Any]
    ) -> float:
        """拡張版品質評価"""
        base_quality = await super()._assess_documentation_quality(
            documentation, 
            DocumentationConfig(
                doc_type="design_document",
                format="markdown", 
                language="japanese"
            )
        )
        
        # 分析結果活用度ボーナス
        entities_mentioned = sum(1 for entity in analysis_results.get("entities", []) 
                                if entity.name in documentation)
        rules_mentioned = sum(1 for rule in analysis_results.get("business_rules", [])
                             if rule.action in documentation)
        
        analysis_bonus = min(
            (entities_mentioned * 5 + rules_mentioned * 3), 20.0
        )
        
        return min(base_quality + analysis_bonus, 100.0)
    
    async def _apply_quality_improvements(
        self, 
        documentation: str,
        analysis_results: Dict[str, Any],
        current_quality: float
    ) -> str:
        """品質改善を適用"""
        improvements = []
        
        # 目次が不足している場合
        if "目次" not in documentation:
            improvements.append("目次を追加しています...")
            documentation = "## 📋 目次\n（自動生成）\n\n" + documentation
        
        # 図表が不足している場合
        if "```" not in documentation:
            improvements.append("図表を追加しています...")
            entities = analysis_results.get("entities", [])
            if entities:
                diagram = "\n## システム構成図\n```\n"
                for entity in entities[:3]:
                    # Process each item in collection
                    diagram += f"[{entity.name}] --> "
                diagram += "[システム]\n```\n\n"
                documentation = documentation + diagram
        
        if improvements:
            self.logger.info(f"Applied improvements: {', '.join(improvements)}")
        
        return documentation