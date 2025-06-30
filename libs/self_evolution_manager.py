#!/usr/bin/env python3
"""
AI Company 自己進化ファイル配置マネージャー
AIが生成したファイルを適切な場所に自動配置して自己改良を実現
"""

import os
import re
from pathlib import Path
from datetime import datetime
import logging
import shutil

logger = logging.getLogger(__name__)

class SelfEvolutionManager:
    def __init__(self):
        # プロジェクトルートを相対パスで特定
        self.project_root = Path(__file__).parent.parent
        
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
        ファイルを内容・名前から自動配置
        
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
                # 内容からファイル名推測
                filename = self._guess_filename_from_content(source_content)
            
            # 配置先決定
            target_relative_dir = self.analyze_file_type(filename, source_content)
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
            
            result = {
                "success": True,
                "file_path": str(target_file),
                "relative_path": str(target_file.relative_to(self.project_root)),
                "target_dir": target_relative_dir,
                "filename": filename,
                "size": len(source_content),
                "task_id": task_id,
                "placed_at": datetime.now().isoformat()
            }
            
            logger.info(f"自己進化配置成功: {result['relative_path']}")
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
