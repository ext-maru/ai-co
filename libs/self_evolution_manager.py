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
        """複数の手法で配置候補を分析"""
        candidates = []
        
        # 1. 従来のルールベース
        rule_based_dir = self.analyze_file_type(filename, content)
        candidates.append({
            'dir': rule_based_dir,
            'score': 0.7,
            'method': 'rule_based',
            'reason': 'Traditional pattern matching'
        })
        
        # 2. 内容類似度ベース
        similarity_candidates = self._analyze_content_similarity(content)
        candidates.extend(similarity_candidates)
        
        # 3. 機械学習予測
        ml_candidates = self._ml_predict_placement(filename, content)
        candidates.extend(ml_candidates)
        
        # 4. 統計的パターン分析
        pattern_candidates = self._analyze_statistical_patterns(filename, content)
        candidates.extend(pattern_candidates)
        
        # スコアでソート
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 重複削除
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
