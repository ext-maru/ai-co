#!/usr/bin/env python3
"""
Upload Image プロジェクト直接作成スクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.project_scaffolder import ProjectScaffolder


async def create_upload_image_project():
    """Upload Imageプロジェクトを直接作成"""

    # プロジェクト設定
    config = {
        "name": "upload-image-service",
        "type": "upload-service",
        "description": "画像アップロード管理システム - 承認フロー付き",
        "backend": "fastapi",
        "frontend": "react-ts",
        "database": "postgresql",
        "features": [
            "multi-upload",
            "image-preview",
            "progress-tracking",
            "auth",
            "approval-flow",
            "cloud-storage",
            "image-optimization",
            "responsive",
        ],
        "storage": "google-drive",
        "elders_integration": ["tdd", "four-sages", "quality-dashboard", "cicd"],
        "docker": True,
        "deployment": "docker-compose",
    }

    print("🚀 Upload Image Service プロジェクト生成開始...")

    # スキャフォルダー実行
    scaffolder = ProjectScaffolder()
    project_path = await scaffolder.create_project(config)

    print(f"✅ プロジェクト作成完了: {project_path}")
    print("\n🎯 次のステップ:")
    print(f"  cd {project_path}")
    print("  docker-compose up")
    print("\n📊 PDCA分析:")
    print("  ai-project pdca upload-image-service")


if __name__ == "__main__":
    asyncio.run(create_upload_image_project())
