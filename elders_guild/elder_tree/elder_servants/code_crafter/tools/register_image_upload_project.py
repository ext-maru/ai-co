#!/usr/bin/env python3
"""
image-upload-managerプロジェクトをElder階層プロジェクト管理システムに登録
"""

import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_project_manager import (
    ElderProjectManager,
    ElderRole,
    ProjectInfo,
    ProjectPriority,
    ProjectStatus,
)
from libs.unified_auth_provider import User, create_demo_auth_system


def main():
    """mainメソッド"""
    # 認証システム初期化（デモユーザーを使用）
    auth_system = create_demo_auth_system()

    # プロジェクト管理システム初期化
    manager = ElderProjectManager(auth_system)

    # プロジェクト情報作成
    project_info = ProjectInfo(
        id="image-upload-manager",
        name="画像アップロード管理システム",
        path="/home/aicompany/ai_co/projects/image-upload-manager",
        description="顧客が画像をアップロードし、管理者が承認・管理できるWebアプリケーション",
        status=ProjectStatus.DEVELOPMENT,
        priority=ProjectPriority.MEDIUM,
        owner="claude_elder",
        elder_role=ElderRole.CLAUDE_ELDER,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        file_count=0,  # scan_projectsで自動更新される
        size_mb=0.0,  # scan_projectsで自動更新される
        tags=["web-app", "docker", "google-drive", "image-upload"],
        dependencies=["flask", "google-api-python-client", "docker"],
        progress=1.0,  # 100%完了
        estimated_completion=None,
        actual_completion=datetime.now(),  # 既に完了
    )

    # プロジェクトを登録
    print("🏛️ Elder階層プロジェクト管理システム - プロジェクト登録")
    print("=" * 60)
    print(f"📋 プロジェクトID: {project_info.id}")
    print(f"📝 プロジェクト名: {project_info.name}")
    print(f"📊 ステータス: {project_info.status.value}")
    print(f"⚡ 優先度: {project_info.priority.value}")
    print(f"👤 所有者: {project_info.owner}")
    print(f"🏛️ Elder権限: {project_info.elder_role.value}")
    print(f"📊 進捗: {project_info.progress*100:0.1f}%")
    print(f"🏷️ タグ: {', '.join(project_info.tags)}")
    print("")

    manager.register_project(project_info)
    print("✅ プロジェクトが正常に登録されました！")

    # プロジェクトスキャンを実行して詳細情報を更新
    print("\n📂 プロジェクトディレクトリをスキャン中...")
    manager.scan_projects()

    # 登録されたプロジェクトの詳細を表示
    user = User(
        username="claude_elder", elder_role=ElderRole.CLAUDE_ELDER, sage_type=None
    )
    registered_project = manager.get_project_details("image-upload-manager", user)

    if registered_project:
        print("\n📋 登録されたプロジェクトの詳細:")
        print(f"   📁 ファイル数: {registered_project.file_count}")
        print(f"   💾 サイズ: {registered_project.size_mb} MB")
        print(
            f"   📅 更新日時: {registered_project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    print("\n✨ 登録処理が完了しました！")


if __name__ == "__main__":
    main()
