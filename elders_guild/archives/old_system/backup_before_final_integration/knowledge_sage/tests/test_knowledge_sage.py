"""
🧪 Knowledge Sage テストスイート

Knowledge Sageの知識管理機能をテスト駆動開発で実装
テストファーストアプローチで仕様を明確化
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# 実装予定のクラスをインポート
from knowledge_sage.soul import KnowledgeSage
from knowledge_sage.abilities.knowledge_models import (
    KnowledgeItem, 
    BestPractice, 
    LearningPattern,
    KnowledgeCategory,
    SearchQuery,
    SearchResult
)


@pytest.fixture
def temp_knowledge_base():
    """テスト用一時ナレッジベース"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def knowledge_sage(temp_knowledge_base):
    """テスト用Knowledge Sageインスタンス"""
    return KnowledgeSage(knowledge_base_path=temp_knowledge_base)


@pytest.fixture
def sample_knowledge_item():
    """サンプル知識アイテム"""
    return KnowledgeItem(
        title="TDD実装パターン",
        content="Test-Driven Development の実装手順: Red→Green→Refactor",
        category=KnowledgeCategory.DEVELOPMENT_PATTERN,
        tags=["TDD", "testing", "development"],
        source="実装経験",
        confidence_score=0.9
    )


class TestKnowledgeModels:
    """データモデルのテスト"""
    
    def test_knowledge_item_creation(self):
        """KnowledgeItem作成テスト"""
        item = KnowledgeItem(
            title="テスト知識",
            content="テストコンテンツ",
            category=KnowledgeCategory.GENERAL,
            tags=["test"],
            source="テスト"
        )
        
        assert item.title == "テスト知識"
        assert item.content == "テストコンテンツ"
        assert item.category == KnowledgeCategory.GENERAL
        assert item.tags == ["test"]
        assert item.confidence_score == 0.8  # デフォルト値
        assert item.created_at is not None
        assert item.id is not None
    
    def test_best_practice_creation(self):
        """BestPractice作成テスト"""
        practice = BestPractice(
            title="コミット前テスト実行",
            description="コミット前に必ずテストを実行してからプッシュする",
            domain="version_control",
            impact_level="high",
            implementation_steps=["テスト実行", "成功確認", "コミット", "プッシュ"]
        )
        
        assert practice.title == "コミット前テスト実行"
        assert practice.domain == "version_control"
        assert practice.impact_level == "high"
        assert len(practice.implementation_steps) == 4
    
    def test_learning_pattern_creation(self):
        """LearningPattern作成テスト"""
        pattern = LearningPattern(
            pattern_name="エラー修正パターン",
            trigger="実装エラー発生",
            approach="根本原因分析→修正→テスト→学習記録",
            success_rate=0.85,
            usage_count=12
        )
        
        assert pattern.pattern_name == "エラー修正パターン"
        assert pattern.success_rate == 0.85
        assert pattern.usage_count == 12


class TestKnowledgeSageCore:
    """Knowledge Sage コア機能のテスト"""
    
    def test_knowledge_sage_initialization(self, temp_knowledge_base):
        """Knowledge Sage初期化テスト"""
        sage = KnowledgeSage(knowledge_base_path=temp_knowledge_base)
        
        assert sage.knowledge_base_path == temp_knowledge_base
        assert sage.soul_type == "knowledge_sage"
        assert sage.is_ready() is True
    
    def test_store_knowledge_item(self, knowledge_sage, sample_knowledge_item):
        """知識アイテム保存テスト"""
        result = knowledge_sage.store_knowledge(sample_knowledge_item)
        
        assert result["status"] == "success"
        assert "knowledge_id" in result
        
        # 保存確認
        stored_item = knowledge_sage.get_knowledge(result["knowledge_id"])
        assert stored_item is not None
        assert stored_item.title == sample_knowledge_item.title
    
    def test_store_best_practice(self, knowledge_sage):
        """ベストプラクティス保存テスト"""
        practice = BestPractice(
            title="Iron Will遵守",
            description="TODO/FIXMEコメントを使用せず、完全な実装を行う",
            domain="development_standards",
            impact_level="critical",
            implementation_steps=["仕様確認", "完全実装", "テスト確認"]
        )
        
        result = knowledge_sage.store_best_practice(practice)
        
        assert result["status"] == "success"
        assert "practice_id" in result
        
        # 取得確認
        stored_practice = knowledge_sage.get_best_practice(result["practice_id"])
        assert stored_practice.title == "Iron Will遵守"
    
    def test_store_learning_pattern(self, knowledge_sage):
        """学習パターン保存テスト"""
        pattern = LearningPattern(
            pattern_name="TDD実装パターン",
            trigger="新機能実装要求",
            approach="Red→Green→Refactor→Commit",
            success_rate=0.95
        )
        
        result = knowledge_sage.store_learning_pattern(pattern)
        
        assert result["status"] == "success"
        
        # 取得確認
        patterns = knowledge_sage.get_learning_patterns(pattern_name="TDD実装パターン")
        assert len(patterns) == 1
        assert patterns[0].success_rate == 0.95


