#!/usr/bin/env python3
"""
Elders Guild 自己進化ファイル配置マネージャー
AIが生成したファイルを適切な場所に自動配置して自己改良を実現
Enhanced with ML-based intelligent placement
"""

import hashlib
import json
import logging
import math
import os
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SelfEvolutionManager:
    def __init__(self):
        # プロジェクトルートを相対パスで特定
        self.project_root = Path(__file__).parent.parent

        # 学習データベース初期化
        self.learning_db_path = self.project_root / "db" / "placement_learning.db"
        self._init_learning_db()

        # 配置先マッピング（相対パス）
        self.placement_rules = {
            # Pythonスクリプト系
            r".*_worker\.py$": "workers/",
            r".*_manager\.py$": "libs/",
            r".*_notifier\.py$": "libs/",
            r".*_db\.py$": "libs/",
            r"send_.*\.py$": "scripts/",
            r"setup_.*\.py$": "scripts/",
            r"test_.*\.py$": "tests/",
            # 設定ファイル系
            r".*\.conf$": "config/",
            r"config\..*": "config/",
            r".*\.env$": "config/",
            # シェルスクリプト系
            r".*\.sh$": "scripts/",
            r"start_.*\.sh$": "scripts/",
            r"setup_.*\.sh$": "scripts/",
            # Web系
            r".*\.html$": "web/",
            r".*\.css$": "web/css/",
            r".*\.js$": "web/js/",
            # ドキュメント系
            r".*\.md$": "docs/",
            r"README.*": "docs/",
            # データ系
            r".*\.json$": "data/",
            r".*\.csv$": "data/",
            r".*\.sql$": "data/",
            # 新機能プロトタイプ
            r"prototype_.*\.py$": "prototypes/",
            r"experimental_.*\.py$": "experimental/",
        }

        # 特殊な配置ルール（内容解析ベース）
        self.content_based_rules = {
            "import pika": "workers/",
            "import flask": "web/",
            "import fastapi": "api/",
            "class.*Worker": "workers/",
            "class.*Manager": "libs/",
            "class.*Notifier": "libs/",
            "def send_task": "scripts/",
            "#!/bin/bash": "scripts/",
        }

        # 機械学習ベース配置ルール設定
        self.ml_features = {
            "import_statements": [],
            "class_patterns": [],
            "function_patterns": [],
            "file_size_ranges": [],
            "content_similarity": [],
        }

        # Enhanced ML components
        self.content_clusters = {}
        self.directory_embeddings = {}
        self.reinforcement_scores = defaultdict(lambda: defaultdict(float))
        self.placement_success_rates = defaultdict(float)

        # New ML enhancements
        self.neural_weights = self._initialize_neural_weights()
        self.feature_importance = defaultdict(float)
        self.adaptive_thresholds = {
            "similarity_threshold": 0.3,
            "confidence_threshold": 0.5,
            "ensemble_threshold": 0.6,
        }
        self.placement_feedback = defaultdict(list)  # For reinforcement learning
        self.concept_drift_detector = {"window_size": 100, "drift_threshold": 0.15}

        # Initialize advanced models
        self._initialize_advanced_ml_components()

        # 配置履歴による学習
        self.placement_history = defaultdict(list)
        self._load_placement_history()

    def analyze_file_type(self, file_path, content=""):
        """
        ファイルタイプ・内容を解析して最適な配置先を決定

        Args:
            file_path: ファイルパス
            content: ファイル内容

        Returns:
            str: 配置先相対パス
        """
        file_name = Path(file_path).name

        # 1. ファイル名パターンマッチング
        for pattern, target_dir in self.placement_rules.items():
            if re.match(pattern, file_name, re.IGNORECASE):
                logger.info(f"ファイル名マッチ: {file_name} → {target_dir}")
                return target_dir

        # 2. 内容ベース解析
        if content:
            for keyword, target_dir in self.content_based_rules.items():
                if re.search(keyword, content, re.IGNORECASE | re.MULTILINE):
                    logger.info(f"内容マッチ: {keyword} → {target_dir}")
                    return target_dir

        # 3. 拡張子ベースフォールバック
        suffix = Path(file_path).suffix.lower()
        if suffix == ".py":
            return "libs/"  # Pythonファイルデフォルト
        elif suffix == ".sh":
            return "scripts/"  # シェルスクリプトデフォルト
        elif suffix in [".txt", ".log"]:
            return "output/"  # ログ・テキストファイル

        # 4. 最終フォールバック
        logger.warning(f"配置先不明: {file_name} → output/misc/")
        return "output/misc/"

    def auto_place_file(self, source_content, suggested_filename=None, task_id=None):
        """
        Next-generation intelligent file placement with advanced ML-based analysis

        New Features:
        - Deep learning-inspired multi-layer analysis
        - Adaptive confidence thresholds
        - Real-time learning from placement outcomes
        - Cross-file relationship analysis
        - Semantic code understanding

        Args:
            source_content: ファイル内容
            suggested_filename: 推奨ファイル名
            task_id: タスクID

        Returns:
            dict: 配置結果
        """
        try:
            # Phase 1: Enhanced filename determination with semantic analysis
            if suggested_filename:
                filename = suggested_filename
            else:
                filename = self._guess_filename_from_content_enhanced(source_content)

            # Phase 2: Multi-layer candidate analysis
            placement_candidates = self._analyze_placement_candidates_enhanced(
                filename, source_content
            )

            # Phase 3: Deep learning-inspired selection with adaptive thresholds
            target_relative_dir = self._select_optimal_placement_enhanced(
                placement_candidates, source_content, filename, task_id
            )

            # Phase 4: Cross-file relationship validation
            target_relative_dir = self._validate_placement_with_relationships(
                target_relative_dir, filename, source_content
            )

            target_dir = self.project_root / target_relative_dir
            target_file = target_dir / filename

            # Directory creation with intelligent permissions
            self._ensure_directory_enhanced(target_dir, target_relative_dir)

            # Smart backup strategy based on file importance
            backup_info = None
            if target_file.exists():
                backup_info = self._create_smart_backup(target_file, source_content)
                logger.info(
                    f"スマートバックアップ: {backup_info['path']} (importance: {backup_info['importance']})"
                )

            # Write file with metadata preservation
            self._write_file_with_metadata(target_file, source_content, task_id)

            # Intelligent permission setting
            self._set_intelligent_permissions(target_file, filename, source_content)

            # Enhanced learning with real-time feedback
            confidence = self._record_enhanced_placement_learning(
                filename,
                source_content,
                target_relative_dir,
                placement_candidates,
                task_id,
            )

            # Generate comprehensive result with analytics
            result = self._generate_placement_result(
                target_file,
                target_relative_dir,
                filename,
                source_content,
                task_id,
                placement_candidates,
                confidence,
                backup_info,
            )

            # Post-placement analysis and learning
            self._post_placement_analysis(result)

            logger.info(
                f"次世代自己進化配置成功: {result['relative_path']} (confidence: {confidence:.3f})"
            )
            return result

        except Exception as e:
            error_msg = f"自己配置エラー: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
            }

    def _guess_filename_from_content(self, content):
        """内容からファイル名を推測"""
        lines = content.split("\n")

        # クラス名から推測
        for line in lines:
            if "class " in line:
                match = re.search(r"class\s+(\w+)", line)
                if match:
                    class_name = match.group(1)
                    # CamelCase → snake_case 変換
                    snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
                    return f"{snake_name}.py"

        # 関数名から推測
        for line in lines:
            if line.startswith("def ") and not line.startswith("def __"):
                match = re.search(r"def\s+(\w+)", line)
                if match:
                    func_name = match.group(1)
                    return f"{func_name}.py"

        # シェルスクリプト判定
        if content.startswith("#!/bin/bash"):
            return f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"

        # デフォルト
        return f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    def _ensure_directory(self, dir_path):
        """ディレクトリ確保"""
        dir_path.mkdir(parents=True, exist_ok=True)
        os.chmod(dir_path, 0o775)

    def _create_backup(self, file_path):
        """既存ファイルのバックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup_{timestamp}")
        shutil.copy2(file_path, backup_path)
        return backup_path

    def get_placement_preview(self, content, filename=None):
        """配置先プレビュー（実際の配置はしない）"""
        if filename is None:
            filename = self._guess_filename_from_content(content)

        target_dir = self.analyze_file_type(filename, content)
        target_path = self.project_root / target_dir / filename

        return {
            "filename": filename,
            "target_dir": target_dir,
            "full_path": str(target_path),
            "relative_path": str(target_path.relative_to(self.project_root)),
            "would_backup": target_path.exists(),
        }

    def list_evolution_candidates(self):
        """自己進化候補ファイルリスト"""
        output_dir = self.project_root / "output"
        candidates = []

        for file_path in output_dir.rglob("*.py"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            preview = self.get_placement_preview(content, file_path.name)
            candidates.append(
                {
                    "current_path": str(file_path),
                    "suggested_placement": preview,
                    "size": file_path.stat().st_size,
                }
            )

        return candidates

    # ML-Based Enhancement Methods

    def _init_learning_db(self):
        """学習データベース初期化"""
        try:
            self.learning_db_path.parent.mkdir(exist_ok=True)
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS placement_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    content_hash TEXT,
                    content_features TEXT,
                    target_dir TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_similarities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT,
                    similar_files TEXT,
                    similarity_scores TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("Learning database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize learning database: {e}")

    def _load_placement_history(self):
        """配置履歴をロード"""
        try:
            if not self.learning_db_path.exists():
                return

            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT target_dir, content_features, confidence
                FROM placement_history
                ORDER BY created_at DESC LIMIT 1000
            """
            )

            for row in cursor.fetchall():
                target_dir, features_json, confidence = row
                try:
                    features = json.loads(features_json)
                    self.placement_history[target_dir].append(
                        {"features": features, "confidence": confidence}
                    )
                except json.JSONDecodeError:
                    continue

            conn.close()
            logger.info(f"Loaded {len(self.placement_history)} placement patterns")
        except Exception as e:
            logger.error(f"Failed to load placement history: {e}")

    def _analyze_placement_candidates(self, filename: str, content: str) -> List[Dict]:
        """複数の手法で配置候補を分析 - Enhanced with advanced ML algorithms"""
        candidates = []

        # 1. 従来のルールベース (重み調整)
        rule_based_dir = self.analyze_file_type(filename, content)
        rule_confidence = self._calculate_rule_confidence(
            filename, content, rule_based_dir
        )
        candidates.append(
            {
                "dir": rule_based_dir,
                "score": 0.6 + (rule_confidence * 0.3),
                "method": "rule_based",
                "reason": f"Pattern matching (confidence: {rule_confidence:.2f})",
            }
        )

        # 2. 内容類似度ベース (改良版)
        similarity_candidates = self._analyze_content_similarity_enhanced(content)
        candidates.extend(similarity_candidates)

        # 3. 機械学習予測 (強化版)
        ml_candidates = self._ml_predict_placement_enhanced(filename, content)
        candidates.extend(ml_candidates)

        # 4. 統計的パターン分析 (改良版)
        pattern_candidates = self._analyze_statistical_patterns_enhanced(
            filename, content
        )
        candidates.extend(pattern_candidates)

        # 5. 依存関係分析
        dependency_candidates = self._analyze_dependency_patterns(content)
        candidates.extend(dependency_candidates)

        # 6. 意味的類似度分析
        semantic_candidates = self._analyze_semantic_similarity(filename, content)
        candidates.extend(semantic_candidates)

        # 7. NEW: Advanced embedding-based similarity
        embedding_candidates = self._advanced_embedding_similarity(content, filename)
        candidates.extend(embedding_candidates)

        # 8. NEW: Contextual pattern analysis
        contextual_candidates = self._contextual_pattern_analysis(filename, content)
        candidates.extend(contextual_candidates)

        # Apply enhanced ML ensemble with meta-learning
        candidates = self._enhanced_ensemble_with_meta_learning(candidates)

        # If no clear winner, fallback to probabilistic ensemble
        if (
            not candidates
            or candidates[0]["score"] < self.adaptive_thresholds["ensemble_threshold"]
        ):
            candidates = self._probabilistic_ensemble(
                [c for c in candidates if c["method"] != "meta_learning_ensemble"]
            )

            # Final fallback to traditional ensemble
            if not candidates or candidates[0]["score"] < 0.5:
                fallback_candidates = self._ensemble_scoring(
                    [c for c in candidates if "ensemble" not in c["method"]]
                )
                if fallback_candidates:
                    candidates = fallback_candidates

        # 重複削除とランキング
        seen_dirs = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate["dir"] not in seen_dirs:
                unique_candidates.append(candidate)
                seen_dirs.add(candidate["dir"])

        return unique_candidates[:5]

    def _analyze_content_similarity(self, content: str) -> List[Dict]:
        """既存ファイルとの内容類似度分析"""
        candidates = []
        content_features = self._extract_content_features(content)

        # 既存ファイルとの類似度計算
        similar_placements = self._find_similar_files(content_features)

        for placement, similarity in similar_placements:
            candidates.append(
                {
                    "dir": placement,
                    "score": 0.5 + (similarity * 0.4),
                    "method": "content_similarity",
                    "reason": f"Similar to existing files (similarity: {similarity:.2f})",
                }
            )

        return candidates

    def _ml_predict_placement(self, filename: str, content: str) -> List[Dict]:
        """機械学習による配置予測"""
        candidates = []

        # 簡易特徴量抽出
        features = self._extract_ml_features(filename, content)

        # 履歴ベースの予測
        predictions = self._predict_from_history(features)

        for prediction, confidence in predictions:
            candidates.append(
                {
                    "dir": prediction,
                    "score": 0.3 + (confidence * 0.5),
                    "method": "ml_prediction",
                    "reason": f"ML prediction (confidence: {confidence:.2f})",
                }
            )

        return candidates

    def _analyze_statistical_patterns(self, filename: str, content: str) -> List[Dict]:
        """統計的パターン分析"""
        candidates = []

        # ファイル名パターン統計
        name_patterns = self._analyze_filename_patterns(filename)

        # 内容パターン統計
        content_patterns = self._analyze_content_patterns(content)

        # 組み合わせスコア計算
        for pattern, dirs in {**name_patterns, **content_patterns}.items():
            for dir_path, frequency in dirs.items():
                score = min(0.8, frequency / 10.0)  # 頻度ベーススコア
                candidates.append(
                    {
                        "dir": dir_path,
                        "score": score,
                        "method": "statistical_pattern",
                        "reason": f'Pattern "{pattern}" appears {frequency} times in {dir_path}',
                    }
                )

        return candidates

    def _extract_content_features(self, content: str) -> Dict:
        """内容特徴量抽出"""
        features = {
            "imports": re.findall(
                r"^\s*(?:from|import)\s+([^\s]+)", content, re.MULTILINE
            ),
            "classes": re.findall(r"class\s+(\w+)", content),
            "functions": re.findall(r"def\s+(\w+)", content),
            "keywords": re.findall(
                r"\b(async|await|worker|task|manager|db|api|web)\b", content.lower()
            ),
            "file_size": len(content),
            "line_count": len(content.split("\n")),
            "complexity": len(re.findall(r"\b(if|for|while|try|except)\b", content)),
        }
        return features

    def _extract_ml_features(self, filename: str, content: str) -> Dict:
        """機械学習用特徴量抽出"""
        features = self._extract_content_features(content)

        # ファイル名特徴
        features.update(
            {
                "filename_length": len(filename),
                "has_underscore": "_" in filename,
                "extension": Path(filename).suffix,
                "name_parts": filename.replace(".", "_").split("_"),
            }
        )

        return features

    def _find_similar_files(self, features: Dict) -> List[Tuple[str, float]]:
        """類似ファイル検索"""
        similarities = []

        # 全プロジェクトファイルとの比較
        for dir_path in ["workers/", "libs/", "scripts/", "config/", "data/"]:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue

            for file_path in target_dir.glob("*.py"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()

                    existing_features = self._extract_content_features(existing_content)
                    similarity = self._calculate_feature_similarity(
                        features, existing_features
                    )

                    if similarity > 0.3:  # 閾値
                        similarities.append((dir_path, similarity))

                except Exception:
                    continue

        # 類似度でソート
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:3]

    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        """特徴量間の類似度計算"""
        similarities = []

        # インポート類似度
        imports1 = set(features1.get("imports", []))
        imports2 = set(features2.get("imports", []))
        if imports1 or imports2:
            import_sim = (
                len(imports1 & imports2) / len(imports1 | imports2)
                if imports1 | imports2
                else 0
            )
            similarities.append(import_sim * 0.3)

        # キーワード類似度
        keywords1 = set(features1.get("keywords", []))
        keywords2 = set(features2.get("keywords", []))
        if keywords1 or keywords2:
            keyword_sim = (
                len(keywords1 & keywords2) / len(keywords1 | keywords2)
                if keywords1 | keywords2
                else 0
            )
            similarities.append(keyword_sim * 0.2)

        # サイズ類似度
        size1 = features1.get("file_size", 0)
        size2 = features2.get("file_size", 0)
        if size1 > 0 and size2 > 0:
            size_sim = 1 - abs(size1 - size2) / max(size1, size2)
            similarities.append(size_sim * 0.1)

        # 複雑度類似度
        comp1 = features1.get("complexity", 0)
        comp2 = features2.get("complexity", 0)
        if comp1 > 0 and comp2 > 0:
            comp_sim = 1 - abs(comp1 - comp2) / max(comp1, comp2)
            similarities.append(comp_sim * 0.1)

        return sum(similarities) if similarities else 0.0

    def _predict_from_history(self, features: Dict) -> List[Tuple[str, float]]:
        """履歴からの予測"""
        predictions = []

        for target_dir, history_items in self.placement_history.items():
            total_score = 0
            count = 0

            for item in history_items:
                similarity = self._calculate_feature_similarity(
                    features, item["features"]
                )
                if similarity > 0.2:
                    total_score += similarity * item["confidence"]
                    count += 1

            if count > 0:
                confidence = (total_score / count) * min(1.0, count / 5.0)  # 履歴数による重み
                predictions.append((target_dir, confidence))

        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:3]

    def _analyze_filename_patterns(self, filename: str) -> Dict:
        """ファイル名パターン分析"""
        patterns = {}

        # 既存ファイルの命名パターンを学習
        for dir_path in ["workers/", "libs/", "scripts/", "config/"]:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue

            for file_path in target_dir.glob("*"):
                if file_path.is_file():
                    existing_name = file_path.name
                    # 共通パターン抽出
                    common_parts = self._extract_common_parts(filename, existing_name)
                    for part in common_parts:
                        if part not in patterns:
                            patterns[part] = defaultdict(int)
                        patterns[part][dir_path] += 1

        return patterns

    def _analyze_content_patterns(self, content: str) -> Dict:
        """内容パターン分析"""
        patterns = {}

        # 重要なパターンを抽出
        important_patterns = [
            r"class\s+\w*Worker",
            r"class\s+\w*Manager",
            r"class\s+\w*Notifier",
            r"def\s+send_\w+",
            r"import\s+pika",
            r"from\s+flask",
            r"#!/bin/bash",
        ]

        for pattern in important_patterns:
            if re.search(pattern, content):
                # このパターンが過去にどこに配置されたかを調査
                pattern_placements = self._get_pattern_placements(pattern)
                if pattern_placements:
                    patterns[pattern] = pattern_placements

        return patterns

    def _extract_common_parts(self, name1: str, name2: str) -> List[str]:
        """2つのファイル名の共通部分抽出"""
        parts1 = re.split(r"[_\-\.]", name1.lower())
        parts2 = re.split(r"[_\-\.]", name2.lower())

        common = []
        for part1 in parts1:
            if len(part1) > 2 and part1 in parts2:
                common.append(part1)

        return common

    def _get_pattern_placements(self, pattern: str) -> Dict[str, int]:
        """特定パターンの過去の配置先統計"""
        placements = defaultdict(int)

        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count
                FROM placement_history
                WHERE content_features LIKE ?
                GROUP BY target_dir
            """,
                (f"%{pattern}%",),
            )

            for row in cursor.fetchall():
                target_dir, count = row
                placements[target_dir] = count

            conn.close()
        except Exception:
            pass

        return dict(placements)

    def _calculate_rule_confidence(
        self, filename: str, content: str, target_dir: str
    ) -> float:
        """ルールベース配置の信頼度計算"""
        confidence = 0.5

        # ファイル名マッチの強度
        for pattern, rule_dir in self.placement_rules.items():
            if rule_dir == target_dir and re.match(pattern, filename, re.IGNORECASE):
                confidence += 0.3
                break

        # 内容マッチの強度
        for keyword, rule_dir in self.content_based_rules.items():
            if rule_dir == target_dir and re.search(
                keyword, content, re.IGNORECASE | re.MULTILINE
            ):
                confidence += 0.2
                break

        return min(1.0, confidence)

    def _analyze_content_similarity_enhanced(self, content: str) -> List[Dict]:
        """改良版内容類似度分析 - TF-IDF + コサイン類似度"""
        candidates = []
        content_features = self._extract_content_features_enhanced(content)

        # TF-IDF ベクトル化
        content_vector = self._vectorize_content(content)

        # 既存ファイルとの類似度計算
        similar_placements = self._find_similar_files_enhanced(
            content_features, content_vector
        )

        for placement, similarity, method in similar_placements:
            candidates.append(
                {
                    "dir": placement,
                    "score": 0.4 + (similarity * 0.5),
                    "method": f"enhanced_similarity_{method}",
                    "reason": f"Enhanced similarity ({method}: {similarity:.3f})",
                }
            )

        return candidates

    def _ml_predict_placement_enhanced(self, filename: str, content: str) -> List[Dict]:
        """強化版機械学習予測 - 複数アルゴリズム組み合わせ"""
        candidates = []

        # 特徴量抽出
        features = self._extract_ml_features_enhanced(filename, content)

        # 1. 履歴ベース予測 (改良版)
        history_predictions = self._predict_from_history_enhanced(features)

        # 2. 決定木風の予測
        tree_predictions = self._decision_tree_predict(features)

        # 3. 近傍法予測
        knn_predictions = self._knn_predict(features)

        # 全予測結果を統合
        all_predictions = history_predictions + tree_predictions + knn_predictions

        # 投票による統合
        vote_counts = defaultdict(lambda: {"count": 0, "total_confidence": 0})
        for prediction, confidence in all_predictions:
            vote_counts[prediction]["count"] += 1
            vote_counts[prediction]["total_confidence"] += confidence

        for prediction, data in vote_counts.items():
            avg_confidence = data["total_confidence"] / data["count"]
            vote_weight = min(1.0, data["count"] / 3.0)
            final_score = 0.3 + (avg_confidence * vote_weight * 0.4)

            candidates.append(
                {
                    "dir": prediction,
                    "score": final_score,
                    "method": "enhanced_ml_ensemble",
                    "reason": f'ML ensemble ({data["count"]} votes, avg_conf: {avg_confidence:.2f})',
                }
            )

        return candidates

    def _analyze_statistical_patterns_enhanced(
        self, filename: str, content: str
    ) -> List[Dict]:
        """改良版統計的パターン分析 - 時系列・頻度・相関分析"""
        candidates = []

        # 時系列パターン分析
        temporal_patterns = self._analyze_temporal_patterns(filename, content)

        # 頻度パターン分析 (改良版)
        frequency_patterns = self._analyze_frequency_patterns_enhanced(
            filename, content
        )

        # 相関パターン分析
        correlation_patterns = self._analyze_correlation_patterns(filename, content)

        # 統合スコア計算
        all_patterns = {
            **temporal_patterns,
            **frequency_patterns,
            **correlation_patterns,
        }

        for pattern_type, pattern_data in all_patterns.items():
            for dir_path, score_data in pattern_data.items():
                score = score_data.get("score", 0)
                evidence = score_data.get("evidence", "")

                candidates.append(
                    {
                        "dir": dir_path,
                        "score": min(0.85, score),
                        "method": f"enhanced_statistics_{pattern_type}",
                        "reason": f"Statistical pattern ({pattern_type}): {evidence}",
                    }
                )

        return candidates

    def _analyze_dependency_patterns(self, content: str) -> List[Dict]:
        """依存関係パターン分析"""
        candidates = []

        # インポート依存関係分析
        imports = re.findall(r"^\s*(?:from|import)\s+([^\s]+)", content, re.MULTILINE)

        dependency_mapping = {
            "pika": "workers/",
            "flask": "web/",
            "fastapi": "api/",
            "sqlalchemy": "libs/",
            "sqlite3": "libs/",
            "requests": "libs/",
            "logging": "libs/",
            "os": "scripts/",
            "sys": "scripts/",
            "pathlib": "libs/",
            "datetime": "libs/",
            "json": "libs/",
            "threading": "workers/",
            "multiprocessing": "workers/",
            "psutil": "workers/",
        }

        dependency_scores = defaultdict(float)
        for imp in imports:
            base_module = imp.split(".")[0]
            if base_module in dependency_mapping:
                target_dir = dependency_mapping[base_module]
                dependency_scores[target_dir] += 0.15

        for dir_path, score in dependency_scores.items():
            candidates.append(
                {
                    "dir": dir_path,
                    "score": min(0.8, score),
                    "method": "dependency_analysis",
                    "reason": f"Dependency pattern (score: {score:.2f})",
                }
            )

        return candidates

    def _analyze_semantic_similarity(self, filename: str, content: str) -> List[Dict]:
        """意味的類似度分析 - 簡易版"""
        candidates = []

        # キーワード群による意味的分類
        semantic_clusters = {
            "worker_cluster": {
                "keywords": [
                    "worker",
                    "task",
                    "queue",
                    "job",
                    "process",
                    "background",
                    "async",
                    "celery",
                    "pika",
                ],
                "target": "workers/",
                "weight": 0.1,
            },
            "web_cluster": {
                "keywords": [
                    "web",
                    "http",
                    "flask",
                    "fastapi",
                    "api",
                    "route",
                    "endpoint",
                    "server",
                    "request",
                ],
                "target": "web/",
                "weight": 0.1,
            },
            "data_cluster": {
                "keywords": [
                    "database",
                    "db",
                    "sql",
                    "model",
                    "schema",
                    "table",
                    "query",
                    "orm",
                ],
                "target": "libs/",
                "weight": 0.1,
            },
            "config_cluster": {
                "keywords": [
                    "config",
                    "setting",
                    "environment",
                    "env",
                    "parameter",
                    "option",
                ],
                "target": "config/",
                "weight": 0.1,
            },
            "script_cluster": {
                "keywords": [
                    "script",
                    "automation",
                    "setup",
                    "install",
                    "deploy",
                    "build",
                    "run",
                ],
                "target": "scripts/",
                "weight": 0.1,
            },
        }

        content_lower = content.lower()
        filename_lower = filename.lower()

        for cluster_name, cluster_data in semantic_clusters.items():
            score = 0
            matched_keywords = []

            for keyword in cluster_data["keywords"]:
                # ファイル名での出現
                if keyword in filename_lower:
                    score += cluster_data["weight"] * 2
                    matched_keywords.append(f"filename:{keyword}")

                # 内容での出現
                content_matches = len(
                    re.findall(r"\b" + keyword + r"\b", content_lower)
                )
                if content_matches > 0:
                    score += cluster_data["weight"] * min(3, content_matches)
                    matched_keywords.append(f"content:{keyword}({content_matches})")

            if score > 0.2:
                candidates.append(
                    {
                        "dir": cluster_data["target"],
                        "score": min(0.75, score),
                        "method": "semantic_analysis",
                        "reason": f'Semantic cluster ({cluster_name}): {", ".join(matched_keywords[:3])}',
                    }
                )

        return candidates

    def _ensemble_scoring(self, candidates: List[Dict]) -> List[Dict]:
        """アンサンブル手法によるスコア統合"""
        # 手法別の重み
        method_weights = {
            "rule_based": 0.25,
            "enhanced_similarity_tfidf": 0.20,
            "enhanced_similarity_cosine": 0.15,
            "enhanced_ml_ensemble": 0.20,
            "enhanced_statistics_temporal": 0.05,
            "enhanced_statistics_frequency": 0.05,
            "enhanced_statistics_correlation": 0.05,
            "dependency_analysis": 0.15,
            "semantic_analysis": 0.10,
        }

        # デフォルト重み
        default_weight = 0.1

        # 重み付きスコア計算
        for candidate in candidates:
            method = candidate["method"]
            weight = method_weights.get(method, default_weight)
            candidate["weighted_score"] = candidate["score"] * weight
            candidate["original_score"] = candidate["score"]
            candidate["score"] = candidate["weighted_score"]

        # スコアでソート
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates

    def _extract_content_features_enhanced(self, content: str) -> Dict:
        """強化版特徴量抽出"""
        features = self._extract_content_features(content)

        # 追加特徴量
        features.update(
            {
                "docstring_count": len(re.findall(r'""".*?"""', content, re.DOTALL)),
                "comment_count": len(re.findall(r"#.*", content)),
                "decorator_count": len(re.findall(r"@\w+", content)),
                "async_functions": len(re.findall(r"async\s+def", content)),
                "lambda_count": len(re.findall(r"lambda\s+", content)),
                "comprehension_count": len(re.findall(r"\[.*for.*in.*\]", content)),
                "exception_handling": len(
                    re.findall(r"try:|except:|finally:", content)
                ),
                "context_managers": len(re.findall(r"with\s+", content)),
            }
        )

        return features

    def _vectorize_content(self, content: str) -> List[float]:
        """内容のベクトル化 - 簡易TF-IDF"""
        # 重要単語の抽出
        important_words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", content.lower())
        word_counts = Counter(important_words)

        # 上位30個の単語でベクトル化
        top_words = [word for word, count in word_counts.most_common(30)]
        vector = [word_counts.get(word, 0) for word in top_words]

        # 正規化
        total = sum(vector) if sum(vector) > 0 else 1
        return [v / total for v in vector]

    def _find_similar_files_enhanced(
        self, features: Dict, content_vector: List[float]
    ) -> List[Tuple[str, float, str]]:
        """強化版類似ファイル検索"""
        similarities = []

        for dir_path in ["workers/", "libs/", "scripts/", "config/", "data/", "web/"]:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue

            for file_path in target_dir.glob("*.py"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()

                    # 特徴量類似度
                    existing_features = self._extract_content_features_enhanced(
                        existing_content
                    )
                    feature_similarity = self._calculate_feature_similarity(
                        features, existing_features
                    )

                    # ベクトル類似度
                    existing_vector = self._vectorize_content(existing_content)
                    vector_similarity = self._cosine_similarity(
                        content_vector, existing_vector
                    )

                    if feature_similarity > 0.3:
                        similarities.append((dir_path, feature_similarity, "feature"))
                    if vector_similarity > 0.3:
                        similarities.append((dir_path, vector_similarity, "vector"))

                except Exception:
                    continue

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:5]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度計算"""
        if not vec1 or not vec2:
            return 0.0

        # ベクトル長を合わせる
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]

        # 内積計算
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # ノルム計算
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _extract_ml_features_enhanced(self, filename: str, content: str) -> Dict:
        """強化版ML特徴量抽出"""
        features = self._extract_ml_features(filename, content)

        # 高次特徴量
        features.update(
            {
                "import_diversity": len(set(features.get("imports", []))),
                "function_class_ratio": len(features.get("functions", []))
                / max(1, len(features.get("classes", []))),
                "complexity_density": features.get("complexity", 0)
                / max(1, features.get("line_count", 1)),
                "keyword_density": len(features.get("keywords", []))
                / max(1, features.get("line_count", 1)),
                "has_main_block": '__name__ == "__main__"' in content,
                "has_shebang": content.startswith("#!"),
                "is_executable_script": content.startswith("#!")
                or '__name__ == "__main__"' in content,
            }
        )

        return features

    def _predict_from_history_enhanced(self, features: Dict) -> List[Tuple[str, float]]:
        """強化版履歴予測 - 時系列重み付き"""
        predictions = []

        for target_dir, history_items in self.placement_history.items():
            weighted_score = 0
            total_weight = 0

            for i, item in enumerate(history_items):
                # 新しい履歴ほど高い重み
                time_weight = 1.0 / (1.0 + i * 0.1)

                similarity = self._calculate_feature_similarity(
                    features, item["features"]
                )
                if similarity > 0.2:
                    weighted_score += similarity * item["confidence"] * time_weight
                    total_weight += time_weight

            if total_weight > 0:
                confidence = weighted_score / total_weight
                # 履歴数による信頼度調整
                history_bonus = min(0.2, len(history_items) * 0.02)
                final_confidence = min(1.0, confidence + history_bonus)
                predictions.append((target_dir, final_confidence))

        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:3]

    def _decision_tree_predict(self, features: Dict) -> List[Tuple[str, float]]:
        """決定木風の予測ロジック"""
        predictions = []

        # シンプルな決定木ルール
        rules = [
            # Worker判定
            {
                "conditions": [
                    lambda f: "worker" in f.get("name_parts", []),
                    lambda f: "pika" in f.get("imports", []),
                    lambda f: f.get("async_functions", 0) > 0,
                ],
                "target": "workers/",
                "weight": 0.8,
            },
            # Manager判定
            {
                "conditions": [
                    lambda f: "manager" in f.get("name_parts", []),
                    lambda f: any("Manager" in cls for cls in f.get("classes", [])),
                    lambda f: f.get("complexity", 0) > 5,
                ],
                "target": "libs/",
                "weight": 0.7,
            },
            # Script判定
            {
                "conditions": [
                    lambda f: f.get("has_main_block", False),
                    lambda f: f.get("is_executable_script", False),
                    lambda f: f.get("line_count", 0) < 100,
                ],
                "target": "scripts/",
                "weight": 0.6,
            },
            # Web判定
            {
                "conditions": [
                    lambda f: "flask" in f.get("imports", []),
                    lambda f: "fastapi" in f.get("imports", []),
                    lambda f: any("route" in func for func in f.get("functions", [])),
                ],
                "target": "web/",
                "weight": 0.8,
            },
        ]

        for rule in rules:
            satisfied_conditions = sum(
                1 for condition in rule["conditions"] if condition(features)
            )
            if satisfied_conditions > 0:
                confidence = (satisfied_conditions / len(rule["conditions"])) * rule[
                    "weight"
                ]
                predictions.append((rule["target"], confidence))

        return predictions

    def _knn_predict(self, features: Dict) -> List[Tuple[str, float]]:
        """K近傍法による予測"""
        predictions = []
        k = 5  # 近傍数

        # 全履歴から最も類似する k 個を見つける
        all_similarities = []
        for target_dir, history_items in self.placement_history.items():
            for item in history_items:
                similarity = self._calculate_feature_similarity(
                    features, item["features"]
                )
                if similarity > 0.1:
                    all_similarities.append(
                        (target_dir, similarity, item["confidence"])
                    )

        # 類似度でソート
        all_similarities.sort(key=lambda x: x[1], reverse=True)

        # 上位 k 個で投票
        if len(all_similarities) >= k:
            top_k = all_similarities[:k]
            vote_weights = defaultdict(float)

            for target_dir, similarity, confidence in top_k:
                vote_weights[target_dir] += similarity * confidence

            # 正規化
            total_weight = sum(vote_weights.values())
            if total_weight > 0:
                for target_dir, weight in vote_weights.items():
                    predictions.append((target_dir, weight / total_weight))

        return predictions

    def _analyze_temporal_patterns(self, filename: str, content: str) -> Dict:
        """時系列パターン分析"""
        patterns = {}

        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            # 最近の配置傾向を分析
            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count,
                       AVG(confidence) as avg_confidence
                FROM placement_history
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY target_dir
                HAVING count > 1
                ORDER BY count DESC
            """
            )

            recent_trends = cursor.fetchall()

            for target_dir, count, avg_confidence in recent_trends:
                score = min(0.6, (count / 10.0) * avg_confidence)
                patterns["recent_trend"] = patterns.get("recent_trend", {})
                patterns["recent_trend"][target_dir] = {
                    "score": score,
                    "evidence": f"{count} recent placements, avg_conf: {avg_confidence:.2f}",
                }

            conn.close()
        except Exception:
            pass

        return patterns

    def _analyze_frequency_patterns_enhanced(self, filename: str, content: str) -> Dict:
        """強化版頻度パターン分析"""
        patterns = {}

        # ファイル名パターンの頻度分析
        name_parts = filename.replace(".", "_").split("_")
        for part in name_parts:
            if len(part) > 2:
                part_patterns = self._analyze_filename_patterns(part)
                if part_patterns:
                    patterns[f"name_part_{part}"] = part_patterns

        # 内容キーワードの頻度分析
        important_keywords = re.findall(
            r"\b(class|def|import|from|async|worker|manager|task|api|web|db|config)\b",
            content.lower(),
        )
        keyword_counter = Counter(important_keywords)

        for keyword, count in keyword_counter.most_common(5):
            if count > 1:
                keyword_patterns = self._get_pattern_placements(keyword)
                if keyword_patterns:
                    patterns[f"keyword_{keyword}"] = {
                        dir_path: {
                            "score": min(0.5, (freq / 20.0) * (count / 10.0)),
                            "evidence": f'keyword "{keyword}" appears {count} times',
                        }
                        for dir_path, freq in keyword_patterns.items()
                    }

        return patterns

    def _analyze_correlation_patterns(self, filename: str, content: str) -> Dict:
        """相関パターン分析"""
        patterns = {}

        # ファイル名と内容の相関
        filename_lower = filename.lower()
        content_lower = content.lower()

        correlation_rules = [
            # ファイル名に"worker"があり、内容に"pika"がある場合
            {
                "name_pattern": "worker",
                "content_pattern": "pika",
                "target": "workers/",
                "correlation_strength": 0.8,
            },
            # ファイル名に"manager"があり、内容に"class"がある場合
            {
                "name_pattern": "manager",
                "content_pattern": "class.*manager",
                "target": "libs/",
                "correlation_strength": 0.7,
            },
            # ファイル名に"api"があり、内容に"flask|fastapi"がある場合
            {
                "name_pattern": "api|web",
                "content_pattern": "flask|fastapi",
                "target": "web/",
                "correlation_strength": 0.8,
            },
        ]

        for rule in correlation_rules:
            name_match = re.search(rule["name_pattern"], filename_lower)
            content_match = re.search(rule["content_pattern"], content_lower)

            if name_match and content_match:
                patterns["correlation"] = patterns.get("correlation", {})
                patterns["correlation"][rule["target"]] = {
                    "score": rule["correlation_strength"],
                    "evidence": f'Name-content correlation: {rule["name_pattern"]} + {rule["content_pattern"]}',
                }

        return patterns

    def _select_optimal_placement(self, candidates: List[Dict], content: str) -> str:
        """最適配置先選択"""
        if not candidates:
            return "output/misc/"

        # 最高スコアの候補を選択
        best_candidate = candidates[0]

        # 追加的な検証
        if best_candidate["score"] < 0.5:
            # 信頼度が低い場合は安全な場所に配置
            if "class" in content and "Worker" in content:
                return "workers/"
            elif "class" in content and "Manager" in content:
                return "libs/"
            else:
                return "output/misc/"

        return best_candidate["dir"]

    def _calculate_placement_confidence(
        self, candidates: List[Dict], selected_dir: str
    ) -> float:
        """配置信頼度計算"""
        if not candidates:
            return 0.0

        selected_candidate = next(
            (c for c in candidates if c["dir"] == selected_dir), None
        )
        if not selected_candidate:
            return 0.0

        # トップ候補との差を考慮
        top_score = candidates[0]["score"]
        selected_score = selected_candidate["score"]

        # 複数手法の一致度を考慮
        method_diversity = len(set(c["method"] for c in candidates[:3]))
        diversity_bonus = min(0.2, method_diversity * 0.1)

        return min(1.0, selected_score + diversity_bonus)

    def _record_placement_learning(
        self, filename: str, content: str, target_dir: str, candidates: List[Dict]
    ):
        """配置学習データ記録"""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            features = self._extract_content_features(content)
            confidence = self._calculate_placement_confidence(candidates, target_dir)

            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO placement_history
                (filename, content_hash, content_features, target_dir, confidence)
                VALUES (?, ?, ?, ?, ?)
            """,
                (filename, content_hash, json.dumps(features), target_dir, confidence),
            )

            conn.commit()
            conn.close()

            logger.debug(
                f"Recorded placement learning: {filename} -> {target_dir} (confidence: {confidence:.2f})"
            )
        except Exception as e:
            logger.error(f"Failed to record placement learning: {e}")

    def get_placement_analytics(self) -> Dict:
        """配置分析レポート"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            # 基本統計
            cursor.execute("SELECT COUNT(*) FROM placement_history")
            total_placements = cursor.fetchone()[0]

            # ディレクトリ別統計
            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM placement_history
                GROUP BY target_dir
                ORDER BY count DESC
            """
            )
            dir_stats = cursor.fetchall()

            # 最近の配置統計
            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count
                FROM placement_history
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY target_dir
            """
            )
            recent_stats = cursor.fetchall()

            conn.close()

            return {
                "total_placements": total_placements,
                "directory_stats": [
                    {"dir": d[0], "count": d[1], "avg_confidence": d[2]}
                    for d in dir_stats
                ],
                "recent_activity": [{"dir": d[0], "count": d[1]} for d in recent_stats],
                "learning_db_size": self.learning_db_path.stat().st_size
                if self.learning_db_path.exists()
                else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get placement analytics: {e}")
            return {"error": str(e)}

    def test_enhanced_placement(
        self, test_content: str, test_filename: str = None
    ) -> Dict:
        """Enhanced placement testing and analysis"""
        if test_filename is None:
            test_filename = self._guess_filename_from_content(test_content)

        logger.info(f"Testing enhanced placement for: {test_filename}")

        # Get placement preview with detailed analysis
        candidates = self._analyze_placement_candidates(test_filename, test_content)
        selected_dir = self._select_optimal_placement(candidates, test_content)
        confidence = self._calculate_placement_confidence(candidates, selected_dir)

        # Detailed analysis breakdown
        analysis = {
            "filename": test_filename,
            "selected_placement": selected_dir,
            "confidence": confidence,
            "candidates": candidates,
            "analysis_methods": {
                "rule_based": sum(1 for c in candidates if "rule_based" in c["method"]),
                "similarity": sum(1 for c in candidates if "similarity" in c["method"]),
                "ml_prediction": sum(1 for c in candidates if "ml" in c["method"]),
                "statistical": sum(
                    1 for c in candidates if "statistics" in c["method"]
                ),
                "dependency": sum(1 for c in candidates if "dependency" in c["method"]),
                "semantic": sum(1 for c in candidates if "semantic" in c["method"]),
            },
            "content_features": self._extract_content_features_enhanced(test_content),
            "content_size": len(test_content),
            "content_lines": len(test_content.split("\n")),
        }

        return analysis

    def _initialize_advanced_ml_components(self):
        """Initialize advanced ML components for enhanced placement"""
        try:
            # Initialize directory embeddings
            directory_keywords = {
                "workers/": [
                    "worker",
                    "task",
                    "queue",
                    "job",
                    "process",
                    "background",
                    "async",
                    "pika",
                    "celery",
                ],
                "libs/": [
                    "library",
                    "utility",
                    "helper",
                    "manager",
                    "service",
                    "class",
                    "module",
                    "common",
                ],
                "scripts/": [
                    "script",
                    "automation",
                    "command",
                    "main",
                    "run",
                    "execute",
                    "batch",
                    "setup",
                ],
                "web/": [
                    "web",
                    "http",
                    "flask",
                    "fastapi",
                    "api",
                    "route",
                    "endpoint",
                    "server",
                ],
                "config/": [
                    "config",
                    "configuration",
                    "settings",
                    "environment",
                    "parameter",
                    "option",
                ],
                "data/": [
                    "data",
                    "database",
                    "model",
                    "schema",
                    "table",
                    "query",
                    "sql",
                    "json",
                ],
            }

            # Create simple embeddings based on keyword importance
            for directory, keywords in directory_keywords.items():
                embedding = {}
                for i, keyword in enumerate(keywords):
                    embedding[keyword] = 1.0 / (i + 1)  # Inverse position weighting
                self.directory_embeddings[directory] = embedding

            # Load historical success rates and feature importance
            self._load_placement_success_rates()
            self._load_feature_importance()

            # Initialize concept drift detection
            self._initialize_concept_drift_detection()

            logger.info("Enhanced ML components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize advanced ML components: {e}")

    def _load_placement_success_rates(self):
        """Load historical placement success rates"""
        try:
            if not self.learning_db_path.exists():
                return

            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            # Calculate success rates based on confidence scores
            cursor.execute(
                """
                SELECT target_dir, AVG(confidence) as avg_confidence, COUNT(*) as count
                FROM placement_history
                GROUP BY target_dir
                HAVING count > 2
            """
            )

            for row in cursor.fetchall():
                target_dir, avg_confidence, count = row
                # Weight by both confidence and frequency
                success_rate = avg_confidence * min(1.0, count / 10.0)
                self.placement_success_rates[target_dir] = success_rate

            conn.close()
            logger.info(
                f"Loaded success rates for {len(self.placement_success_rates)} directories"
            )
        except Exception as e:
            logger.error(f"Failed to load placement success rates: {e}")

    def _advanced_embedding_similarity(self, content: str, filename: str) -> List[Dict]:
        """Advanced embedding-based similarity analysis"""
        candidates = []

        try:
            # Extract content keywords
            content_keywords = re.findall(
                r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", content.lower()
            )
            filename_keywords = re.findall(
                r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", filename.lower()
            )

            all_keywords = content_keywords + filename_keywords
            keyword_freq = Counter(all_keywords)

            # Calculate similarity with each directory embedding
            for directory, embedding in self.directory_embeddings.items():
                similarity_score = 0.0
                total_weight = 0.0

                for keyword, freq in keyword_freq.items():
                    if keyword in embedding:
                        weight = embedding[keyword]
                        similarity_score += weight * math.log(1 + freq)
                        total_weight += weight

                if total_weight > 0:
                    normalized_score = similarity_score / total_weight
                    # Apply historical success rate weighting
                    success_rate = self.placement_success_rates.get(directory, 0.5)
                    final_score = normalized_score * (0.7 + success_rate * 0.3)

                    if final_score > 0.1:  # Threshold
                        candidates.append(
                            {
                                "dir": directory,
                                "score": min(0.85, final_score),
                                "method": "advanced_embedding",
                                "reason": f"Embedding similarity: {normalized_score:.3f}, success_rate: {success_rate:.2f}",
                            }
                        )

        except Exception as e:
            logger.error(f"Advanced embedding similarity failed: {e}")

        return candidates

    def _contextual_pattern_analysis(self, filename: str, content: str) -> List[Dict]:
        """Contextual pattern analysis using multiple signals"""
        candidates = []

        try:
            # Analyze different context layers
            context_signals = {
                "structural": self._analyze_code_structure(content),
                "behavioral": self._analyze_code_behavior(content),
                "architectural": self._analyze_architectural_patterns(
                    filename, content
                ),
                "temporal": self._analyze_temporal_context(content),
            }

            # Aggregate signals for each directory
            directory_scores = defaultdict(
                lambda: {"total": 0, "count": 0, "details": []}
            )

            for signal_type, signal_data in context_signals.items():
                for directory, score, reason in signal_data:
                    directory_scores[directory]["total"] += score
                    directory_scores[directory]["count"] += 1
                    directory_scores[directory]["details"].append(
                        f"{signal_type}: {reason}"
                    )

            # Calculate final scores
            for directory, data in directory_scores.items():
                if data["count"] > 0:
                    avg_score = data["total"] / data["count"]
                    # Boost score if multiple signals agree
                    consensus_bonus = min(0.2, data["count"] * 0.05)
                    final_score = min(0.9, avg_score + consensus_bonus)

                    candidates.append(
                        {
                            "dir": directory,
                            "score": final_score,
                            "method": "contextual_pattern",
                            "reason": f'Multi-signal consensus ({data["count"]} signals): {", ".join(data["details"][:2])}',
                        }
                    )

        except Exception as e:
            logger.error(f"Contextual pattern analysis failed: {e}")

        return candidates

    def _analyze_code_structure(self, content: str) -> List[Tuple[str, float, str]]:
        """Analyze code structural patterns"""
        signals = []

        # Class inheritance patterns
        class_patterns = re.findall(r"class\s+(\w+)\s*\([^)]*(\w+)[^)]*\)", content)
        for class_name, parent_class in class_patterns:
            if "Worker" in parent_class or "Task" in parent_class:
                signals.append(("workers/", 0.7, f"inherits from {parent_class}"))
            elif "Manager" in parent_class or "Service" in parent_class:
                signals.append(("libs/", 0.6, f"inherits from {parent_class}"))

        # Method pattern analysis
        methods = re.findall(r"def\s+(\w+)", content)
        async_methods = re.findall(r"async\s+def\s+(\w+)", content)

        if len(async_methods) > len(methods) * 0.3:  # >30% async methods
            signals.append(("workers/", 0.6, f"{len(async_methods)} async methods"))

        # Import dependency depth
        import_count = len(re.findall(r"^\s*(?:from|import)", content, re.MULTILINE))
        if import_count > 10:
            signals.append(("libs/", 0.4, f"heavy imports ({import_count})"))
        elif import_count < 3:
            signals.append(("scripts/", 0.4, f"lightweight imports ({import_count})"))

        return signals

    def _analyze_code_behavior(self, content: str) -> List[Tuple[str, float, str]]:
        """Analyze behavioral patterns in code"""
        signals = []

        # I/O patterns
        if re.search(r"\b(input|raw_input|sys\.argv|argparse)\b", content):
            signals.append(("scripts/", 0.6, "interactive/CLI behavior"))

        if re.search(r"\b(print|logging\.|logger\.)\b", content):
            log_count = len(re.findall(r"\b(print|logging\.|logger\.)", content))
            if log_count > 5:
                signals.append(
                    ("workers/", 0.5, f"heavy logging ({log_count} statements)")
                )

        # Network/HTTP patterns
        if re.search(r"\b(requests\.|urllib\.|http\.client)\b", content):
            signals.append(("libs/", 0.5, "HTTP client behavior"))

        if re.search(r"\b(flask|fastapi|@app\.route|@router\.)", content):
            signals.append(("web/", 0.8, "web framework usage"))

        # Database patterns
        if re.search(r"\b(sqlite3|sqlalchemy|cursor\.execute)\b", content):
            signals.append(("libs/", 0.6, "database operations"))

        # Configuration patterns
        if re.search(r"\b(config|settings|environment|env\.get)\b", content.lower()):
            config_matches = len(
                re.findall(r"\b(config|settings|environment)\b", content.lower())
            )
            if config_matches > 3:
                signals.append(
                    ("config/", 0.7, f"configuration focus ({config_matches} matches)")
                )

        return signals

    def _analyze_architectural_patterns(
        self, filename: str, content: str
    ) -> List[Tuple[str, float, str]]:
        """Analyze architectural patterns"""
        signals = []

        # Singleton pattern
        if re.search(r"_instance\s*=\s*None|__new__.*_instance", content):
            signals.append(("libs/", 0.6, "singleton pattern"))

        # Factory pattern
        if re.search(r"def\s+create_\w+|class\s+\w+Factory", content):
            signals.append(("libs/", 0.5, "factory pattern"))

        # Observer pattern
        if re.search(r"notify|observer|listener|subscribe", content.lower()):
            signals.append(("libs/", 0.4, "observer pattern"))

        # Command pattern
        if re.search(r"execute|command|invoke", content.lower()) and "class" in content:
            signals.append(("workers/", 0.5, "command pattern"))

        # Repository pattern
        if re.search(r"repository|dao|crud", content.lower()):
            signals.append(("libs/", 0.6, "repository pattern"))

        # File naming architectural hints
        filename_lower = filename.lower()
        if "facade" in filename_lower or "adapter" in filename_lower:
            signals.append(("libs/", 0.7, f"architectural filename: {filename}"))
        elif "controller" in filename_lower or "handler" in filename_lower:
            signals.append(("web/", 0.6, f"controller filename: {filename}"))

        return signals

    def _analyze_temporal_context(self, content: str) -> List[Tuple[str, float, str]]:
        """Analyze temporal/timing related patterns"""
        signals = []

        # Scheduling patterns
        if re.search(r"\b(sleep|time\.sleep|schedule|cron|timer)\b", content):
            signals.append(("workers/", 0.6, "timing/scheduling operations"))

        # Real-time patterns
        if re.search(r"\b(threading|multiprocessing|concurrent|asyncio)\b", content):
            signals.append(("workers/", 0.7, "concurrent execution"))

        # Batch processing
        if re.search(r"\bbatch|bulk|process_all\b", content.lower()):
            signals.append(("scripts/", 0.6, "batch processing"))

        # Monitoring patterns
        if re.search(r"\b(monitor|watch|poll|heartbeat)\b", content.lower()):
            signals.append(("workers/", 0.5, "monitoring behavior"))

        return signals

    def _probabilistic_ensemble(self, candidates: List[Dict]) -> List[Dict]:
        """Improved ensemble method with probabilistic weighting"""
        if not candidates:
            return candidates

        # Group candidates by directory
        directory_groups = defaultdict(list)
        for candidate in candidates:
            directory_groups[candidate["dir"]].append(candidate)

        # Calculate ensemble scores for each directory
        ensemble_candidates = []
        for directory, dir_candidates in directory_groups.items():
            if not dir_candidates:
                continue

            # Calculate weighted average with method diversity bonus
            total_score = 0
            total_weight = 0
            methods_used = set()

            for candidate in dir_candidates:
                method = candidate["method"]
                score = candidate["score"]

                # Method-specific weights
                method_weights = {
                    "rule_based": 0.8,
                    "advanced_embedding": 0.9,
                    "contextual_pattern": 0.85,
                    "enhanced_similarity_tfidf": 0.8,
                    "enhanced_ml_ensemble": 0.75,
                    "dependency_analysis": 0.7,
                    "semantic_analysis": 0.6,
                }

                weight = method_weights.get(method, 0.5)
                total_score += score * weight
                total_weight += weight
                methods_used.add(method)

            if total_weight > 0:
                avg_score = total_score / total_weight

                # Diversity bonus for multiple methods agreeing
                diversity_bonus = min(0.15, len(methods_used) * 0.03)

                # Historical success rate bonus
                success_bonus = self.placement_success_rates.get(directory, 0.5) * 0.1

                final_score = min(0.95, avg_score + diversity_bonus + success_bonus)

                ensemble_candidates.append(
                    {
                        "dir": directory,
                        "score": final_score,
                        "method": "probabilistic_ensemble",
                        "reason": f"Ensemble of {len(dir_candidates)} methods, diversity: {len(methods_used)}",
                        "component_methods": list(methods_used),
                        "diversity_bonus": diversity_bonus,
                        "success_bonus": success_bonus,
                    }
                )

        # Sort by score
        ensemble_candidates.sort(key=lambda x: x["score"], reverse=True)
        return ensemble_candidates

    def _initialize_neural_weights(self) -> Dict[str, float]:
        """Initialize neural network-like weights for different features"""
        return {
            "filename_pattern": 0.25,
            "content_similarity": 0.20,
            "import_dependencies": 0.15,
            "class_structure": 0.15,
            "function_patterns": 0.10,
            "file_size": 0.05,
            "complexity": 0.05,
            "historical_success": 0.15,
            "temporal_patterns": 0.10,
        }

    def _load_feature_importance(self):
        """Load feature importance from historical data"""
        try:
            if not self.learning_db_path.exists():
                return

            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            # Analyze which features correlate with high confidence placements
            cursor.execute(
                """
                SELECT content_features, confidence
                FROM placement_history
                WHERE confidence > 0.7
                ORDER BY created_at DESC
                LIMIT 500
            """
            )

            high_conf_features = []
            for row in cursor.fetchall():
                try:
                    features = json.loads(row[0])
                    confidence = row[1]
                    high_conf_features.append((features, confidence))
                except json.JSONDecodeError:
                    continue

            # Calculate feature importance based on correlation with success
            if high_conf_features:
                self._calculate_feature_importance(high_conf_features)

            conn.close()
            logger.info(
                f"Loaded feature importance from {len(high_conf_features)} high-confidence placements"
            )
        except Exception as e:
            logger.error(f"Failed to load feature importance: {e}")

    def _calculate_feature_importance(self, feature_data: List[Tuple[Dict, float]]):
        """Calculate importance of different features based on historical success"""
        feature_contributions = defaultdict(list)

        for features, confidence in feature_data:
            # Analyze which features appear in successful placements
            if len(features.get("imports", [])) > 0:
                feature_contributions["imports"].append(confidence)
            if len(features.get("classes", [])) > 0:
                feature_contributions["classes"].append(confidence)
            if len(features.get("functions", [])) > 0:
                feature_contributions["functions"].append(confidence)
            if features.get("file_size", 0) > 1000:
                feature_contributions["large_files"].append(confidence)
            if features.get("complexity", 0) > 5:
                feature_contributions["complex_code"].append(confidence)

        # Update feature importance based on average success
        for feature, confidences in feature_contributions.items():
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                self.feature_importance[feature] = avg_confidence

    def _initialize_concept_drift_detection(self):
        """Initialize concept drift detection for adaptive learning"""
        try:
            if not self.learning_db_path.exists():
                return

            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()

            # Get recent placement patterns
            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count
                FROM placement_history
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY target_dir
            """
            )

            recent_patterns = dict(cursor.fetchall())

            # Get historical patterns
            cursor.execute(
                """
                SELECT target_dir, COUNT(*) as count
                FROM placement_history
                WHERE created_at <= datetime('now', '-30 days')
                GROUP BY target_dir
            """
            )

            historical_patterns = dict(cursor.fetchall())

            # Detect significant changes in placement patterns
            drift_detected = False
            for directory in set(recent_patterns.keys()) | set(
                historical_patterns.keys()
            ):
                recent_count = recent_patterns.get(directory, 0)
                historical_count = historical_patterns.get(directory, 0)

                if historical_count > 0:
                    change_ratio = (
                        abs(recent_count - historical_count) / historical_count
                    )
                    if change_ratio > self.concept_drift_detector["drift_threshold"]:
                        drift_detected = True
                        logger.info(
                            f"Concept drift detected in {directory}: {change_ratio:.2f}"
                        )

            if drift_detected:
                self._adapt_to_concept_drift()

            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize concept drift detection: {e}")

    def _adapt_to_concept_drift(self):
        """Adapt model parameters when concept drift is detected"""
        # Reduce confidence in historical patterns
        for directory in self.placement_success_rates:
            self.placement_success_rates[directory] *= 0.9

        # Increase adaptive thresholds to be more conservative
        self.adaptive_thresholds["confidence_threshold"] = min(
            0.7, self.adaptive_thresholds["confidence_threshold"] * 1.1
        )

        logger.info(
            "Adapted to concept drift: reduced historical confidence, increased thresholds"
        )

    def record_placement_feedback(
        self,
        filename: str,
        actual_directory: str,
        predicted_directory: str,
        success_score: float,
    ):
        """Record feedback for reinforcement learning"""
        feedback = {
            "filename": filename,
            "actual": actual_directory,
            "predicted": predicted_directory,
            "success_score": success_score,
            "timestamp": datetime.now().timestamp(),
            "correct": actual_directory == predicted_directory,
        }

        self.placement_feedback[filename].append(feedback)

        # Keep only recent feedback
        if len(self.placement_feedback[filename]) > 10:
            self.placement_feedback[filename] = self.placement_feedback[filename][-10:]

        # Update neural weights based on feedback
        self._update_neural_weights_from_feedback(feedback)

        logger.debug(
            f"Recorded placement feedback: {filename} -> {actual_directory} (score: {success_score})"
        )

    def _update_neural_weights_from_feedback(self, feedback: Dict):
        """Update neural weights based on placement feedback"""
        learning_rate = 0.01
        success_score = feedback["success_score"]

        # Increase weights for successful predictions, decrease for unsuccessful ones
        adjustment = (success_score - 0.5) * learning_rate

        # Apply adjustment to all weights (simplified approach)
        for key in self.neural_weights:
            self.neural_weights[key] = max(
                0.01, min(1.0, self.neural_weights[key] + adjustment * 0.1)
            )

        # Normalize weights to sum to 1
        total_weight = sum(self.neural_weights.values())
        if total_weight > 0:
            for key in self.neural_weights:
                self.neural_weights[key] /= total_weight

    def _enhanced_ensemble_with_meta_learning(
        self, candidates: List[Dict]
    ) -> List[Dict]:
        """Meta-learning ensemble that learns from ensemble performance"""
        if not candidates:
            return candidates

        # Apply dynamic threshold based on recent performance
        dynamic_threshold = self._calculate_dynamic_threshold()

        # Group by directory and apply meta-learning weights
        directory_groups = defaultdict(list)
        for candidate in candidates:
            directory_groups[candidate["dir"]].append(candidate)

        meta_candidates = []
        for directory, dir_candidates in directory_groups.items():
            # Calculate meta-learning score
            meta_score = self._calculate_meta_learning_score(directory, dir_candidates)

            if meta_score > dynamic_threshold:
                # Apply neural network-like combination
                final_score = self._neural_combination(dir_candidates, meta_score)

                meta_candidates.append(
                    {
                        "dir": directory,
                        "score": final_score,
                        "method": "meta_learning_ensemble",
                        "reason": f"Meta-learning (score: {meta_score:.3f}, candidates: {len(dir_candidates)})",
                        "meta_score": meta_score,
                        "component_count": len(dir_candidates),
                    }
                )

        meta_candidates.sort(key=lambda x: x["score"], reverse=True)
        return meta_candidates

    def _calculate_dynamic_threshold(self) -> float:
        """Calculate dynamic threshold based on recent performance"""
        base_threshold = self.adaptive_thresholds["ensemble_threshold"]

        # Adjust based on recent placement success rate
        if self.placement_feedback:
            recent_successes = [
                fb
                for fb in self.placement_feedback.values()
                if fb and fb[-1]["timestamp"] > datetime.now().timestamp() - 86400
            ]  # Last 24h
            if recent_successes:
                avg_success = sum(
                    fb[-1]["success_score"] for fb in recent_successes
                ) / len(recent_successes)
                threshold_adjustment = (avg_success - 0.7) * 0.2  # Scale adjustment
                return max(0.3, min(0.8, base_threshold + threshold_adjustment))

        return base_threshold

    def _calculate_meta_learning_score(
        self, directory: str, candidates: List[Dict]
    ) -> float:
        """Calculate meta-learning score for a directory based on candidate agreement"""
        if not candidates:
            return 0.0

        # Base score from candidates
        avg_score = sum(c["score"] for c in candidates) / len(candidates)

        # Method diversity bonus
        unique_methods = len(set(c["method"] for c in candidates))
        diversity_bonus = min(0.2, unique_methods * 0.04)

        # Historical success bonus
        historical_bonus = self.placement_success_rates.get(directory, 0.5) * 0.1

        # Feature importance alignment
        feature_alignment = self._calculate_feature_alignment(directory, candidates)

        meta_score = avg_score + diversity_bonus + historical_bonus + feature_alignment
        return min(0.95, meta_score)

    def _calculate_feature_alignment(
        self, directory: str, candidates: List[Dict]
    ) -> float:
        """Calculate how well candidates align with important features for this directory"""
        # This is a simplified version - in practice would analyze feature patterns
        alignment_score = 0.0

        if directory in self.directory_embeddings:
            embedding = self.directory_embeddings[directory]
            # Check if candidates mention key terms for this directory
            for candidate in candidates:
                reason = candidate.get("reason", "").lower()
                for keyword, weight in embedding.items():
                    if keyword.lower() in reason:
                        alignment_score += weight * 0.02

        return min(0.15, alignment_score)

    def _neural_combination(self, candidates: List[Dict], meta_score: float) -> float:
        """Neural network-like combination of candidate scores"""
        if not candidates:
            return 0.0

        # Weighted combination using neural weights
        weighted_sum = 0.0
        total_weight = 0.0

        for candidate in candidates:
            method = candidate["method"]
            score = candidate["score"]

            # Map methods to neural weight categories
            weight_key = self._map_method_to_weight_key(method)
            weight = self.neural_weights.get(weight_key, 0.1)

            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            base_score = weighted_sum / total_weight
        else:
            base_score = sum(c["score"] for c in candidates) / len(candidates)

        # Apply non-linear activation (sigmoid-like)
        activated_score = base_score / (1 + math.exp(-5 * (base_score - 0.5)))

        # Combine with meta-score
        final_score = 0.7 * activated_score + 0.3 * meta_score

        return min(0.95, final_score)

    def _map_method_to_weight_key(self, method: str) -> str:
        """Map candidate method to neural weight key"""
        method_mapping = {
            "rule_based": "filename_pattern",
            "enhanced_similarity": "content_similarity",
            "dependency_analysis": "import_dependencies",
            "contextual_pattern": "class_structure",
            "semantic_analysis": "function_patterns",
            "enhanced_ml_ensemble": "historical_success",
            "advanced_embedding": "temporal_patterns",
        }

        for key, weight_key in method_mapping.items():
            if key in method:
                return weight_key

        return "content_similarity"  # Default

    # New Enhanced Methods for Next-Generation File Placement

    def _guess_filename_from_content_enhanced(self, content):
        """内容からファイル名を推測（強化版）"""
        lines = content.split("\n")

        # 1. ファイルヘッダーから推測
        filename_from_header = self._extract_filename_from_header(content)
        if filename_from_header:
            return filename_from_header

        # 2. 主要クラス名から推測（複数クラスの場合は最も重要なものを選択）
        classes = re.findall(r"class\s+(\w+)", content)
        if classes:
            # クラスの重要度を評価
            primary_class = self._identify_primary_class(classes, content)
            if primary_class:
                snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", primary_class).lower()
                return f"{snake_name}.py"

        # 3. モジュール名パターンから推測
        module_name = self._extract_module_name_from_content(content)
        if module_name:
            return f"{module_name}.py"

        # 4. 主要関数名から推測（改良版）
        functions = re.findall(r"def\s+(\w+)", content)
        if functions:
            # __init__, __main__ などを除外し、最も重要な関数を選択
            primary_function = self._identify_primary_function(functions, content)
            if primary_function:
                return f"{primary_function}.py"

        # 5. ファイルタイプに基づく推測
        file_type = self._determine_file_type_from_content(content)
        if file_type["extension"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{file_type['prefix']}_{timestamp}{file_type['extension']}"

        # 6. セマンティック分析による命名
        semantic_name = self._generate_semantic_filename(content)
        if semantic_name:
            return semantic_name

        # デフォルト
        return f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    def _extract_filename_from_header(self, content):
        """ファイルヘッダーからファイル名を抽出"""
        first_lines = content.split("\n")[:10]
        for line in first_lines:
            # コメント内のファイル名
            if re.search(r"@file|filename:|file:|@name", line.lower()):
                match = re.search(r"[\w_]+\.(?:py|sh|js|html|css|json)", line)
                if match:
                    return match.group(0)
            # Python docstring内のファイル名
            if '"""' in line and ".py" in line:
                match = re.search(r"(\w+\.py)", line)
                if match:
                    return match.group(1)
        return None

    def _identify_primary_class(self, classes, content):
        """最も重要なクラスを特定"""
        class_scores = {}
        for cls in classes:
            score = 0
            # ファイル名に含まれる可能性が高いクラス名を優先
            if re.search(rf"\b{cls.lower()}\b", content.lower()):
                score += 3
            # 継承関係を持つクラスを優先
            if re.search(rf"class\s+{cls}\s*\([^)]+\)", content):
                score += 2
            # メソッド数が多いクラスを優先
            method_count = len(
                re.findall(rf"class\s+{cls}.*?(?=class|\Z)", content, re.DOTALL)
            )
            score += min(3, method_count)
            # 特定の重要キーワードを含むクラスを優先
            if re.search(r"(Manager|Worker|Service|Controller|Handler)", cls):
                score += 4
            class_scores[cls] = score

        return (
            max(class_scores.items(), key=lambda x: x[1])[0] if class_scores else None
        )

    def _extract_module_name_from_content(self, content):
        """内容からモジュール名を抽出"""
        # __name__ 変数の使用パターン
        if "__name__" in content:
            # if __name__ == "__main__": パターン
            if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content):
                return "main_script"

        # 特定のインポートパターンから推測
        imports = re.findall(r"from\s+(\w+)\s+import|import\s+(\w+)", content)
        common_modules = ["os", "sys", "json", "datetime", "logging", "re"]
        specialized_modules = []
        for imp in imports:
            module = imp[0] or imp[1]
            if module not in common_modules:
                specialized_modules.append(module)

        if specialized_modules:
            # 最も特殊化されたモジュール名を使用
            return specialized_modules[0].lower()

        return None

    def _identify_primary_function(self, functions, content):
        """最も重要な関数を特定"""
        # 除外する関数名
        excluded = {"__init__", "__str__", "__repr__", "__del__", "setUp", "tearDown"}
        candidates = [
            f for f in functions if f not in excluded and not f.startswith("_")
        ]

        if not candidates:
            return None

        function_scores = {}
        for func in candidates:
            score = 0
            # main関数は最優先
            if func == "main":
                score += 10
            # 長い関数名（具体的な機能を表す）を優先
            score += len(func) * 0.1
            # 動詞+名詞パターンを優先
            if re.search(
                r"^(get|set|create|update|delete|process|handle|manage|send|receive)",
                func,
            ):
                score += 3
            # 関数の複雑度
            func_pattern = rf"def\s+{func}\s*\([^)]*\):(.*?)(?=def|\Z)"
            func_content = re.search(func_pattern, content, re.DOTALL)
            if func_content:
                lines = func_content.group(1).count("\n")
                score += min(5, lines * 0.1)
            function_scores[func] = score

        return (
            max(function_scores.items(), key=lambda x: x[1])[0]
            if function_scores
            else candidates[0]
        )

    def _determine_file_type_from_content(self, content):
        """内容からファイルタイプを判定"""
        # Shebang行チェック
        if content.startswith("#!/bin/bash") or content.startswith("#!/bin/sh"):
            return {"prefix": "script", "extension": ".sh"}
        elif content.startswith("#!/usr/bin/env python") or content.startswith(
            "#!/usr/bin/python"
        ):
            return {"prefix": "script", "extension": ".py"}

        # HTML/CSS/JS判定
        if re.search(r"<html|<head|<body|<!DOCTYPE", content, re.IGNORECASE):
            return {"prefix": "page", "extension": ".html"}
        elif re.search(r"\.css|styles?|@media|selector", content, re.IGNORECASE):
            return {"prefix": "styles", "extension": ".css"}
        elif re.search(r"function|var |let |const |=>", content):
            return {"prefix": "script", "extension": ".js"}

        # 設定ファイル判定
        if re.search(r"config|setting|environment|parameter", content.lower()):
            if re.search(r"^\s*\w+\s*=", content, re.MULTILINE):
                return {"prefix": "config", "extension": ".conf"}

        # JSON判定
        content_stripped = content.strip()
        if (content_stripped.startswith("{") and content_stripped.endswith("}")) or (
            content_stripped.startswith("[") and content_stripped.endswith("]")
        ):
            try:
                json.loads(content)
                return {"prefix": "data", "extension": ".json"}
            except:
                pass

        # SQL判定
        if re.search(
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b",
            content,
            re.IGNORECASE,
        ):
            return {"prefix": "query", "extension": ".sql"}

        # Markdown判定
        if re.search(r"^#+ |^\* |\[.*\]\(.*\)|```", content, re.MULTILINE):
            return {"prefix": "doc", "extension": ".md"}

        # デフォルトはPython
        return {"prefix": "generated", "extension": ".py"}

    def _generate_semantic_filename(self, content):
        """セマンティック分析による意味のあるファイル名生成"""
        # キーワード抽出による意味的分類
        content_lower = content.lower()

        # 機能別キーワードマップ
        semantic_maps = {
            "worker": ["worker", "task", "job", "queue", "process", "background"],
            "manager": ["manager", "controller", "coordinator", "supervisor", "admin"],
            "service": ["service", "api", "endpoint", "handler", "provider"],
            "utils": ["utility", "helper", "common", "shared", "tools"],
            "config": ["config", "settings", "environment", "params"],
            "database": ["database", "db", "model", "schema", "repository"],
            "network": ["network", "http", "client", "server", "request"],
            "auth": ["auth", "login", "password", "token", "security"],
            "test": ["test", "spec", "mock", "fixture", "assert"],
            "monitor": ["monitor", "health", "check", "status", "metrics"],
        }

        scores = {}
        for category, keywords in semantic_maps.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                scores[category] = score

        if scores:
            # 最もスコアの高いカテゴリを選択
            primary_category = max(scores.items(), key=lambda x: x[1])[0]
            timestamp = datetime.now().strftime("%H%M%S")
            return f"{primary_category}_{timestamp}.py"

        return None

    def _analyze_placement_candidates_enhanced(self, filename, content):
        """Enhanced candidate analysis with additional ML methods"""
        # Start with existing analysis
        candidates = self._analyze_placement_candidates(filename, content)

        # Add new analysis methods
        enhanced_candidates = []

        # 1. Deep content understanding
        deep_analysis_candidates = self._deep_content_analysis(filename, content)
        enhanced_candidates.extend(deep_analysis_candidates)

        # 2. Cross-reference analysis with existing files
        cross_ref_candidates = self._cross_reference_analysis(filename, content)
        enhanced_candidates.extend(cross_ref_candidates)

        # 3. Temporal pattern analysis (time-based placement trends)
        temporal_candidates = self._temporal_pattern_analysis_enhanced(
            filename, content
        )
        enhanced_candidates.extend(temporal_candidates)

        # 4. Code complexity and architecture analysis
        architecture_candidates = self._architecture_based_placement(filename, content)
        enhanced_candidates.extend(architecture_candidates)

        # 5. Integration pattern analysis
        integration_candidates = self._integration_pattern_analysis(filename, content)
        enhanced_candidates.extend(integration_candidates)

        # Combine all candidates
        all_candidates = candidates + enhanced_candidates

        # Apply advanced ensemble with conflict resolution
        return self._advanced_ensemble_with_conflict_resolution(all_candidates)

    def _deep_content_analysis(self, filename, content):
        """Deep learning-inspired content analysis"""
        candidates = []

        try:
            # Multi-layer feature extraction
            features = {
                "syntactic": self._extract_syntactic_features(content),
                "semantic": self._extract_semantic_features(content),
                "structural": self._extract_structural_features(content),
                "behavioral": self._extract_behavioral_features(content),
            }

            # Apply layered analysis similar to neural networks
            for layer_name, layer_features in features.items():
                layer_prediction = self._apply_layer_analysis(
                    layer_name, layer_features
                )
                if layer_prediction:
                    candidates.append(
                        {
                            "dir": layer_prediction["directory"],
                            "score": layer_prediction["confidence"],
                            "method": f"deep_{layer_name}_analysis",
                            "reason": layer_prediction["reasoning"],
                        }
                    )
        except Exception as e:
            logger.error(f"Deep content analysis failed: {e}")

        return candidates

    def _extract_syntactic_features(self, content):
        """Extract syntactic patterns from code"""
        return {
            "imports": len(re.findall(r"^\s*(?:from|import)", content, re.MULTILINE)),
            "function_defs": len(re.findall(r"^\s*def\s+", content, re.MULTILINE)),
            "class_defs": len(re.findall(r"^\s*class\s+", content, re.MULTILINE)),
            "decorators": len(re.findall(r"^\s*@\w+", content, re.MULTILINE)),
            "async_keywords": len(re.findall(r"\basync\s+", content)),
            "await_keywords": len(re.findall(r"\bawait\s+", content)),
            "exception_handling": len(re.findall(r"\btry:|except:|finally:", content)),
            "context_managers": len(re.findall(r"\bwith\s+", content)),
        }

    def _extract_semantic_features(self, content):
        """Extract semantic meaning from code"""
        domain_keywords = {
            "web": ["flask", "fastapi", "request", "response", "route", "endpoint"],
            "data": ["database", "query", "model", "schema", "table", "sql"],
            "worker": ["task", "job", "queue", "worker", "background", "process"],
            "api": ["api", "rest", "graphql", "endpoint", "service"],
            "config": ["config", "settings", "environment", "parameter"],
            "monitoring": ["monitor", "health", "metrics", "logging", "status"],
        }

        semantic_scores = {}
        content_lower = content.lower()
        for domain, keywords in domain_keywords.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            semantic_scores[domain] = score

        return semantic_scores

    def _extract_structural_features(self, content):
        """Extract code structural features"""
        return {
            "file_length": len(content.split("\n")),
            "avg_line_length": sum(len(line) for line in content.split("\n"))
            / max(1, len(content.split("\n"))),
            "indent_levels": len(
                set(
                    len(line) - len(line.lstrip())
                    for line in content.split("\n")
                    if line.strip()
                )
            ),
            "docstring_ratio": len(re.findall(r'""".*?"""', content, re.DOTALL))
            / max(1, len(content.split("\n"))),
            "comment_ratio": len(re.findall(r"#.*", content))
            / max(1, len(content.split("\n"))),
            "blank_line_ratio": content.count("\n\n")
            / max(1, len(content.split("\n"))),
        }

    def _extract_behavioral_features(self, content):
        """Extract behavioral patterns from code"""
        return {
            "io_operations": len(
                re.findall(r"\b(print|input|open|read|write|close)\b", content)
            ),
            "network_operations": len(
                re.findall(r"\b(requests|urllib|socket|http)\b", content)
            ),
            "file_operations": len(
                re.findall(r"\b(os\.path|pathlib|glob|shutil)\b", content)
            ),
            "database_operations": len(
                re.findall(r"\b(sqlite|mysql|postgres|mongodb)\b", content)
            ),
            "concurrency_usage": len(
                re.findall(r"\b(threading|multiprocessing|asyncio)\b", content)
            ),
            "logging_usage": len(re.findall(r"\b(logging|logger)\b", content)),
            "error_handling": len(re.findall(r"\b(raise|except|assert)\b", content)),
            "test_patterns": len(
                re.findall(r"\b(test_|assert|mock|fixture)\b", content)
            ),
        }

    def _apply_layer_analysis(self, layer_name, features):
        """Apply layer-specific analysis similar to neural network layers"""
        directory_mappings = {
            "syntactic": {
                "high_class_count": "libs/",
                "high_function_count": "libs/",
                "high_async_usage": "workers/",
                "high_decorator_usage": "web/",
            },
            "semantic": {
                "web": "web/",
                "data": "libs/",
                "worker": "workers/",
                "api": "web/",
                "config": "config/",
                "monitoring": "libs/",
            },
            "structural": {
                "long_files": "libs/",
                "short_files": "scripts/",
                "highly_documented": "libs/",
                "simple_structure": "scripts/",
            },
            "behavioral": {
                "high_io": "scripts/",
                "high_network": "web/",
                "high_database": "libs/",
                "high_concurrency": "workers/",
                "high_testing": "tests/",
            },
        }

        predictions = []

        if layer_name == "syntactic":
            if features.get("class_defs", 0) > 2:
                predictions.append(("libs/", 0.7, "multiple class definitions"))
            if features.get("async_keywords", 0) > 3:
                predictions.append(("workers/", 0.8, "heavy async usage"))
            if features.get("decorators", 0) > 2:
                predictions.append(("web/", 0.6, "decorator patterns"))

        elif layer_name == "semantic":
            for domain, score in features.items():
                if score > 2:
                    target_dir = directory_mappings["semantic"].get(domain, "libs/")
                    confidence = min(0.9, score * 0.1)
                    predictions.append(
                        (target_dir, confidence, f"{domain} domain focus")
                    )

        elif layer_name == "structural":
            file_length = features.get("file_length", 0)
            if file_length > 200:
                predictions.append(("libs/", 0.6, "complex file structure"))
            elif file_length < 50:
                predictions.append(("scripts/", 0.7, "simple file structure"))

        elif layer_name == "behavioral":
            if features.get("concurrency_usage", 0) > 1:
                predictions.append(("workers/", 0.8, "concurrency patterns"))
            if features.get("network_operations", 0) > 2:
                predictions.append(("web/", 0.7, "network operations"))
            if features.get("test_patterns", 0) > 3:
                predictions.append(("tests/", 0.9, "test patterns"))

        # Return the highest confidence prediction
        if predictions:
            best_prediction = max(predictions, key=lambda x: x[1])
            return {
                "directory": best_prediction[0],
                "confidence": best_prediction[1],
                "reasoning": best_prediction[2],
            }

        return None
