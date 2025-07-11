#!/usr/bin/env python3
"""
Mind Reading Core v0.1
maru様の意図を理解するためのコアシステム

🧠 nWo Mind Reading Protocol Implementation
Think it, Rule it, Own it - 思考読み取り議定書
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging


class IntentType(Enum):
    """意図タイプ"""
    DEVELOPMENT = "development"        # 開発要求
    FEATURE_REQUEST = "feature_request"  # 機能要求
    BUG_FIX = "bug_fix"               # バグ修正
    OPTIMIZATION = "optimization"      # 最適化
    RESEARCH = "research"             # 調査・研究
    STRATEGY = "strategy"             # 戦略・計画
    PRAISE = "praise"                 # 評価・賞賛
    QUESTION = "question"             # 質問
    DIRECTIVE = "directive"           # 指示・命令
    VISION = "vision"                 # ビジョン・未来像


class ConfidenceLevel(Enum):
    """信頼度レベル"""
    VERY_HIGH = "very_high"    # 95%以上
    HIGH = "high"              # 80-94%
    MEDIUM = "medium"          # 60-79%
    LOW = "low"                # 40-59%
    VERY_LOW = "very_low"      # 40%未満


@dataclass
class IntentResult:
    """意図理解結果"""
    intent_type: IntentType
    confidence: float
    confidence_level: ConfidenceLevel
    extracted_keywords: List[str]
    parameters: Dict[str, Any]
    suggested_actions: List[str]
    priority: str
    urgency: str
    timestamp: str


@dataclass
class Pattern:
    """パターン情報"""
    pattern_id: str
    pattern_type: str
    frequency: int
    success_rate: float
    keywords: List[str]
    context: Dict[str, Any]
    last_seen: str


class MindReadingCore:
    """Mind Reading Core System - maru様思考理解の中核"""

    def __init__(self, data_dir: str = "data/mind_reading"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()

        # 学習データ管理
        self.patterns_file = self.data_dir / "learned_patterns.json"
        self.feedback_file = self.data_dir / "feedback_history.json"
        self.intent_history_file = self.data_dir / "intent_history.json"

        # メモリ内データ
        self.learned_patterns: List[Pattern] = []
        self.feedback_history: List[Dict] = []
        self.intent_keywords = self._load_intent_keywords()

        # 初期化
        self._load_patterns()

        self.logger.info("🧠 Mind Reading Core v0.1 initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("mind_reading_core")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Mind Reading - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_intent_keywords(self) -> Dict[IntentType, List[str]]:
        """意図別キーワード辞書"""
        return {
            IntentType.DEVELOPMENT: [
                "実装", "開発", "作成", "作って", "build", "create", "implement",
                "コード", "プログラム", "システム", "機能", "API", "ライブラリ"
            ],
            IntentType.FEATURE_REQUEST: [
                "機能", "追加", "新しい", "欲しい", "必要", "feature", "add",
                "拡張", "enhancement", "改良", "アップデート"
            ],
            IntentType.BUG_FIX: [
                "バグ", "エラー", "修正", "直して", "fix", "bug", "error",
                "問題", "issue", "不具合", "動かない"
            ],
            IntentType.OPTIMIZATION: [
                "最適化", "高速化", "改善", "optimize", "performance", "速度",
                "効率", "パフォーマンス", "軽量化", "リファクタリング"
            ],
            IntentType.RESEARCH: [
                "調査", "研究", "調べて", "分析", "research", "analyze",
                "検証", "確認", "テスト", "実験", "調べる"
            ],
            IntentType.STRATEGY: [
                "戦略", "計画", "方針", "strategy", "plan", "roadmap",
                "ビジョン", "目標", "方向性", "アーキテクチャ"
            ],
            IntentType.PRAISE: [
                "良い", "素晴らしい", "完璧", "excellent", "great", "perfect",
                "感謝", "ありがとう", "thanks", "よくできた"
            ],
            IntentType.QUESTION: [
                "？", "?", "どう", "なぜ", "何", "いつ", "どこ", "誰",
                "how", "why", "what", "when", "where", "who"
            ],
            IntentType.DIRECTIVE: [
                "やって", "実行", "開始", "始めて", "do", "execute", "start",
                "命令", "指示", "お願い", "頼む", "実施"
            ],
            IntentType.VISION: [
                "未来", "将来", "ビジョン", "目標", "夢", "理想",
                "future", "vision", "goal", "dream", "ideal"
            ]
        }

    def _load_patterns(self):
        """学習済みパターンを読み込み"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    self.learned_patterns = [
                        Pattern(**p) for p in data
                    ]
                self.logger.info(f"📚 Loaded {len(self.learned_patterns)} patterns")
            except Exception as e:
                self.logger.error(f"Pattern loading error: {e}")

    def _save_patterns(self):
        """学習済みパターンを保存"""
        try:
            with open(self.patterns_file, 'w') as f:
                json.dump([asdict(p) for p in self.learned_patterns], f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Pattern saving error: {e}")

    async def understand_intent(self, text: str) -> IntentResult:
        """
        maru様のメッセージから意図を理解

        Args:
            text: 入力テキスト（maru様のメッセージ）

        Returns:
            IntentResult: 理解した意図の詳細
        """
        self.logger.info(f"🧠 Analyzing intent: {text[:50]}...")

        # テキスト前処理
        normalized_text = self._normalize_text(text)

        # キーワード抽出
        keywords = self._extract_keywords(normalized_text)

        # 意図分類
        intent_scores = self._classify_intent(normalized_text, keywords)
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_type, confidence = best_intent

        # 信頼度レベル決定
        confidence_level = self._determine_confidence_level(confidence)

        # パラメータ抽出
        parameters = self._extract_parameters(normalized_text, intent_type)

        # アクション提案
        suggested_actions = self._suggest_actions(intent_type, parameters, keywords)

        # 優先度・緊急度判定
        priority = self._determine_priority(intent_type, keywords, parameters)
        urgency = self._determine_urgency(intent_type, keywords, parameters)

        result = IntentResult(
            intent_type=intent_type,
            confidence=confidence,
            confidence_level=confidence_level,
            extracted_keywords=keywords,
            parameters=parameters,
            suggested_actions=suggested_actions,
            priority=priority,
            urgency=urgency,
            timestamp=datetime.now().isoformat()
        )

        # 履歴保存
        await self._save_intent_history(text, result)

        self.logger.info(f"✅ Intent understood: {intent_type.value} (confidence: {confidence:.2f})")

        return result

    def _normalize_text(self, text: str) -> str:
        """テキスト正規化"""
        # 小文字化
        normalized = text.lower()

        # 特殊文字除去（句読点は残す）
        normalized = re.sub(r'[^\w\s\.\?\!、。]', ' ', normalized)

        # 複数空白を単一空白に
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出"""
        # 基本的な単語分割
        words = text.split()

        # 意味のある単語を抽出（2文字以上）
        keywords = [w for w in words if len(w) >= 2]

        # 重複除去
        keywords = list(set(keywords))

        return keywords[:10]  # 上位10個まで

    def _classify_intent(self, text: str, keywords: List[str]) -> Dict[IntentType, float]:
        """意図分類"""
        scores = {}

        for intent_type, intent_keywords in self.intent_keywords.items():
            score = 0.0

            # キーワードマッチング
            for keyword in keywords:
                for intent_keyword in intent_keywords:
                    if keyword in intent_keyword or intent_keyword in keyword:
                        score += 1.0

            # テキスト全体でのマッチング
            for intent_keyword in intent_keywords:
                if intent_keyword in text:
                    score += 0.5

            # 学習パターンによる補正
            score += self._apply_learned_patterns(text, keywords, intent_type)

            # 正規化（0-1の範囲）
            scores[intent_type] = min(1.0, score / 10.0)

        # 最低スコアの設定
        if all(score < 0.1 for score in scores.values()):
            # 不明な場合はQUESTIONとして分類
            scores[IntentType.QUESTION] = 0.3

        return scores

    def _apply_learned_patterns(self, text: str, keywords: List[str], intent_type: IntentType) -> float:
        """学習済みパターンを適用"""
        bonus = 0.0

        for pattern in self.learned_patterns:
            if pattern.pattern_type == intent_type.value:
                # パターンキーワードとのマッチング
                match_count = sum(1 for k in keywords if k in pattern.keywords)
                if match_count > 0:
                    bonus += (match_count / len(pattern.keywords)) * pattern.success_rate * 0.3

        return bonus

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """信頼度レベル決定"""
        if confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _extract_parameters(self, text: str, intent_type: IntentType) -> Dict[str, Any]:
        """パラメータ抽出"""
        parameters = {}

        # 基本パラメータ
        parameters["text_length"] = len(text)
        parameters["word_count"] = len(text.split())

        # 意図別パラメータ
        if intent_type == IntentType.DEVELOPMENT:
            # 技術スタック検出
            tech_keywords = ["python", "javascript", "react", "api", "database", "ai", "ml"]
            parameters["technologies"] = [tech for tech in tech_keywords if tech in text]

            # ファイル拡張子検出
            file_extensions = re.findall(r'\.\w{2,4}', text)
            parameters["file_types"] = file_extensions

        elif intent_type == IntentType.BUG_FIX:
            # エラーレベル検出
            if any(word in text for word in ["critical", "urgent", "重大", "緊急"]):
                parameters["severity"] = "critical"
            elif any(word in text for word in ["major", "important", "重要"]):
                parameters["severity"] = "major"
            else:
                parameters["severity"] = "minor"

        elif intent_type == IntentType.QUESTION:
            # 質問タイプ検出
            if "how" in text or "どう" in text:
                parameters["question_type"] = "how"
            elif "why" in text or "なぜ" in text:
                parameters["question_type"] = "why"
            elif "what" in text or "何" in text:
                parameters["question_type"] = "what"
            else:
                parameters["question_type"] = "general"

        return parameters

    def _suggest_actions(self, intent_type: IntentType, parameters: Dict, keywords: List[str]) -> List[str]:
        """アクション提案"""
        actions = []

        if intent_type == IntentType.DEVELOPMENT:
            actions.extend([
                "TDDでテストを先に作成",
                "要件を詳細化",
                "技術選定の検討",
                "実装計画の策定"
            ])

            if "api" in keywords:
                actions.append("API仕様書の作成")

            if parameters.get("technologies"):
                actions.append(f"技術スタック確認: {', '.join(parameters['technologies'])}")

        elif intent_type == IntentType.BUG_FIX:
            actions.extend([
                "バグの再現手順確認",
                "ログの調査",
                "テストケースの作成",
                "修正後の検証計画"
            ])

            if parameters.get("severity") == "critical":
                actions.insert(0, "緊急対応開始")

        elif intent_type == IntentType.RESEARCH:
            actions.extend([
                "情報収集の開始",
                "調査計画の策定",
                "参考資料の整理",
                "調査レポートの準備"
            ])

        elif intent_type == IntentType.OPTIMIZATION:
            actions.extend([
                "現状のパフォーマンス測定",
                "ボトルネック分析",
                "最適化計画の策定",
                "ベンチマーク実行"
            ])

        else:
            actions.extend([
                "詳細確認",
                "要件の明確化",
                "次のステップの検討"
            ])

        return actions[:5]  # 上位5個まで

    def _determine_priority(self, intent_type: IntentType, keywords: List[str], parameters: Dict) -> str:
        """優先度判定"""
        # 基本優先度
        base_priority = {
            IntentType.BUG_FIX: "high",
            IntentType.DIRECTIVE: "high",
            IntentType.DEVELOPMENT: "medium",
            IntentType.FEATURE_REQUEST: "medium",
            IntentType.OPTIMIZATION: "medium",
            IntentType.RESEARCH: "low",
            IntentType.QUESTION: "low",
            IntentType.STRATEGY: "medium",
            IntentType.PRAISE: "low",
            IntentType.VISION: "low"
        }.get(intent_type, "medium")

        # キーワードによる補正
        if any(word in keywords for word in ["緊急", "urgent", "critical", "重要", "important"]):
            if base_priority == "low":
                return "medium"
            elif base_priority == "medium":
                return "high"
            else:
                return "critical"

        # パラメータによる補正
        if intent_type == IntentType.BUG_FIX and parameters.get("severity") == "critical":
            return "critical"

        return base_priority

    def _determine_urgency(self, intent_type: IntentType, keywords: List[str], parameters: Dict) -> str:
        """緊急度判定"""
        # 緊急キーワード
        urgent_keywords = ["今すぐ", "急いで", "immediately", "asap", "緊急", "urgent"]

        if any(word in keywords for word in urgent_keywords):
            return "urgent"

        # 意図別デフォルト緊急度
        if intent_type in [IntentType.BUG_FIX, IntentType.DIRECTIVE]:
            return "high"
        elif intent_type in [IntentType.DEVELOPMENT, IntentType.FEATURE_REQUEST]:
            return "medium"
        else:
            return "low"

    async def learn_from_feedback(self, intent: IntentResult, result: Dict, feedback: Dict):
        """
        フィードバックから学習

        Args:
            intent: 予測した意図
            result: 実際の実行結果
            feedback: maru様からのフィードバック
        """
        self.logger.info("📚 Learning from feedback...")

        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "intent": asdict(intent),
            "result": result,
            "feedback": feedback,
            "success": feedback.get("success", False)
        }

        # フィードバック履歴に追加
        self.feedback_history.append(feedback_entry)

        # パターン更新
        if feedback.get("success", False):
            self._update_successful_pattern(intent)
        else:
            self._update_failed_pattern(intent, feedback)

        # データ保存
        await self._save_feedback_history()
        self._save_patterns()

        self.logger.info("✅ Learning completed")

    def _update_successful_pattern(self, intent: IntentResult):
        """成功パターンの更新"""
        pattern_id = f"{intent.intent_type.value}_{hash(''.join(intent.extracted_keywords)) % 10000}"

        # 既存パターンを探す
        existing_pattern = None
        for pattern in self.learned_patterns:
            if pattern.pattern_id == pattern_id:
                existing_pattern = pattern
                break

        if existing_pattern:
            # 既存パターンを更新
            existing_pattern.frequency += 1
            existing_pattern.success_rate = min(1.0, existing_pattern.success_rate + 0.1)
            existing_pattern.last_seen = datetime.now().isoformat()
        else:
            # 新しいパターンを作成
            new_pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type=intent.intent_type.value,
                frequency=1,
                success_rate=0.8,
                keywords=intent.extracted_keywords,
                context={
                    "priority": intent.priority,
                    "urgency": intent.urgency,
                    "confidence": intent.confidence
                },
                last_seen=datetime.now().isoformat()
            )
            self.learned_patterns.append(new_pattern)

    def _update_failed_pattern(self, intent: IntentResult, feedback: Dict):
        """失敗パターンの更新"""
        pattern_id = f"{intent.intent_type.value}_{hash(''.join(intent.extracted_keywords)) % 10000}"

        # 既存パターンを探す
        for pattern in self.learned_patterns:
            if pattern.pattern_id == pattern_id:
                # 成功率を下げる
                pattern.success_rate = max(0.1, pattern.success_rate - 0.2)
                pattern.last_seen = datetime.now().isoformat()
                break

    async def _save_feedback_history(self):
        """フィードバック履歴保存"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Feedback history saving error: {e}")

    async def _save_intent_history(self, text: str, result: IntentResult):
        """意図履歴保存"""
        try:
            history_entry = {
                "timestamp": result.timestamp,
                "input_text": text,
                "result": asdict(result)
            }

            # 既存履歴を読み込み
            history = []
            if self.intent_history_file.exists():
                with open(self.intent_history_file, 'r') as f:
                    history = json.load(f)

            # 新しいエントリを追加
            history.append(history_entry)

            # 最大1000件まで保持
            if len(history) > 1000:
                history = history[-1000:]

            # 保存
            with open(self.intent_history_file, 'w') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Intent history saving error: {e}")

    def get_confidence_score(self, text: str) -> float:
        """
        テキストに対する理解信頼度を取得

        Args:
            text: 入力テキスト

        Returns:
            float: 信頼度スコア (0.0-1.0)
        """
        # 簡易的な信頼度計算
        normalized_text = self._normalize_text(text)
        keywords = self._extract_keywords(normalized_text)
        intent_scores = self._classify_intent(normalized_text, keywords)

        return max(intent_scores.values()) if intent_scores else 0.0

    def analyze_patterns(self) -> List[Pattern]:
        """
        学習済みパターンの分析

        Returns:
            List[Pattern]: パターン分析結果
        """
        # 成功率でソート
        sorted_patterns = sorted(
            self.learned_patterns,
            key=lambda p: p.success_rate * p.frequency,
            reverse=True
        )

        self.logger.info(f"📊 Analyzed {len(sorted_patterns)} patterns")

        return sorted_patterns

    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "total_patterns": len(self.learned_patterns),
            "feedback_count": len(self.feedback_history),
            "avg_confidence": sum(p.success_rate for p in self.learned_patterns) / len(self.learned_patterns) if self.learned_patterns else 0,
            "intent_distribution": self._get_intent_distribution(),
            "last_updated": datetime.now().isoformat()
        }

    def _get_intent_distribution(self) -> Dict[str, int]:
        """意図分布取得"""
        distribution = {}
        for pattern in self.learned_patterns:
            pattern_type = pattern.pattern_type
            distribution[pattern_type] = distribution.get(pattern_type, 0) + pattern.frequency

        return distribution


# 使用例とテスト用関数
async def demo_mind_reading():
    """Mind Reading Coreのデモ"""
    print("🧠 Mind Reading Core v0.1 Demo")
    print("=" * 50)

    mind_reader = MindReadingCore()

    # テストケース
    test_cases = [
        "Elder Flow Turbo Modeを実装してください",
        "バグを修正して",
        "これはどういう意味ですか？",
        "素晴らしい実装ですね！",
        "今すぐ緊急でAPIを修正してください",
        "未来のビジョンを教えて"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Input: {text}")

        result = await mind_reader.understand_intent(text)

        print(f"Intent: {result.intent_type.value}")
        print(f"Confidence: {result.confidence:.2f} ({result.confidence_level.value})")
        print(f"Keywords: {', '.join(result.extracted_keywords)}")
        print(f"Priority: {result.priority}, Urgency: {result.urgency}")
        print(f"Actions: {', '.join(result.suggested_actions[:3])}")

    # 統計表示
    print("\n📊 Statistics:")
    stats = mind_reader.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo_mind_reading())