class TestKnowledgeSearch:
    """知識検索機能のテスト"""
    
    def test_search_by_keyword(self, knowledge_sage, sample_knowledge_item):
        """キーワード検索テスト"""
        # 知識を保存
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        # 検索実行
        results = knowledge_sage.search_knowledge(query="TDD")
        
        assert len(results) == 1
        assert results[0].title == sample_knowledge_item.title
    
    def test_search_by_category(self, knowledge_sage, sample_knowledge_item):
        """カテゴリ検索テスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        results = knowledge_sage.search_by_category(KnowledgeCategory.DEVELOPMENT_PATTERN)
        
        assert len(results) == 1
        assert results[0].category == KnowledgeCategory.DEVELOPMENT_PATTERN
    
    def test_search_by_tags(self, knowledge_sage, sample_knowledge_item):
        """タグ検索テスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        results = knowledge_sage.search_by_tags(["testing"])
        
        assert len(results) == 1
        assert "testing" in results[0].tags
    
    def test_advanced_search(self, knowledge_sage, sample_knowledge_item):
        """高度な検索テスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        query = SearchQuery(
            keywords=["TDD"],
            category=KnowledgeCategory.DEVELOPMENT_PATTERN,
            tags=["testing"],
            min_confidence=0.8
        )
        
        results = knowledge_sage.advanced_search(query)
        
        assert len(results) >= 1
        assert all(r.item.confidence_score >= 0.8 for r in results)


class TestKnowledgeAnalytics:
    """知識分析機能のテスト"""
    
    def test_knowledge_statistics(self, knowledge_sage, sample_knowledge_item):
        """知識統計情報テスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        stats = knowledge_sage.get_knowledge_statistics()
        
        assert stats.total_items == 1
        assert stats.categories[KnowledgeCategory.DEVELOPMENT_PATTERN] == 1
        assert stats.average_confidence > 0
    
    def test_popular_tags(self, knowledge_sage):
        """人気タグ分析テスト"""
        # 複数の知識を保存（異なるタグ）
        items = [
            KnowledgeItem(
                title="Test1", content="Content1", 
                category=KnowledgeCategory.GENERAL, tags=["python", "testing"],
                source="test"
            ),
            KnowledgeItem(
                title="Test2", content="Content2", 
                category=KnowledgeCategory.GENERAL, tags=["python", "development"],
                source="test"
            )
        ]
        
        for item in items:
            knowledge_sage.store_knowledge(item)
        
        popular_tags = knowledge_sage.get_popular_tags(limit=5)
        
        assert len(popular_tags) >= 1
        assert popular_tags[0]["tag"] == "python"  # 最も使用されている
        assert popular_tags[0]["count"] == 2
    
    def test_knowledge_trends(self, knowledge_sage):
        """知識トレンド分析テスト"""
        # 時系列データの作成は複雑なので、基本的なテストのみ
        trends = knowledge_sage.analyze_knowledge_trends()
        
        assert "daily_growth" in trends
        assert "category_trends" in trends
        assert isinstance(trends["daily_growth"], list)


