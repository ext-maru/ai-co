#!/usr/bin/env python3
"""
BaseManager - AI Company マネージャー基底クラス

すべてのマネージャーが継承すべき基底クラス。
ログ設定、エラーハンドリング、共通処理を提供。
"""

import logging
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .common_utils import setup_logging, get_project_paths


class BaseManager(ABC):
    """マネージャー基底クラス"""
    
    def __init__(self, manager_name: str, enable_logging: bool = True):
        """
        Args:
            manager_name: マネージャー名
            enable_logging: ログ出力を有効にするか
        """
        self.manager_name = manager_name
        
        # プロジェクトパス設定
        self.paths = get_project_paths()
        self.project_dir = self.paths['project']
        self.output_dir = self.paths['output']
        self.log_dir = self.paths['logs']
        self.config_dir = self.paths['config']
        
        # ログ設定
        if enable_logging:
            self.logger = setup_logging(
                name=self.manager_name,
                log_file=self.log_dir / f"{manager_name.lower()}.log"
            )
        else:
            self.logger = logging.getLogger(self.manager_name)
            self.logger.addHandler(logging.NullHandler())
        
        # 統計情報
        self._stats = {
            'created_at': datetime.now().isoformat(),
            'operations': 0,
            'errors': 0,
            'last_operation': None
        }
        
        self.logger.info(f"🎯 {self.manager_name} 初期化完了")
    
    def _increment_stats(self, operation: str, error: bool = False):
        """統計情報の更新"""
        self._stats['operations'] += 1
        if error:
            self._stats['errors'] += 1
        self._stats['last_operation'] = {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {
            **self._stats,
            'uptime_seconds': (
                datetime.now() - datetime.fromisoformat(self._stats['created_at'])
            ).total_seconds()
        }
    
    def handle_error(self, error: Exception, operation: str, 
                     critical: bool = False) -> None:
        """
        エラーハンドリング
        
        Args:
            error: 発生したエラー
            operation: 実行中の操作
            critical: クリティカルエラーかどうか
        """
        self._increment_stats(operation, error=True)
        
        if critical:
            self.logger.error(f"❌ クリティカルエラー [{operation}]: {error}")
        else:
            self.logger.warning(f"⚠️ エラー [{operation}]: {error}")
        
        # デバッグ情報を含む場合はトレースバックも出力
        if self.logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
    
    def validate_config(self, config: Dict[str, Any], 
                       required_fields: List[str]) -> bool:
        """
        設定の検証
        
        Args:
            config: 検証する設定
            required_fields: 必須フィールドのリスト
            
        Returns:
            検証成功かどうか
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in config or config[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.error(
                f"設定検証エラー: 必須フィールドが不足 {missing_fields}"
            )
            return False
        
        return True
    
    def load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        設定ファイルの読み込み
        
        Args:
            filename: 設定ファイル名
            
        Returns:
            設定内容（エラー時はNone）
        """
        config_path = self.config_dir / filename
        
        try:
            if config_path.suffix == '.json':
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif config_path.suffix == '.conf':
                config = {}
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                return config
            
            else:
                self.logger.error(f"未対応の設定ファイル形式: {config_path.suffix}")
                return None
                
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {config_path}")
            return None
        except Exception as e:
            self.handle_error(e, f"設定ファイル読み込み: {filename}")
            return None
    
    def ensure_directory(self, directory: Path) -> bool:
        """
        ディレクトリの存在確認・作成
        
        Args:
            directory: 確認するディレクトリ
            
        Returns:
            成功かどうか
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.handle_error(e, f"ディレクトリ作成: {directory}")
            return False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初期化処理（サブクラスで実装必須）
        
        Returns:
            初期化成功かどうか
        """
        pass
    
    def cleanup(self) -> None:
        """
        クリーンアップ処理（サブクラスでオーバーライド可能）
        """
        self.logger.info(f"🧹 {self.manager_name} クリーンアップ完了")
    
    def __enter__(self):
        """コンテキストマネージャー対応"""
        if not self.initialize():
            raise RuntimeError(f"{self.manager_name} の初期化に失敗しました")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了処理"""
        self.cleanup()
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック（サブクラスで拡張可能）
        
        Returns:
            ヘルスチェック結果
        """
        stats = self.get_stats()
        error_rate = (
            stats['errors'] / stats['operations'] 
            if stats['operations'] > 0 else 0
        )
        
        return {
            'manager_name': self.manager_name,
            'healthy': error_rate < 0.1,  # エラー率10%未満
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
