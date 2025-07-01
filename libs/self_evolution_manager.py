#!/usr/bin/env python3
"""
AI Company 自己進化ファイル配置マネージャー
AIが生成したファイルを適切な場所に自動配置して自己改良を実現
Enhanced with ML-based intelligent placement
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
import logging
import shutil
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import sqlite3

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
            r'.*_worker\.py$': 'workers/',
            r'.*_manager\.py$': 'libs/',
            r'.*_notifier\.py$': 'libs/',
            r'.*_db\.py$': 'libs/',
            r'send_.*\.py$': 'scripts/',
            r'setup_.*\.py$': 'scripts/',
            r'test_.*\.py$': 'tests/',
            
            # 設定ファイル系
            r'.*\.conf$': 'config/',
            r'config\..*': 'config/',
            r'.*\.env$': 'config/',
            
            # シェルスクリプト系
            r'.*\.sh$': 'scripts/',
            r'start_.*\.sh$': 'scripts/',
            r'setup_.*\.sh$': 'scripts/',
            
            # Web系
            r'.*\.html$': 'web/',
            r'.*\.css$': 'web/css/',
            r'.*\.js$': 'web/js/',
            
            # ドキュメント系
            r'.*\.md$': 'docs/',
            r'README.*': 'docs/',
            
            # データ系
            r'.*\.json$': 'data/',
            r'.*\.csv$': 'data/',
            r'.*\.sql$': 'data/',
            
            # 新機能プロトタイプ
            r'prototype_.*\.py$': 'prototypes/',
            r'experimental_.*\.py$': 'experimental/',
        }
        
        # 特殊な配置ルール（内容解析ベース）
        self.content_based_rules = {
            'import pika': 'workers/',
            'import flask': 'web/',
            'import fastapi': 'api/',
            'class.*Worker': 'workers/',
            'class.*Manager': 'libs/',
            'class.*Notifier': 'libs/',
            'def send_task': 'scripts/',
            '#!/bin/bash': 'scripts/',
        }
        
        # 機械学習ベース配置ルール設定
        self.ml_features = {
            'import_statements': [],
            'class_patterns': [],
            'function_patterns': [],
            'file_size_ranges': [],
            'content_similarity': []
        }
        
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
        if suffix == '.py':
            return 'libs/'  # Pythonファイルデフォルト
        elif suffix == '.sh':
            return 'scripts/'  # シェルスクリプトデフォルト
        elif suffix in ['.txt', '.log']:
            return 'output/'  # ログ・テキストファイル
        
        # 4. 最終フォールバック
        logger.warning(f"配置先不明: {file_name} → output/misc/")
        return 'output/misc/'
    
    def auto_place_file(self, source_content, suggested_filename=None, task_id=None):
        """
        Enhanced intelligent file placement with ML-based analysis
        
        Args:
            source_content: ファイル内容
            suggested_filename: 推奨ファイル名
            task_id: タスクID
            
        Returns:
            dict: 配置結果
        """
        try:
            # ファイル名決定
            if suggested_filename:
                filename = suggested_filename
            else:
                filename = self._guess_filename_from_content(source_content)
            
            # 多段階配置先決定
            placement_candidates = self._analyze_placement_candidates(filename, source_content)
            
            # 最適配置先選択
            target_relative_dir = self._select_optimal_placement(placement_candidates, source_content)
            target_dir = self.project_root / target_relative_dir
            target_file = target_dir / filename
            
            # ディレクトリ作成
            self._ensure_directory(target_dir)
            
            # 既存ファイルのバックアップ
            if target_file.exists():
                backup_path = self._create_backup(target_file)
                logger.info(f"既存ファイルバックアップ: {backup_path}")
            
            # ファイル書き込み
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(source_content)
            
            # 実行権限付与（.pyや.shファイル）
            if filename.endswith(('.py', '.sh')):
                os.chmod(target_file, 0o755)
            
            # 配置結果を学習データに追加
            self._record_placement_learning(filename, source_content, target_relative_dir, placement_candidates)
            
            result = {
                "success": True,
                "file_path": str(target_file),
                "relative_path": str(target_file.relative_to(self.project_root)),
                "target_dir": target_relative_dir,
                "filename": filename,
                "size": len(source_content),
                "task_id": task_id,
                "placed_at": datetime.now().isoformat(),
                "placement_confidence": self._calculate_placement_confidence(placement_candidates, target_relative_dir),
                "alternatives": [{"dir": pc["dir"], "score": pc["score"]} for pc in placement_candidates[:3]]
            }
            
            logger.info(f"自己進化配置成功: {result['relative_path']} (confidence: {result['placement_confidence']:.2f})")
            return result
            
        except Exception as e:
            error_msg = f"自己配置エラー: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _guess_filename_from_content(self, content):
        """内容からファイル名を推測"""
        lines = content.split('\n')
        
        # クラス名から推測
        for line in lines:
            if 'class ' in line:
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    class_name = match.group(1)
                    # CamelCase → snake_case 変換
                    snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
                    return f"{snake_name}.py"
        
        # 関数名から推測
        for line in lines:
            if line.startswith('def ') and not line.startswith('def __'):
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    func_name = match.group(1)
                    return f"{func_name}.py"
        
        # シェルスクリプト判定
        if content.startswith('#!/bin/bash'):
            return f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
        
        # デフォルト
        return f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    def _ensure_directory(self, dir_path):
        """ディレクトリ確保"""
        dir_path.mkdir(parents=True, exist_ok=True)
        os.chmod(dir_path, 0o775)
    
    def _create_backup(self, file_path):
        """既存ファイルのバックアップ作成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'{file_path.suffix}.backup_{timestamp}')
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
            "would_backup": target_path.exists()
        }
    
    def list_evolution_candidates(self):
        """自己進化候補ファイルリスト"""
        output_dir = self.project_root / "output"
        candidates = []
        
        for file_path in output_dir.rglob("*.py"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            preview = self.get_placement_preview(content, file_path.name)
            candidates.append({
                "current_path": str(file_path),
                "suggested_placement": preview,
                "size": file_path.stat().st_size
            })
        
        return candidates
    
    # ML-Based Enhancement Methods
    
    def _init_learning_db(self):
        """学習データベース初期化"""
        try:
            self.learning_db_path.parent.mkdir(exist_ok=True)
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    content_hash TEXT,
                    content_features TEXT,
                    target_dir TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_similarities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT,
                    similar_files TEXT,
                    similarity_scores TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
            
            cursor.execute('''
                SELECT target_dir, content_features, confidence 
                FROM placement_history 
                ORDER BY created_at DESC LIMIT 1000
            ''')
            
            for row in cursor.fetchall():
                target_dir, features_json, confidence = row
                try:
                    features = json.loads(features_json)
                    self.placement_history[target_dir].append({
                        'features': features,
                        'confidence': confidence
                    })
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
        rule_confidence = self._calculate_rule_confidence(filename, content, rule_based_dir)
        candidates.append({
            'dir': rule_based_dir,
            'score': 0.6 + (rule_confidence * 0.3),
            'method': 'rule_based',
            'reason': f'Pattern matching (confidence: {rule_confidence:.2f})'
        })
        
        # 2. 内容類似度ベース (改良版)
        similarity_candidates = self._analyze_content_similarity_enhanced(content)
        candidates.extend(similarity_candidates)
        
        # 3. 機械学習予測 (強化版)
        ml_candidates = self._ml_predict_placement_enhanced(filename, content)
        candidates.extend(ml_candidates)
        
        # 4. 統計的パターン分析 (改良版)
        pattern_candidates = self._analyze_statistical_patterns_enhanced(filename, content)
        candidates.extend(pattern_candidates)
        
        # 5. 新機能: 依存関係分析
        dependency_candidates = self._analyze_dependency_patterns(content)
        candidates.extend(dependency_candidates)
        
        # 6. 新機能: 意味的類似度分析
        semantic_candidates = self._analyze_semantic_similarity(filename, content)
        candidates.extend(semantic_candidates)
        
        # アンサンブル手法でスコア統合
        candidates = self._ensemble_scoring(candidates)
        
        # 重複削除とランキング
        seen_dirs = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate['dir'] not in seen_dirs:
                unique_candidates.append(candidate)
                seen_dirs.add(candidate['dir'])
        
        return unique_candidates[:5]
    
    def _analyze_content_similarity(self, content: str) -> List[Dict]:
        """既存ファイルとの内容類似度分析"""
        candidates = []
        content_features = self._extract_content_features(content)
        
        # 既存ファイルとの類似度計算
        similar_placements = self._find_similar_files(content_features)
        
        for placement, similarity in similar_placements:
            candidates.append({
                'dir': placement,
                'score': 0.5 + (similarity * 0.4),
                'method': 'content_similarity',
                'reason': f'Similar to existing files (similarity: {similarity:.2f})'
            })
        
        return candidates
    
    def _ml_predict_placement(self, filename: str, content: str) -> List[Dict]:
        """機械学習による配置予測"""
        candidates = []
        
        # 簡易特徴量抽出
        features = self._extract_ml_features(filename, content)
        
        # 履歴ベースの予測
        predictions = self._predict_from_history(features)
        
        for prediction, confidence in predictions:
            candidates.append({
                'dir': prediction,
                'score': 0.3 + (confidence * 0.5),
                'method': 'ml_prediction',
                'reason': f'ML prediction (confidence: {confidence:.2f})'
            })
        
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
                candidates.append({
                    'dir': dir_path,
                    'score': score,
                    'method': 'statistical_pattern',
                    'reason': f'Pattern "{pattern}" appears {frequency} times in {dir_path}'
                })
        
        return candidates
    
    def _extract_content_features(self, content: str) -> Dict:
        """内容特徴量抽出"""
        features = {
            'imports': re.findall(r'^\s*(?:from|import)\s+([^\s]+)', content, re.MULTILINE),
            'classes': re.findall(r'class\s+(\w+)', content),
            'functions': re.findall(r'def\s+(\w+)', content),
            'keywords': re.findall(r'\b(async|await|worker|task|manager|db|api|web)\b', content.lower()),
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'complexity': len(re.findall(r'\b(if|for|while|try|except)\b', content))
        }
        return features
    
    def _extract_ml_features(self, filename: str, content: str) -> Dict:
        """機械学習用特徴量抽出"""
        features = self._extract_content_features(content)
        
        # ファイル名特徴
        features.update({
            'filename_length': len(filename),
            'has_underscore': '_' in filename,
            'extension': Path(filename).suffix,
            'name_parts': filename.replace('.', '_').split('_'),
        })
        
        return features
    
    def _find_similar_files(self, features: Dict) -> List[Tuple[str, float]]:
        """類似ファイル検索"""
        similarities = []
        
        # 全プロジェクトファイルとの比較
        for dir_path in ['workers/', 'libs/', 'scripts/', 'config/', 'data/']:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue
                
            for file_path in target_dir.glob('*.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    
                    existing_features = self._extract_content_features(existing_content)
                    similarity = self._calculate_feature_similarity(features, existing_features)
                    
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
        imports1 = set(features1.get('imports', []))
        imports2 = set(features2.get('imports', []))
        if imports1 or imports2:
            import_sim = len(imports1 & imports2) / len(imports1 | imports2) if imports1 | imports2 else 0
            similarities.append(import_sim * 0.3)
        
        # キーワード類似度
        keywords1 = set(features1.get('keywords', []))
        keywords2 = set(features2.get('keywords', []))
        if keywords1 or keywords2:
            keyword_sim = len(keywords1 & keywords2) / len(keywords1 | keywords2) if keywords1 | keywords2 else 0
            similarities.append(keyword_sim * 0.2)
        
        # サイズ類似度
        size1 = features1.get('file_size', 0)
        size2 = features2.get('file_size', 0)
        if size1 > 0 and size2 > 0:
            size_sim = 1 - abs(size1 - size2) / max(size1, size2)
            similarities.append(size_sim * 0.1)
        
        # 複雑度類似度
        comp1 = features1.get('complexity', 0)
        comp2 = features2.get('complexity', 0)
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
                similarity = self._calculate_feature_similarity(features, item['features'])
                if similarity > 0.2:
                    total_score += similarity * item['confidence']
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
        for dir_path in ['workers/', 'libs/', 'scripts/', 'config/']:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue
                
            for file_path in target_dir.glob('*'):
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
            r'class\s+\w*Worker',
            r'class\s+\w*Manager', 
            r'class\s+\w*Notifier',
            r'def\s+send_\w+',
            r'import\s+pika',
            r'from\s+flask',
            r'#!/bin/bash'
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
        parts1 = re.split(r'[_\-\.]', name1.lower())
        parts2 = re.split(r'[_\-\.]', name2.lower())
        
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
            
            cursor.execute('''
                SELECT target_dir, COUNT(*) as count
                FROM placement_history 
                WHERE content_features LIKE ?
                GROUP BY target_dir
            ''', (f'%{pattern}%',))
            
            for row in cursor.fetchall():
                target_dir, count = row
                placements[target_dir] = count
                
            conn.close()
        except Exception:
            pass
        
        return dict(placements)
    
    def _calculate_rule_confidence(self, filename: str, content: str, target_dir: str) -> float:
        """ルールベース配置の信頼度計算"""
        confidence = 0.5
        
        # ファイル名マッチの強度
        for pattern, rule_dir in self.placement_rules.items():
            if rule_dir == target_dir and re.match(pattern, filename, re.IGNORECASE):
                confidence += 0.3
                break
        
        # 内容マッチの強度
        for keyword, rule_dir in self.content_based_rules.items():
            if rule_dir == target_dir and re.search(keyword, content, re.IGNORECASE | re.MULTILINE):
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
        similar_placements = self._find_similar_files_enhanced(content_features, content_vector)
        
        for placement, similarity, method in similar_placements:
            candidates.append({
                'dir': placement,
                'score': 0.4 + (similarity * 0.5),
                'method': f'enhanced_similarity_{method}',
                'reason': f'Enhanced similarity ({method}: {similarity:.3f})'
            })
        
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
        vote_counts = defaultdict(lambda: {'count': 0, 'total_confidence': 0})
        for prediction, confidence in all_predictions:
            vote_counts[prediction]['count'] += 1
            vote_counts[prediction]['total_confidence'] += confidence
        
        for prediction, data in vote_counts.items():
            avg_confidence = data['total_confidence'] / data['count']
            vote_weight = min(1.0, data['count'] / 3.0)
            final_score = 0.3 + (avg_confidence * vote_weight * 0.4)
            
            candidates.append({
                'dir': prediction,
                'score': final_score,
                'method': 'enhanced_ml_ensemble',
                'reason': f'ML ensemble ({data["count"]} votes, avg_conf: {avg_confidence:.2f})'
            })
        
        return candidates
    
    def _analyze_statistical_patterns_enhanced(self, filename: str, content: str) -> List[Dict]:
        """改良版統計的パターン分析 - 時系列・頻度・相関分析"""
        candidates = []
        
        # 時系列パターン分析
        temporal_patterns = self._analyze_temporal_patterns(filename, content)
        
        # 頻度パターン分析 (改良版)
        frequency_patterns = self._analyze_frequency_patterns_enhanced(filename, content)
        
        # 相関パターン分析
        correlation_patterns = self._analyze_correlation_patterns(filename, content)
        
        # 統合スコア計算
        all_patterns = {**temporal_patterns, **frequency_patterns, **correlation_patterns}
        
        for pattern_type, pattern_data in all_patterns.items():
            for dir_path, score_data in pattern_data.items():
                score = score_data.get('score', 0)
                evidence = score_data.get('evidence', '')
                
                candidates.append({
                    'dir': dir_path,
                    'score': min(0.85, score),
                    'method': f'enhanced_statistics_{pattern_type}',
                    'reason': f'Statistical pattern ({pattern_type}): {evidence}'
                })
        
        return candidates
    
    def _analyze_dependency_patterns(self, content: str) -> List[Dict]:
        """依存関係パターン分析"""
        candidates = []
        
        # インポート依存関係分析
        imports = re.findall(r'^\s*(?:from|import)\s+([^\s]+)', content, re.MULTILINE)
        
        dependency_mapping = {
            'pika': 'workers/',
            'flask': 'web/',
            'fastapi': 'api/',
            'sqlalchemy': 'libs/',
            'sqlite3': 'libs/',
            'requests': 'libs/',
            'logging': 'libs/',
            'os': 'scripts/',
            'sys': 'scripts/',
            'pathlib': 'libs/',
            'datetime': 'libs/',
            'json': 'libs/',
            'threading': 'workers/',
            'multiprocessing': 'workers/',
            'psutil': 'workers/',
        }
        
        dependency_scores = defaultdict(float)
        for imp in imports:
            base_module = imp.split('.')[0]
            if base_module in dependency_mapping:
                target_dir = dependency_mapping[base_module]
                dependency_scores[target_dir] += 0.15
        
        for dir_path, score in dependency_scores.items():
            candidates.append({
                'dir': dir_path,
                'score': min(0.8, score),
                'method': 'dependency_analysis',
                'reason': f'Dependency pattern (score: {score:.2f})'
            })
        
        return candidates
    
    def _analyze_semantic_similarity(self, filename: str, content: str) -> List[Dict]:
        """意味的類似度分析 - 簡易版"""
        candidates = []
        
        # キーワード群による意味的分類
        semantic_clusters = {
            'worker_cluster': {
                'keywords': ['worker', 'task', 'queue', 'job', 'process', 'background', 'async', 'celery', 'pika'],
                'target': 'workers/',
                'weight': 0.1
            },
            'web_cluster': {
                'keywords': ['web', 'http', 'flask', 'fastapi', 'api', 'route', 'endpoint', 'server', 'request'],
                'target': 'web/',
                'weight': 0.1
            },
            'data_cluster': {
                'keywords': ['database', 'db', 'sql', 'model', 'schema', 'table', 'query', 'orm'],
                'target': 'libs/',
                'weight': 0.1
            },
            'config_cluster': {
                'keywords': ['config', 'setting', 'environment', 'env', 'parameter', 'option'],
                'target': 'config/',
                'weight': 0.1
            },
            'script_cluster': {
                'keywords': ['script', 'automation', 'setup', 'install', 'deploy', 'build', 'run'],
                'target': 'scripts/',
                'weight': 0.1
            }
        }
        
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        for cluster_name, cluster_data in semantic_clusters.items():
            score = 0
            matched_keywords = []
            
            for keyword in cluster_data['keywords']:
                # ファイル名での出現
                if keyword in filename_lower:
                    score += cluster_data['weight'] * 2
                    matched_keywords.append(f"filename:{keyword}")
                
                # 内容での出現
                content_matches = len(re.findall(r'\b' + keyword + r'\b', content_lower))
                if content_matches > 0:
                    score += cluster_data['weight'] * min(3, content_matches)
                    matched_keywords.append(f"content:{keyword}({content_matches})")
            
            if score > 0.2:
                candidates.append({
                    'dir': cluster_data['target'],
                    'score': min(0.75, score),
                    'method': 'semantic_analysis',
                    'reason': f'Semantic cluster ({cluster_name}): {", ".join(matched_keywords[:3])}'
                })
        
        return candidates
    
    def _ensemble_scoring(self, candidates: List[Dict]) -> List[Dict]:
        """アンサンブル手法によるスコア統合"""
        # 手法別の重み
        method_weights = {
            'rule_based': 0.25,
            'enhanced_similarity_tfidf': 0.20,
            'enhanced_similarity_cosine': 0.15,
            'enhanced_ml_ensemble': 0.20,
            'enhanced_statistics_temporal': 0.05,
            'enhanced_statistics_frequency': 0.05,
            'enhanced_statistics_correlation': 0.05,
            'dependency_analysis': 0.15,
            'semantic_analysis': 0.10
        }
        
        # デフォルト重み
        default_weight = 0.1
        
        # 重み付きスコア計算
        for candidate in candidates:
            method = candidate['method']
            weight = method_weights.get(method, default_weight)
            candidate['weighted_score'] = candidate['score'] * weight
            candidate['original_score'] = candidate['score']
            candidate['score'] = candidate['weighted_score']
        
        # スコアでソート
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates
    
    def _extract_content_features_enhanced(self, content: str) -> Dict:
        """強化版特徴量抽出"""
        features = self._extract_content_features(content)
        
        # 追加特徴量
        features.update({
            'docstring_count': len(re.findall(r'""".*?"""', content, re.DOTALL)),
            'comment_count': len(re.findall(r'#.*', content)),
            'decorator_count': len(re.findall(r'@\w+', content)),
            'async_functions': len(re.findall(r'async\s+def', content)),
            'lambda_count': len(re.findall(r'lambda\s+', content)),
            'comprehension_count': len(re.findall(r'\[.*for.*in.*\]', content)),
            'exception_handling': len(re.findall(r'try:|except:|finally:', content)),
            'context_managers': len(re.findall(r'with\s+', content)),
        })
        
        return features
    
    def _vectorize_content(self, content: str) -> List[float]:
        """内容のベクトル化 - 簡易TF-IDF"""
        # 重要単語の抽出
        important_words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', content.lower())
        word_counts = Counter(important_words)
        
        # 上位30個の単語でベクトル化
        top_words = [word for word, count in word_counts.most_common(30)]
        vector = [word_counts.get(word, 0) for word in top_words]
        
        # 正規化
        total = sum(vector) if sum(vector) > 0 else 1
        return [v / total for v in vector]
    
    def _find_similar_files_enhanced(self, features: Dict, content_vector: List[float]) -> List[Tuple[str, float, str]]:
        """強化版類似ファイル検索"""
        similarities = []
        
        for dir_path in ['workers/', 'libs/', 'scripts/', 'config/', 'data/', 'web/']:
            target_dir = self.project_root / dir_path
            if not target_dir.exists():
                continue
                
            for file_path in target_dir.glob('*.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    
                    # 特徴量類似度
                    existing_features = self._extract_content_features_enhanced(existing_content)
                    feature_similarity = self._calculate_feature_similarity(features, existing_features)
                    
                    # ベクトル類似度
                    existing_vector = self._vectorize_content(existing_content)
                    vector_similarity = self._cosine_similarity(content_vector, existing_vector)
                    
                    if feature_similarity > 0.3:
                        similarities.append((dir_path, feature_similarity, 'feature'))
                    if vector_similarity > 0.3:
                        similarities.append((dir_path, vector_similarity, 'vector'))
                        
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
        features.update({
            'import_diversity': len(set(features.get('imports', []))),
            'function_class_ratio': len(features.get('functions', [])) / max(1, len(features.get('classes', []))),
            'complexity_density': features.get('complexity', 0) / max(1, features.get('line_count', 1)),
            'keyword_density': len(features.get('keywords', [])) / max(1, features.get('line_count', 1)),
            'has_main_block': '__name__ == "__main__"' in content,
            'has_shebang': content.startswith('#!'),
            'is_executable_script': content.startswith('#!') or '__name__ == "__main__"' in content,
        })
        
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
                
                similarity = self._calculate_feature_similarity(features, item['features'])
                if similarity > 0.2:
                    weighted_score += similarity * item['confidence'] * time_weight
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
                'conditions': [
                    lambda f: 'worker' in f.get('name_parts', []),
                    lambda f: 'pika' in f.get('imports', []),
                    lambda f: f.get('async_functions', 0) > 0
                ],
                'target': 'workers/',
                'weight': 0.8
            },
            # Manager判定
            {
                'conditions': [
                    lambda f: 'manager' in f.get('name_parts', []),
                    lambda f: any('Manager' in cls for cls in f.get('classes', [])),
                    lambda f: f.get('complexity', 0) > 5
                ],
                'target': 'libs/',
                'weight': 0.7
            },
            # Script判定
            {
                'conditions': [
                    lambda f: f.get('has_main_block', False),
                    lambda f: f.get('is_executable_script', False),
                    lambda f: f.get('line_count', 0) < 100
                ],
                'target': 'scripts/',
                'weight': 0.6
            },
            # Web判定
            {
                'conditions': [
                    lambda f: 'flask' in f.get('imports', []),
                    lambda f: 'fastapi' in f.get('imports', []),
                    lambda f: any('route' in func for func in f.get('functions', []))
                ],
                'target': 'web/',
                'weight': 0.8
            }
        ]
        
        for rule in rules:
            satisfied_conditions = sum(1 for condition in rule['conditions'] if condition(features))
            if satisfied_conditions > 0:
                confidence = (satisfied_conditions / len(rule['conditions'])) * rule['weight']
                predictions.append((rule['target'], confidence))
        
        return predictions
    
    def _knn_predict(self, features: Dict) -> List[Tuple[str, float]]:
        """K近傍法による予測"""
        predictions = []
        k = 5  # 近傍数
        
        # 全履歴から最も類似する k 個を見つける
        all_similarities = []
        for target_dir, history_items in self.placement_history.items():
            for item in history_items:
                similarity = self._calculate_feature_similarity(features, item['features'])
                if similarity > 0.1:
                    all_similarities.append((target_dir, similarity, item['confidence']))
        
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
            cursor.execute('''
                SELECT target_dir, COUNT(*) as count,
                       AVG(confidence) as avg_confidence
                FROM placement_history 
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY target_dir
                HAVING count > 1
                ORDER BY count DESC
            ''')
            
            recent_trends = cursor.fetchall()
            
            for target_dir, count, avg_confidence in recent_trends:
                score = min(0.6, (count / 10.0) * avg_confidence)
                patterns['recent_trend'] = patterns.get('recent_trend', {})
                patterns['recent_trend'][target_dir] = {
                    'score': score,
                    'evidence': f'{count} recent placements, avg_conf: {avg_confidence:.2f}'
                }
            
            conn.close()
        except Exception:
            pass
            
        return patterns
    
    def _analyze_frequency_patterns_enhanced(self, filename: str, content: str) -> Dict:
        """強化版頻度パターン分析"""
        patterns = {}
        
        # ファイル名パターンの頻度分析
        name_parts = filename.replace('.', '_').split('_')
        for part in name_parts:
            if len(part) > 2:
                part_patterns = self._analyze_filename_patterns(part)
                if part_patterns:
                    patterns[f'name_part_{part}'] = part_patterns
        
        # 内容キーワードの頻度分析
        important_keywords = re.findall(r'\b(class|def|import|from|async|worker|manager|task|api|web|db|config)\b', content.lower())
        keyword_counter = Counter(important_keywords)
        
        for keyword, count in keyword_counter.most_common(5):
            if count > 1:
                keyword_patterns = self._get_pattern_placements(keyword)
                if keyword_patterns:
                    patterns[f'keyword_{keyword}'] = {
                        dir_path: {
                            'score': min(0.5, (freq / 20.0) * (count / 10.0)),
                            'evidence': f'keyword "{keyword}" appears {count} times'
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
                'name_pattern': 'worker',
                'content_pattern': 'pika',
                'target': 'workers/',
                'correlation_strength': 0.8
            },
            # ファイル名に"manager"があり、内容に"class"がある場合
            {
                'name_pattern': 'manager',
                'content_pattern': 'class.*manager',
                'target': 'libs/',
                'correlation_strength': 0.7
            },
            # ファイル名に"api"があり、内容に"flask|fastapi"がある場合
            {
                'name_pattern': 'api|web',
                'content_pattern': 'flask|fastapi',
                'target': 'web/',
                'correlation_strength': 0.8
            }
        ]
        
        for rule in correlation_rules:
            name_match = re.search(rule['name_pattern'], filename_lower)
            content_match = re.search(rule['content_pattern'], content_lower)
            
            if name_match and content_match:
                patterns['correlation'] = patterns.get('correlation', {})
                patterns['correlation'][rule['target']] = {
                    'score': rule['correlation_strength'],
                    'evidence': f'Name-content correlation: {rule["name_pattern"]} + {rule["content_pattern"]}'
                }
        
        return patterns
    
    def _select_optimal_placement(self, candidates: List[Dict], content: str) -> str:
        """最適配置先選択"""
        if not candidates:
            return 'output/misc/'
        
        # 最高スコアの候補を選択
        best_candidate = candidates[0]
        
        # 追加的な検証
        if best_candidate['score'] < 0.5:
            # 信頼度が低い場合は安全な場所に配置
            if 'class' in content and 'Worker' in content:
                return 'workers/'
            elif 'class' in content and 'Manager' in content:
                return 'libs/'
            else:
                return 'output/misc/'
        
        return best_candidate['dir']
    
    def _calculate_placement_confidence(self, candidates: List[Dict], selected_dir: str) -> float:
        """配置信頼度計算"""
        if not candidates:
            return 0.0
        
        selected_candidate = next((c for c in candidates if c['dir'] == selected_dir), None)
        if not selected_candidate:
            return 0.0
        
        # トップ候補との差を考慮
        top_score = candidates[0]['score']
        selected_score = selected_candidate['score']
        
        # 複数手法の一致度を考慮
        method_diversity = len(set(c['method'] for c in candidates[:3]))
        diversity_bonus = min(0.2, method_diversity * 0.1)
        
        return min(1.0, selected_score + diversity_bonus)
    
    def _record_placement_learning(self, filename: str, content: str, target_dir: str, candidates: List[Dict]):
        """配置学習データ記録"""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            features = self._extract_content_features(content)
            confidence = self._calculate_placement_confidence(candidates, target_dir)
            
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO placement_history 
                (filename, content_hash, content_features, target_dir, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, content_hash, json.dumps(features), target_dir, confidence))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Recorded placement learning: {filename} -> {target_dir} (confidence: {confidence:.2f})")
        except Exception as e:
            logger.error(f"Failed to record placement learning: {e}")
    
    def get_placement_analytics(self) -> Dict:
        """配置分析レポート"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            # 基本統計
            cursor.execute('SELECT COUNT(*) FROM placement_history')
            total_placements = cursor.fetchone()[0]
            
            # ディレクトリ別統計
            cursor.execute('''
                SELECT target_dir, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM placement_history 
                GROUP BY target_dir 
                ORDER BY count DESC
            ''')
            dir_stats = cursor.fetchall()
            
            # 最近の配置統計
            cursor.execute('''
                SELECT target_dir, COUNT(*) as count
                FROM placement_history 
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY target_dir
            ''')
            recent_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_placements': total_placements,
                'directory_stats': [{'dir': d[0], 'count': d[1], 'avg_confidence': d[2]} for d in dir_stats],
                'recent_activity': [{'dir': d[0], 'count': d[1]} for d in recent_stats],
                'learning_db_size': self.learning_db_path.stat().st_size if self.learning_db_path.exists() else 0
            }
        except Exception as e:
            logger.error(f"Failed to get placement analytics: {e}")
            return {'error': str(e)}
    
    def test_enhanced_placement(self, test_content: str, test_filename: str = None) -> Dict:
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
            'filename': test_filename,
            'selected_placement': selected_dir,
            'confidence': confidence,
            'candidates': candidates,
            'analysis_methods': {
                'rule_based': sum(1 for c in candidates if 'rule_based' in c['method']),
                'similarity': sum(1 for c in candidates if 'similarity' in c['method']),
                'ml_prediction': sum(1 for c in candidates if 'ml' in c['method']),
                'statistical': sum(1 for c in candidates if 'statistics' in c['method']),
                'dependency': sum(1 for c in candidates if 'dependency' in c['method']),
                'semantic': sum(1 for c in candidates if 'semantic' in c['method'])
            },
            'content_features': self._extract_content_features_enhanced(test_content),
            'content_size': len(test_content),
            'content_lines': len(test_content.split('\n'))
        }
        
        return analysis