class TestKnowledgeIntegration:
    """知識統合・推論機能のテスト"""
    
    def test_knowledge_synthesis(self, knowledge_sage):
        """知識統合テスト"""
        # 関連する知識を複数保存
        items = [
            KnowledgeItem(
                title="TDD Red Phase", content="失敗するテストを先に書く",
                category=KnowledgeCategory.DEVELOPMENT_PATTERN, tags=["TDD", "red"],
                source="test"
            ),
            KnowledgeItem(
                title="TDD Green Phase", content="最小限の実装でテストを通す",
                category=KnowledgeCategory.DEVELOPMENT_PATTERN, tags=["TDD", "green"],
                source="test"
            ),
            KnowledgeItem(
                title="TDD Refactor Phase", content="コードを改善する",
                category=KnowledgeCategory.DEVELOPMENT_PATTERN, tags=["TDD", "refactor"],
                source="test"
            )
        ]
        
        for item in items:
            knowledge_sage.store_knowledge(item)
        
        # 知識統合実行
        synthesis = knowledge_sage.synthesize_knowledge(topic="TDD")
        
        assert synthesis["topic"] == "TDD"
        assert "summary" in synthesis
        assert "key_points" in synthesis
        assert len(synthesis["related_items"]) == 3
    
    def test_recommend_knowledge(self, knowledge_sage, sample_knowledge_item):
        """知識推奨テスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        recommendations = knowledge_sage.recommend_knowledge(
            context="新機能実装",
            user_expertise="intermediate"
        )
        
        assert isinstance(recommendations, list)
        # 推奨システムの基本動作確認
        if recommendations:
            assert "title" in recommendations[0]
            assert "relevance_score" in recommendations[0]


class TestKnowledgeExportImport:
    """知識のエクスポート・インポート機能テスト"""
    
    def test_export_knowledge_base(self, knowledge_sage, sample_knowledge_item):
        """ナレッジベース エクスポートテスト"""
        knowledge_sage.store_knowledge(sample_knowledge_item)
        
        export_data = knowledge_sage.export_knowledge_base()
        
        assert "knowledge_items" in export_data
        assert "best_practices" in export_data
        assert "learning_patterns" in export_data
        assert len(export_data["knowledge_items"]) == 1
    
    def test_import_knowledge_base(self, knowledge_sage):
        """ナレッジベース インポートテスト"""
        import_data = {
            "knowledge_items": [{
                "title": "Imported Knowledge",
                "content": "Imported content",
                "category": "general",
                "tags": ["imported"],
                "source": "test_import"
            }]
        }
        
        result = knowledge_sage.import_knowledge_base(import_data)
        
        assert result["status"] == "success"
        assert result["imported_items"] == 1
        
        # インポート確認
        results = knowledge_sage.search_knowledge("Imported Knowledge")
        assert len(results) == 1


# 統合テスト用のクラス
class TestKnowledgeSageIntegration:
    """Knowledge Sage 統合テスト"""
    
    def test_full_knowledge_workflow(self, knowledge_sage):
        """完全な知識管理ワークフローテスト"""
        # 1.0 知識の保存
        knowledge = KnowledgeItem(
            title="Flask API実装パターン",
            content="Flaskでの RESTful API実装のベストプラクティス",
            category=KnowledgeCategory.DEVELOPMENT_PATTERN,
            tags=["flask", "api", "python"],
            source="実装経験"
        )
        store_result = knowledge_sage.store_knowledge(knowledge)
        assert store_result["status"] == "success"
        
        # 2.0 ベストプラクティスの関連付け
        practice = BestPractice(
            title="API エラーハンドリング",
            description="適切なHTTPステータスコードとエラーメッセージを返す",
            domain="web_development",
            impact_level="high"
        )
        practice_result = knowledge_sage.store_best_practice(practice)
        assert practice_result["status"] == "success"
        
        # 3.0 学習パターンの記録
        pattern = LearningPattern(
            pattern_name="API実装学習パターン",
            trigger="API開発タスク",
            approach="設計→実装→テスト→ドキュメント化",
            success_rate=0.9
        )
        pattern_result = knowledge_sage.store_learning_pattern(pattern)
        assert pattern_result["status"] == "success"
        
        # 4.0 統合検索
        results = knowledge_sage.search_knowledge("API")
        assert len(results) >= 1
        
        # 5.0 知識統合
        synthesis = knowledge_sage.synthesize_knowledge(topic="API開発")
        assert synthesis["topic"] == "API開発"
        
        # 6.0 統計確認
        stats = knowledge_sage.get_knowledge_statistics()
        assert stats.total_items >= 1