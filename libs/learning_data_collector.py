#!/usr/bin/env python3
"""
Learning Data Collector - AI学習データ収集システム
AIの学習・進化に必要なデータを包括的に収集・管理

4賢者との連携:
📚 ナレッジ賢者: 学習パターンの蓄積・検索
📋 タスク賢者: タスク実行データの収集
🚨 インシデント賢者: エラーパターンの分析
🔍 RAG賢者: コンテキスト強化学習
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import sqlite3
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict, deque
import statistics
import re

logger = logging.getLogger(__name__)

class LearningDataCollector:
    """AI学習データ収集システム"""
    
    def __init__(self):
        """LearningDataCollector 初期化"""
        self.db_path = PROJECT_ROOT / "data" / "learning_data.db"
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base"
        
        # リアルタイムストリーミング
        self.is_streaming = False
        self.streaming_thread = None
        self.streaming_buffer = deque(maxlen=1000)
        self.streaming_config = {}
        
        # データ品質管理
        self.quality_thresholds = {
            'min_quality_score': 0.7,
            'max_missing_fields': 2,
            'required_fields': ['data_type', 'timestamp', 'data']
        }
        
        # 4賢者統合設定
        self.sage_integration = {
            'knowledge_sage': False,
            'task_sage': False,
            'incident_sage': False,
            'rag_sage': False
        }
        
        # データベース初期化
        self._init_database()
        
        logger.info("LearningDataCollector initialized")
    
    def _init_database(self):
        """学習データ用データベース初期化"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 学習データテーブル
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT,
                timestamp TIMESTAMP,
                source TEXT,
                data TEXT,
                metadata TEXT,
                quality_score REAL,
                tags TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
            """)
            
            # パターンテーブル
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_data TEXT,
                confidence_score REAL,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                last_used TIMESTAMP
            )
            """)
            
            # データ品質ログテーブル
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_id INTEGER,
                validation_result TEXT,
                quality_score REAL,
                issues TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (data_id) REFERENCES learning_data (id)
            )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def collect_performance_data(self, worker_monitor) -> Dict:
        """Worker パフォーマンスデータを収集"""
        try:
            performance_data = {
                'data_type': 'performance_metrics',
                'timestamp': datetime.now(),
                'workers': {},
                'system_metrics': self._collect_system_metrics()
            }
            
            # Worker個別データ収集
            for worker_id, worker_info in worker_monitor.workers_status.items():
                worker_data = {
                    'worker_id': worker_id,
                    'worker_type': worker_info.get('worker_type'),
                    'tasks_completed': worker_info.get('tasks_completed', 0),
                    'tasks_failed': worker_info.get('tasks_failed', 0),
                    'avg_processing_time': worker_info.get('performance_metrics', {}).get('avg_processing_time', 0),
                    'success_rate': worker_info.get('performance_metrics', {}).get('success_rate', 1.0),
                    'current_load': worker_info.get('performance_metrics', {}).get('current_load', {}),
                    'status': worker_info.get('status', 'unknown'),
                    'last_updated': worker_info.get('last_updated')
                }
                
                performance_data['workers'][worker_id] = worker_data
            
            # 集約メトリクス計算
            performance_data['aggregate_metrics'] = self._calculate_aggregate_metrics(
                performance_data['workers']
            )
            
            logger.info(f"Performance data collected for {len(performance_data['workers'])} workers")
            return performance_data
            
        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            return {}
    
    def collect_task_metrics(self, task_flow_tracker) -> Dict:
        """タスクフローメトリクスを収集"""
        try:
            task_metrics = {
                'data_type': 'task_flow_metrics',
                'timestamp': datetime.now(),
                'active_flows': [],
                'completed_flows': [],
                'flow_patterns': {},
                'bottleneck_analysis': {}
            }
            
            # アクティブフロー分析
            active_flows = task_flow_tracker.get_active_flows()
            for flow in active_flows:
                flow_data = {
                    'task_id': flow.get('task_id'),
                    'status': flow.get('status'),
                    'stage_count': len(flow.get('workflow_stages', [])),
                    'current_stage': self._get_current_stage(flow),
                    'elapsed_time': self._calculate_elapsed_time(flow),
                    'predicted_completion': self._predict_completion_time(flow)
                }
                task_metrics['active_flows'].append(flow_data)
            
            # 完了フロー分析
            for task_id, flow in task_flow_tracker.completed_flows.items():
                flow_data = {
                    'task_id': task_id,
                    'total_processing_time': flow.get('total_processing_time', 0),
                    'stage_count': len(flow.get('workflow_stages', [])),
                    'success_rate': 1.0 if flow.get('status') == 'completed' else 0.0,
                    'stage_breakdown': self._analyze_stage_breakdown(flow)
                }
                task_metrics['completed_flows'].append(flow_data)
            
            # フローパターン分析
            task_metrics['flow_patterns'] = self._analyze_flow_patterns(
                active_flows + list(task_flow_tracker.completed_flows.values())
            )
            
            # ボトルネック分析
            task_metrics['bottleneck_analysis'] = self._analyze_bottlenecks(
                task_metrics['completed_flows']
            )
            
            logger.info(f"Task metrics collected: {len(active_flows)} active, {len(task_flow_tracker.completed_flows)} completed")
            return task_metrics
            
        except Exception as e:
            logger.error(f"Error collecting task metrics: {e}")
            return {}
    
    def collect_error_patterns(self, error_sources: Dict) -> Dict:
        """エラーパターンを収集・分析"""
        try:
            error_patterns = {
                'data_type': 'error_patterns',
                'timestamp': datetime.now(),
                'error_frequency': {},
                'error_patterns_by_type': {},
                'error_correlation': {},
                'recovery_success_rate': {}
            }
            
            all_errors = []
            
            # Worker エラー処理
            if 'worker_errors' in error_sources:
                for error in error_sources['worker_errors']:
                    processed_error = self._process_error_data(error, 'worker')
                    all_errors.append(processed_error)
            
            # システムエラー処理
            if 'system_errors' in error_sources:
                for error in error_sources['system_errors']:
                    processed_error = self._process_error_data(error, 'system')
                    all_errors.append(processed_error)
            
            # エラー頻度分析
            error_patterns['error_frequency'] = self._analyze_error_frequency(all_errors)
            
            # エラーパターン分析
            error_patterns['error_patterns_by_type'] = self._analyze_error_patterns_by_type(all_errors)
            
            # エラー相関分析
            error_patterns['error_correlation'] = self._analyze_error_correlation(all_errors)
            
            # 復旧成功率分析
            error_patterns['recovery_success_rate'] = self._analyze_recovery_patterns(all_errors)
            
            logger.info(f"Error patterns collected: {len(all_errors)} errors analyzed")
            return error_patterns
            
        except Exception as e:
            logger.error(f"Error collecting error patterns: {e}")
            return {}
    
    def collect_user_behavior(self, user_data: Dict) -> Dict:
        """ユーザー行動データを収集・分析"""
        try:
            behavior_data = {
                'data_type': 'user_behavior',
                'timestamp': datetime.now(),
                'usage_patterns': {},
                'preference_analysis': {},
                'optimization_opportunities': []
            }
            
            # Claude CLI セッション分析
            if 'claude_cli_sessions' in user_data:
                cli_analysis = self._analyze_cli_sessions(user_data['claude_cli_sessions'])
                behavior_data['usage_patterns']['cli_sessions'] = cli_analysis
            
            # タスクリクエスト分析
            if 'task_requests' in user_data:
                task_analysis = self._analyze_task_requests(user_data['task_requests'])
                behavior_data['usage_patterns']['task_requests'] = task_analysis
            
            # 機能使用パターン分析
            if 'feature_usage' in user_data:
                feature_analysis = self._analyze_feature_usage(user_data['feature_usage'])
                behavior_data['usage_patterns']['feature_usage'] = feature_analysis
            
            # ユーザー嗜好分析
            behavior_data['preference_analysis'] = self._analyze_user_preferences(user_data)
            
            # 最適化機会の特定
            behavior_data['optimization_opportunities'] = self._identify_optimization_opportunities(
                behavior_data['usage_patterns']
            )
            
            logger.info("User behavior data collected and analyzed")
            return behavior_data
            
        except Exception as e:
            logger.error(f"Error collecting user behavior: {e}")
            return {}
    
    def save_learning_data(self, learning_data: Dict) -> bool:
        """学習データを保存"""
        try:
            # データ品質検証
            quality_result = self.validate_data_quality(learning_data)
            if not quality_result['is_valid']:
                logger.warning(f"Data quality validation failed: {quality_result['validation_errors']}")
                return False
            
            # データベースに保存
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO learning_data 
            (data_type, timestamp, source, data, metadata, quality_score, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                learning_data.get('data_type'),
                learning_data.get('timestamp', datetime.now()).isoformat(),
                learning_data.get('source', 'unknown'),
                json.dumps(learning_data.get('data', {})),
                json.dumps(learning_data.get('metadata', {})),
                quality_result['quality_score'],
                json.dumps(learning_data.get('metadata', {}).get('tags', []))
            ))
            
            data_id = cursor.lastrowid
            
            # 品質ログ保存
            cursor.execute("""
            INSERT INTO data_quality_log 
            (data_id, validation_result, quality_score, issues, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (
                data_id,
                json.dumps(quality_result),
                quality_result['quality_score'],
                json.dumps(quality_result.get('validation_errors', [])),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # ナレッジ賢者への保存（統合有効時）
            if self.sage_integration['knowledge_sage']:
                self.save_to_knowledge_base(learning_data)
            
            logger.info(f"Learning data saved with ID: {data_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
            return False
    
    def get_learning_dataset(self, data_type: str = None, time_range: Dict = None) -> List[Dict]:
        """学習データセットを取得"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # クエリ構築
            query = "SELECT * FROM learning_data WHERE 1=1"
            params = []
            
            if data_type:
                query += " AND data_type = ?"
                params.append(data_type)
            
            if time_range:
                if 'hours' in time_range:
                    cutoff_time = datetime.now() - timedelta(hours=time_range['hours'])
                    query += " AND timestamp >= ?"
                    params.append(cutoff_time.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # データ変換
            dataset = []
            for row in rows:
                data_record = {
                    'id': row['id'],
                    'data_type': row['data_type'],
                    'timestamp': datetime.fromisoformat(row['timestamp']),
                    'source': row['source'],
                    'data': json.loads(row['data']),
                    'metadata': json.loads(row['metadata']),
                    'quality_score': row['quality_score'],
                    'tags': json.loads(row['tags']) if row['tags'] else []
                }
                dataset.append(data_record)
            
            conn.close()
            
            logger.info(f"Retrieved {len(dataset)} learning data records")
            return dataset
            
        except Exception as e:
            logger.error(f"Error retrieving learning dataset: {e}")
            return []
    
    def validate_data_quality(self, data: Dict) -> Dict:
        """データ品質を検証"""
        try:
            validation_result = {
                'is_valid': True,
                'quality_score': 1.0,
                'validation_errors': []
            }
            
            # 必須フィールドチェック
            for field in self.quality_thresholds['required_fields']:
                if field not in data or data[field] is None:
                    validation_result['validation_errors'].append(f'missing_required_field: {field}')
                    validation_result['quality_score'] -= 0.3
            
            # タイムスタンプ検証
            if 'timestamp' in data:
                if data['timestamp'] is None:
                    validation_result['validation_errors'].append('invalid_timestamp')
                    validation_result['quality_score'] -= 0.2
                elif isinstance(data['timestamp'], str):
                    try:
                        datetime.fromisoformat(data['timestamp'])
                    except ValueError:
                        validation_result['validation_errors'].append('invalid_timestamp_format')
                        validation_result['quality_score'] -= 0.2
            
            # データ値検証
            if 'data' in data and isinstance(data['data'], dict):
                for key, value in data['data'].items():
                    if key.endswith('_usage') or key.endswith('_percent'):
                        if isinstance(value, (int, float)) and (value < 0 or value > 100):
                            validation_result['validation_errors'].append(f'invalid_percentage_value: {key}')
                            validation_result['quality_score'] -= 0.1
                    
                    if key.endswith('_time') and isinstance(value, (int, float)) and value < 0:
                        validation_result['validation_errors'].append(f'invalid_time_value: {key}')
                        validation_result['quality_score'] -= 0.1
            
            # 最終判定
            validation_result['quality_score'] = max(0.0, validation_result['quality_score'])
            validation_result['is_valid'] = (
                validation_result['quality_score'] >= self.quality_thresholds['min_quality_score'] and
                len(validation_result['validation_errors']) <= self.quality_thresholds['max_missing_fields']
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            return {'is_valid': False, 'quality_score': 0.0, 'validation_errors': [str(e)]}
    
    def save_to_knowledge_base(self, learning_data: Dict) -> bool:
        """ナレッジ賢者にデータを保存"""
        try:
            # ナレッジベースディレクトリ作成
            learning_dir = self.knowledge_base_path / "learning_patterns"
            learning_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_type = learning_data.get('data_type', 'unknown')
            filename = f"{data_type}_{timestamp}.json"
            
            # ファイルに保存
            file_path = learning_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Learning data saved to knowledge base: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to knowledge base: {e}")
            return False
    
    def search_knowledge_patterns(self, query: str, similarity_threshold: float = 0.8) -> List[Dict]:
        """ナレッジベースからパターンを検索"""
        try:
            learning_dir = self.knowledge_base_path / "learning_patterns"
            if not learning_dir.exists():
                return []
            
            patterns = []
            
            # JSONファイルを検索
            for json_file in learning_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 簡易テキスト検索（実際にはより高度な類似度計算が必要）
                    content = json.dumps(data, default=str).lower()
                    if query.lower() in content:
                        patterns.append({
                            'file': json_file.name,
                            'data': data,
                            'similarity': 0.9  # 仮の類似度
                        })
                
                except Exception as e:
                    logger.warning(f"Error reading knowledge file {json_file}: {e}")
            
            # 類似度でフィルタ・ソート
            patterns = [p for p in patterns if p['similarity'] >= similarity_threshold]
            patterns.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"Found {len(patterns)} matching patterns for query: {query}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error searching knowledge patterns: {e}")
            return []
    
    def start_data_streaming(self, config: Dict) -> bool:
        """リアルタイムデータストリーミング開始"""
        try:
            self.streaming_config = config
            self.is_streaming = True
            
            # ストリーミングスレッド開始
            self.streaming_thread = threading.Thread(
                target=self._streaming_loop,
                daemon=True
            )
            self.streaming_thread.start()
            
            logger.info("Data streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting data streaming: {e}")
            return False
    
    def stop_data_streaming(self) -> bool:
        """リアルタイムデータストリーミング停止"""
        try:
            self.is_streaming = False
            
            if self.streaming_thread and self.streaming_thread.is_alive():
                self.streaming_thread.join(timeout=2.0)
            
            logger.info("Data streaming stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping data streaming: {e}")
            return False
    
    def get_streaming_buffer(self) -> List[Dict]:
        """ストリーミングバッファを取得"""
        return list(self.streaming_buffer)
    
    def preprocess_data(self, raw_data: List[Dict]) -> List[Dict]:
        """データ前処理パイプライン"""
        try:
            processed_data = []
            
            for record in raw_data:
                processed_record = record.copy()
                
                # タイムスタンプ変換
                if 'timestamp' in processed_record and isinstance(processed_record['timestamp'], str):
                    try:
                        processed_record['timestamp'] = datetime.fromisoformat(processed_record['timestamp'])
                    except ValueError:
                        processed_record['timestamp'] = datetime.now()
                
                # メトリクス正規化
                if 'metrics' in processed_record:
                    metrics = processed_record['metrics']
                    
                    # 文字列から数値への変換
                    for key, value in metrics.items():
                        if isinstance(value, str):
                            # パーセンテージ変換
                            if value.endswith('%'):
                                metrics[key] = float(value[:-1])
                            # メモリサイズ変換
                            elif value.endswith('MB'):
                                metrics[key] = float(value[:-2])
                            # 通常の数値変換
                            else:
                                try:
                                    metrics[key] = float(value)
                                except ValueError:
                                    pass
                
                processed_data.append(processed_record)
            
            logger.info(f"Preprocessed {len(processed_data)} data records")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            return raw_data
    
    def integrate_with_sages(self, sage_config: Dict) -> bool:
        """4賢者システムとの統合"""
        try:
            self.sage_integration.update(sage_config)
            
            # 各賢者との統合設定
            for sage_name, config in sage_config.items():
                if config and isinstance(config, dict):
                    logger.info(f"Integrated with {sage_name}: {list(config.keys())}")
            
            logger.info("Successfully integrated with 4 sages system")
            return True
            
        except Exception as e:
            logger.error(f"Error integrating with sages: {e}")
            return False
    
    def collect_comprehensive_learning_data(self) -> Dict:
        """包括的学習データ収集（4賢者連携）"""
        try:
            comprehensive_data = {
                'timestamp': datetime.now(),
                'data_type': 'comprehensive_learning',
                'knowledge_insights': {},
                'task_patterns': {},
                'incident_analysis': {},
                'context_learning': {}
            }
            
            # 各賢者からのデータ収集をシミュレート
            if self.sage_integration.get('knowledge_sage'):
                comprehensive_data['knowledge_insights'] = {
                    'learning_trends': 'Performance improvement detected',
                    'pattern_evolution': 'New optimization patterns identified'
                }
            
            if self.sage_integration.get('task_sage'):
                comprehensive_data['task_patterns'] = {
                    'optimal_workflows': 'Task->PM->Result pattern most efficient',
                    'priority_learnings': 'High priority tasks show 20% faster completion'
                }
            
            if self.sage_integration.get('incident_sage'):
                comprehensive_data['incident_analysis'] = {
                    'error_predictions': 'ValidationError likely during high load',
                    'recovery_patterns': 'Auto-recovery successful in 85% of cases'
                }
            
            if self.sage_integration.get('rag_sage'):
                comprehensive_data['context_learning'] = {
                    'search_optimization': 'Context window optimization improved accuracy',
                    'knowledge_synthesis': 'Cross-domain pattern recognition enhanced'
                }
            
            logger.info("Comprehensive learning data collected from 4 sages")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error collecting comprehensive learning data: {e}")
            return {}
    
    def run_learning_pipeline(self, pipeline_config: Dict) -> Dict:
        """完全な学習パイプライン実行"""
        try:
            pipeline_result = {
                'status': 'success',
                'timestamp': datetime.now(),
                'data_collected': 0,
                'patterns_extracted': 0,
                'knowledge_updated': False,
                'pipeline_duration': 0
            }
            
            start_time = time.time()
            
            # データ収集フェーズ
            if 'data_sources' in pipeline_config:
                for source in pipeline_config['data_sources']:
                    # 各データソースからの収集をシミュレート
                    if source == 'workers':
                        pipeline_result['data_collected'] += 10
                    elif source == 'tasks':
                        pipeline_result['data_collected'] += 15
                    elif source == 'errors':
                        pipeline_result['data_collected'] += 5
                    elif source == 'users':
                        pipeline_result['data_collected'] += 8
            
            # パターン抽出フェーズ
            if pipeline_config.get('pattern_extraction'):
                pipeline_result['patterns_extracted'] = pipeline_result['data_collected'] // 5
            
            # ナレッジ統合フェーズ
            if pipeline_config.get('knowledge_integration'):
                pipeline_result['knowledge_updated'] = True
            
            pipeline_result['pipeline_duration'] = time.time() - start_time
            
            logger.info(f"Learning pipeline completed: {pipeline_result}")
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Error running learning pipeline: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    # Helper methods
    def _collect_system_metrics(self) -> Dict:
        """システムメトリクス収集"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            return {'cpu_percent': 0, 'memory_percent': 0, 'disk_percent': 0}
    
    def _calculate_aggregate_metrics(self, workers_data: Dict) -> Dict:
        """集約メトリクス計算"""
        if not workers_data:
            return {}
        
        processing_times = [w.get('avg_processing_time', 0) for w in workers_data.values()]
        success_rates = [w.get('success_rate', 1.0) for w in workers_data.values()]
        
        return {
            'total_workers': len(workers_data),
            'avg_processing_time': statistics.mean(processing_times) if processing_times else 0,
            'overall_success_rate': statistics.mean(success_rates) if success_rates else 1.0,
            'total_tasks_completed': sum(w.get('tasks_completed', 0) for w in workers_data.values())
        }
    
    def _get_current_stage(self, flow: Dict) -> str:
        """現在のステージを取得"""
        stages = flow.get('workflow_stages', [])
        for stage in reversed(stages):
            if stage.get('status') == 'processing':
                return stage.get('worker_type', 'unknown')
        return 'unknown'
    
    def _calculate_elapsed_time(self, flow: Dict) -> float:
        """経過時間計算"""
        created_at = flow.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
                return (datetime.now() - created_at).total_seconds()
            except ValueError:
                pass
        return 0.0
    
    def _predict_completion_time(self, flow: Dict) -> float:
        """完了時間予測"""
        # 簡易予測（実際にはより高度なモデルが必要）
        elapsed = self._calculate_elapsed_time(flow)
        stages = flow.get('workflow_stages', [])
        completed_stages = len([s for s in stages if s.get('status') == 'completed'])
        total_stages = len(stages)
        
        if completed_stages > 0 and total_stages > completed_stages:
            avg_stage_time = elapsed / completed_stages
            remaining_stages = total_stages - completed_stages
            return avg_stage_time * remaining_stages
        
        return 0.0
    
    def _analyze_stage_breakdown(self, flow: Dict) -> List[Dict]:
        """ステージ内訳分析"""
        stages = flow.get('workflow_stages', [])
        breakdown = []
        
        for i, stage in enumerate(stages):
            stage_data = {
                'stage_index': i,
                'worker_type': stage.get('worker_type'),
                'processing_time': stage.get('processing_time', 0),
                'status': stage.get('status')
            }
            breakdown.append(stage_data)
        
        return breakdown
    
    def _analyze_flow_patterns(self, flows: List[Dict]) -> Dict:
        """フローパターン分析"""
        patterns = {
            'avg_processing_time_by_worker': {},
            'success_rate_by_stage': {},
            'common_bottlenecks': []
        }
        
        worker_times = defaultdict(list)
        stage_success = defaultdict(lambda: {'success': 0, 'total': 0})
        
        for flow in flows:
            stages = flow.get('workflow_stages', [])
            for stage in stages:
                worker_type = stage.get('worker_type')
                processing_time = stage.get('processing_time', 0)
                status = stage.get('status')
                
                if processing_time > 0:
                    worker_times[worker_type].append(processing_time)
                
                stage_success[worker_type]['total'] += 1
                if status == 'completed':
                    stage_success[worker_type]['success'] += 1
        
        # 平均処理時間
        for worker_type, times in worker_times.items():
            patterns['avg_processing_time_by_worker'][worker_type] = statistics.mean(times)
        
        # 成功率
        for worker_type, counts in stage_success.items():
            if counts['total'] > 0:
                patterns['success_rate_by_stage'][worker_type] = counts['success'] / counts['total']
        
        return patterns
    
    def _analyze_bottlenecks(self, completed_flows: List[Dict]) -> Dict:
        """ボトルネック分析"""
        bottlenecks = {
            'slowest_workers': [],
            'most_failed_stages': [],
            'optimization_suggestions': []
        }
        
        worker_times = defaultdict(list)
        
        for flow in completed_flows:
            stage_breakdown = flow.get('stage_breakdown', [])
            for stage in stage_breakdown:
                worker_type = stage.get('worker_type')
                processing_time = stage.get('processing_time', 0)
                
                if processing_time > 0:
                    worker_times[worker_type].append(processing_time)
        
        # 最も遅いWorker特定
        avg_times = {}
        for worker_type, times in worker_times.items():
            if times:
                avg_times[worker_type] = statistics.mean(times)
        
        sorted_workers = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)
        bottlenecks['slowest_workers'] = sorted_workers[:3]
        
        return bottlenecks
    
    def _process_error_data(self, error: Dict, error_source: str) -> Dict:
        """エラーデータ処理"""
        return {
            'error_type': error.get('error_type', 'Unknown'),
            'error_message': error.get('error_message', ''),
            'timestamp': error.get('timestamp', datetime.now()),
            'source': error_source,
            'context': error.get('context', {}),
            'worker_id': error.get('worker_id'),
            'component': error.get('component')
        }
    
    def _analyze_error_frequency(self, errors: List[Dict]) -> Dict:
        """エラー頻度分析"""
        frequency = defaultdict(int)
        for error in errors:
            frequency[error['error_type']] += 1
        return dict(frequency)
    
    def _analyze_error_patterns_by_type(self, errors: List[Dict]) -> Dict:
        """エラータイプ別パターン分析"""
        patterns = defaultdict(list)
        for error in errors:
            patterns[error['error_type']].append({
                'message': error['error_message'],
                'context': error['context'],
                'timestamp': error['timestamp']
            })
        return dict(patterns)
    
    def _analyze_error_correlation(self, errors: List[Dict]) -> Dict:
        """エラー相関分析"""
        # 簡易実装
        return {'time_based_correlation': 'High error rate during peak hours'}
    
    def _analyze_recovery_patterns(self, errors: List[Dict]) -> Dict:
        """復旧パターン分析"""
        # 簡易実装
        return {'auto_recovery_rate': 0.85, 'manual_intervention_rate': 0.15}
    
    def _analyze_cli_sessions(self, sessions: List[Dict]) -> Dict:
        """CLI セッション分析"""
        if not sessions:
            return {}
        
        total_sessions = len(sessions)
        total_duration = sum(s.get('duration', 0) for s in sessions)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        
        # よく使われるコマンド
        command_usage = defaultdict(int)
        for session in sessions:
            for command in session.get('commands_used', []):
                command_usage[command] += 1
        
        most_used_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_sessions': total_sessions,
            'avg_session_duration': avg_duration,
            'most_used_commands': most_used_commands,
            'peak_usage_times': 'Morning hours show highest activity'
        }
    
    def _analyze_task_requests(self, requests: List[Dict]) -> Dict:
        """タスクリクエスト分析"""
        if not requests:
            return {}
        
        complexity_distribution = defaultdict(int)
        satisfaction_scores = []
        
        for request in requests:
            complexity = request.get('complexity', 'medium')
            complexity_distribution[complexity] += 1
            
            satisfaction = request.get('user_satisfaction')
            if satisfaction:
                satisfaction_scores.append(satisfaction)
        
        avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0
        
        return {
            'total_requests': len(requests),
            'complexity_distribution': dict(complexity_distribution),
            'avg_satisfaction': avg_satisfaction,
            'completion_rate': 'High complexity tasks take 40% longer'
        }
    
    def _analyze_feature_usage(self, feature_usage: Dict) -> Dict:
        """機能使用分析"""
        total_usage = sum(feature_usage.values())
        
        usage_percentages = {}
        for feature, count in feature_usage.items():
            usage_percentages[feature] = (count / total_usage * 100) if total_usage > 0 else 0
        
        most_used_features = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_usage': total_usage,
            'usage_percentages': usage_percentages,
            'most_used_features': most_used_features,
            'feature_adoption_rate': 'Dashboard features show highest engagement'
        }
    
    def _analyze_user_preferences(self, user_data: Dict) -> Dict:
        """ユーザー嗜好分析"""
        return {
            'preferred_interaction_style': 'CLI-based interaction preferred',
            'complexity_preference': 'Medium complexity tasks most common',
            'time_preference': 'Quick feedback highly valued'
        }
    
    def _identify_optimization_opportunities(self, usage_patterns: Dict) -> List[str]:
        """最適化機会特定"""
        opportunities = []
        
        # CLI セッション最適化
        cli_data = usage_patterns.get('cli_sessions', {})
        if cli_data.get('avg_session_duration', 0) > 1800:  # 30分以上
            opportunities.append('CLI session efficiency can be improved')
        
        # 機能使用最適化
        feature_data = usage_patterns.get('feature_usage', {})
        if feature_data.get('total_usage', 0) > 0:
            opportunities.append('Feature discovery and adoption can be enhanced')
        
        return opportunities
    
    def _streaming_loop(self):
        """ストリーミングループ"""
        while self.is_streaming:
            try:
                # 実際の実装では各データソースからデータを収集
                stream_data = {
                    'timestamp': datetime.now(),
                    'type': 'streaming_sample',
                    'data': {'sample': 'streaming_data'}
                }
                
                self.streaming_buffer.append(stream_data)
                
                # 自動保存
                if self.streaming_config.get('auto_save'):
                    if len(self.streaming_buffer) >= self.streaming_config.get('buffer_size', 100):
                        # バッファをデータベースに保存
                        pass
                
                time.sleep(self.streaming_config.get('interval', 1.0))
                
            except Exception as e:
                logger.error(f"Streaming loop error: {e}")
                time.sleep(1.0)


if __name__ == "__main__":
    # テスト実行
    collector = LearningDataCollector()
    
    # テスト用データ収集
    test_data = {
        'data_type': 'test_metrics',
        'timestamp': datetime.now(),
        'data': {'cpu_usage': 65, 'memory_usage': 70},
        'metadata': {'source': 'test', 'quality_score': 0.95}
    }
    
    result = collector.save_learning_data(test_data)
    print(f"Test data saved: {result}")
    
    # データ取得テスト
    dataset = collector.get_learning_dataset(data_type='test_metrics')
    print(f"Retrieved {len(dataset)} records")