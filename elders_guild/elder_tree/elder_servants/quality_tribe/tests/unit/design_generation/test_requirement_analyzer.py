#!/usr/bin/env python3
"""
要件分析エンジンのテストスイート
TDD: Red Phase - 失敗するテストを先に書く
"""

import pytest
from typing import Dict, List
from unittest.mock import Mock, patch

from elders_guild.elder_tree.design_generation.requirement_analyzer import (
    EnhancedRequirementAnalyzer,
    BusinessEntity,
    BusinessRelationship,
    BusinessRule,
    ImplicitNeed
)


class TestEnhancedRequirementAnalyzer:
    """要件分析エンジンのテストクラス"""
    
    @pytest.fixture
    def analyzer(self):
        """テスト用のアナライザーインスタンス"""
        return EnhancedRequirementAnalyzer()
    
    def test_extract_entities_from_user_story(self, analyzer):
        """ユーザーストーリーからエンティティを抽出"""
        requirements = """
        ユーザーとして、商品をカートに追加し、
        クーポンを適用して注文を完了したい。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # エンティティが抽出されること
        assert "entities" in result
        entities = result["entities"]
        entity_names = [e.name for e in entities]
        
        assert "ユーザー" in entity_names
        assert "商品" in entity_names
        assert "カート" in entity_names
        assert "クーポン" in entity_names
        assert "注文" in entity_names
    
    def test_identify_relationships(self, analyzer):
        """エンティティ間の関係性を識別"""
        requirements = """
        顧客は複数の注文を持つことができ、
        各注文は複数の商品を含むことができる。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # 関係性が識別されること
        assert "relationships" in result
        relationships = result["relationships"]
        
        # 顧客-注文の1対多関係
        customer_order_rel = next(
            (r for r in relationships 
             if r.from_entity == "顧客" and r.to_entity == "注文"),
            None
        )
        assert customer_order_rel is not None
        assert customer_order_rel.cardinality == "1:N"
        
        # 注文-商品の多対多関係
        order_product_rel = next(
            (r for r in relationships
             if r.from_entity == "注文" and r.to_entity == "商品"),
            None
        )
        assert order_product_rel is not None
        assert order_product_rel.cardinality == "N:M"
    
    def test_infer_business_rules(self, analyzer):
        """ビジネスルールの推論"""
        requirements = """
        会員ランクがゴールドの場合、全商品15%割引を適用する。
        注文金額が1万円以上の場合、送料無料とする。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # ビジネスルールが推論されること
        assert "business_rules" in result
        rules = result["business_rules"]
        
        # ゴールド会員割引ルール
        gold_discount_rule = next(
            (r for r in rules if "ゴールド" in r.condition),
            None
        )
        assert gold_discount_rule is not None
        assert gold_discount_rule.action == "15%割引適用"
        assert gold_discount_rule.entity == "商品"
        
        # 送料無料ルール
        free_shipping_rule = next(
            (r for r in rules if "1万円" in r.condition),
            None
        )
        assert free_shipping_rule is not None
        assert free_shipping_rule.action == "送料無料"
    
    def test_discover_implicit_needs(self, analyzer):
        """潜在的なニーズの発見"""
        requirements = """
        管理者は売上レポートを確認したい。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # 潜在ニーズが発見されること
        assert "implicit_needs" in result
        implicit_needs = result["implicit_needs"]
        
        # 期待される潜在ニーズ
        need_descriptions = [n.description for n in implicit_needs]
        
        # 権限管理の必要性
        assert any("権限" in desc or "認証" in desc for desc in need_descriptions)
        
        # データ可視化の必要性
        assert any("グラフ" in desc or "可視化" in desc for desc in need_descriptions)
        
        # エクスポート機能の必要性
        assert any("エクスポート" in desc or "ダウンロード" in desc for desc in need_descriptions)
    
    def test_handle_complex_requirements(self, analyzer):
        """複雑な要件の処理"""
        requirements = """
        ECサイトでは、顧客が商品を検索し、カートに追加して購入できる。
        在庫管理システムと連携し、リアルタイムで在庫を更新する。
        決済はクレジットカード、PayPal、銀行振込に対応する。
        購入履歴から推薦商品を表示する。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # すべての要素が抽出されること
        entities = [e.name for e in result["entities"]]
        assert len(entities) >= 5  # 顧客、商品、カート、在庫、決済など
        
        relationships = result["relationships"]
        assert len(relationships) >= 4  # 複数の関係性
        
        rules = result["business_rules"]
        assert len(rules) >= 2  # 在庫連携、推薦ロジックなど
        
        implicit_needs = result["implicit_needs"]
        assert len(implicit_needs) >= 3  # セキュリティ、API統合など
    
    def test_domain_specific_analysis(self, analyzer):
        """ドメイン特化型の分析"""
        requirements = """
        医療システムで患者の診療記録を管理する。
        HIPAA準拠のセキュリティが必要。
        """
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # 医療ドメイン特有の要素が識別されること
        implicit_needs = result["implicit_needs"]
        need_descriptions = [n.description for n in implicit_needs]
        
        # プライバシー保護
        assert any("プライバシー" in desc or "個人情報" in desc for desc in need_descriptions)
        
        # 監査ログ
        assert any("監査" in desc or "アクセスログ" in desc for desc in need_descriptions)
        
        # データ暗号化
        assert any("暗号化" in desc for desc in need_descriptions)
    
    def test_confidence_scoring(self, analyzer):
        """分析結果の信頼度スコアリング"""
        requirements = "ユーザーが商品を購入する"
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # 各要素に信頼度スコアが付与されること
        for entity in result["entities"]:
            assert hasattr(entity, "confidence")
            assert 0.0 <= entity.confidence <= 1.0
        
        for relationship in result["relationships"]:
            assert hasattr(relationship, "confidence")
            assert 0.0 <= relationship.confidence <= 1.0
    
    def test_empty_requirements_handling(self, analyzer):
        """空の要件の処理"""
        requirements = ""
        
        result = analyzer.analyze_business_requirements(requirements)
        
        # エラーにならず、空の結果を返すこと
        assert result["entities"] == []
        assert result["relationships"] == []
        assert result["business_rules"] == []
        assert result["implicit_needs"] == []
    
    @pytest.mark.parametrize("lang", ["en", "ja", "zh"])
    def test_multilingual_support(self, analyzer, lang):
        """多言語サポート"""
        requirements_map = {
            "en": "Users can add products to cart and checkout",
            "ja": "ユーザーは商品をカートに追加してチェックアウトできる",
            "zh": "用户可以将产品添加到购物车并结账"
        }
        
        result = analyzer.analyze_business_requirements(
            requirements_map[lang],
            language=lang
        )
        
        # 言語に関わらず基本的なエンティティが抽出されること
        entities = [e.name.lower() for e in result["entities"]]
        assert any("user" in e or "ユーザー" in e or "用户" in e for e in entities)
        assert any("product" in e or "商品" in e or "产品" in e for e in entities)