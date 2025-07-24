"""
🗄️ Ancient Magic Audit Cache System
監査結果のキャッシング機構
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AuditCache:
    """監査結果のキャッシュシステム"""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """
        Args:
            cache_dir: キャッシュディレクトリ
            ttl_hours: キャッシュ有効期限（時間）
        """
        self.cache_dir = cache_dir or Path.home() / ".ancient_magic_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        # キャッシュ統計
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
    def _generate_cache_key(self, auditor: str, target: Dict[str, Any]) -> str:
        """キャッシュキーを生成"""
        # ターゲット情報をソートして一貫性を保つ
        target_str = json.dumps(target, sort_keys=True)
        combined = f"{auditor}:{target_str}"
        
        # SHA256ハッシュでキーを生成
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, auditor: str, target: Dict[str, Any]) -> Optional[Dict[str, Any]]cache_key = self._generate_cache_key(auditor, target)
    """キャッシュから結果を取得"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            self.stats["misses"] += 1
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                
            # 有効期限チェック
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.now() - cached_time > self.ttl:
                # 期限切れ
                cache_file.unlink()
                self.stats["evictions"] += 1
                self.stats["misses"] += 1
                return None
                
            self.stats["hits"] += 1
            logger.info(f"Cache hit for {auditor}: {cache_key[:8]}...")
            return cached_data["result"]
            
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, auditor: str, target: Dict[str, Any], result: Dict[str, Any])cache_key = self._generate_cache_key(auditor, target)
    """結果をキャッシュに保存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cached_data = {
                "timestamp": datetime.now().isoformat(),
                "auditor": auditor,
                "target": target,
                "result": result
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2, default=str)
                
            logger.info(f"Cached result for {auditor}: {cache_key[:8]}...")
            
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def clear(self, auditor: Optional[str] = None):
        """キャッシュをクリア"""
        if auditor:
            # 特定の監査者のキャッシュのみクリア
            pattern = f"*{auditor}*"
        else:
            # 全キャッシュクリア
            pattern = "*.json"
            
        cleared = 0
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
                cleared += 1
            except Exception as e:
                logger.error(f"Failed to delete cache file {cache_file}: {e}")
                
        logger.info(f"Cleared {cleared} cache entries")
        return cleared
    
    def cleanup_expired(self):
        """期限切れのキャッシュを削除"""
        cleaned = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                cached_time = datetime.fromisoformat(cached_data["timestamp"])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    cleaned += 1
                    
            except Exception as e:
                logger.error(f"Cleanup error for {cache_file}: {e}")
                
        self.stats["evictions"] += cleaned
        logger.info(f"Cleaned up {cleaned} expired cache entries")
        return cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / max(1, total_requests) * 100
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": f"{hit_rate:0.1f}%",
            "total_requests": total_requests,
            "cache_size": len(list(self.cache_dir.glob("*.json")))
        }
    
    def get_size(self) -> Dict[str, Any]:
        """キャッシュサイズ情報を取得"""
        total_size = 0
        file_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            total_size += cache_file.stat().st_size
            file_count += 1
            
        return {
            "files": file_count,
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
            "directory": str(self.cache_dir)
        }


class CachedAuditEngine:
    """キャッシュ機能付き監査エンジンラッパー"""
    
    def __init__(self, engine, cache: Optional[AuditCache] = None):
        """初期化メソッド"""
        self.engine = engine
        self.cache = cache or AuditCache()
        
    async def run_comprehensive_audit(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュを使用した包括的監査"""
        # キャッシュキーとして使用
        cache_key = f"comprehensive_{json.dumps(target, sort_keys}"
        
        # キャッシュチェック
        cached_result = self.cache.get("comprehensive", target)
        if cached_result:
            # キャッシュヒット
            cached_result["from_cache"] = True
            cached_result["cache_stats"] = self.cache.get_stats()
            return cached_result
            
        # キャッシュミス - 実際の監査を実行
        start_time = time.time()
        result = await self.engine.run_comprehensive_audit(target)
        execution_time = time.time() - start_time
        
        # 結果をキャッシュ
        if result and "error" not in result:
            self.cache.set("comprehensive", target, result)
            
        # キャッシュ情報を追加
        result["from_cache"] = False
        result["actual_execution_time"] = execution_time
        result["cache_stats"] = self.cache.get_stats()
        
        return result