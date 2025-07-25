#!/usr/bin/env python3
"""
DocForge Enhanced のテストスイート
TDD: Red Phase - 先にテストを書く
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from elders_guild.elder_tree.elder_servants.dwarf_workshop.doc_forge_enhanced import DocForgeEnhanced


class TestDocForgeEnhanced:
    """DocForge Enhanced のテストクラス"""
    
    @pytest.fixture
    def doc_forge_enhanced(self):
        """テスト用のDocForgeEnhancedインスタンス"""
        return DocForgeEnhanced()
    
    @pytest.mark.asyncio
    async def test_craft_artifact_with_requirements(self, doc_forge_enhanced):
        """要件テキストから設計書を生成"""
        specification = {
            "requirements": "ECサイトで顧客が商品を購入できるシステム",
            "doc_type": "design_document",
            "project_name": "ECサイト"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is True
        assert "documentation" in result
        assert "analysis_results" in result
        assert result["quality_score"] > 0
        
        # 設計書の内容確認
        documentation = result["documentation"]
        assert "設計書" in documentation
        assert "顧客" in documentation
        assert "商品" in documentation
        assert "目次" in documentation
    
    @pytest.mark.asyncio
    async def test_comprehensive_design_document_generation(self, doc_forge_enhanced):
        """包括的な設計書生成をテスト"""
        specification = {
            "requirements": """
            医療システムで患者の診療記録を管理する。
            医師が診断結果を入力し、患者が予約を取れる。
            HIPAA準拠のセキュリティが必要。
            """,
            "doc_type": "design_document",
            "project_name": "医療管理システム",
            "language": "ja"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        # 成功確認
        assert result["success"] is True
        
        # 分析結果確認
        analysis = result["analysis_results"]
        entity_names = [e.name for e in analysis["entities"]]
        assert "患者" in entity_names
        assert "医師" in entity_names
        
        # 潜在ニーズ確認
        implicit_needs = analysis["implicit_needs"]
        security_needs = [n for n in implicit_needs if n.category == "security"]
        assert len(security_needs) > 0
        
        # 設計書の構造確認
        documentation = result["documentation"]
        assert "## 概要" in documentation
        assert "## ビジネス要件" in documentation
        assert "## エンティティ関係図" in documentation
        assert "## 技術的考慮事項" in documentation
        assert "## 実装ガイドライン" in documentation
        assert "mermaid" in documentation  # ERDが含まれる
    
    @pytest.mark.asyncio
    async def test_system_architecture_document(self, doc_forge_enhanced):
        """システムアーキテクチャ文書生成をテスト"""
        specification = {
            "requirements": "大規模なECサイトでマイクロサービス構成",
            "doc_type": "system_architecture",
            "project_name": "大規模ECサイト"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is True
        documentation = result["documentation"]
        
        assert "システムアーキテクチャ仕様書" in documentation
        assert "アーキテクチャ概要" in documentation
        assert "mermaid" in documentation
        assert ("マイクロサービス" in documentation or 
                "モノリシック" in documentation)
    
    @pytest.mark.asyncio
    async def test_business_requirements_document(self, doc_forge_enhanced):
        """ビジネス要件書生成をテスト"""
        specification = {
            "requirements": "会員ランクがゴールドの場合15%割引、1万円以上で送料無料",
            "doc_type": "business_requirements",
            "project_name": "会員システム"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is True
        documentation = result["documentation"]
        
        assert "ビジネス要件定義書" in documentation
        assert "エグゼクティブサマリー" in documentation
        assert "機能要件" in documentation
        assert "FR01" in documentation  # 機能要件番号
    
    @pytest.mark.asyncio
    async def test_quality_assessment_and_improvement(self, doc_forge_enhanced):
        """品質評価と自動改善をテスト"""
        specification = {
            "requirements": "簡単なユーザー管理",
            "doc_type": "design_document",
            "project_name": "ユーザー管理"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is True
        assert "quality_score" in result
        
        # 品質スコアが計算されている
        quality_score = result["quality_score"]
        assert 0 <= quality_score <= 100
        
        # メタデータ確認
        metadata = result["metadata"]
        assert metadata["elder_flow_enhanced"] is True
        assert "analyzer_used" in metadata
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self, doc_forge_enhanced):
        """多言語サポートをテスト"""
        specification = {
            "requirements": "Users can add products to cart and checkout",
            "doc_type": "design_document", 
            "project_name": "E-commerce System",
            "language": "en"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is True
        
        # 英語エンティティが抽出されている
        analysis = result["analysis_results"]
        entity_names = [e.name for e in analysis["entities"]]
        assert any("User" in name or "Product" in name for name in entity_names)
    
    @pytest.mark.asyncio
    async def test_fallback_to_source_code(self, doc_forge_enhanced):
        """ソースコードベース生成へのフォールバック"""
        specification = {
            "source_code": "def hello(): return 'world'",
            "doc_type": "api_documentation",
            "language": "python"
        }
        
        # parent classのメソッドをモック
        with patch.object(doc_forge_enhanced.__class__.__bases__[0], 
                         'craft_artifact', new_callable=AsyncMock) as mock_parent:
            mock_parent.return_value = {
                "success": True,
                "documentation": "API Documentation",
                "quality_score": 85.0
            }
            
            result = await doc_forge_enhanced.craft_artifact(specification)
            
            assert result["success"] is True
            mock_parent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, doc_forge_enhanced):
        """エラーハンドリングをテスト"""
        specification = {
            # 必須パラメータが不足
            "doc_type": "design_document"
        }
        
        result = await doc_forge_enhanced.craft_artifact(specification)
        
        assert result["success"] is False
        assert "error" in result
        assert result["quality_score"] == 0.0
    
    def test_entity_type_translation(self, doc_forge_enhanced):
        """エンティティタイプの翻訳をテスト"""
        assert doc_forge_enhanced._translate_entity_type("actor") == "アクター（システム利用者）"
        assert doc_forge_enhanced._translate_entity_type("object") == "オブジェクト（データ・機能）"
        assert doc_forge_enhanced._translate_entity_type("concept") == "コンセプト（概念・ルール）"
    
    def test_category_translation(self, doc_forge_enhanced):
        """カテゴリの翻訳をテスト"""
        assert doc_forge_enhanced._translate_category("security") == "セキュリティ要件"
        assert doc_forge_enhanced._translate_category("performance") == "パフォーマンス要件"
        assert doc_forge_enhanced._translate_category("scalability") == "スケーラビリティ要件"
    
    def test_actor_goals_generation(self, doc_forge_enhanced):
        """アクター目標の生成をテスト"""
        assert "効率的に" in doc_forge_enhanced._generate_actor_goals("ユーザー")
        assert "購入" in doc_forge_enhanced._generate_actor_goals("顧客")
        assert "運用" in doc_forge_enhanced._generate_actor_goals("管理者")
    
    def test_tech_stack_recommendation(self, doc_forge_enhanced):
        """技術スタック推奨をテスト"""
        from elders_guild.elder_tree.design_generation.requirement_analyzer import ImplicitNeed
        
        needs = [
            ImplicitNeed("セキュリティ", "security", "理由", "high"),
            ImplicitNeed("スケーラビリティ", "scalability", "理由", "high"),
        ]
        
        stack = doc_forge_enhanced._recommend_tech_stack(needs)
        
        assert "フロントエンド" in stack
        assert "バックエンド" in stack
        assert "データベース" in stack
        assert "セキュリティ" in stack  # セキュリティニーズに対応
        assert "クラウド" in stack      # スケーラビリティニーズに対応
    
    def test_risk_analysis(self, doc_forge_enhanced):
        """リスク分析をテスト"""
        from elders_guild.elder_tree.design_generation.requirement_analyzer import ImplicitNeed, BusinessRule
        
        implicit_needs = [
            ImplicitNeed("セキュリティ", "security", "理由", "critical")
        ]
        business_rules = [
            BusinessRule("条件1", "アクション1", "エンティティ1"),
            BusinessRule("条件2", "アクション2", "エンティティ2"),
            BusinessRule("条件3", "アクション3", "エンティティ3"),
        ]
        
        risks = doc_forge_enhanced._analyze_project_risks(implicit_needs, business_rules)
        
        assert len(risks) > 0
        assert any("セキュリティ" in r["description"] or "漏洩" in r["description"] 
                  for r in risks)
    
    @pytest.mark.asyncio
    async def test_quality_improvement_application(self, doc_forge_enhanced):
        """品質改善適用をテスト"""
        documentation = "簡単な文書"
        analysis_results = {
            "entities": [],
            "business_rules": []
        }
        
        improved_doc = await doc_forge_enhanced._apply_quality_improvements(
            documentation, analysis_results, 70.0
        )
        
        # 改善が適用されている
        assert len(improved_doc) > len(documentation)
        assert "目次" in improved_doc
    
    @pytest.mark.asyncio
    async def test_enhanced_quality_assessment(self, doc_forge_enhanced):
        """拡張版品質評価をテスト"""
        documentation = """
        # テスト設計書
        ## 概要
        顧客が商品を購入するシステム
        ## エンティティ
        顧客、商品が含まれる
        """
        
        analysis_results = {
            "entities": [
                type('MockEntity', (), {'name': '顧客'})(),
                type('MockEntity', (), {'name': '商品'})()
            ],
            "business_rules": [
                type('MockRule', (), {'action': '購入'})()
            ]
        }
        
        quality = await doc_forge_enhanced._assess_enhanced_documentation_quality(
            documentation, analysis_results
        )
        
        assert 0 <= quality <= 100
        # 分析結果活用ボーナスにより基本品質より高くなる
        # （エンティティと ルールが文書に言及されているため）