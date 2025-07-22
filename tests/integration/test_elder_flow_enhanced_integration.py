#!/usr/bin/env python3
"""
Elder Flow Enhanced統合テスト
要件テキストから完成した設計書まで一気通貫でテスト
"""

import pytest
import asyncio
from libs.elder_servants.dwarf_workshop.doc_forge_enhanced import DocForgeEnhanced


class TestElderFlowEnhancedIntegration:
    """Elder Flow Enhanced統合テストクラス"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_design_generation(self):
        """E2E: 要件から完成設計書まで"""
        doc_forge = DocForgeEnhanced()
        
        # 実際のユースケース：ECサイト
        specification = {
            "requirements": """
            ECサイトでは、顧客が商品を検索し、カートに追加して購入できる。
            会員ランクがゴールドの場合、全商品15%割引を適用する。
            注文金額が1万円以上の場合、送料無料とする。
            在庫管理システムと連携し、リアルタイムで在庫を更新する。
            決済はクレジットカード、PayPal、銀行振込に対応する。
            購入履歴から推薦商品を表示する。
            """,
            "doc_type": "design_document",
            "project_name": "統合ECサイト",
            "language": "ja"
        }
        
        # Elder Flow Enhanced実行
        result = await doc_forge.craft_artifact(specification)
        
        # 成功確認
        assert result["success"] is True
        
        # 分析結果の品質確認
        analysis = result["analysis_results"]
        
        # エンティティが適切に抽出されている
        entity_names = [e.name for e in analysis["entities"]]
        expected_entities = ["顧客", "商品", "カート", "注文", "在庫", "決済"]
        found_entities = [e for e in expected_entities if e in entity_names]
        assert len(found_entities) >= 4, f"Expected entities: {expected_entities}, Found: {entity_names}"
        
        # ビジネスルールが抽出されている
        business_rules = analysis["business_rules"]
        assert len(business_rules) >= 2
        
        # ゴールド会員割引ルールが検出されている
        gold_rule = next((r for r in business_rules if "ゴールド" in r.condition), None)
        assert gold_rule is not None
        assert "15%" in gold_rule.action or "割引" in gold_rule.action
        
        # 送料無料ルールが検出されている
        shipping_rule = next((r for r in business_rules if "送料無料" in r.action), None)
        assert shipping_rule is not None
        
        # 潜在ニーズが適切に識別されている
        implicit_needs = analysis["implicit_needs"]
        assert len(implicit_needs) >= 3
        
        # セキュリティニーズ（決済関連）
        security_needs = [n for n in implicit_needs if n.category == "security"]
        assert len(security_needs) >= 1
        
        # パフォーマンスニーズ（検索、在庫更新関連）
        performance_needs = [n for n in implicit_needs if n.category == "performance"]
        assert len(performance_needs) >= 1
        
        # 設計書の完成度確認
        documentation = result["documentation"]
        
        # 必須セクションの存在確認
        required_sections = [
            "## 概要",
            "## ビジネス要件", 
            "## システム構成要素",
            "## エンティティ関係図",
            "## ビジネスルール",
            "## 技術的考慮事項",
            "## 実装ガイドライン"
        ]
        
        for section in required_sections:
            assert section in documentation, f"Missing section: {section}"
        
        # ビジネス要素が設計書に反映されている
        assert "顧客" in documentation
        assert "商品" in documentation
        assert "15%割引" in documentation or "ゴールド" in documentation
        assert "送料無料" in documentation
        
        # 技術要素が含まれている
        assert "mermaid" in documentation  # ERD図
        assert "データベース" in documentation or "API" in documentation
        
        # 品質スコアが高い
        quality_score = result["quality_score"]
        assert quality_score >= 75.0, f"Quality score too low: {quality_score}"
        
        # メタデータが正しく設定されている
        metadata = result["metadata"]
        assert metadata["elder_flow_enhanced"] is True
        assert metadata["analyzer_used"] == "EnhancedRequirementAnalyzer"
        assert "analysis_results" in metadata
        
        # 文書の長さが十分（完成度の指標）
        word_count = len(documentation.split())
        assert word_count >= 500, f"Document too short: {word_count} words"
        
        print(f"\n🎉 Integration Test Success!")
        print(f"📊 Quality Score: {quality_score:.1f}")
        print(f"📝 Word Count: {word_count}")
        print(f"🔍 Entities Found: {len(entity_names)}")
        print(f"📋 Business Rules: {len(business_rules)}")
        print(f"💡 Implicit Needs: {len(implicit_needs)}")
    
    @pytest.mark.asyncio
    async def test_medical_system_case(self):
        """医療システムケースのE2Eテスト"""
        doc_forge = DocForgeEnhanced()
        
        specification = {
            "requirements": """
            医療システムで患者の診療記録を管理する。
            医師が診断結果を入力し、患者が予約を取れる。
            HIPAA準拠のセキュリティが必要。
            患者データは暗号化して保存する。
            """,
            "doc_type": "design_document",
            "project_name": "医療管理システム",
            "language": "ja"
        }
        
        result = await doc_forge.craft_artifact(specification)
        
        assert result["success"] is True
        
        # 医療ドメイン特有の要素確認
        analysis = result["analysis_results"]
        entity_names = [e.name for e in analysis["entities"]]
        assert "患者" in entity_names
        assert "医師" in entity_names
        
        # セキュリティ・コンプライアンス要件
        implicit_needs = analysis["implicit_needs"]
        security_needs = [n for n in implicit_needs if n.category in ["security", "compliance"]]
        assert len(security_needs) >= 2
        
        # HIPAA言及確認
        documentation = result["documentation"]
        assert "HIPAA" in documentation or "セキュリティ" in documentation
        assert "暗号化" in documentation
    
    @pytest.mark.asyncio 
    async def test_performance_under_complex_requirements(self):
        """複雑な要件での性能テスト"""
        doc_forge = DocForgeEnhanced()
        
        # 複雑な要件テキスト
        specification = {
            "requirements": """
            金融取引システムでは、顧客が口座を開設し、資金の預入・引出・送金を行える。
            取引履歴を管理し、月次明細書を自動生成する。
            不正取引検知システムと連携し、リアルタイムで監視する。
            規制当局への報告書を自動作成する。
            多要素認証によるセキュリティを実装する。
            高頻度取引に対応するため、秒間1000件の処理能力が必要。
            データは3拠点でレプリケーションし、災害対応を行う。
            顧客は取引をモバイル、Web、ATMから実行できる。
            """,
            "doc_type": "design_document",
            "project_name": "金融取引システム",
            "language": "ja"
        }
        
        import time
        start_time = time.time()
        
        result = await doc_forge.craft_artifact(specification)
        
        execution_time = time.time() - start_time
        
        # 成功とパフォーマンス確認
        assert result["success"] is True
        assert execution_time < 10.0, f"Too slow: {execution_time:.2f}s"
        
        # 複雑な要件でも適切に分析
        analysis = result["analysis_results"]
        assert len(analysis["entities"]) >= 6
        assert len(analysis["business_rules"]) >= 3
        assert len(analysis["implicit_needs"]) >= 5
        
        # 品質維持確認
        assert result["quality_score"] >= 70.0
        
        print(f"⚡ Performance Test: {execution_time:.2f}s")