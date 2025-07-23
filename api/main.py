#!/usr/bin/env python3
"""
🚀 Project Web Portal API
FastAPIバックエンド実装

RAGエルダー推奨アーキテクチャによる高性能API
プロジェクト一覧表示・自動資料生成・類似検索機能

Author: Claude Elder
Date: 2025-07-10
Architecture: RAG Elder Recommended
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(PROJECT_ROOT))

from libs.project_web_portal import (
    ProjectDocumentation,
    ProjectMetadata,
    ProjectStatus,
    ProjectType,
    ProjectWebPortal,
)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリ初期化
app = FastAPI(
    title="Elders Guild Project Web Portal API",
    description="RAGエルダー推奨による自動プロジェクト管理・資料生成API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルポータルインスタンス
portal = ProjectWebPortal()


# Pydantic Models
class ProjectSummary(BaseModel):
    """プロジェクト要約"""

    project_id: str
    name: str
    project_type: str
    status: str
    tech_stack: List[str]
    description: str
    updated_at: str


class ProjectDetail(BaseModel):
    """プロジェクト詳細"""

    project_id: str
    name: str
    path: str
    project_type: str
    status: str
    tech_stack: List[str]
    description: str
    created_at: str
    updated_at: str
    code_structure: Optional[Dict[str, Any]] = None
    git_metrics: Optional[Dict[str, Any]] = None
    dependencies: List[Dict[str, Any]] = []


class DocumentationResponse(BaseModel):
    """資料レスポンス"""

    project_id: str
    generated_at: str
    overview: str
    architecture: str
    setup_guide: str
    api_reference: str
    usage_examples: str
    diagrams: Dict[str, str]
    quality_score: float
    related_projects: List[Dict[str, Any]] = []


class SimilarProject(BaseModel):
    """類似プロジェクト"""

    project_id: str
    name: str
    description: str
    similarity: float
    tech_stack: List[str]


class ScanRequest(BaseModel):
    """スキャン要求"""

    root_path: Optional[str] = None
    force_refresh: bool = False


class GenerateDocsRequest(BaseModel):
    """資料生成要求"""

    project_id: str
    include_similar: bool = True


# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Project Web Portal API",
        "version": "1.0.0",
    }


# プロジェクト一覧取得
@app.get("/api/projects", response_model=List[ProjectSummary])
async def get_projects(
    project_type: Optional[str] = Query(None, description="プロジェクトタイプフィルター"),
    status: Optional[str] = Query(None, description="ステータスフィルター"),
    tech_stack: Optional[str] = Query(None, description="技術スタックフィルター"),
    limit: int = Query(50, ge=1, le=100, description="取得件数制限"),
    offset: int = Query(0, ge=0, description="オフセット"),
):
    """
    プロジェクト一覧取得

    - **project_type**: プロジェクトタイプでフィルタ
    - **status**: ステータスでフィルタ
    - **tech_stack**: 技術スタックでフィルタ
    - **limit**: 取得件数制限
    - **offset**: ページネーション用オフセット
    """
    try:
        logger.info(f"プロジェクト一覧取得: type={project_type}, status={status}")

        projects = await portal.get_project_list()

        # フィルタリング
        filtered_projects = projects

        if project_type:
            filtered_projects = [
                p for p in filtered_projects if p["project_type"] == project_type
            ]

        if status:
            filtered_projects = [p for p in filtered_projects if p["status"] == status]

        if tech_stack:
            filtered_projects = [
                p
                for p in filtered_projects
                if tech_stack.lower() in [tech.lower() for tech in p["tech_stack"]]
            ]

        # ページネーション
        total = len(filtered_projects)
        paginated = filtered_projects[offset : offset + limit]

        response_projects = [
            ProjectSummary(
                project_id=p["project_id"],
                name=p["name"],
                project_type=p["project_type"],
                status=p["status"],
                tech_stack=p["tech_stack"],
                description=p["description"],
                updated_at=p["updated_at"],
            )
            for p in paginated
        ]

        logger.info(f"プロジェクト一覧返却: {len(response_projects)}件 (total: {total})")
        return response_projects

    except Exception as e:
        logger.error(f"プロジェクト一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# プロジェクト詳細取得
@app.get("/api/projects/{project_id}", response_model=ProjectDetail)
async def get_project_detail(project_id: str):
    """
    プロジェクト詳細取得

    - **project_id**: プロジェクトID
    """
    try:
        logger.info(f"プロジェクト詳細取得: {project_id}")

        project_data = await portal.get_project_details(project_id)

        if not project_data:
            raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

        detail = ProjectDetail(**project_data)

        logger.info(f"プロジェクト詳細返却: {detail.name}")
        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"プロジェクト詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# プロジェクトスキャン
@app.post("/api/projects/scan")
async def scan_projects(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    プロジェクトスキャン実行

    - **root_path**: スキャン対象ルートパス（省略時はデフォルト）
    - **force_refresh**: 強制更新フラグ
    """
    try:
        logger.info(f"プロジェクトスキャン開始: path={request.root_path}")

        # バックグラウンドでスキャン実行
        background_tasks.add_task(
            execute_project_scan, request.root_path, request.force_refresh
        )

        return {
            "message": "プロジェクトスキャンを開始しました",
            "status": "started",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"プロジェクトスキャンエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_project_scan(root_path: Optional[str], force_refresh: bool):
    """プロジェクトスキャン実行"""
    try:
        scan_path = Path(root_path) if root_path else PROJECT_ROOT
        projects = await portal.scan_projects(scan_path)
        logger.info(f"プロジェクトスキャン完了: {len(projects)}件")
    except Exception as e:
        logger.error(f"プロジェクトスキャン実行エラー: {e}")


# 資料生成
@app.post(
    "/api/projects/{project_id}/documentation", response_model=DocumentationResponse
)
async def generate_documentation(
    project_id: str, request: GenerateDocsRequest, background_tasks: BackgroundTasks
):
    """
    プロジェクト資料自動生成

    - **project_id**: プロジェクトID
    - **include_similar**: 類似プロジェクト含める
    """
    try:
        logger.info(f"資料生成開始: {project_id}")

        # 即座にレスポンス返却、バックグラウンドで生成
        background_tasks.add_task(
            execute_documentation_generation, project_id, request.include_similar
        )

        # 既存の資料があれば返却
        project_data = await portal.get_project_details(project_id)
        if project_data and "documentation" in project_data:
            doc = project_data["documentation"]
            return DocumentationResponse(
                project_id=project_id,
                generated_at=datetime.now().isoformat(),
                overview=doc.get("overview", ""),
                architecture=doc.get("architecture", ""),
                setup_guide=doc.get("setup_guide", ""),
                api_reference=doc.get("api_reference", ""),
                usage_examples=doc.get("usage_examples", ""),
                diagrams=doc.get("diagrams", {}),
                quality_score=doc.get("quality_score", 0.0),
                related_projects=[],
            )
        else:
            # 新規生成中のレスポンス
            return DocumentationResponse(
                project_id=project_id,
                generated_at=datetime.now().isoformat(),
                overview="📄 資料生成中...",
                architecture="🏗️ アーキテクチャ解析中...",
                setup_guide="📋 セットアップガイド作成中...",
                api_reference="🔍 API解析中...",
                usage_examples="💡 使用例生成中...",
                diagrams={},
                quality_score=0.0,
                related_projects=[],
            )

    except Exception as e:
        logger.error(f"資料生成エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_documentation_generation(project_id: str, include_similar: bool):
    """資料生成実行"""
    try:
        documentation = await portal.generate_project_documentation(project_id)
        if documentation:
            logger.info(f"資料生成完了: {project_id} (品質: {documentation.quality_score:.2f})")
        else:
            logger.warning(f"資料生成失敗: {project_id}")
    except Exception as e:
        logger.error(f"資料生成実行エラー: {e}")


# 類似プロジェクト検索
@app.get("/api/projects/{project_id}/similar", response_model=List[SimilarProject])
async def find_similar_projects(
    project_id: str, limit: int = Query(5, ge=1, le=20, description="取得件数制限")
):
    """
    類似プロジェクト検索

    - **project_id**: 基準プロジェクトID
    - **limit**: 取得件数制限
    """
    try:
        logger.info(f"類似プロジェクト検索: {project_id}")

        similar_projects = await portal.find_similar_projects(project_id, limit)

        response_projects = [
            SimilarProject(
                project_id=p["project_id"],
                name=p["name"],
                description=p["description"],
                similarity=p["similarity"],
                tech_stack=p["tech_stack"],
            )
            for p in similar_projects
        ]

        logger.info(f"類似プロジェクト返却: {len(response_projects)}件")
        return response_projects

    except Exception as e:
        logger.error(f"類似プロジェクト検索エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 統計情報取得
@app.get("/api/stats")
async def get_statistics():
    """
    統計情報取得
    """
    try:
        projects = await portal.get_project_list()

        # 基本統計
        total_projects = len(projects)

        # プロジェクトタイプ別集計
        type_counts = {}
        status_counts = {}
        tech_counts = {}

        for project in projects:
            # タイプ別
            ptype = project["project_type"]
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

            # ステータス別
            status = project["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

            # 技術スタック別
            for tech in project["tech_stack"]:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1

        return {
            "timestamp": datetime.now().isoformat(),
            "total_projects": total_projects,
            "by_type": type_counts,
            "by_status": status_counts,
            "by_tech_stack": tech_counts,
            "most_used_tech": max(tech_counts.items(), key=lambda x: x[1])
            if tech_counts
            else None,
        }

    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 検索エンドポイント
@app.get("/api/search")
async def search_projects(
    q: str = Query(..., description="検索クエリ"),
    limit: int = Query(20, ge=1, le=50, description="取得件数制限"),
):
    """
    プロジェクト検索

    - **q**: 検索クエリ（名前、説明、技術スタックで検索）
    - **limit**: 取得件数制限
    """
    try:
        logger.info(f"プロジェクト検索: '{q}'")

        projects = await portal.get_project_list()
        query_lower = q.lower()

        # 簡易検索実装
        matched_projects = []

        for project in projects:
            score = 0
        # 繰り返し処理

            # 名前マッチ
            if query_lower in project["name"].lower():
                score += 3

            # 説明マッチ
            if query_lower in project["description"].lower():
                score += 2

            # 技術スタックマッチ
            for tech in project["tech_stack"]:
                if query_lower in tech.lower():
                    score += 1

            if score > 0:
                matched_projects.append({"project": project, "score": score})

        # スコア順でソート
        matched_projects.sort(key=lambda x: x["score"], reverse=True)

        results = [
            {**item["project"], "search_score": item["score"]}
            for item in matched_projects[:limit]
        ]

        logger.info(f"検索結果: {len(results)}件")
        return {"query": q, "total_results": len(results), "results": results}

    except Exception as e:
        logger.error(f"プロジェクト検索エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket接続（将来の拡張用）
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """
    WebSocket接続（リアルタイム更新用）
    """
    await websocket.accept()
    try:
        while True:
            # 定期的にステータス送信
            stats = await get_statistics()
            await websocket.send_json({"type": "stats_update", "data": stats})
            await asyncio.sleep(30)  # 30秒ごと

    except Exception as e:
        logger.info(f"WebSocket接続終了: {e}")


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
    """not_found_handlerを処理"""
        status_code=404,
        content={
            "error": "Not Found",
            "message": "要求されたリソースが見つかりません",
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """internal_error_handlerを処理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "内部サーバーエラーが発生しました",
            "timestamp": datetime.now().isoformat(),
        },
    )


# 起動時イベント
@app.on_event("startup")
async def startup_event():
    """起動時初期化"""
    logger.info("🚀 Project Web Portal API 起動中...")

    # データベース初期化確認
    try:
        await portal.get_project_list()
        logger.info("✅ データベース接続確認完了")
    except Exception as e:
        logger.error(f"❌ データベース接続エラー: {e}")

    logger.info("🎉 Project Web Portal API 起動完了!")


# 終了時イベント
@app.on_event("shutdown")
async def shutdown_event():
    """終了時クリーンアップ"""
    logger.info("🔽 Project Web Portal API 終了中...")
    # クリーンアップ処理
    logger.info("✅ Project Web Portal API 終了完了")


# 開発サーバー起動
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
