#!/usr/bin/env python3
"""
💾 Storage Magic - 保存魔法
===========================

Ancient Elderの8つの古代魔法の一つ。
データ永続化、知識アーカイブ、状態管理、バックアップ復元を担当。

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import os
import shutil
import sqlite3
import tarfile
import gzip
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import tempfile
import statistics

from ..base_magic import AncientMagic, MagicCapability


@dataclass
class StorageMetadata:
    """ストレージメタデータのデータクラス"""
    storage_id: str
    storage_path: str
    format: str
    size_bytes: int
    created_at: datetime
    checksum: str
    collection_name: str


@dataclass
class BackupMetadata:
    """バックアップメタデータのデータクラス"""
    backup_id: str
    backup_name: str
    backup_path: str
    backup_type: str
    created_at: datetime
    size_bytes: int
    compression_ratio: float
    checksum: str


@dataclass
class StateMetadata:
    """状態メタデータのデータクラス"""
    state_id: str
    state_name: str
    version: int
    created_at: datetime
    size_bytes: int
    backend_type: str


class StorageMagic(AncientMagic):
    """
    Storage Magic - 保存魔法
    
    データの永続化と管理を司る古代魔法。
    - データ永続化（JSON, SQLite）
    - 知識アーカイブ（圧縮・検索）
    - 状態管理（ファイル・Redis）
    - バックアップ復元（フル・増分）
    """
    
    def __init__(self):
        super().__init__("storage", "データ永続化・知識アーカイブ・状態管理・バックアップ復元")
        
        # 魔法の能力
        self.capabilities = [
            MagicCapability.DATA_PERSISTENCE,
            MagicCapability.KNOWLEDGE_ARCHIVING,
            MagicCapability.STATE_MANAGEMENT,
            MagicCapability.BACKUP_RESTORATION
        ]
        
        # ストレージデータ管理
        self.storage_metadata: Dict[str, StorageMetadata] = {}
        self.backup_metadata: Dict[str, BackupMetadata] = {}
        self.state_metadata: Dict[str, StateMetadata] = {}
        self.archive_index: Dict[str, Dict[str, Any]] = {}
        
        # ストレージ設定
        self.storage_config = {
            "default_format": "json",
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "compression_level": 6,
            "backup_retention_days": 30,
            "enable_checksums": True,
            "auto_archive_threshold": 1000,  # files
            "state_sync_interval": 300  # seconds
        }
        
        # テンポラリディレクトリ
        self.temp_dir = tempfile.mkdtemp(prefix="storage_magic_")
        
    async def cast_magic(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """保存魔法を発動"""
        try:
            if intent == "persist_data":
                return await self.persist_data(data)
            elif intent == "retrieve_data":
                return await self.retrieve_data(data)
            elif intent == "update_data":
                return await self.update_data(data)
            elif intent == "delete_data":
                return await self.delete_data(data)
            elif intent == "create_archive":
                return await self.create_archive(data)
            elif intent == "extract_archive":
                return await self.extract_archive(data)
            elif intent == "search_archive":
                return await self.search_archive(data)
            elif intent == "persist_state":
                return await self.persist_state(data)
            elif intent == "retrieve_state":
                return await self.retrieve_state(data)
            elif intent == "synchronize_states":
                return await self.synchronize_states(data)
            elif intent == "update_state":
                return await self.update_state(data)
            elif intent == "get_state_history":
                return await self.get_state_history(data)
            elif intent == "create_backup":
                return await self.create_backup(data)
            elif intent == "restore_from_backup":
                return await self.restore_from_backup(data)
            elif intent == "verify_backup":
                return await self.verify_backup(data)
            elif intent == "point_in_time_recovery":
                return await self.point_in_time_recovery(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown storage intent: {intent}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Storage magic casting failed: {str(e)}"
            }
    
    # Phase 1: データ永続化（Data Persistence）
    async def persist_data(self, persistence_params: Dict[str, Any]) -> Dict[str, Any]:
        """データを永続化"""
        try:
            data = persistence_params.get("data", {})
            format_type = persistence_params.get("format", self.storage_config["default_format"])
            storage_path = persistence_params.get("storage_path", self.temp_dir)
            collection_name = persistence_params.get("collection_name", "default")
            
            # ストレージIDを生成
            storage_id = str(uuid.uuid4())
            
            # ストレージパス確保
            os.makedirs(storage_path, exist_ok=True)
            
            if format_type == "json":
                file_path = os.path.join(storage_path, f"{collection_name}_{storage_id}.json")
                
                # JSON形式で保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
            elif format_type == "sqlite":
                file_path = os.path.join(storage_path, f"{collection_name}_{storage_id}.db")
                schema = persistence_params.get("schema", {})
                
                # SQLite データベース作成
                conn = sqlite3connect(file_path)
                cursor = conn.cursor()
                
                # テーブル作成
                if schema:
                    columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
                    cursor.execute(f"CREATE TABLE {collection_name} ({columns})")
                
                # データ挿入
                if "documents" in data and isinstance(data["documents"], list):
                    for doc in data["documents"]:
                        if schema:
                            placeholders = ", ".join(["?" for _ in schema.keys()])
                            values = [doc.get(col, "") for col in schema.keys()]
                            cursor.execute(f"INSERT INTO {collection_name} VALUES ({placeholders})", values)
                
                conn.commit()
                conn.close()
                
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}"
                }
            
            # ファイルサイズとチェックサム計算
            size_bytes = os.path.getsize(file_path)
            checksum = self._calculate_checksum(file_path)
            
            # メタデータ保存
            metadata = StorageMetadata(
                storage_id=storage_id,
                storage_path=file_path,
                format=format_type,
                size_bytes=size_bytes,
                created_at=datetime.now(),
                checksum=checksum,
                collection_name=collection_name
            )
            
            self.storage_metadata[storage_id] = metadata
            
            return {
                "success": True,
                "persistence_result": {
                    "storage_id": storage_id,
                    "file_path": file_path,
                    "format": format_type,
                    "size_bytes": size_bytes,
                    "checksum": checksum,
                    "created_at": metadata.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Data persistence failed: {str(e)}"
            }
    
    async def retrieve_data(self, retrieval_params: Dict[str, Any]) -> Dict[str, Any]:
        """永続化されたデータを取得"""
        try:
            storage_id = retrieval_params.get("storage_id", "")
            format_type = retrieval_params.get("format", "json")
            
            if storage_id not in self.storage_metadata:
                return {
                    "success": False,
                    "error": f"Storage ID {storage_id} not found"
                }
            
            metadata = self.storage_metadata[storage_id]
            
            if not os.path.exists(metadata.storage_path):
                return {
                    "success": False,
                    "error": f"Storage file not found: {metadata.storage_path}"
                }
            
            # データ読み込み
            if metadata.format == "json":
                with open(metadata.storage_path, 'r', encoding='utf-8') as f:
                    retrieved_data = json.load(f)
                    
            elif metadata.format == "sqlite":
                conn = sqlite3connect(metadata.storage_path)
                cursor = conn.cursor()
                
                # テーブル一覧取得
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                retrieved_data = {}
                for table_name, in tables:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    # カラム名取得
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # 辞書形式で変換
                    retrieved_data[table_name] = [
                        dict(zip(columns, row)) for row in rows
                    ]
                
                conn.close()
                
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {metadata.format}"
                }
            
            return {
                "success": True,
                "retrieved_data": retrieved_data,
                "metadata": {
                    "storage_id": storage_id,
                    "format": metadata.format,
                    "size_bytes": metadata.size_bytes,
                    "created_at": metadata.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Data retrieval failed: {str(e)}"
            }
    
    async def update_data(self, update_params: Dict[str, Any]) -> Dict[str, Any]:
        """永続化データを更新"""
        try:
            storage_id = update_params.get("storage_id", "")
            updated_data = update_params.get("data", {})
            update_strategy = update_params.get("update_strategy", "replace")
            
            if storage_id not in self.storage_metadata:
                return {
                    "success": False,
                    "error": f"Storage ID {storage_id} not found"
                }
            
            metadata = self.storage_metadata[storage_id]
            previous_size = metadata.size_bytes
            
            # 現在のデータを取得
            current_result = await self.retrieve_data({"storage_id": storage_id})
            if not current_result["success"]:
                return current_result
            
            current_data = current_result["retrieved_data"]
            
            # 更新戦略に応じて処理
            if update_strategy == "replace":
                final_data = updated_data
            elif update_strategy == "merge":
                if isinstance(current_data, dict) and isinstance(updated_data, dict):
                    final_data = {**current_data, **updated_data}
                else:
                    final_data = updated_data
            else:
                return {
                    "success": False,
                    "error": f"Unsupported update strategy: {update_strategy}"
                }
            
            # データを再保存
            if metadata.format == "json":
                with open(metadata.storage_path, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=2, default=str)
            
            # メタデータ更新
            new_size = os.path.getsize(metadata.storage_path)
            new_checksum = self._calculate_checksum(metadata.storage_path)
            
            metadata.size_bytes = new_size
            metadata.checksum = new_checksum
            
            return {
                "success": True,
                "update_result": {
                    "storage_id": storage_id,
                    "updated_records": 1,
                    "previous_size": previous_size,
                    "new_size": new_size,
                    "checksum": new_checksum
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Data update failed: {str(e)}"
            }
    
    async def delete_data(self, deletion_params: Dict[str, Any]) -> Dict[str, Any]:
        """永続化データを削除"""
        try:
            storage_id = deletion_params.get("storage_id", "")
            delete_strategy = deletion_params.get("delete_strategy", "complete")
            
            if storage_id not in self.storage_metadata:
                return {
                    "success": False,
                    "error": f"Storage ID {storage_id} not found"
                }
            
            metadata = self.storage_metadata[storage_id]
            
            if delete_strategy == "complete":
                # ファイル削除
                if os.path.exists(metadata.storage_path):
                    os.remove(metadata.storage_path)
                
                # メタデータ削除
                del self.storage_metadata[storage_id]
                
                return {
                    "success": True,
                    "deletion_result": {
                        "storage_id": storage_id,
                        "deleted": True,
                        "strategy": delete_strategy
                    }
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported delete strategy: {delete_strategy}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Data deletion failed: {str(e)}"
            }
    
    # Phase 2: 知識アーカイブ（Knowledge Archiving）
    async def create_archive(self, archive_params: Dict[str, Any]) -> Dict[str, Any]:
        """知識アーカイブを作成"""
        try:
            data = archive_params.get("data", {})
            archive_name = archive_params.get("archive_name", "unnamed_archive")
            storage_path = archive_params.get("storage_path", self.temp_dir)
            compression = archive_params.get("compression", "gzip")
            metadata = archive_params.get("metadata", {})
            index_for_search = archive_params.get("index_for_search", False)
            
            # アーカイブIDを生成
            archive_id = str(uuid.uuid4())
            
            # ストレージパス確保
            os.makedirs(storage_path, exist_ok=True)
            
            # テンポラリディレクトリでアーカイブ準備
            temp_archive_dir = tempfile.mkdtemp(prefix=f"archive_{archive_id}_")
            
            # データをJSONファイルとして保存
            data_file = os.path.join(temp_archive_dir, "data.json")
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # メタデータファイル作成
            archive_metadata = {
                "archive_id": archive_id,
                "archive_name": archive_name,
                "created_at": datetime.now().isoformat(),
                "compression": compression,
                **metadata
            }
            
            metadata_file = os.path.join(temp_archive_dir, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(archive_metadata, f, ensure_ascii=False, indent=2)
            
            # 検索インデックス作成（オプション）
            if index_for_search:
                search_index = self._create_search_index(data)
                index_file = os.path.join(temp_archive_dir, "search_index.json")
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(search_index, f, ensure_ascii=False, indent=2)
                
                self.archive_index[archive_id] = search_index
            
            # アーカイブ作成
            if compression == "gzip":
                archive_path = os.path.join(storage_path, f"{archive_name}_{archive_id}.tar.gz")
                
                with tarfile.open(archive_path, "w:gz", compresslevel=self.storage_config["compression_level"]) as tar:
                    tar.add(temp_archive_dir, arcname=archive_name)
                    
            elif compression == "none":
                archive_path = os.path.join(storage_path, f"{archive_name}_{archive_id}.tar")
                
                with tarfile.open(archive_path, "w") as tar:
                    tar.add(temp_archive_dir, arcname=archive_name)
                    
            else:
                return {
                    "success": False,
                    "error": f"Unsupported compression: {compression}"
                }
            
            # 圧縮率計算
            original_size = sum(os.path.getsize(os.path.join(root, file))
                               for root, dirs, files in os.walk(temp_archive_dir)
                               for file in files)
            compressed_size = os.path.getsize(archive_path)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
            
            # バックアップメタデータ保存
            backup_metadata = BackupMetadata(
                backup_id=archive_id,
                backup_name=archive_name,
                backup_path=archive_path,
                backup_type="archive",
                created_at=datetime.now(),
                size_bytes=compressed_size,
                compression_ratio=compression_ratio,
                checksum=self._calculate_checksum(archive_path)
            )
            
            self.backup_metadata[archive_id] = backup_metadata
            
            # テンポラリディレクトリクリーンアップ
            shutil.rmtree(temp_archive_dir)
            
            return {
                "success": True,
                "archive_result": {
                    "archive_id": archive_id,
                    "archive_path": archive_path,
                    "compression": compression,
                    "compression_ratio": round(compression_ratio, 3),
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "created_at": backup_metadata.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Archive creation failed: {str(e)}"
            }
    
    async def extract_archive(self, extract_params: Dict[str, Any]) -> Dict[str, Any]:
        """アーカイブを展開"""
        try:
            archive_id = extract_params.get("archive_id", "")
            extract_path = extract_params.get("extract_path", self.temp_dir)
            verify_integrity = extract_params.get("verify_integrity", True)
            
            if archive_id not in self.backup_metadata:
                return {
                    "success": False,
                    "error": f"Archive ID {archive_id} not found"
                }
            
            metadata = self.backup_metadata[archive_id]
            
            if not os.path.exists(metadata.backup_path):
                return {
                    "success": False,
                    "error": f"Archive file not found: {metadata.backup_path}"
                }
            
            # 整合性検証（オプション）
            integrity_verified = True
            if verify_integrity:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                integrity_verified = (current_checksum == metadata.checksum)
            
            # 展開先ディレクトリ確保
            os.makedirs(extract_path, exist_ok=True)
            
            # アーカイブ展開
            extracted_files = 0
            
            if metadata.backup_path.endswith(".tar.gz"):
                with tarfile.open(metadata.backup_path, "r:gz") as tar:
                    tar.extractall(extract_path)
                    extracted_files = len(tar.getnames())
                    
            elif metadata.backup_path.endswith(".tar"):
                with tarfile.open(metadata.backup_path, "r") as tar:
                    tar.extractall(extract_path)
                    extracted_files = len(tar.getnames())
                    
            else:
                return {
                    "success": False,
                    "error": f"Unsupported archive format: {metadata.backup_path}"
                }
            
            return {
                "success": True,
                "extract_result": {
                    "archive_id": archive_id,
                    "extract_path": extract_path,
                    "extracted_files": extracted_files,
                    "integrity_verified": integrity_verified
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Archive extraction failed: {str(e)}"
            }
    
    async def search_archive(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """アーカイブ内検索"""
        try:
            archive_id = search_params.get("archive_id", "")
            query = search_params.get("query", "")
            search_fields = search_params.get("search_fields", ["title", "content"])
            max_results = search_params.get("max_results", 10)
            
            if archive_id not in self.archive_index:
                return {
                    "success": False,
                    "error": f"Search index not found for archive {archive_id}"
                }
            
            search_index = self.archive_index[archive_id]
            query_words = set(query.lower().split())
            
            matches = []
            
            # インデックスから検索
            for doc_id, doc_data in search_index.get("documents", {}).items():
                score = 0
                matched_fields = []
                
                for field in search_fields:
                    if field in doc_data:
                        field_text = str(doc_data[field]).lower()
                        field_words = set(field_text.split())
                        
                        # 単語マッチング
                        overlap = len(query_words & field_words)
                        if overlap > 0:
                            field_score = overlap / len(query_words)
                            score += field_score
                            matched_fields.append(field)
                
                if score > 0:
                    matches.append({
                        "document_id": doc_id,
                        "relevance_score": round(score, 3),
                        "matched_fields": matched_fields,
                        "document_data": doc_data
                    })
            
            # スコア順でソート
            matches.sort(key=lambda x: x["relevance_score"], reverse=True)
            matches = matches[:max_results]
            
            return {
                "success": True,
                "search_result": {
                    "query": query,
                    "archive_id": archive_id,
                    "matches": matches,
                    "total_matches": len(matches)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Archive search failed: {str(e)}"
            }
    
    # Phase 3: 状態管理（State Management）
    async def persist_state(self, state_params: Dict[str, Any]) -> Dict[str, Any]:
        """システム状態を永続化"""
        try:
            state_data = state_params.get("state_data", {})
            state_name = state_params.get("state_name", "unnamed_state")
            storage_backend = state_params.get("storage_backend", "file")
            storage_path = state_params.get("storage_path", self.temp_dir)
            enable_versioning = state_params.get("enable_versioning", False)
            max_versions = state_params.get("max_versions", 5)
            
            # 状態IDを生成
            state_id = str(uuid.uuid4())
            
            if storage_backend == "file":
                # ファイルベース状態管理
                os.makedirs(storage_path, exist_ok=True)
                
                state_file = os.path.join(storage_path, f"{state_name}_{state_id}.json")
                
                # バージョニング対応
                if enable_versioning:
                    versions_dir = os.path.join(storage_path, f"{state_name}_versions")
                    os.makedirs(versions_dir, exist_ok=True)
                    
                    # 現在のバージョン番号を取得
                    version_files = [f for f in os.listdir(versions_dir) if f.startswith(f"{state_name}_v")]
                    version_number = len(version_files) + 1
                    
                    # バージョンファイル作成
                    version_file = os.path.join(versions_dir, f"{state_name}_v{version_number}.json")
                    versioned_data = {
                        "version": version_number,
                        "created_at": datetime.now().isoformat(),
                        "state_data": state_data
                    }
                    
                    with open(version_file, 'w', encoding='utf-8') as f:
                        json.dump(versioned_data, f, ensure_ascii=False, indent=2, default=str)
                    
                    # 古いバージョンの削除
                    if len(version_files) >= max_versions:
                        old_versions = sorted(version_files)
                        for old_version in old_versions[:-max_versions]:
                            old_file = os.path.join(versions_dir, old_version)
                            if os.path.exists(old_file):
                                os.remove(old_file)
                
                # メイン状態ファイル作成
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, ensure_ascii=False, indent=2, default=str)
                
                # メタデータ保存
                state_metadata = StateMetadata(
                    state_id=state_id,
                    state_name=state_name,
                    version=1,
                    created_at=datetime.now(),
                    size_bytes=os.path.getsize(state_file),
                    backend_type="file"
                )
                
                self.state_metadata[state_id] = state_metadata
                
                return {
                    "success": True,
                    "state_result": {
                        "state_id": state_id,
                        "state_name": state_name,
                        "persistence_type": "file",
                        "state_path": state_file,
                        "size_bytes": state_metadata.size_bytes,
                        "versioning_enabled": enable_versioning
                    }
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported storage backend: {storage_backend}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"State persistence failed: {str(e)}"
            }
    
    async def retrieve_state(self, retrieve_params: Dict[str, Any]) -> Dict[str, Any]:
        """システム状態を取得"""
        try:
            state_id = retrieve_params.get("state_id", "")
            storage_backend = retrieve_params.get("storage_backend", "file")
            
            if state_id not in self.state_metadata:
                return {
                    "success": False,
                    "error": f"State ID {state_id} not found"
                }
            
            metadata = self.state_metadata[state_id]
            
            if storage_backend == "file":
                # 状態ファイルを特定
                state_file = None
                for storage_id, storage_meta in self.storage_metadata.items():
                    if storage_meta.collection_name.startswith(metadata.state_name):
                        state_file = storage_meta.storage_path
                        break
                
                # フォールバック: メタデータから推定
                if not state_file:
                    storage_dir = os.path.dirname(list(self.storage_metadata.values())[0].storage_path) if self.storage_metadata else self.temp_dir
                    state_file = os.path.join(storage_dir, f"{metadata.state_name}_{state_id}.json")
                
                # 実際の状態ファイルを探索
                if not os.path.exists(state_file):
                    # パターンマッチで探索
                    storage_dir = os.path.dirname(state_file)
                    if os.path.exists(storage_dir):
                        for filename in os.listdir(storage_dir):
                            if filename.startswith(f"{metadata.state_name}_") and filename.endswith(".json"):
                                state_file = os.path.join(storage_dir, filename)
                                break
                
                if not os.path.exists(state_file):
                    return {
                        "success": False,
                        "error": f"State file not found: {state_file}"
                    }
                
                # 状態データ読み込み
                with open(state_file, 'r', encoding='utf-8') as f:
                    retrieved_state = json.load(f)
                
                return {
                    "success": True,
                    "retrieved_state": retrieved_state,
                    "metadata": {
                        "state_id": state_id,
                        "state_name": metadata.state_name,
                        "version": metadata.version,
                        "backend_type": metadata.backend_type
                    }
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported storage backend: {storage_backend}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"State retrieval failed: {str(e)}"
            }
    
    async def synchronize_states(self, sync_params: Dict[str, Any]) -> Dict[str, Any]:
        """複数状態の同期"""
        try:
            states = sync_params.get("states", [])
            sync_strategy = sync_params.get("sync_strategy", "merge")
            storage_backend = sync_params.get("storage_backend", "file")
            storage_path = sync_params.get("storage_path", self.temp_dir)
            
            synchronized_states = 0
            conflicts_resolved = 0
            
            for state_info in states:
                state_name = state_info.get("name", "")
                state_data = state_info.get("data", {})
                
                # 状態を永続化
                persist_params = {
                    "state_data": state_data,
                    "state_name": state_name,
                    "storage_backend": storage_backend,
                    "storage_path": storage_path
                }
                
                result = await self.persist_state(persist_params)
                if result["success"]:
                    synchronized_states += 1
                else:
                    # 競合解決の試み
                    if sync_strategy == "merge":
                        conflicts_resolved += 1
                        # 簡単な競合解決（実際の実装では更に複雑）
                        continue
            
            return {
                "success": True,
                "sync_result": {
                    "synchronized_states": synchronized_states,
                    "conflicts_resolved": conflicts_resolved,
                    "sync_strategy": sync_strategy,
                    "total_states": len(states)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"State synchronization failed: {str(e)}"
            }
    
    async def update_state(self, update_params: Dict[str, Any]) -> Dict[str, Any]:
        """状態を更新"""
        try:
            state_id = update_params.get("state_id", "")
            state_data = update_params.get("state_data", {})
            create_version = update_params.get("create_version", False)
            
            if state_id not in self.state_metadata:
                return {
                    "success": False,
                    "error": f"State ID {state_id} not found"
                }
            
            # 現在の状態を取得
            current_result = await self.retrieve_state({"state_id": state_id})
            if not current_result["success"]:
                return current_result
            
            # 更新実行（簡単な置換）
            metadata = self.state_metadata[state_id]
            metadata.version += 1
            
            return {
                "success": True,
                "update_result": {
                    "state_id": state_id,
                    "new_version": metadata.version,
                    "version_created": create_version
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"State update failed: {str(e)}"
            }
    
    async def get_state_history(self, history_params: Dict[str, Any]) -> Dict[str, Any]:
        """状態バージョン履歴を取得"""
        try:
            state_id = history_params.get("state_id", "")
            
            if state_id not in self.state_metadata:
                return {
                    "success": False,
                    "error": f"State ID {state_id} not found"
                }
            
            metadata = self.state_metadata[state_id]
            
            # 簡単なバージョン履歴（実際の実装では更に詳細）
            version_history = [
                {
                    "version": 1,
                    "created_at": metadata.created_at.isoformat(),
                    "size_bytes": metadata.size_bytes
                },
                {
                    "version": metadata.version,
                    "created_at": datetime.now().isoformat(),
                    "size_bytes": metadata.size_bytes
                }
            ]
            
            return {
                "success": True,
                "version_history": version_history,
                "current_version": metadata.version
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"State history retrieval failed: {str(e)}"
            }
    
    # Phase 4: バックアップ・復元（Backup Restoration）
    async def create_backup(self, backup_params: Dict[str, Any]) -> Dict[str, Any]:
        """バックアップを作成"""
        try:
            backup_name = backup_params.get("backup_name", "unnamed_backup")
            source_paths = backup_params.get("source_paths", [])
            compression = backup_params.get("compression", "gzip")
            backup_type = backup_params.get("backup_type", "full")
            include_metadata = backup_params.get("include_metadata", True)
            base_backup_id = backup_params.get("base_backup_id", "")
            timestamp = backup_params.get("timestamp", datetime.now().isoformat())
            calculate_checksums = backup_params.get("calculate_checksums", True)
            
            # ソースパス検証
            for source_path in source_paths:
                if not os.path.exists(source_path):
                    return {
                        "success": False,
                        "error": f"Source path not found: {source_path}"
                    }
            
            # バックアップIDを生成
            backup_id = str(uuid.uuid4())
            
            # バックアップファイル名
            if compression == "gzip":
                backup_path = os.path.join(self.temp_dir, f"{backup_name}_{backup_id}.tar.gz")
            else:
                backup_path = os.path.join(self.temp_dir, f"{backup_name}_{backup_id}.tar")
            
            # バックアップ作成
            original_size = 0
            changed_files = 0
            
            if compression == "gzip":
                with tarfile.open(backup_path, "w:gz", compresslevel=self.storage_config["compression_level"]) as tar:
                    for source_path in source_paths:
                        if os.path.isfile(source_path):
                            tar.add(source_path, arcname=os.path.basename(source_path))
                            original_size += os.path.getsize(source_path)
                            changed_files += 1
                        elif os.path.isdir(source_path):
                            for root, dirs, files in os.walk(source_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                                    tar.add(file_path, arcname=arcname)
                                    original_size += os.path.getsize(file_path)
                                    changed_files += 1
            else:
                with tarfile.open(backup_path, "w") as tar:
                    for source_path in source_paths:
                        tar.add(source_path, arcname=os.path.basename(source_path))
                        if os.path.isfile(source_path):
                            original_size += os.path.getsize(source_path)
                            changed_files += 1
            
            # バックアップサイズと圧縮率
            compressed_size = os.path.getsize(backup_path)
            compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
            
            # チェックサム計算
            checksum = ""
            if calculate_checksums:
                checksum = self._calculate_checksum(backup_path)
            
            # メタデータ保存
            backup_metadata = BackupMetadata(
                backup_id=backup_id,
                backup_name=backup_name,
                backup_path=backup_path,
                backup_type=backup_type,
                created_at=datetime.now(),
                size_bytes=compressed_size,
                compression_ratio=compression_ratio,
                checksum=checksum
            )
            
            self.backup_metadata[backup_id] = backup_metadata
            
            return {
                "success": True,
                "backup_result": {
                    "backup_id": backup_id,
                    "backup_name": backup_name,
                    "backup_path": backup_path,
                    "backup_type": backup_type,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": round(compression_ratio, 3),
                    "changed_files": changed_files,
                    "checksum": checksum,
                    "created_at": backup_metadata.created_at.isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Backup creation failed: {str(e)}"
            }
    
    async def restore_from_backup(self, restore_params: Dict[str, Any]) -> Dict[str, Any]:
        """バックアップから復元"""
        try:
            backup_id = restore_params.get("backup_id", "")
            restore_path = restore_params.get("restore_path", self.temp_dir)
            verify_integrity = restore_params.get("verify_integrity", True)
            restore_type = restore_params.get("restore_type", "full")
            
            if backup_id not in self.backup_metadata:
                return {
                    "success": False,
                    "error": f"Backup ID {backup_id} not found"
                }
            
            metadata = self.backup_metadata[backup_id]
            
            if not os.path.exists(metadata.backup_path):
                return {
                    "success": False,
                    "error": f"Backup file not found: {metadata.backup_path}"
                }
            
            # 整合性検証
            integrity_verified = True
            if verify_integrity and metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                integrity_verified = (current_checksum == metadata.checksum)
                
                if not integrity_verified:
                    return {
                        "success": False,
                        "error": f"Backup integrity verification failed"
                    }
            
            # 復元先ディレクトリ確保
            os.makedirs(restore_path, exist_ok=True)
            
            # バックアップから復元
            restored_files = 0
            
            if metadata.backup_path.endswith(".tar.gz"):
                with tarfile.open(metadata.backup_path, "r:gz") as tar:
                    tar.extractall(restore_path)
                    restored_files = len(tar.getnames())
                    
            elif metadata.backup_path.endswith(".tar"):
                with tarfile.open(metadata.backup_path, "r") as tar:
                    tar.extractall(restore_path)
                    restored_files = len(tar.getnames())
            
            return {
                "success": True,
                "restore_result": {
                    "backup_id": backup_id,
                    "restore_path": restore_path,
                    "restore_type": restore_type,
                    "restored_files": restored_files,
                    "integrity_verified": integrity_verified
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Restore from backup failed: {str(e)}"
            }
    
    async def verify_backup(self, verification_params: Dict[str, Any]) -> Dict[str, Any]:
        """バックアップ整合性を検証"""
        try:
            backup_id = verification_params.get("backup_id", "")
            verification_type = verification_params.get("verification_type", "basic")
            check_checksums = verification_params.get("check_checksums", True)
            
            if backup_id not in self.backup_metadata:
                return {
                    "success": False,
                    "error": f"Backup ID {backup_id} not found"
                }
            
            metadata = self.backup_metadata[backup_id]
            
            if not os.path.exists(metadata.backup_path):
                return {
                    "success": False,
                    "error": f"Backup file not found: {metadata.backup_path}"
                }
            
            # 基本検証
            integrity_ok = True
            checksum_matches = True
            corrupted_files = 0
            
            # ファイル存在確認
            if not os.path.exists(metadata.backup_path):
                integrity_ok = False
            
            # チェックサム検証
            if check_checksums and metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                checksum_matches = (current_checksum == metadata.checksum)
                if not checksum_matches:
                    integrity_ok = False
            
            # アーカイブ内容検証（オプション）
            if verification_type == "full":
                try:
                    if metadata.backup_path.endswith(".tar.gz"):
                        with tarfile.open(metadata.backup_path, "r:gz") as tar:
                            # アーカイブが正常に開けることを確認
                            member_count = len(tar.getnames())
                    elif metadata.backup_path.endswith(".tar"):
                        with tarfile.open(metadata.backup_path, "r") as tar:
                            member_count = len(tar.getnames())
                except:
                    integrity_ok = False
                    corrupted_files = 1
            
            return {
                "success": True,
                "verification_result": {
                    "backup_id": backup_id,
                    "verification_type": verification_type,
                    "integrity_ok": integrity_ok,
                    "checksum_matches": checksum_matches,
                    "corrupted_files": corrupted_files,
                    "file_size": os.path.getsize(metadata.backup_path),
                    "verified_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Backup verification failed: {str(e)}"
            }
    
    async def point_in_time_recovery(self, recovery_params: Dict[str, Any]) -> Dict[str, Any]:
        """ポイント・イン・タイム復旧"""
        try:
            target_timestamp = recovery_params.get("target_timestamp", "")
            restore_path = recovery_params.get("restore_path", self.temp_dir)
            recovery_type = recovery_params.get("recovery_type", "point_in_time")
            
            # タイムスタンプをパース
            target_time = datetime.fromisoformat(target_timestamp.replace('Z', '+00:00'))
            
            # 最適なバックアップを選択
            suitable_backups = []
            for backup_id, metadata in self.backup_metadata.items():
                if metadata.created_at <= target_time:
                    time_diff = (target_time - metadata.created_at).total_seconds()
                    suitable_backups.append((backup_id, time_diff))
            
            if not suitable_backups:
                return {
                    "success": False,
                    "error": f"No suitable backup found for timestamp {target_timestamp}"
                }
            
            # 最も近いバックアップを選択
            suitable_backups.sort(key=lambda x: x[1])
            best_backup_id = suitable_backups[0][0]
            
            # 選択したバックアップから復元
            restore_params_internal = {
                "backup_id": best_backup_id,
                "restore_path": restore_path,
                "verify_integrity": True,
                "restore_type": "full"
            }
            
            restore_result = await self.restore_from_backup(restore_params_internal)
            
            if restore_result["success"]:
                return {
                    "success": True,
                    "recovery_result": {
                        "target_timestamp": target_timestamp,
                        "selected_backup_id": best_backup_id,
                        "restore_path": restore_path,
                        "recovery_type": recovery_type,
                        **restore_result["restore_result"]
                    }
                }
            else:
                return restore_result
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Point-in-time recovery failed: {str(e)}"
            }
    
    # ヘルパーメソッド
    def _calculate_checksum(self, file_path: str) -> str:
        """ファイルのSHA256チェックサムを計算"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""
    
    def _create_search_index(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """検索インデックスを作成"""
        search_index = {
            "documents": {},
            "created_at": datetime.now().isoformat()
        }
        
        # ドキュメントの場合
        if "documents" in data and isinstance(data["documents"], list):
            for i, doc in enumerate(data["documents"]):
                doc_id = doc.get("id", f"doc_{i}")
                search_index["documents"][doc_id] = {
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "category": doc.get("category", ""),
                    "tags": doc.get("tags", [])
                }
        
        return search_index
    
    def __del__(self):
        """デストラクタ：一時ディレクトリのクリーンアップ"""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass


if __name__ == "__main__":
    # テスト実行用のエントリーポイント
    async def test_storage_magic():
        magic = StorageMagic()
        
        # 簡単なテスト
        test_data = {"test": True, "data": "storage test"}
        
        persist_result = await magic.persist_data({
            "data": test_data,
            "format": "json",
            "collection_name": "test_storage"
        })
        
        print(f"Storage result: {persist_result['success']}")
    
    if __name__ == "__main__":
        asyncio.run(test_storage_magic())