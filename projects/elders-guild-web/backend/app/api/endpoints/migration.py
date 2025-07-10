from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...core.security import require_elder
from ...models.auth import User
from ...services.migration_service import data_sync_service
from ...services.migration_service import feature_toggle_service
from ...services.migration_service import migration_service

router = APIRouter()


@router.get("/status")
async def get_migration_status(current_user: User = Depends(require_elder), db: Session = Depends(get_db)):
    """Get current migration status - Elder access required"""
    return await migration_service.get_migration_status()


@router.post("/sync/sages")
async def sync_sage_data(current_user: User = Depends(require_elder), db: Session = Depends(get_db)):
    """Sync sage data from Flask API - Elder access required"""
    return await data_sync_service.sync_sage_data()


@router.post("/sync/elder-council")
async def sync_elder_council_data(current_user: User = Depends(require_elder), db: Session = Depends(get_db)):
    """Sync elder council data from Flask API - Elder access required"""
    return await data_sync_service.sync_elder_council_data()


@router.get("/coverage")
async def get_coverage_data(current_user: User = Depends(get_current_user)):
    """Get 66.7% coverage system data"""
    return await data_sync_service.get_coverage_data()


@router.post("/feature-toggle/{feature}")
async def toggle_feature(
    feature: str, enabled: bool, user_id: Optional[int] = None, current_user: User = Depends(require_elder)
):
    """Toggle feature flag - Elder access required"""
    if enabled:
        await feature_toggle_service.enable_feature(feature, user_id)
    else:
        await feature_toggle_service.disable_feature(feature, user_id)

    return {
        "feature": feature,
        "enabled": enabled,
        "user_id": user_id,
        "message": f"Feature {feature} {'enabled' if enabled else 'disabled'}",
    }


@router.get("/feature-toggle/{feature}")
async def check_feature(feature: str, current_user: User = Depends(get_current_user)):
    """Check if feature is enabled for current user"""
    enabled = await feature_toggle_service.is_feature_enabled(feature, current_user.id)

    return {"feature": feature, "enabled": enabled, "user_id": current_user.id}


@router.post("/migrate-endpoint")
async def migrate_endpoint(
    endpoint: str, action: str, current_user: User = Depends(require_elder)  # "migrate" or "proxy"
):
    """Migrate endpoint between FastAPI and Flask - Elder access required"""
    if action == "migrate":
        await migration_service.add_migrated_endpoint(endpoint)
        message = f"Endpoint {endpoint} migrated to FastAPI"
    elif action == "proxy":
        await migration_service.add_proxy_endpoint(endpoint)
        message = f"Endpoint {endpoint} set to proxy to Flask"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'migrate' or 'proxy'")

    return {"endpoint": endpoint, "action": action, "message": message}
