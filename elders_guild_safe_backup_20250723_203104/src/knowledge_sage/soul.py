"""
📚 Knowledge Sage - 知識管理賢者

ナレッジベース管理、ベストプラクティス蓄積、学習パターン記録を担当する賢者
分散型の知識管理システムの核となる魂
"""

import json
import logging
import pickle
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict, Counter

# 共通基盤
from shared_libs.soul_base import BaseSoul
# A2A protocol removed - not needed for current implementation

# Knowledge Sage専用モデル
from knowledge_sage.abilities.knowledge_models import (
    KnowledgeItem,
    BestPractice,
    LearningPattern,
    KnowledgeCategory,
    SearchQuery,
    SearchResult,
    KnowledgeStatistics,
    KnowledgeSynthesis,
    create_knowledge_item_from_dict
)


class KnowledgeSage(BaseSoul):
    pass


"""
    📚 Knowledge Sage - 知識管理賢者
    
    機能:
    - ナレッジベース管理（知識の保存・検索・更新）
    - ベストプラクティス蓄積・推奨
    - 学習パターン記録・分析
    - 知識統合・推論機能
    - 知識統計・トレンド分析
    """ Path = None):
        """初期化"""
        super().__init__(soul_type="knowledge_sage", domain="knowledge_management")
        
        # 知識ベースの設定
        self.knowledge_base_path = knowledge_base_path or Path("/home/aicompany/ai_co/knowledge_base" \
            "/home/aicompany/ai_co/knowledge_base" \
            "/home/aicompany/ai_co/knowledge_base")
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        
        # データストレージ設定
        self.data_dir = self.knowledge_base_path / "sage_data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.knowledge_file = self.data_dir / "knowledge_items.json"
        self.practices_file = self.data_dir / "best_practices.json"
        self.patterns_file = self.data_dir / "learning_patterns.json"
        self.index_file = self.data_dir / "search_index.json"
        
        # インメモリストレージ（開発時用、本番はDBに移行予定）
        self._knowledge_items: Dict[str, KnowledgeItem] = {}
        self._best_practices: Dict[str, BestPractice] = {}
        self._learning_patterns: Dict[str, LearningPattern] = {}
        self._search_index: Dict[str, List[str]] = defaultdict(list)
        
        # Logger設定
        self.logger = logging.getLogger(f"KnowledgeSage.{self.soul_name}")
        
        # 起動時にデータロード
        self._load_all_data()
        
        self.logger.info(f"Knowledge Sage initialized with {len(self._knowledge_items)} knowledge items" \
            "Knowledge Sage initialized with {len(self._knowledge_items)} knowledge items" \
            "Knowledge Sage initialized with {len(self._knowledge_items)} knowledge items")
    
    async def initialize(self) -> bool:
        pass

        
        """BaseSoulの抽象メソッド実装"""
            # データロード
            self._load_all_data()
            
            # 能力登録
            self.register_ability("knowledge_management")
            self.register_ability("best_practices")
            self.register_ability("learning_patterns")
            self.register_ability("knowledge_search")
            self.register_ability("knowledge_synthesis")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Knowledge Sage: {e}")
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """BaseSoulの抽象メソッド実装"""
        try:
            action = message.get("action")
            
            if action == "search_knowledge":
                query = message.get("query", "")
                results = self.search_knowledge(query)
                return self._create_success_response(
                    message,
                    {"results": [item.to_dict() for item in results]}
                )
            
            elif action == "store_knowledge":
                knowledge_data = message.get("knowledge")
                if knowledge_data:
                    item = create_knowledge_item_from_dict(knowledge_data)
                    result = self.store_knowledge(item)
                    return self._create_success_response(message, result)
            
            elif action == "get_statistics":
                stats = self.get_knowledge_statistics()
                return self._create_success_response(message, stats.to_dict())
            
            else:
                return self._create_error_response(message, f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def shutdown(self):
        pass

            """BaseSoulの抽象メソッド実装"""
            # データ保存
            self._save_all_data()
            self.logger.info("Knowledge Sage shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def is_ready(self) -> bool:
        pass

    
    """準備完了確認""" KnowledgeItem) -> Dict[str, Any]:
        """知識アイテム保存"""
        try:
            # 既存チェック
            if knowledge.id in self._knowledge_items:
                return {"status": "error", "message": "Knowledge item already exists"}
            
            # 保存
            self._knowledge_items[knowledge.id] = knowledge
            self._update_search_index(knowledge)
            self._save_knowledge_items()
            
            self.logger.info(f"Stored knowledge item: {knowledge.title}")
            
            return {
                "status": "success",
                "knowledge_id": knowledge.id,
                "message": f"Knowledge '{knowledge.title}' stored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error storing knowledge: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]item = self._knowledge_items.get(knowledge_id):
    """識アイテム取得""":
        if item:
            item.access()  # アクセス記録
            self._save_knowledge_items()
        return item
    
    def update_knowledge(self, knowledge_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """知識アイテム更新"""
        try:
            if knowledge_id not in self._knowledge_items:
                return {"status": "error", "message": "Knowledge item not found"}
            
            item = self._knowledge_items[knowledge_id]
            
            # 許可された更新項目
            allowed_fields = ["title", "content", "tags", "confidence_score", "references"]
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "content":
                        item.update_content(value, updates.get("source"))
                    else:
                        setattr(item, field, value)
            
            item.updated_at = datetime.now(timezone.utc)
            self._update_search_index(item)
            self._save_knowledge_items()
            
            return {"status": "success", "message": "Knowledge updated successfully"}
            
        except Exception as e:
            self.logger.error(f"Error updating knowledge: {e}")
            return {"status": "error", "message": str(e)}
    
    # === ベストプラクティス管理 ===
    
    def store_best_practice(self, practice: BestPractice) -> Dict[str, Any]:
        """ベストプラクティス保存"""
        try:
            self._best_practices[practice.id] = practice
            self._save_best_practices()
            
            self.logger.info(f"Stored best practice: {practice.title}")
            
            return {
                "status": "success",
                "practice_id": practice.id,
                "message": f"Best practice '{practice.title}' stored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error storing best practice: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_best_practice(self, practice_id: str) -> Optional[BestPractice]return self._best_practices.get(practice_id):
    """ストプラクティス取得"""
    :
    def get_best_practices_by_domain(self, domain: str) -> List[BestPractice]return [p for p in self._best_practices.values() if p.domain == domain]:
    """メイン別ベストプラクティス取得"""
    :
    def get_best_practices_by_impact(self, impact_level: str) -> List[BestPractice]return [p for p in self._best_practices.values() if p.impact_level == impact_level]:
    """響レベル別ベストプラクティス取得"""
    
    # === 学習パターン管理 ===
    :
    def store_learning_pattern(self, pattern: LearningPattern) -> Dict[str, Any]:
        """学習パターン保存"""
        try:
            self._learning_patterns[pattern.id] = pattern
            self._save_learning_patterns()
            
            self.logger.info(f"Stored learning pattern: {pattern.pattern_name}")
            
            return {
                "status": "success",
                "pattern_id": pattern.id,
                "message": f"Learning pattern '{pattern.pattern_name}' stored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error storing learning pattern: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_learning_pattern(self, pattern_id: str) -> Optional[LearningPattern]return self._learning_patterns.get(pattern_id):
    """習パターン取得"""
    :
    def get_learning_patterns(self, pattern_name: str = None, 
                            trigger: str = None) -> List[LearningPattern]:
        """学習パターン検索"""
        patterns = list(self._learning_patterns.values())
        
        if pattern_name:
            patterns = [p for p in patterns if pattern_name in p.pattern_name]
        
        if trigger:
            patterns = [p for p in patterns if trigger in p.trigger]
        
        return patterns
    
    # === 知識検索機能 ===
    
    def search_knowledge(self, query: str, limit: int = 20) -> List[KnowledgeItem]query_lower = query.lower():
    """本的な知識検索"""
        results = []
        :
        for item in self._knowledge_items.values():
            # タイトル、コンテンツ、タグでマッチング
            if (query_lower in item.title.lower() or 
                query_lower in item.content.lower() or
                any(query_lower in tag for tag in item.tags)):
                results.append(item)
        
        # 関連度でソート（単純な実装）
        results.sort(key=lambda x: self._calculate_relevance(x, query_lower), reverse=True)
        
        # アクセス記録
        for item in results[:limit]:
            item.access()
        
        self._save_knowledge_items()
        return results[:limit]
    
    def search_by_category(self, category: KnowledgeCategory) -> List[KnowledgeItem]return [item for item in self._knowledge_items.values() if item.category == category]:
    """テゴリ検索"""
    :
    def search_by_tags(self, tags: List[str]) -> List[KnowledgeItem]tag_set = {tag.lower() for tag in tags}:
    """グ検索"""
        results = []
        :
        for item in self._knowledge_items.values():
            item_tags = {tag.lower() for tag in item.tags}
            if tag_set & item_tags:  # 共通タグがある
                results.append(item)
        
        return results
    
    def advanced_search(self, query: SearchQuery) -> List[SearchResult]:
        """高度な検索"""
        results = []
        
        for item in self._knowledge_items.values():
            relevance = 0.0
            match_reasons = []
            
            # カテゴリフィルタ
            if query.category and item.category != query.category:
                continue
            
            # 信頼度フィルタ
            if item.confidence_score < query.min_confidence:
                continue
            
            # キーワードマッチング
            if query.keywords:
                keyword_match = sum(
                    1 for keyword in query.keywords 
                    if keyword in item.title.lower() or keyword in item.content.lower()
                )
                if keyword_match > 0:
                    relevance += keyword_match / len(query.keywords) * 0.4
                    match_reasons.append(f"Keywords: {keyword_match}/{len(query.keywords)}")
            
            # タグマッチング
            if query.tags:
                tag_match = len(set(query.tags) & set(item.tags))
                if tag_match > 0:
                    relevance += tag_match / len(query.tags) * 0.3
                    match_reasons.append(f"Tags: {tag_match}/{len(query.tags)}")
            
            # 信頼度スコア
            relevance += item.confidence_score * 0.3
            
            if relevance > 0:
                search_result = SearchResult(
                    item=item,
                    relevance_score=min(relevance, 1.0),
                    match_reasons=match_reasons
                )
                results.append(search_result)
        
        # ソート
        if query.sort_by == "relevance":
            results.sort(key=lambda x: x.relevance_score, reverse=(query.sort_order == "desc"))
        elif query.sort_by == "date":
            results.sort(key=lambda x: x.item.created_at, reverse=(query.sort_order == "desc"))
        elif query.sort_by == "confidence":
            results.sort(key=lambda x: x.item.confidence_score, reverse=(query.sort_order == "desc" \
                "desc" \
                "desc"))
        elif query.sort_by == "access_count":
            results.sort(key=lambda x: x.item.access_count, reverse=(query.sort_order == "desc"))
        
        return results[:query.max_results]
    
    # === 知識統計・分析 ===
    
    def get_knowledge_statistics(self) -> KnowledgeStatistics:
        pass

    
    """知識統計情報取得"""
            stats.average_confidence = sum(
                item.confidence_score for item in self._knowledge_items.values()
            ) / len(self._knowledge_items)
        
        # 最もアクセスされたアイテム
        sorted_by_access = sorted(
            self._knowledge_items.values(),
            key=lambda x: x.access_count,
            reverse=True
        )
        stats.most_accessed_items = [
            {"title": item.title, "access_count": item.access_count, "id": item.id}
            for item in sorted_by_access[:10]
        ]
        
        # 人気タグ
        stats.popular_tags = self.get_popular_tags(limit=20)
        
        return stats
    
    def get_popular_tags(self, limit: int = 10) -> List[Dict[str, Any]]tag_counts = Counter():
    """気タグ分析"""
        
        # 繰り返し処理:
        for item in self._knowledge_items.values():
            for tag in item.tags:
                tag_counts[tag] += 1
        
        return [
            {"tag": tag, "count": count}
            for tag, count in tag_counts.most_common(limit)
        ]
    
    def analyze_knowledge_trends(self) -> Dict[str, Any]:
        pass

            """知識トレンド分析""" [],
            "category_trends": {},
            "tag_trends": {}
        }
        
        # 日次成長（簡易実装）
        daily_counts = defaultdict(int)
        for item in self._knowledge_items.values():
            day = item.created_at.strftime("%Y-%m-%d")
            daily_counts[day] += 1
        
        trends["daily_growth"] = [
            {"date": day, "count": count}
            for day, count in sorted(daily_counts.items())
        ]
        
        return trends
    
    # === 知識統合・推論 ===
    
    def synthesize_knowledge(self, topic: str) -> Dict[str, Any]:
        """知識統合"""
        # トピックに関連する知識を検索
        related_items = self.search_knowledge(topic, limit=10)
        
        if not related_items:
            return {
                "topic": topic,
                "summary": "関連する知識が見つかりません。",
                "key_points": [],
                "related_items": []
            }
        
        # 簡易統合（実際にはより高度なNLP処理が必要）
        key_points = []
        all_content = []
        
        for item in related_items:
            all_content.append(item.content)
            if len(item.content.split()) < 50:  # 短い内容はキーポイントとして扱う
                key_points.append(item.content.strip())
        
        # サマリー生成（簡易版）
        summary = f"{topic}に関する{len(related_items)}件の知識を統合しました。"
        
        return {
            "topic": topic,
            "summary": summary,
            "key_points": key_points[:5],  # 上位5つのポイント
            "related_items": [item.id for item in related_items],
            "synthesis_method": "basic_aggregation",
            "confidence": min(
                sum(item.confidence_score for item in related_items) / len(related_items),
                1.0
            )
        }
    
    def recommend_knowledge(
        self,
        context: str,
        user_expertise: str = "intermediate"
    ) -> List[Dict[str, Any]]:

    """知識推奨"""
            relevance_score = self._calculate_recommendation_score(item, context, user_expertise)
            
            recommendations.append({
                "title": item.title,
                "content_preview": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "category": item.category.value,
                "tags": item.tags,
                "relevance_score": relevance_score,
                "confidence": item.confidence_score,
                "id": item.id
            })
        
        return sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True)
    
    # === エクスポート・インポート ===
    
    def export_knowledge_base(self) -> Dict[str, Any]:
        pass

    
    """ナレッジベースエクスポート""" [item.to_dict() for item in self._knowledge_items.values()],
            "best_practices": [practice.to_dict() for practice in self._best_practices.values()],
            "learning_patterns": [pattern.to_dict() for pattern in self._learning_patterns.values()],
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        }
    
    def import_knowledge_base(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベースインポート"""
        try:
            imported_items = 0
            
            # 知識アイテムのインポート
            if "knowledge_items" in import_data:
                for item_data in import_data["knowledge_items"]:
                    try:
                        item = create_knowledge_item_from_dict(item_data)
                        if not (item.id not in self._knowledge_items):
                        if item.id not in self._knowledge_items:
                            self._knowledge_items[item.id] = item
                            self._update_search_index(item)
                            imported_items += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to import knowledge item: {e}")
            
            # データ保存
            if imported_items > 0:
                self._save_all_data()
            
            return {
                "status": "success",
                "imported_items": imported_items,
                "message": f"Successfully imported {imported_items} knowledge items"
            }
            
        except Exception as e:
            self.logger.error(f"Error importing knowledge base: {e}")
            return {"status": "error", "message": str(e)}
    
    # === A2A通信対応 ===
    # A2A communication methods removed - not needed for current implementation
    
    # === プライベートメソッド ===
    
    def _calculate_relevance(self, item: KnowledgeItem, query: str) -> float:
        """関連度計算"""
        score = 0.0
        
        # タイトルマッチ（高重要度）
        if query in item.title.lower():
            score += 0.5
        
        # コンテンツマッチ（中重要度）
        content_matches = item.content.lower().count(query)
        score += min(content_matches * 0.1, 0.3)
        
        # タグマッチ（中重要度）
        tag_matches = sum(1 for tag in item.tags if query in tag)
        score += min(tag_matches * 0.15, 0.2)
        
        # 信頼度スコア加算
        score *= item.confidence_score
        
        return min(score, 1.0)
    
    def _calculate_recommendation_score(
        self,
        item: KnowledgeItem,
        context: str,
        expertise: str
    ) -> float:

    """推奨スコア計算""" 1.2 if item.category in [KnowledgeCategory.GENERAL, KnowledgeCategory.BEST_PRACTICE] else 0.8,
            "intermediate": 1.0,
            "advanced": 1.2 if item.category in [KnowledgeCategory.ARCHITECTURE, KnowledgeCategory.PERFORMANCE] else 0.9
        }.get(expertise, 1.0)
        
        # アクセス頻度による調整
        access_multiplier = min(1.0 + item.access_count * 0.01, 1.3)
        
        return min(base_score * expertise_multiplier * access_multiplier, 1.0)
    
    def _update_search_index(self, item: KnowledgeItem):
        """検索インデックス更新"""
        # 簡易インデックス（本番では専用の検索エンジンを使用予定）
        words = (item.title + " " + item.content).lower().split()
        for word in words:
            if len(word) > 2:  # 短い単語は除外
                if item.id not in self._search_index[word]:
                    self._search_index[word].append(item.id)
    
    def _load_all_data(self):
        pass

                    """全データロード"""
            # 知識アイテム
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = create_knowledge_item_from_dict(item_data)
                        self._knowledge_items[item.id] = item
                        self._update_search_index(item)
            
            # ベストプラクティス
            if self.practices_file.exists():
                with open(self.practices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for practice_data in data:
                        practice = BestPractice(**practice_data)
                        self._best_practices[practice.id] = practice
            
            # 学習パターン
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = LearningPattern(**pattern_data)
                        self._learning_patterns[pattern.id] = pattern
            
            self.logger.info(f"Loaded {len(self._knowledge_items)} knowledge items, "
                           f"{len(self._best_practices)} best practices, "
                           f"{len(self._learning_patterns)} learning patterns")
        
        except Exception as e:
            self.logger.warning(f"Error loading data: {e}")
    
    def _save_all_data(self):
        pass

    
    """全データ保存"""
        """知識アイテム保存"""
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [item.to_dict() for item in self._knowledge_items.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            self.logger.error(f"Error saving knowledge items: {e}")
    
    def _save_best_practices(self):
        pass

    
    """ベストプラクティス保存"""
            with open(self.practices_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [practice.to_dict() for practice in self._best_practices.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            self.logger.error(f"Error saving best practices: {e}")
    
    def _save_learning_patterns(self):
        pass

    
    """学習パターン保存"""
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [pattern.to_dict() for pattern in self._learning_patterns.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            self.logger.error(f"Error saving learning patterns: {e}")