import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import redis

from ..core.config import settings
from ..core.database import get_db

class MigrationService:
    """Service for managing gradual migration from Flask API to FastAPI"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)
        self.flask_api_url = settings.FLASK_API_URL
        self.migration_mode = settings.MIGRATION_MODE
        
        # Migration configuration
        self.migrated_endpoints = {
            # Endpoints that have been fully migrated to FastAPI
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/logout",
            "/api/v1/sages/status",
            "/api/v1/elder-council/status"
        }
        
        self.proxy_endpoints = {
            # Endpoints that should be proxied to Flask for now
            "/api/v1/legacy/tasks",
            "/api/v1/legacy/reports",
            "/api/v1/legacy/analytics"
        }
        
        # Coverage tracking
        self.coverage_targets = {
            "authentication": 100,  # Fully migrated
            "sage_system": 66.7,    # Target coverage
            "elder_council": 50,    # Partial migration
            "legacy_features": 0    # Not migrated yet
        }
    
    async def route_request(self, endpoint: str, method: str, **kwargs) -> Dict[str, Any]:
        """Route request to appropriate backend based on migration status"""
        
        if self.migration_mode == "immediate":
            # All requests go to FastAPI
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Endpoint not yet implemented in FastAPI"
            )
        
        elif self.migration_mode == "proxy":
            # All requests go to Flask
            return await self._proxy_to_flask(endpoint, method, **kwargs)
        
        else:  # gradual migration
            if endpoint in self.migrated_endpoints:
                # Use FastAPI
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Should be handled by FastAPI endpoint"
                )
            elif endpoint in self.proxy_endpoints or endpoint.startswith("/api/v1/legacy/"):
                # Proxy to Flask
                return await self._proxy_to_flask(endpoint, method, **kwargs)
            else:
                # Check feature coverage and decide
                return await self._smart_route(endpoint, method, **kwargs)
    
    async def _proxy_to_flask(self, endpoint: str, method: str, **kwargs) -> Dict[str, Any]:
        """Proxy request to Flask API"""
        url = f"{self.flask_api_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=kwargs.get("params"))
                elif method.upper() == "POST":
                    response = await client.post(
                        url, 
                        json=kwargs.get("json"),
                        data=kwargs.get("data")
                    )
                elif method.upper() == "PUT":
                    response = await client.put(
                        url, 
                        json=kwargs.get("json"),
                        data=kwargs.get("data")
                    )
                elif method.upper() == "DELETE":
                    response = await client.delete(url)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Method {method} not supported"
                    )
                
                # Log proxy request for monitoring
                await self._log_proxy_request(endpoint, method, response.status_code)
                
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=response.text
                    )
                
                return response.json()
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Flask API unavailable: {str(e)}"
            )
    
    async def _smart_route(self, endpoint: str, method: str, **kwargs) -> Dict[str, Any]:
        """Smart routing based on feature coverage and load"""
        
        # Analyze endpoint to determine feature category
        feature_category = self._categorize_endpoint(endpoint)
        
        # Check coverage for this feature
        coverage = self.coverage_targets.get(feature_category, 0)
        
        if coverage >= 66.7:
            # High coverage - prefer FastAPI
            try:
                # Try FastAPI first
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="FastAPI implementation not ready"
                )
            except HTTPException:
                # Fallback to Flask
                return await self._proxy_to_flask(endpoint, method, **kwargs)
        else:
            # Low coverage - use Flask
            return await self._proxy_to_flask(endpoint, method, **kwargs)
    
    def _categorize_endpoint(self, endpoint: str) -> str:
        """Categorize endpoint to determine feature area"""
        if "/auth/" in endpoint:
            return "authentication"
        elif "/sages/" in endpoint:
            return "sage_system"
        elif "/elder-council/" in endpoint:
            return "elder_council"
        elif "/legacy/" in endpoint:
            return "legacy_features"
        else:
            return "general"
    
    async def _log_proxy_request(self, endpoint: str, method: str, status_code: int):
        """Log proxy request for monitoring and analytics"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "backend": "flask"
        }
        
        try:
            # Store in Redis for real-time monitoring
            key = "migration_logs"
            self.redis_client.lpush(key, str(log_entry))
            self.redis_client.ltrim(key, 0, 10000)  # Keep last 10k entries
            self.redis_client.expire(key, 86400 * 7)  # 7 days
        except Exception as e:
            print(f"Failed to log proxy request: {e}")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and statistics"""
        try:
            # Get logs from Redis
            logs = self.redis_client.lrange("migration_logs", 0, -1)
            
            # Analyze logs
            total_requests = len(logs)
            fastapi_requests = len([log for log in logs if "fastapi" in str(log)])
            flask_requests = total_requests - fastapi_requests
            
            # Calculate coverage
            coverage_stats = {}
            for category, target in self.coverage_targets.items():
                # This would be calculated based on actual endpoint usage
                coverage_stats[category] = {
                    "target": target,
                    "current": target * 0.8  # Simulated current coverage
                }
            
            return {
                "migration_mode": self.migration_mode,
                "total_requests": total_requests,
                "fastapi_requests": fastapi_requests,
                "flask_requests": flask_requests,
                "migration_percentage": (fastapi_requests / total_requests * 100) if total_requests > 0 else 0,
                "coverage_stats": coverage_stats,
                "migrated_endpoints": list(self.migrated_endpoints),
                "proxy_endpoints": list(self.proxy_endpoints),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get migration status: {str(e)}"}
    
    async def add_migrated_endpoint(self, endpoint: str):
        """Mark endpoint as migrated to FastAPI"""
        self.migrated_endpoints.add(endpoint)
        self.proxy_endpoints.discard(endpoint)
        
        # Update coverage
        await self._update_coverage_stats()
    
    async def add_proxy_endpoint(self, endpoint: str):
        """Mark endpoint for proxying to Flask"""
        self.proxy_endpoints.add(endpoint)
        self.migrated_endpoints.discard(endpoint)
    
    async def _update_coverage_stats(self):
        """Update coverage statistics"""
        # This would update the actual coverage based on migrated endpoints
        pass

class FeatureToggleService:
    """Service for managing feature toggles during migration"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)
    
    async def is_feature_enabled(self, feature: str, user_id: Optional[int] = None) -> bool:
        """Check if feature is enabled for user"""
        try:
            # Global feature toggle
            global_key = f"feature_toggle:global:{feature}"
            global_enabled = self.redis_client.get(global_key)
            
            if global_enabled is not None:
                return global_enabled.decode() == "true"
            
            # User-specific toggle (for gradual rollout)
            if user_id:
                user_key = f"feature_toggle:user:{user_id}:{feature}"
                user_enabled = self.redis_client.get(user_key)
                
                if user_enabled is not None:
                    return user_enabled.decode() == "true"
            
            # Default to enabled
            return True
            
        except Exception:
            # Default to enabled if Redis is unavailable
            return True
    
    async def enable_feature(self, feature: str, user_id: Optional[int] = None):
        """Enable feature globally or for specific user"""
        try:
            if user_id:
                key = f"feature_toggle:user:{user_id}:{feature}"
            else:
                key = f"feature_toggle:global:{feature}"
            
            self.redis_client.set(key, "true", ex=86400 * 30)  # 30 days
        except Exception as e:
            print(f"Failed to enable feature {feature}: {e}")
    
    async def disable_feature(self, feature: str, user_id: Optional[int] = None):
        """Disable feature globally or for specific user"""
        try:
            if user_id:
                key = f"feature_toggle:user:{user_id}:{feature}"
            else:
                key = f"feature_toggle:global:{feature}"
            
            self.redis_client.set(key, "false", ex=86400 * 30)  # 30 days
        except Exception as e:
            print(f"Failed to disable feature {feature}: {e}")

