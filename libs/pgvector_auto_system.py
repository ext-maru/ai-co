#!/usr/bin/env python3
"""
pgvector自動化システム
ファイル監視・自動更新・アラート
"""

import os
import asyncio
import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import subprocess

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBaseWatcher(FileSystemEventHandler):
    """ナレッジベースファイル監視"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = {}
        
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.md'):
            return
            
        # 重複イベント防止
        now = time.time()
        if event.src_path in self.last_modified:
            if now - self.last_modified[event.src_path] < 2.0:
                return
                
        self.last_modified[event.src_path] = now
        
        # コールバック実行
        asyncio.create_task(self.callback('modified', event.src_path))
        
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        asyncio.create_task(self.callback('created', event.src_path))
        
    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        asyncio.create_task(self.callback('deleted', event.src_path))

class PgVectorAutoSystem:
    """pgvector自動化システム"""
    
    def __init__(self):
        self.config = {
            'knowledge_base_path': '/home/aicompany/ai_co/knowledge_base',
            'sqlite_db': '/home/aicompany/ai_co/knowledge_base/integrated_knowledge.db',
            'watch_enabled': True,
            'auto_reindex_interval': 3600,  # 1時間
            'health_check_interval': 300,   # 5分
            'alert_log': '/home/aicompany/ai_co/logs/pgvector_alerts.log'
        }
        self.observer = None
        self.running = False
        self.stats = {
            'files_processed': 0,
            'last_update': None,
            'errors_count': 0,
            'start_time': datetime.now()
        }
        
    async def start_monitoring(self):
        """監視開始"""
        logger.info("🔄 pgvector自動化システム開始")
        self.running = True
        
        # ファイルシステム監視開始
        if self.config['watch_enabled']:
            await self._start_file_watcher()
            
        # 定期タスク開始
        asyncio.create_task(self._periodic_reindex())
        asyncio.create_task(self._periodic_health_check())
        
        logger.info("✅ 自動化システム稼働中")
        
    async def _start_file_watcher(self):
        """ファイル監視開始"""
        logger.info("👁️ ファイル監視開始")
        
        self.observer = Observer()
        handler = KnowledgeBaseWatcher(self._handle_file_event)
        
        self.observer.schedule(
            handler,
            self.config['knowledge_base_path'],
            recursive=True
        )
        
        self.observer.start()
        logger.info(f"📁 監視対象: {self.config['knowledge_base_path']}")
        
    async def _handle_file_event(self, event_type: str, file_path: str):
        """ファイルイベント処理"""
        logger.info(f"📝 ファイルイベント: {event_type} - {file_path}")
        
        try:
            if event_type in ['created', 'modified']:
                await self._process_file_update(file_path)
            elif event_type == 'deleted':
                await self._process_file_deletion(file_path)
                
            self.stats['files_processed'] += 1
            self.stats['last_update'] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ ファイルイベント処理エラー: {e}")
            self.stats['errors_count'] += 1
            await self._send_alert(f"ファイル処理エラー: {file_path} - {e}")
            
    async def _process_file_update(self, file_path: str):
        """ファイル更新処理"""
        try:
            # ファイル内容読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if len(content.strip()) < 50:
                logger.warning(f"⚠️ ファイルが短すぎます: {file_path}")
                return
                
            # メタデータ生成
            relative_path = os.path.relpath(file_path, self.config['knowledge_base_path'])
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # SQLiteデータベース更新
            await self._update_sqlite_record(relative_path, content, file_hash)
            
            logger.info(f"✅ ファイル更新完了: {relative_path}")
            
        except Exception as e:
            logger.error(f"❌ ファイル更新エラー {file_path}: {e}")
            raise
            
    async def _process_file_deletion(self, file_path: str):
        """ファイル削除処理"""
        try:
            relative_path = os.path.relpath(file_path, self.config['knowledge_base_path'])
            
            # SQLiteから削除
            conn = sqlite3.connect(self.config['sqlite_db'])
            cursor = conn.execute(
                "DELETE FROM knowledge_documents WHERE source_file = ?",
                [relative_path]
            )
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ ファイル削除完了: {relative_path} ({deleted_count}レコード削除)")
            
        except Exception as e:
            logger.error(f"❌ ファイル削除エラー {file_path}: {e}")
            raise
            
    async def _update_sqlite_record(self, source_file: str, content: str, file_hash: str):
        """SQLiteレコード更新"""
        try:
            conn = sqlite3.connect(self.config['sqlite_db'])
            
            # 既存レコード確認
            cursor = conn.execute(
                "SELECT file_hash FROM knowledge_documents WHERE source_file = ? LIMIT 1",
                [source_file]
            )
            existing = cursor.fetchone()
            
            if existing and existing[0] == file_hash:
                # ハッシュが同じ場合は更新不要
                conn.close()
                return
                
            # 既存レコード削除
            conn.execute("DELETE FROM knowledge_documents WHERE source_file = ?", [source_file])
            
            # 新レコード挿入
            import uuid
            from libs.knowledge_integration_mapper import KnowledgeIntegrationMapper
            
            mapper = KnowledgeIntegrationMapper()
            title = Path(source_file).stem
            priority = mapper.get_file_priority(source_file)
            category = mapper.categorize_file(source_file)
            chunks = mapper.chunk_content(content)
            
            for i, chunk in enumerate(chunks):
                doc_uuid = str(uuid.uuid4())
                metadata = {
                    'processed_at': datetime.now().isoformat(),
                    'auto_updated': True,
                    'chunk_size': len(chunk),
                    'update_source': 'file_watcher'
                }
                
                conn.execute("""
                    INSERT INTO knowledge_documents (
                        uuid, title, content, source_file, file_hash,
                        chunk_index, total_chunks, category, priority,
                        file_size, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    doc_uuid, title, chunk, source_file, file_hash,
                    i, len(chunks), category, priority,
                    len(content), json.dumps(metadata)
                ])
                
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ SQLite更新エラー: {e}")
            raise
            
    async def _periodic_reindex(self):
        """定期再インデックス"""
        while self.running:
            try:
                await asyncio.sleep(self.config['auto_reindex_interval'])
                
                if not self.running:
                    break
                    
                logger.info("🔄 定期再インデックス開始")
                
                # PostgreSQL統合管理システム使用
                cmd = ['python3', '/home/aicompany/ai_co/libs/pgvector_unified_manager.py', 'migrate']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ 定期再インデックス完了")
                else:
                    logger.error(f"❌ 定期再インデックス失敗: {result.stderr}")
                    await self._send_alert(f"定期再インデックス失敗: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"❌ 定期再インデックスエラー: {e}")
                await self._send_alert(f"定期再インデックスエラー: {e}")
                
    async def _periodic_health_check(self):
        """定期ヘルスチェック"""
        while self.running:
            try:
                await asyncio.sleep(self.config['health_check_interval'])
                
                if not self.running:
                    break
                    
                # ヘルスチェック実行
                cmd = ['python3', '/home/aicompany/ai_co/libs/pgvector_unified_manager.py', 'health']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    health_data = json.loads(result.stdout)
                    
                    if health_data['overall_status'] == 'error':
                        await self._send_alert(f"システムエラー検出: {health_data}")
                    elif health_data['overall_status'] == 'degraded':
                        logger.warning(f"⚠️ システム機能低下: {health_data}")
                        
                else:
                    await self._send_alert(f"ヘルスチェック失敗: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"❌ 定期ヘルスチェックエラー: {e}")
                
    async def _send_alert(self, message: str):
        """アラート送信"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'system': 'pgvector_auto_system',
            'stats': self.stats
        }
        
        # ログファイルに記録
        try:
            os.makedirs(os.path.dirname(self.config['alert_log']), exist_ok=True)
            with open(self.config['alert_log'], 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ アラートログ書き込みエラー: {e}")
            
        logger.error(f"🚨 アラート: {message}")
        
    async def get_status(self) -> Dict[str, Any]:
        """システム状況取得"""
        uptime = datetime.now() - self.stats['start_time']
        
        # JSON直列化可能な形式に変換
        stats_json = self.stats.copy()
        stats_json['start_time'] = self.stats['start_time'].isoformat()
        if stats_json.get('last_update'):
            stats_json['last_update'] = stats_json['last_update'].isoformat()
        
        return {
            'running': self.running,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime),
            'stats': stats_json,
            'config': self.config,
            'file_watcher_active': self.observer is not None and self.observer.is_alive() if self.observer else False
        }
        
    async def stop(self):
        """システム停止"""
        logger.info("🛑 pgvector自動化システム停止")
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        logger.info("✅ システム停止完了")

# コマンドライン運用
async def main():
    """メイン運用"""
    import sys
    
    auto_system = PgVectorAutoSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'daemon':
        # デーモンモード
        try:
            await auto_system.start_monitoring()
            
            # 無限ループで稼働
            while auto_system.running:
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("📝 停止シグナル受信")
        finally:
            await auto_system.stop()
            
    elif len(sys.argv) > 1 and sys.argv[1] == 'status':
        # 状況確認モード
        # 実行中のプロセスがあるか確認
        status = await auto_system.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    else:
        print("使用方法:")
        print("  python3 pgvector_auto_system.py daemon   # デーモン起動")
        print("  python3 pgvector_auto_system.py status   # 状況確認")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))