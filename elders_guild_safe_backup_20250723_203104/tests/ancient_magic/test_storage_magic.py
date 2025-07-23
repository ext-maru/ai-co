#!/usr/bin/env python3
"""
💾 Storage Magic テストスイート
==============================

Storage Magic（保存魔法）の包括的なテストスイート。
データ永続化、知識アーカイブ、状態管理、バックアップ復元をテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
import tempfile
import os
import json
import shutil
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import tarfile
import gzip

# テスト対象をインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ancient_magic.storage_magic.storage_magic import StorageMagic


class TestStorageMagic:


"""Storage Magic テストクラス"""
        """Storage Magic インスタンスを作成"""
        return StorageMagic()
        
    @pytest.fixture
    def temp_storage_dir(self):

        """テスト用一時ディレクトリ"""
            shutil.rmtree(temp_dir)
            
    @pytest.fixture
    def sample_knowledge_data(self):

            """テスト用知識データ""" [
                {
                    "id": "kb_001",
                    "title": "Python TDD Best Practices",
                    "content": "Test-driven development with Python requires clear test organization and proper mocking strategies.",
                    "category": "development",
                    "tags": ["python", "tdd", "testing"],
                    "created_at": "2025-07-23T10:00:00",
                    "author": "Claude Elder"
                },
                {
                    "id": "kb_002",
                    "title": "Ancient Elder Magic System",
                    "content": "The Ancient Elder system provides 8 magical capabilities for autonomous AI evolution.",
                    "category": "architecture",
                    "tags": ["ancient-elder", "magic", "ai"],
                    "created_at": "2025-07-23T10:30:00",
                    "author": "Grand Elder Maru"
                }
            ],
            "metadata": {
                "version": "1.0",
                "total_documents": 2,
                "last_updated": "2025-07-23T11:00:00"
            }
        }
    
    @pytest.fixture
    def sample_state_data(self):

            """テスト用状態データ""" {
                "knowledge_sage": {
                    "active": True,
                    "last_query": "2025-07-23T10:45:00",
                    "query_count": 127
                },
                "task_sage": {
                    "active": True,
                    "last_task": "2025-07-23T10:50:00",
                    "completed_tasks": 89
                },
                "incident_sage": {
                    "active": True,
                    "last_incident": "2025-07-23T09:30:00",
                    "resolved_incidents": 23
                },
                "rag_sage": {
                    "active": True,
                    "last_search": "2025-07-23T10:55:00",
                    "search_count": 234
                }
            },
            "system_metrics": {
                "cpu_usage": 0.65,
                "memory_usage": 0.78,
                "disk_usage": 0.45,
                "uptime": 86400
            }
        }
    
    # Phase 1: データ永続化（Data Persistence）
    async def test_persist_knowledge_data_json(self, storage_magic, sample_knowledge_data, temp_storage_dir):

    """JSON形式での知識データ永続化テスト""" sample_knowledge_data,
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "knowledge_base"
        }
        
        result = await storage_magic.persist_data(persistence_params)
        
        assert result["success"] is True
        persistence_result = result["persistence_result"]
        
        # 永続化結果の確認
        assert "storage_id" in persistence_result
        assert "file_path" in persistence_result
        assert persistence_result["format"] == "json"
        assert persistence_result["size_bytes"] > 0
        
        # ファイル存在確認
        assert os.path.exists(persistence_result["file_path"])
        
        # データ整合性確認
        with open(persistence_result["file_path"], 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        
        assert stored_data["documents"][0]["title"] == "Python TDD Best Practices"
        assert stored_data["metadata"]["total_documents"] == 2
        
    async def test_persist_knowledge_data_sqlite(self, storage_magic, sample_knowledge_data, temp_storage_dir):

            """SQLite形式での知識データ永続化テスト""" sample_knowledge_data,
            "format": "sqlite",
            "storage_path": temp_storage_dir,
            "collection_name": "knowledge_documents",
            "schema": {
                "id": "TEXT PRIMARY KEY",
                "title": "TEXT NOT NULL",
                "content": "TEXT",
                "category": "TEXT",
                "created_at": "TEXT"
            }
        }
        
        result = await storage_magic.persist_data(persistence_params)
        
        assert result["success"] is True
        persistence_result = result["persistence_result"]
        
        # SQLite データベース確認
        db_path = persistence_result["file_path"]
        assert os.path.exists(db_path)
        
        # データ確認
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_documents")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 2
        
    async def test_retrieve_persisted_data(self, storage_magic, sample_knowledge_data, temp_storage_dir):

            """永続化データの取得テスト""" sample_knowledge_data,
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "test_knowledge"
        }
        
        persist_result = await storage_magic.persist_data(persistence_params)
        storage_id = persist_result["persistence_result"]["storage_id"]
        
        # データ取得
        retrieval_params = {
            "storage_id": storage_id,
            "format": "json"
        }
        
        result = await storage_magic.retrieve_data(retrieval_params)
        
        assert result["success"] is True
        retrieved_data = result["retrieved_data"]
        
        # データ整合性確認
        assert retrieved_data["documents"][0]["title"] == "Python TDD Best Practices"
        assert retrieved_data["metadata"]["total_documents"] == 2
        
    async def test_update_persisted_data(self, storage_magic, sample_knowledge_data, temp_storage_dir):

        """永続化データの更新テスト""" sample_knowledge_data,
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "updateable_knowledge"
        }
        
        persist_result = await storage_magic.persist_data(persistence_params)
        storage_id = persist_result["persistence_result"]["storage_id"]
        
        # データ更新
        updated_data = sample_knowledge_data.copy()
        updated_data["documents"].append({
            "id": "kb_003",
            "title": "Updated Knowledge",
            "content": "This is newly added content.",
            "category": "update",
            "tags": ["new", "updated"],
            "created_at": "2025-07-23T11:30:00",
            "author": "Claude Elder"
        })
        updated_data["metadata"]["total_documents"] = 3
        
        update_params = {
            "storage_id": storage_id,
            "data": updated_data,
            "update_strategy": "replace"
        }
        
        result = await storage_magic.update_data(update_params)
        
        assert result["success"] is True
        update_result = result["update_result"]
        
        # 更新確認
        assert update_result["updated_records"] == 1
        assert update_result["new_size"] > update_result["previous_size"]
        
    async def test_delete_persisted_data(self, storage_magic, sample_knowledge_data, temp_storage_dir):

        """永続化データの削除テスト""" sample_knowledge_data,
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "deletable_knowledge"
        }
        
        persist_result = await storage_magic.persist_data(persistence_params)
        storage_id = persist_result["persistence_result"]["storage_id"]
        
        # 削除前の確認
        assert os.path.exists(persist_result["persistence_result"]["file_path"])
        
        # データ削除
        deletion_params = {
            "storage_id": storage_id,
            "delete_strategy": "complete"
        }
        
        result = await storage_magic.delete_data(deletion_params)
        
        assert result["success"] is True
        deletion_result = result["deletion_result"]
        
        # 削除確認
        assert deletion_result["deleted"] is True
        assert not os.path.exists(persist_result["persistence_result"]["file_path"])
        
    # Phase 2: 知識アーカイブ（Knowledge Archiving）
    async def test_create_knowledge_archive(self, storage_magic, temp_storage_dir):

    """知識アーカイブ作成テスト""" {
                "learning_magic": {"type": "self_evolution", "status": "completed"},
                "healing_magic": {"type": "system_recovery", "status": "completed"},
                "search_magic": {"type": "deep_exploration", "status": "in_progress"}
            },
            "four_sages": {
                "knowledge_sage": {"wisdom_level": 85, "knowledge_base_size": 1247},
                "task_sage": {"completed_tasks": 389, "success_rate": 0.94},
                "incident_sage": {"resolved_incidents": 156, "prevention_rate": 0.78},
                "rag_sage": {"search_accuracy": 0.91, "index_size": 25000}
            }
        }
        
        archive_params = {
            "data": knowledge_collection,
            "archive_name": "elders_guild_knowledge_v1",
            "storage_path": temp_storage_dir,
            "compression": "gzip",
            "metadata": {
                "version": "1.0.0",
                "created_by": "Claude Elder",
                "description": "Elders Guild knowledge archive"
            }
        }
        
        result = await storage_magic.create_archive(archive_params)
        
        assert result["success"] is True
        archive_result = result["archive_result"]
        
        # アーカイブ確認
        assert "archive_id" in archive_result
        assert "archive_path" in archive_result
        assert archive_result["compression_ratio"] > 0
        assert os.path.exists(archive_result["archive_path"])
        
    async def test_extract_knowledge_archive(self, storage_magic, temp_storage_dir):

            """知識アーカイブ展開テスト""" {
                "item1": "value1",
                "item2": "value2"
            }
        }
        
        archive_params = {
            "data": test_data,
            "archive_name": "test_archive",
            "storage_path": temp_storage_dir,
            "compression": "gzip"
        }
        
        create_result = await storage_magic.create_archive(archive_params)
        archive_id = create_result["archive_result"]["archive_id"]
        
        # アーカイブ展開
        extract_params = {
            "archive_id": archive_id,
            "extract_path": os.path.join(temp_storage_dir, "extracted"),
            "verify_integrity": True
        }
        
        result = await storage_magic.extract_archive(extract_params)
        
        assert result["success"] is True
        extract_result = result["extract_result"]
        
        # 展開確認
        assert extract_result["integrity_verified"] is True
        assert extract_result["extracted_files"] > 0
        
    async def test_search_archived_knowledge(self, storage_magic, temp_storage_dir):

        """アーカイブ内知識検索テスト""" [
                {"id": "doc1", "title": "Python Advanced Patterns", "content": "Design patterns in Python development"},
                {"id": "doc2", "title": "TDD Methodology", "content": "Test-driven development best practices"},
                {"id": "doc3", "title": "Ancient Elder Magic", "content": "Autonomous AI system with 8 magical capabilities"}
            ]
        }
        
        archive_params = {
            "data": searchable_data,
            "archive_name": "searchable_knowledge",
            "storage_path": temp_storage_dir,
            "index_for_search": True
        }
        
        create_result = await storage_magic.create_archive(archive_params)
        archive_id = create_result["archive_result"]["archive_id"]
        
        # アーカイブ内検索
        search_params = {
            "archive_id": archive_id,
            "query": "python development",
            "search_fields": ["title", "content"],
            "max_results": 10
        }
        
        result = await storage_magic.search_archive(search_params)
        
        assert result["success"] is True
        search_result = result["search_result"]
        
        # 検索結果確認
        assert len(search_result["matches"]) > 0
        assert search_result["matches"][0]["relevance_score"] > 0.5
        
    # Phase 3: 状態管理（State Management）
    async def test_persist_system_state(self, storage_magic, sample_state_data, temp_storage_dir):

    """システム状態永続化テスト""" sample_state_data,
            "state_name": "four_sages_state",
            "storage_backend": "file",  # Redis not available in test
            "storage_path": temp_storage_dir
        }
        
        result = await storage_magic.persist_state(state_params)
        
        assert result["success"] is True
        state_result = result["state_result"]
        
        # 状態永続化確認
        assert "state_id" in state_result
        assert state_result["persistence_type"] == "file"
        assert state_result["size_bytes"] > 0
        
    async def test_retrieve_system_state(self, storage_magic, sample_state_data, temp_storage_dir):

        """システム状態取得テスト""" sample_state_data,
            "state_name": "retrievable_state",
            "storage_backend": "file",
            "storage_path": temp_storage_dir
        }
        
        persist_result = await storage_magic.persist_state(state_params)
        state_id = persist_result["state_result"]["state_id"]
        
        # 状態取得
        retrieve_params = {
            "state_id": state_id,
            "storage_backend": "file"
        }
        
        result = await storage_magic.retrieve_state(retrieve_params)
        
        assert result["success"] is True
        retrieved_state = result["retrieved_state"]
        
        # 状態整合性確認
        assert retrieved_state["four_sages_status"]["knowledge_sage"]["query_count"] == 127
        assert retrieved_state["system_metrics"]["cpu_usage"] == 0.65
        
    async def test_synchronize_states(self, storage_magic, temp_storage_dir):

        """状態同期テスト""" "sage1", "status": "active", "last_update": "2025-07-23T10:00:00"}
        state2 = {"component": "sage2", "status": "active", "last_update": "2025-07-23T10:30:00"}
        
        sync_params = {
            "states": [
                {"name": "sage1_state", "data": state1},
                {"name": "sage2_state", "data": state2}
            ],
            "sync_strategy": "merge",
            "storage_backend": "file",
            "storage_path": temp_storage_dir
        }
        
        result = await storage_magic.synchronize_states(sync_params)
        
        assert result["success"] is True
        sync_result = result["sync_result"]
        
        # 同期確認
        assert sync_result["synchronized_states"] == 2
        assert sync_result["conflicts_resolved"] >= 0
        
    async def test_state_versioning(self, storage_magic, temp_storage_dir):

        """状態バージョニングテスト""" 1, "data": "initial"}
        
        version_params = {
            "state_data": initial_state,
            "state_name": "versioned_state",
            "enable_versioning": True,
            "max_versions": 5,
            "storage_path": temp_storage_dir
        }
        
        result = await storage_magic.persist_state(version_params)
        state_id = result["state_result"]["state_id"]
        
        # 状態更新（バージョン2）
        updated_state = {"version": 2, "data": "updated"}
        update_params = {
            "state_id": state_id,
            "state_data": updated_state,
            "create_version": True
        }
        
        update_result = await storage_magic.update_state(update_params)
        
        assert update_result["success"] is True
        
        # バージョン履歴確認
        history_params = {"state_id": state_id}
        history_result = await storage_magic.get_state_history(history_params)
        
        assert history_result["success"] is True
        assert len(history_result["version_history"]) == 2
        
    # Phase 4: バックアップ・復元（Backup Restoration）
    async def test_create_full_backup(self, storage_magic, temp_storage_dir):

    """完全バックアップ作成テスト"""
            file_path = os.path.join(temp_storage_dir, f"test_file_{i}.json")
            test_data = {"file_id": i, "content": f"Test content {i}"}
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            test_files[f"file_{i}"] = file_path
        
        backup_params = {
            "backup_name": "full_system_backup",
            "source_paths": [temp_storage_dir],
            "compression": "gzip",
            "backup_type": "full",
            "include_metadata": True
        }
        
        result = await storage_magic.create_backup(backup_params)
        
        assert result["success"] is True
        backup_result = result["backup_result"]
        
        # バックアップ確認
        assert "backup_id" in backup_result
        assert "backup_path" in backup_result
        assert backup_result["backup_type"] == "full"
        assert backup_result["compressed_size"] > 0
        assert os.path.exists(backup_result["backup_path"])
        
    async def test_create_incremental_backup(self, storage_magic, temp_storage_dir):

        """増分バックアップ作成テスト"""
            json.dump({"version": 1, "data": "base"}, f)
        
        # フルバックアップ作成
        full_backup_params = {
            "backup_name": "base_backup",
            "source_paths": [temp_storage_dir],
            "backup_type": "full"
        }
        
        full_result = await storage_magic.create_backup(full_backup_params)
        base_backup_id = full_result["backup_result"]["backup_id"]
        
        # ファイル変更
        with open(base_file, 'w') as f:
            json.dump({"version": 2, "data": "modified"}, f)
        
        # 新ファイル追加
        new_file = os.path.join(temp_storage_dir, "new_file.json")
        with open(new_file, 'w') as f:
            json.dump({"new": True}, f)
        
        # 増分バックアップ作成
        incremental_params = {
            "backup_name": "incremental_backup",
            "source_paths": [temp_storage_dir],
            "backup_type": "incremental",
            "base_backup_id": base_backup_id
        }
        
        result = await storage_magic.create_backup(incremental_params)
        
        assert result["success"] is True
        backup_result = result["backup_result"]
        
        # 増分バックアップ確認
        assert backup_result["backup_type"] == "incremental"
        assert backup_result["changed_files"] >= 1
        
    async def test_restore_from_backup(self, storage_magic, temp_storage_dir):

        """バックアップからの復元テスト""" True, "value": 12345}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        backup_params = {
            "backup_name": "restore_test_backup",
            "source_paths": [source_dir],
            "backup_type": "full"
        }
        
        backup_result = await storage_magic.create_backup(backup_params)
        backup_id = backup_result["backup_result"]["backup_id"]
        
        # ソースディレクトリ削除（災害シミュレーション）
        shutil.rmtree(source_dir)
        assert not os.path.exists(source_dir)
        
        # 復元実行
        restore_params = {
            "backup_id": backup_id,
            "restore_path": temp_storage_dir,
            "verify_integrity": True,
            "restore_type": "full"
        }
        
        result = await storage_magic.restore_from_backup(restore_params)
        
        assert result["success"] is True
        restore_result = result["restore_result"]
        
        # 復元確認
        assert restore_result["integrity_verified"] is True
        assert restore_result["restored_files"] > 0
        
        # データ整合性確認
        restored_file = os.path.join(temp_storage_dir, "source", "important_data.json")
        assert os.path.exists(restored_file)
        
        with open(restored_file, 'r') as f:
            restored_data = json.load(f)
        assert restored_data["value"] == 12345
        
    async def test_point_in_time_recovery(self, storage_magic, temp_storage_dir):

            """ポイント・イン・タイム復旧テスト"""
            # データ更新
            timestamp_data = {
                "version": i + 1,
                "timestamp": f"2025-07-23T10:{i*10:02d}:00",
                "data": f"Version {i + 1} data"
            }
            
            with open(data_file, 'w') as f:
                json.dump(timestamp_data, f)
            
            # バックアップ作成
            backup_params = {
                "backup_name": f"pit_backup_v{i+1}",
                "source_paths": [temp_storage_dir],
                "backup_type": "full",
                "timestamp": timestamp_data["timestamp"]
            }
            
            backup_result = await storage_magic.create_backup(backup_params)
            backups.append(backup_result["backup_result"]["backup_id"])
        
        # 特定時点への復旧（Version 2）
        recovery_params = {
            "target_timestamp": "2025-07-23T10:10:00",
            "restore_path": os.path.join(temp_storage_dir, "recovered"),
            "recovery_type": "point_in_time"
        }
        
        result = await storage_magic.point_in_time_recovery(recovery_params)
        
        assert result["success"] is True
        recovery_result = result["recovery_result"]
        
        # 復旧確認（Version 2 になっているはず）
        recovered_file = os.path.join(temp_storage_dir, "recovered", "timestamped_data.json")
        assert os.path.exists(recovered_file)
        
        with open(recovered_file, 'r') as f:
            recovered_data = json.load(f)
        assert recovered_data["version"] == 2
        
    async def test_backup_verification(self, storage_magic, temp_storage_dir):

            """バックアップ整合性検証テスト""" True, "data": "integrity verification"}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        backup_params = {
            "backup_name": "verification_test",
            "source_paths": [temp_storage_dir],
            "backup_type": "full",
            "calculate_checksums": True
        }
        
        backup_result = await storage_magic.create_backup(backup_params)
        backup_id = backup_result["backup_result"]["backup_id"]
        
        # バックアップ検証
        verification_params = {
            "backup_id": backup_id,
            "verification_type": "full",
            "check_checksums": True
        }
        
        result = await storage_magic.verify_backup(verification_params)
        
        assert result["success"] is True
        verification_result = result["verification_result"]
        
        # 検証結果確認
        assert verification_result["integrity_ok"] is True
        assert verification_result["checksum_matches"] is True
        assert verification_result["corrupted_files"] == 0
        
    # Phase 5: エラーハンドリング・エッジケース
    async def test_storage_magic_invalid_intent(self, storage_magic):

    """無効な意図での魔法発動テスト"""
        """空データの永続化テスト"""
        persistence_params = {
            "data": {},
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "empty_data"
        }
        
        result = await storage_magic.persist_data(persistence_params)
        
        assert result["success"] is True
        # 空データでも正常に処理される
        assert result["persistence_result"]["size_bytes"] >= 2  # "{}"
        
    async def test_retrieve_nonexistent_data(self, storage_magic):

        """存在しないデータの取得テスト""" "nonexistent_id_12345",
            "format": "json"
        }
        
        result = await storage_magic.retrieve_data(retrieval_params)
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
        
    async def test_backup_nonexistent_path(self, storage_magic):

        """存在しないパスのバックアップテスト""" "nonexistent_backup",
            "source_paths": ["/nonexistent/path/12345"],
            "backup_type": "full"
        }
        
        result = await storage_magic.create_backup(backup_params)
        
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "not exist" in result["error"].lower()
        
    async def test_large_data_handling(self, storage_magic, temp_storage_dir):

        """大容量データ処理テスト""" ["test_data_item_" + str(i) for i in range(10000)],
            "metadata": {
                "size": "large",
                "items": 10000,
                "description": "Large dataset for performance testing"
            }
        }
        
        persistence_params = {
            "data": large_data,
            "format": "json",
            "storage_path": temp_storage_dir,
            "collection_name": "large_dataset"
        }
        
        result = await storage_magic.persist_data(persistence_params)
        
        assert result["success"] is True
        persistence_result = result["persistence_result"]
        
        # 大容量データでも処理可能
        assert persistence_result["size_bytes"] > 100000  # 100KB以上
        
    async def test_concurrent_storage_operations(self, storage_magic, temp_storage_dir):

        """並行ストレージ操作テスト"""
            data = {"concurrent_test": i, "data": f"Concurrent operation {i}"}
            params = {
                "data": data,
                "format": "json",
                "storage_path": temp_storage_dir,
                "collection_name": f"concurrent_{i}"
            }
            task = storage_magic.persist_data(params)
            tasks.append(task)
        
        # 並行実行
        results = await asyncio.gather(*tasks)
        
        # すべての操作が成功することを確認
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert "storage_id" in result["persistence_result"]


@pytest.mark.asyncio
class TestStorageMagicIntegration:

            """Storage Magic統合テスト"""
        """包括的なストレージワークフローテスト"""
        storage_magic = StorageMagic()
        temp_dir = tempfile.mkdtemp(prefix="storage_integration_")
        
        try:
            # Step 1: データ永続化
            test_data = {
                "workflow_test": True,
                "data": "Comprehensive storage workflow test"
            }
            
            persist_params = {
                "data": test_data,
                "format": "json",
                "storage_path": temp_dir,
                "collection_name": "workflow_test"
            }
            
            persist_result = await storage_magic.persist_data(persist_params)
            assert persist_result["success"] is True
            
            storage_id = persist_result["persistence_result"]["storage_id"]
            
            # Step 2: データ取得
            retrieve_params = {
                "storage_id": storage_id,
                "format": "json"
            }
            
            retrieve_result = await storage_magic.retrieve_data(retrieve_params)
            assert retrieve_result["success"] is True
            assert retrieve_result["retrieved_data"]["workflow_test"] is True
            
            # Step 3: バックアップ作成
            backup_params = {
                "backup_name": "workflow_backup",
                "source_paths": [temp_dir],
                "backup_type": "full"
            }
            
            backup_result = await storage_magic.create_backup(backup_params)
            assert backup_result["success"] is True
            
            backup_id = backup_result["backup_result"]["backup_id"]
            
            # Step 4: データ削除
            delete_params = {
                "storage_id": storage_id,
                "delete_strategy": "complete"
            }
            
            delete_result = await storage_magic.delete_data(delete_params)
            assert delete_result["success"] is True
            
            # Step 5: バックアップから復元
            restore_params = {
                "backup_id": backup_id,
                "restore_path": os.path.join(temp_dir, "restored"),
                "verify_integrity": True
            }
            
            restore_result = await storage_magic.restore_from_backup(restore_params)
            assert restore_result["success"] is True
            
        finally:
            # クリーンアップ
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    async def test_four_sages_storage_integration(self):

                """4賢者ストレージ統合テスト"""
            # 4賢者の状態データ
            sages_data = {
                "knowledge_sage": {
                    "knowledge_count": 1247,
                    "last_query": "2025-07-23T11:00:00",
                    "wisdom_level": 89
                },
                "task_sage": {
                    "completed_tasks": 456,
                    "success_rate": 0.94,
                    "current_load": 0.67
                },
                "incident_sage": {
                    "resolved_incidents": 123,
                    "response_time_avg": 45,  # seconds
                    "prevention_rate": 0.78
                },
                "rag_sage": {
                    "search_accuracy": 0.91,
                    "index_size": 34567,
                    "last_optimization": "2025-07-23T10:30:00"
                }
            }
            
            # 4賢者データの永続化
            for sage_name, sage_data in sages_data.items():
                persist_params = {
                    "data": sage_data,
                    "format": "json",
                    "storage_path": temp_dir,
                    "collection_name": f"{sage_name}_state"
                }
                
                result = await storage_magic.persist_data(persist_params)
                assert result["success"] is True
            
            # 統合バックアップ作成
            backup_params = {
                "backup_name": "four_sages_backup",
                "source_paths": [temp_dir],
                "backup_type": "full",
                "include_metadata": True
            }
            
            backup_result = await storage_magic.create_backup(backup_params)
            assert backup_result["success"] is True
            
            # バックアップ内容検証
            verification_params = {
                "backup_id": backup_result["backup_result"]["backup_id"],
                "verification_type": "full"
            }
            
            verify_result = await storage_magic.verify_backup(verification_params)
            assert verify_result["success"] is True
            assert verify_result["verification_result"]["integrity_ok"] is True
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main(["-v", __file__])