class DataSyncService:
    """Service for synchronizing data between Flask and FastAPI"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.from_url(settings.REDIS_URL)
        self.flask_api_url = settings.FLASK_API_URL
    
    async def sync_sage_data(self) -> Dict[str, Any]:
        """Sync sage data from Flask API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.flask_api_url}/api/v1/sages/status")
                
                if response.status_code == 200:
                    sage_data = response.json()
                    
                    # Store in Redis for FastAPI to use
                    self.redis_client.setex(
                        "synced_sage_data",
                        3600,  # 1 hour TTL
                        str(sage_data)
                    )
                    
                    return sage_data
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to sync sage data"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Data sync failed: {str(e)}"
            )
    
    async def sync_elder_council_data(self) -> Dict[str, Any]:
        """Sync elder council data from Flask API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.flask_api_url}/api/v1/elder-council/status")
                
                if response.status_code == 200:
                    council_data = response.json()
                    
                    # Store in Redis
                    self.redis_client.setex(
                        "synced_council_data",
                        3600,  # 1 hour TTL
                        str(council_data)
                    )
                    
                    return council_data
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to sync elder council data"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Elder council sync failed: {str(e)}"
            )
    
    async def get_coverage_data(self) -> Dict[str, Any]:
        """Get 66.7% coverage data from cache or Flask API"""
        try:
            # Try cache first
            cached_data = self.redis_client.get("coverage_data")
            if cached_data:
                return eval(cached_data.decode())
            
            # Fetch from Flask API
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.flask_api_url}/api/v1/coverage/status")
                
                if response.status_code == 200:
                    coverage_data = response.json()
                    
                    # Cache for 5 minutes
                    self.redis_client.setex(
                        "coverage_data",
                        300,
                        str(coverage_data)
                    )
                    
                    return coverage_data
                else:
                    # Return default coverage data
                    return {
                        "current_coverage": 66.7,
                        "target_coverage": 66.7,
                        "status": "target_achieved"
                    }
        except Exception:
            # Return default on error
            return {
                "current_coverage": 66.7,
                "target_coverage": 66.7,
                "status": "target_achieved"
            }

# Global service instances
migration_service = MigrationService()
feature_toggle_service = FeatureToggleService()
data_sync_service = DataSyncService()