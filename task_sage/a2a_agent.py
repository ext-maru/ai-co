"""
📋 Task Sage A2A Agent - Elder Loop対応
Knowledge Sageパターンを適用した標準A2A実装

python-a2a完全準拠のTask管理エージェント
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from python_a2a import A2AServer, skill, Message, TextContent, MessageRole, A2AError

# ビジネスロジック（Knowledge Sageパターン）
from .business_logic import TaskProcessor


class TaskSageAgent(A2AServer):
    """
    📋 Task Sage A2A Agent
    
    python-a2aを使用したタスク管理エージェント実装
    既存のTaskProcessorビジネスロジックを活用
    """
    
    def __init__(self, host: str = "localhost", port: int = 8002):
        """A2AServer初期化"""
        super().__init__()
        
        # エージェント情報設定
        self.agent_name = "task-sage"
        self.description = "Elders Guild Task Management Sage - A2A Standard Implementation"
        self.host = host
        self.port = port
        
        # Logger設定
        self.logger = logging.getLogger(f"TaskSageAgent")
        
        # ビジネスロジックプロセッサ（Knowledge Sageパターン）
        self.task_processor = TaskProcessor()
        
        self.logger.info(f"Task Sage A2A Agent initialized on {host}:{port}")
    
    async def initialize(self) -> bool:
        """A2Aエージェント初期化"""
        try:
            # ビジネスロジック初期化は既にコンストラクタで完了
            self.logger.info("Task Sage A2A Agent fully initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Task Sage A2A Agent: {e}")
            return False
    
    def _extract_data_from_message(self, message: Message) -> Dict[str, Any]:
        """メッセージからデータを抽出（Knowledge Sageパターン）"""
        if isinstance(message.content, TextContent):
            text_content = message.content.text
            try:
                # JSON形式の場合はパース
                return json.loads(text_content)
            except json.JSONDecodeError:
                # プレーンテキストの場合
                return {"query": text_content}
        else:
            raise A2AError("TextContent required")
    
    def _create_response_message(self, result: Dict[str, Any]) -> Message:
        """結果からレスポンスメッセージを作成（Knowledge Sageパターン）"""
        return Message(
            content=TextContent(text=json.dumps(result)),
            role=MessageRole.AGENT
        )
    
    def _create_error_message(self, error: Exception) -> Message:
        """エラーからエラーメッセージを作成（Knowledge Sageパターン）"""
        return Message(
            content=TextContent(text=json.dumps({
                "success": False,
                "error": str(error)
            })),
            role=MessageRole.AGENT
        )
    
    # === コアタスク管理スキル ===
    
    @skill(name="create_task")
    async def create_task_skill(self, message: Message) -> Message:
        """タスク作成スキル"""
        try:
            # メッセージからデータ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("create_task", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in create_task skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_task")
    async def get_task_skill(self, message: Message) -> Message:
        """タスク取得スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("get_task", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_task skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="update_task")
    async def update_task_skill(self, message: Message) -> Message:
        """タスク更新スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("update_task", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in update_task skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="delete_task")
    async def delete_task_skill(self, message: Message) -> Message:
        """タスク削除スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("delete_task", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in delete_task skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="list_tasks")
    async def list_tasks_skill(self, message: Message) -> Message:
        """タスク一覧取得スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("list_tasks", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in list_tasks skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="search_tasks")
    async def search_tasks_skill(self, message: Message) -> Message:
        """タスク検索スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("search_tasks", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in search_tasks skill: {e}")
            return self._create_error_message(e)
    
    # === 分析・管理スキル ===
    
    @skill(name="estimate_effort")
    async def estimate_effort_skill(self, message: Message) -> Message:
        """工数見積もりスキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("estimate_effort", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in estimate_effort skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="resolve_dependencies")
    async def resolve_dependencies_skill(self, message: Message) -> Message:
        """依存関係解決スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("resolve_dependencies", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in resolve_dependencies skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_task_progress")
    async def get_task_progress_skill(self, message: Message) -> Message:
        """タスク進捗取得スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("get_task_progress", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_task_progress skill: {e}")
            return self._create_error_message(e)
    
    # === プロジェクト管理スキル ===
    
    @skill(name="create_project")
    async def create_project_skill(self, message: Message) -> Message:
        """プロジェクト作成スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("create_project", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in create_project skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="get_project")
    async def get_project_skill(self, message: Message) -> Message:
        """プロジェクト取得スキル"""
        try:
            # データ抽出
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("get_project", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_project skill: {e}")
            return self._create_error_message(e)
    
    @skill(name="list_projects")
    async def list_projects_skill(self, message: Message) -> Message:
        """プロジェクト一覧取得スキル"""
        try:
            # データ抽出（一覧取得なのでパラメータは不要だが統一性のため）
            data = self._extract_data_from_message(message)
            
            # ビジネスロジック実行
            result = await self.task_processor.process_action("list_projects", data)
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in list_projects skill: {e}")
            return self._create_error_message(e)
    
    # === 統計・レポートスキル ===
    
    @skill(name="get_statistics")
    async def get_statistics_skill(self, message: Message) -> Message:
        """統計情報取得スキル"""
        try:
            # ビジネスロジック実行（引数不要）
            result = await self.task_processor.process_action("get_statistics", {})
            
            return self._create_response_message(result)
            
        except Exception as e:
            self.logger.error(f"Error in get_statistics skill: {e}")
            return self._create_error_message(e)
    
    # === 4賢者協調スキル ===
    
    @skill(name="elder_collaboration")
    async def elder_collaboration_skill(self, message: Message) -> Message:
        """4賢者協調スキル"""
        try:
            # A2A協調処理（他の賢者との連携）
            collaboration_request = self._extract_data_from_message(message)
            
            # 協調パターン識別
            collaboration_type = collaboration_request.get("type", "task_planning")
            
            if collaboration_type == "task_planning":
                # タスク計画協調
                task_spec = collaboration_request.get("task_spec", {})
                planning_result = await self.task_processor.process_action(
                    "estimate_effort", 
                    {"complexity_factors": task_spec.get("complexity_factors", {})}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "task_planning",
                    "result": planning_result,
                    "agent": "task-sage"
                }
                
            elif collaboration_type == "project_coordination":
                # プロジェクト調整協調
                project_id = collaboration_request.get("project_id", "")
                coordination_result = await self.task_processor.process_action(
                    "get_task_progress",
                    {"project_id": project_id}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "project_coordination",
                    "result": coordination_result,
                    "agent": "task-sage",
                    "project_id": project_id
                }
                
            elif collaboration_type == "dependency_analysis":
                # 依存関係分析協調
                task_ids = collaboration_request.get("task_ids", [])
                dependency_result = await self.task_processor.process_action(
                    "resolve_dependencies",
                    {"task_ids": task_ids}
                )
                
                result = {
                    "success": True,
                    "collaboration_type": "dependency_analysis",
                    "result": dependency_result,
                    "agent": "task-sage"
                }
                
            else:
                # 一般的な協調処理（統計情報提供）
                stats_result = await self.task_processor.process_action("get_statistics", {})
                
                result = {
                    "success": True,
                    "collaboration_type": "general_statistics",
                    "result": stats_result,
                    "agent": "task-sage"
                }
            
            return self._create_response_message(result)
                
        except Exception as e:
            self.logger.error(f"Error in elder_collaboration skill: {e}")
            return self._create_error_message(e)
    
    # === ヘルスチェック・管理 ===
    
    @skill(name="health_check")
    async def health_check_skill(self, message: Message) -> Message:
        """ヘルスチェックスキル"""
        try:
            # 統計情報取得でシステム状態確認
            stats_result = await self.task_processor.process_action("get_statistics", {})
            
            health_status = {
                "status": "healthy",
                "agent": "task-sage",
                "timestamp": stats_result.get("data", {}).get("timestamp", "unknown"),
                "total_tasks": stats_result.get("data", {}).get("task_statistics", {}).get("total_tasks", 0),
                "total_projects": stats_result.get("data", {}).get("project_statistics", {}).get("total_projects", 0),
                "uptime": "operational"
            }
            
            return self._create_response_message(health_status)
            
        except Exception as e:
            self.logger.error(f"Error in health_check skill: {e}")
            error_status = {
                "status": "unhealthy",
                "agent": "task-sage",
                "error": str(e)
            }
            return self._create_response_message(error_status)
    
    async def shutdown(self):
        """A2Aエージェント終了処理"""
        try:
            self.logger.info("Task Sage A2A Agent shutdown initiated")
            # シンプルな終了処理
            self.logger.info("Task Sage A2A Agent shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# === エージェント実行スクリプト ===

async def main():
    """Task Sage A2Aエージェント実行"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # エージェント作成・起動
    agent = TaskSageAgent()
    
    try:
        if await agent.initialize():
            print(f"🚀 Starting Task Sage A2A Agent on port 8002...")
            await agent.run()  # A2AServerの標準実行メソッド
        else:
            print("❌ Failed to initialize Task Sage A2A Agent")
            
    except KeyboardInterrupt:
        print("\\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error running Task Sage A2A Agent: {e}")
    finally:
        await agent.shutdown()
        print("✅ Task Sage A2A Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())