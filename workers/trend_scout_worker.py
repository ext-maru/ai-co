#!/usr/bin/env python3
"""
Trend Scout Worker v1.0
技術トレンド自動収集ワーカー

🔮 nWo Prophetic Development Matrix - Trend Scouting System
Think it, Rule it, Own it - 未来予測開発システム
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import re


class TrendSource(Enum):
    """トレンドソース"""
    GITHUB = "github"
    HACKERNEWS = "hackernews"
    REDDIT = "reddit"
    STACKOVERFLOW = "stackoverflow"
    DEVTO = "devto"
    PRODUCTHUNT = "producthunt"


class TrendType(Enum):
    """トレンドタイプ"""
    TECHNOLOGY = "technology"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    TOOL = "tool"
    LANGUAGE = "language"
    CONCEPT = "concept"
    NEWS = "news"


@dataclass
class Trend:
    """トレンド情報"""
    title: str
    description: str
    url: str
    source: TrendSource
    trend_type: TrendType
    score: float
    tags: List[str]
    github_stars: Optional[int] = None
    discussions: Optional[int] = None
    created_at: str = ""
    discovered_at: str = ""


@dataclass
class TrendAnalysis:
    """トレンド分析結果"""
    period: str
    total_trends: int
    top_technologies: List[str]
    emerging_frameworks: List[str]
    hot_topics: List[str]
    growth_rate: Dict[str, float]
    predictions: List[str]
    analysis_time: str


class TrendScoutWorker:
    """Trend Scout Worker - 技術トレンド自動収集システム"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.logger = self._setup_logger()
        
        # データストレージ
        self.trends_db = Path("data/trends.json")
        self.trends_db.parent.mkdir(parents=True, exist_ok=True)
        
        # 収集したトレンド
        self.discovered_trends: List[Trend] = []
        self.trend_history: List[TrendAnalysis] = []
        
        # API設定（実際のAPIキーは環境変数から）
        self.api_keys = {
            "github_token": None,  # GitHub API Token
            "reddit_client_id": None,  # Reddit API
        }
        
        # キーワード辞書
        self.tech_keywords = self._load_tech_keywords()
        
        self.logger.info("🔮 Trend Scout Worker v1.0 initialized")
    
    def _default_config(self) -> Dict:
        """デフォルト設定"""
        return {
            "scan_interval": 3600,  # 1時間
            "max_trends_per_source": 50,
            "min_score_threshold": 0.3,
            "enabled_sources": [
                TrendSource.GITHUB,
                TrendSource.HACKERNEWS,
                TrendSource.REDDIT
            ],
            "keywords": [
                "python", "javascript", "react", "vue", "angular",
                "ai", "ml", "machine learning", "deep learning",
                "blockchain", "web3", "cloud", "kubernetes",
                "microservices", "serverless", "devops"
            ]
        }
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("trend_scout_worker")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Trend Scout - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_tech_keywords(self) -> Dict[str, List[str]]:
        """技術キーワード辞書"""
        return {
            "frameworks": [
                "react", "vue", "angular", "svelte", "nextjs", "nuxt",
                "express", "fastapi", "django", "flask", "spring",
                "laravel", "rails", "nestjs"
            ],
            "languages": [
                "python", "javascript", "typescript", "rust", "go",
                "java", "csharp", "kotlin", "swift", "dart"
            ],
            "ai_ml": [
                "tensorflow", "pytorch", "scikit-learn", "keras",
                "huggingface", "openai", "llm", "gpt", "bert",
                "transformer", "neural network"
            ],
            "cloud": [
                "aws", "gcp", "azure", "kubernetes", "docker",
                "terraform", "serverless", "microservices"
            ],
            "tools": [
                "vscode", "github", "gitlab", "jenkins", "docker",
                "webpack", "vite", "eslint", "prettier"
            ]
        }
    
    async def scout_github_trends(self) -> List[Trend]:
        """GitHub トレンド収集"""
        self.logger.info("🔍 Scouting GitHub trends...")
        trends = []
        
        try:
            # GitHub Trending API（簡易版）
            base_url = "https://api.github.com/search/repositories"
            
            # 人気のクエリ
            queries = [
                "created:>2024-01-01 stars:>100",
                "language:python pushed:>2024-07-01",
                "topic:ai stars:>50",
                "topic:web3 created:>2024-06-01"
            ]
            
            async with aiohttp.ClientSession() as session:
                for query in queries:
                    params = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 20
                    }
                    
                    headers = {}
                    if self.api_keys.get("github_token"):
                        headers["Authorization"] = f"token {self.api_keys['github_token']}"
                    
                    try:
                        async with session.get(base_url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                for repo in data.get("items", []):
                                    trend = self._parse_github_repo(repo)
                                    if trend:
                                        trends.append(trend)
                            else:
                                self.logger.warning(f"GitHub API error: {response.status}")
                    
                    except Exception as e:
                        self.logger.error(f"GitHub query error: {e}")
                    
                    # レート制限対策
                    await asyncio.sleep(1)
        
        except Exception as e:
            self.logger.error(f"GitHub trends error: {e}")
        
        self.logger.info(f"📊 Found {len(trends)} GitHub trends")
        return trends[:self.config["max_trends_per_source"]]
    
    def _parse_github_repo(self, repo: Dict) -> Optional[Trend]:
        """GitHubリポジトリをトレンドに変換"""
        try:
            # キーワードマッチング
            repo_text = f"{repo['name']} {repo['description'] or ''} {' '.join(repo.get('topics', []))}"
            
            # トレンドタイプ判定
            trend_type = self._classify_trend_type(repo_text)
            
            # スコア計算
            score = self._calculate_github_score(repo)
            
            if score < self.config["min_score_threshold"]:
                return None
            
            # タグ抽出
            tags = repo.get("topics", [])
            tags.extend(self._extract_tech_tags(repo_text))
            
            return Trend(
                title=repo["name"],
                description=repo["description"] or "No description",
                url=repo["html_url"],
                source=TrendSource.GITHUB,
                trend_type=trend_type,
                score=score,
                tags=list(set(tags)),
                github_stars=repo["stargazers_count"],
                created_at=repo["created_at"],
                discovered_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            self.logger.error(f"GitHub repo parsing error: {e}")
            return None
    
    def _calculate_github_score(self, repo: Dict) -> float:
        """GitHubリポジトリのスコア計算"""
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        
        # 作成日からの経過時間
        created_at = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        days_old = (datetime.now(created_at.tzinfo) - created_at).days
        
        # 最近の更新
        updated_at = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
        days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
        
        # スコア計算
        score = 0.0
        
        # スター数（対数スケール）
        if stars > 0:
            score += min(1.0, (stars / 1000) ** 0.5)
        
        # 活発度
        if days_since_update < 30:
            score += 0.3
        elif days_since_update < 90:
            score += 0.1
        
        # 新しさ
        if days_old < 90:
            score += 0.2
        elif days_old < 365:
            score += 0.1
        
        # フォーク数
        if forks > 10:
            score += 0.1
        
        return min(1.0, score)
    
    async def analyze_hackernews(self) -> TrendAnalysis:
        """Hacker News 分析"""
        self.logger.info("📰 Analyzing Hacker News...")
        
        trends = []
        hot_topics = []
        
        try:
            # Hacker News API
            async with aiohttp.ClientSession() as session:
                # トップストーリー取得
                async with session.get("https://hacker-news.firebaseio.com/v0/topstories.json") as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        
                        # 上位50件を分析
                        for story_id in story_ids[:50]:
                            try:
                                async with session.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json") as story_response:
                                    if story_response.status == 200:
                                        story = await story_response.json()
                                        
                                        if story and story.get("title"):
                                            # 技術関連ストーリーを抽出
                                            if self._is_tech_related(story["title"]):
                                                trend = self._parse_hn_story(story)
                                                if trend:
                                                    trends.append(trend)
                                                    hot_topics.append(story["title"])
                                
                                # レート制限
                                await asyncio.sleep(0.1)
                            
                            except Exception as e:
                                self.logger.error(f"HN story error: {e}")
        
        except Exception as e:
            self.logger.error(f"Hacker News analysis error: {e}")
        
        return TrendAnalysis(
            period="daily",
            total_trends=len(trends),
            top_technologies=self._extract_top_technologies(trends),
            emerging_frameworks=[],
            hot_topics=hot_topics[:10],
            growth_rate={},
            predictions=[],
            analysis_time=datetime.now().isoformat()
        )
    
    def _parse_hn_story(self, story: Dict) -> Optional[Trend]:
        """HN ストーリーをトレンドに変換"""
        try:
            title = story["title"]
            
            # スコア計算
            score = story.get("score", 0) / 500.0  # 正規化
            score = min(1.0, score)
            
            if score < self.config["min_score_threshold"]:
                return None
            
            # トレンドタイプ判定
            trend_type = self._classify_trend_type(title)
            
            # タグ抽出
            tags = self._extract_tech_tags(title)
            
            return Trend(
                title=title,
                description=story.get("text", "")[:200],
                url=story.get("url", f"https://news.ycombinator.com/item?id={story['id']}"),
                source=TrendSource.HACKERNEWS,
                trend_type=trend_type,
                score=score,
                tags=tags,
                discussions=story.get("descendants", 0),
                discovered_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            self.logger.error(f"HN story parsing error: {e}")
            return None
    
    async def scan_reddit_programming(self) -> List[Trend]:
        """Reddit プログラミング関連スキャン"""
        self.logger.info("🔍 Scanning Reddit programming...")
        trends = []
        
        try:
            # Reddit API（JSON endpoints）
            subreddits = ["programming", "webdev", "MachineLearning", "artificial"]
            
            async with aiohttp.ClientSession() as session:
                for subreddit in subreddits:
                    try:
                        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
                        headers = {"User-Agent": "TrendScout/1.0"}
                        
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                for post in data["data"]["children"]:
                                    post_data = post["data"]
                                    
                                    if self._is_tech_related(post_data["title"]):
                                        trend = self._parse_reddit_post(post_data)
                                        if trend:
                                            trends.append(trend)
                        
                        # レート制限
                        await asyncio.sleep(2)
                    
                    except Exception as e:
                        self.logger.error(f"Reddit {subreddit} error: {e}")
        
        except Exception as e:
            self.logger.error(f"Reddit scan error: {e}")
        
        self.logger.info(f"📊 Found {len(trends)} Reddit trends")
        return trends[:self.config["max_trends_per_source"]]
    
    def _parse_reddit_post(self, post: Dict) -> Optional[Trend]:
        """Reddit 投稿をトレンドに変換"""
        try:
            title = post["title"]
            
            # スコア計算
            score = min(1.0, post.get("score", 0) / 1000.0)
            
            if score < self.config["min_score_threshold"]:
                return None
            
            # トレンドタイプ判定
            trend_type = self._classify_trend_type(title)
            
            # タグ抽出
            tags = self._extract_tech_tags(title)
            tags.append(post["subreddit"])
            
            return Trend(
                title=title,
                description=post.get("selftext", "")[:200],
                url=f"https://reddit.com{post['permalink']}",
                source=TrendSource.REDDIT,
                trend_type=trend_type,
                score=score,
                tags=tags,
                discussions=post.get("num_comments", 0),
                discovered_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            self.logger.error(f"Reddit post parsing error: {e}")
            return None
    
    def _classify_trend_type(self, text: str) -> TrendType:
        """テキストからトレンドタイプを分類"""
        text_lower = text.lower()
        
        # フレームワーク
        framework_keywords = ["framework", "library", "react", "vue", "angular", "django", "flask"]
        if any(keyword in text_lower for keyword in framework_keywords):
            return TrendType.FRAMEWORK
        
        # プログラミング言語
        language_keywords = ["python", "javascript", "rust", "go", "java", "language"]
        if any(keyword in text_lower for keyword in language_keywords):
            return TrendType.LANGUAGE
        
        # ツール
        tool_keywords = ["tool", "cli", "editor", "ide", "deploy"]
        if any(keyword in text_lower for keyword in tool_keywords):
            return TrendType.TOOL
        
        # AI/ML
        ai_keywords = ["ai", "ml", "machine learning", "neural", "model"]
        if any(keyword in text_lower for keyword in ai_keywords):
            return TrendType.TECHNOLOGY
        
        # デフォルト
        return TrendType.CONCEPT
    
    def _extract_tech_tags(self, text: str) -> List[str]:
        """テキストから技術タグを抽出"""
        tags = []
        text_lower = text.lower()
        
        for category, keywords in self.tech_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(keyword)
        
        return list(set(tags))
    
    def _is_tech_related(self, text: str) -> bool:
        """技術関連テキストかどうか判定"""
        tech_indicators = [
            "programming", "code", "software", "development", "framework",
            "library", "api", "algorithm", "data", "web", "mobile",
            "ai", "ml", "blockchain", "cloud", "devops"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in tech_indicators)
    
    def _extract_top_technologies(self, trends: List[Trend]) -> List[str]:
        """トレンドから主要技術を抽出"""
        tech_count = {}
        
        for trend in trends:
            for tag in trend.tags:
                tech_count[tag] = tech_count.get(tag, 0) + trend.score
        
        # スコア順にソート
        sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
        
        return [tech for tech, _ in sorted_tech[:10]]
    
    async def generate_trend_report(self) -> Dict[str, Any]:
        """トレンドレポート生成"""
        self.logger.info("📊 Generating trend report...")
        
        # 全ソーススキャン
        all_trends = []
        
        if TrendSource.GITHUB in self.config["enabled_sources"]:
            github_trends = await self.scout_github_trends()
            all_trends.extend(github_trends)
        
        if TrendSource.REDDIT in self.config["enabled_sources"]:
            reddit_trends = await self.scan_reddit_programming()
            all_trends.extend(reddit_trends)
        
        if TrendSource.HACKERNEWS in self.config["enabled_sources"]:
            hn_analysis = await self.analyze_hackernews()
        
        # トレンド分析
        top_trends = sorted(all_trends, key=lambda t: t.score, reverse=True)[:20]
        
        # 技術分布
        tech_distribution = {}
        for trend in all_trends:
            for tag in trend.tags:
                tech_distribution[tag] = tech_distribution.get(tag, 0) + 1
        
        # レポート作成
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_trends": len(all_trends),
            "sources_scanned": len(self.config["enabled_sources"]),
            "top_trends": [asdict(trend) for trend in top_trends],
            "technology_distribution": dict(sorted(tech_distribution.items(), 
                                                 key=lambda x: x[1], reverse=True)[:15]),
            "emerging_technologies": self._identify_emerging_tech(all_trends),
            "predictions": self._generate_predictions(all_trends),
            "summary": self._generate_summary(all_trends)
        }
        
        # レポート保存
        report_path = Path(f"data/trend_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 Trend report saved: {report_path}")
        
        return report
    
    def _identify_emerging_tech(self, trends: List[Trend]) -> List[str]:
        """新興技術の特定"""
        # 最近のトレンドから新しいキーワードを抽出
        recent_trends = [t for t in trends if t.discovered_at and 
                        datetime.fromisoformat(t.discovered_at) > datetime.now() - timedelta(days=7)]
        
        emerging = {}
        for trend in recent_trends:
            for tag in trend.tags:
                if tag not in self.tech_keywords.get("frameworks", []):
                    emerging[tag] = emerging.get(tag, 0) + trend.score
        
        return sorted(emerging.keys(), key=lambda k: emerging[k], reverse=True)[:5]
    
    def _generate_predictions(self, trends: List[Trend]) -> List[str]:
        """予測生成"""
        predictions = [
            "AI/ML integration will continue accelerating in web frameworks",
            "Rust adoption in systems programming will grow significantly",
            "WebAssembly will become mainstream for performance-critical web apps",
            "Edge computing frameworks will see major development",
            "Developer experience tools will focus on AI-assistance"
        ]
        
        return predictions[:3]
    
    def _generate_summary(self, trends: List[Trend]) -> str:
        """サマリー生成"""
        total = len(trends)
        avg_score = sum(t.score for t in trends) / total if total > 0 else 0
        top_source = max(self.config["enabled_sources"], 
                        key=lambda s: len([t for t in trends if t.source == s]))
        
        return f"Analyzed {total} trends with average score {avg_score:.2f}. " \
               f"Primary source: {top_source.value}. " \
               f"Key focus areas: AI/ML, web frameworks, and developer tools."


# 使用例とテスト用関数
async def demo_trend_scout():
    """Trend Scout Worker のデモ"""
    print("🔮 Trend Scout Worker v1.0 Demo")
    print("=" * 50)
    
    scout = TrendScoutWorker()
    
    # GitHub トレンドスキャン
    print("\n📊 Scanning GitHub trends...")
    github_trends = await scout.scout_github_trends()
    
    print(f"Found {len(github_trends)} GitHub trends:")
    for trend in github_trends[:3]:
        print(f"  ⭐ {trend.title} ({trend.github_stars} stars)")
        print(f"     {trend.description[:80]}...")
        print(f"     Tags: {', '.join(trend.tags[:3])}")
    
    # Reddit スキャン
    print("\n📱 Scanning Reddit...")
    reddit_trends = await scout.scan_reddit_programming()
    
    print(f"Found {len(reddit_trends)} Reddit trends:")
    for trend in reddit_trends[:2]:
        print(f"  💬 {trend.title}")
        print(f"     Score: {trend.score:.2f}, Comments: {trend.discussions}")
    
    # 完全レポート生成
    print("\n📄 Generating comprehensive report...")
    report = await scout.generate_trend_report()
    
    print(f"📊 Report Summary:")
    print(f"   Total Trends: {report['total_trends']}")
    print(f"   Sources: {report['sources_scanned']}")
    print(f"   Top Technologies: {', '.join(list(report['technology_distribution'].keys())[:5])}")
    print(f"   Emerging: {', '.join(report['emerging_technologies'][:3])}")


if __name__ == "__main__":
    asyncio.run(demo_trend_scout())