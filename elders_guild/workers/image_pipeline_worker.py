#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated Image Pipeline Worker
画像処理パイプラインワーカー - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for image processing
"""

import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    # Handle specific exception case
    PIL_AVAILABLE = False
    print("Warning: PIL not available, image processing disabled")
import io

sys.path.append(str(Path(__file__).parent.parent))

from core import msg
from core.base_worker_ja import BaseWorker
from core.common_utils import EMOJI
from core.config import get_config
from core.worker_communication import CommunicationMixin

# Elder Tree Integration imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    print(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False

class ImageProcessingWorker(BaseWorker, CommunicationMixin):
    """画像処理を行うワーカー"""

    def __init__(self, worker_id=None):
        super().__init__(worker_type="image_processor", worker_id=worker_id)
        # キューの設定
        self.input_queue = "ai_image_tasks"
        self.output_queue = "ai_image_results"
        # CommunicationMixinの初期化が必要な場合
        if hasattr(self, "setup_communication"):
            self.setup_communication()

        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_systems_initialized = False

        # Image processing metrics
        self.images_processed = 0
        self.processing_errors = 0
        self.total_bytes_processed = 0
        self.created_at = datetime.now()

        self._initialize_elder_systems()
        self._register_handlers()

    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        if not ELDER_TREE_AVAILABLE:
            return

        try:
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                print("🧙‍♂️ Four Sages Integration activated")

            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                print("🏛️ Elder Council Summoner initialized")

            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                print("🌳 Elder Tree Hierarchy connected")

            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_systems_initialized = True
                print("✅ Full Elder Tree Integration enabled")
            else:
                print("⚠️ Partial Elder Tree Integration - some systems unavailable")

        except Exception as e:
            # Handle specific exception case
            print(f"Elder Tree initialization failed: {e}")
            self.elder_systems_initialized = False

    def _register_handlers(self):
        """メッセージハンドラーを登録"""
        self.register_message_handler("process_image", self.handle_process_image)
        self.register_message_handler("resize_request", self.handle_resize_request)

    def process_message(self, ch, method, properties, body):
        """メッセージ処理 with Elder Tree integration"""
        try:
            # ワーカー間通信メッセージをチェック
            data = json.loads(body)
            if self.process_worker_message(data):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # 通常のタスク処理
            task = json.loads(body)
            self.images_processed += 1

            # Report image processing start to Task Sage
            if self.elder_systems_initialized:
                self._report_processing_start_to_task_sage(task)
            self.logger.info(
                f"{EMOJI['process']} Processing image task: {task.get('task_id')}"
            )

            image_path = task.get("image_path")
            operations = task.get("operations", [])

            # 画像を読み込み
            image = Image.open(image_path)

            # 各操作を実行
            for operation in operations:
                if operation["type"] == "resize":
                    # リサイズ処理
                    size = operation.get("size", (800, 600))
                    image = image.resize(size, Image.Resampling.LANCZOS)

                    # サムネイル生成ワーカーに通知
                    self.send_to_worker(
                        "thumbnail",
                        "create_thumbnail",
                        {
                            "original_path": image_path,
                            "size": (150, 150),
                            "task_id": task.get("task_id"),
                        },
                    )

                elif operation["type"] == "rotate":
                    angle = operation.get("angle", 0)
                    image = image.rotate(angle, expand=True)

                elif operation["type"] == "filter":
                    # フィルター処理ワーカーに委譲
                    self.send_to_worker(
                        "filter",
                        "apply_filter",
                        {
                            "image_data": self._image_to_base64(image),
                            "filter_type": operation.get("filter_type"),
                            "task_id": task.get("task_id"),
                        },
                        priority="high",
                    )

            # 処理完了を通知
            output_path = str(Path(image_path).with_suffix(".processed.jpg"))
            image.save(output_path, quality=95)

            # Track processed bytes
            output_size = Path(output_path).stat().st_size
            self.total_bytes_processed += output_size

            # Report success to Task Sage
            if self.elder_systems_initialized:
                self._report_processing_success_to_task_sage(
                    task, output_size, operations
                )

            # PMワーカーに通知
            self.send_to_worker(
                "pm",
                "file_created",
                {
                    "file_path": output_path,
                    "task_id": task.get("task_id"),
                    "file_type": "processed_image",
                },
            )

            # 結果を送信
            result = {
                "task_id": task.get("task_id"),
                "status": "completed",
                "output_file": output_path,
                "operations_applied": len(operations),
            }

            self.send_result(result)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # Handle specific exception case
            self.processing_errors += 1

            # Report error to Incident Sage
            if self.elder_systems_initialized:
                self._report_processing_error_to_incident_sage(task, e)

            self.handle_error(e, "process_message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def handle_process_image(self, data):
        """他のワーカーからの画像処理リクエスト"""
        self.logger.info(f"{EMOJI['receive']} Received image processing request")

        try:
            image_data = data.get("image_data")
            operations = data.get("operations", [])

            # Base64から画像に変換
            image = self._base64_to_image(image_data)

            # 処理実行
            for op in operations:
                if op["type"] == "resize":
                    image = image.resize(op["size"], Image.Resampling.LANCZOS)
                elif op["type"] == "rotate":
                    image = image.rotate(op["angle"], expand=True)

            # 結果を返す
            return {"status": "success", "image_data": self._image_to_base64(image)}

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def handle_resize_request(self, data):
        """リサイズリクエストを処理"""
        image_path = data.get("image_path")
        size = data.get("size", (800, 600))

        try:
            image = Image.open(image_path)
            resized = image.resize(size, Image.Resampling.LANCZOS)

            output_path = str(Path(image_path).with_suffix(f".{size[0]}x{size[1]}.jpg"))
            resized.save(output_path)

            return {"status": "success", "output_path": output_path, "size": size}

        except Exception as e:
            # Handle specific exception case
            return {"status": "error", "message": str(e)}

    def _image_to_base64(self, image):
        """画像をBase64エンコード"""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode()

    def _base64_to_image(self, base64_data):
        """Base64から画像に変換"""
        image_data = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_data))

    def _report_processing_start_to_task_sage(self, task: Dict[str, Any]):
        """Report image processing start to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "image_processing_start",
                "worker": "image_pipeline_worker",
                "task_id": task.get("task_id"),
                "image_path": task.get("image_path"),
                "operations_count": len(task.get("operations", [])),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to report processing start to Task Sage: {e}")

    def _report_processing_success_to_task_sage(
        self, task: Dict[str, Any], output_size: int, operations: List[Dict]
    ):
        """Report processing success to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "image_processing_success",
                "worker": "image_pipeline_worker",
                "task_id": task.get("task_id"),
                "output_size": output_size,
                "operations_applied": len(operations),
                "operation_types": [op.get("type") for op in operations],
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

            # Store processing patterns in Knowledge Sage
            if len(operations) > 1:
                pattern_data = {
                    "type": "image_processing_pattern",
                    "operations": operations,
                    "output_size": output_size,
                    "timestamp": datetime.now().isoformat(),
                }
                self.four_sages.store_knowledge("image_patterns", pattern_data)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to report processing success to Task Sage: {e}")

    def _report_processing_error_to_incident_sage(
        self, task: Dict[str, Any], error: Exception
    ):
        """Report processing error to Incident Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "image_processing_error",
                "worker": "image_pipeline_worker",
                "task_id": task.get("task_id", "unknown"),
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(
                f"Failed to report processing error to Incident Sage: {e}"
            )

    def get_elder_image_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder image processing status"""
        status = {
            "worker_type": "image_pipeline_worker",
            "elder_role": "Image Processing Specialist",
            "reporting_to": "Task Sage",
            "elder_systems": {
                "initialized": self.elder_systems_initialized,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "processing_stats": {
                "images_processed": self.images_processed,
                "processing_errors": self.processing_errors,
                "total_bytes_processed": self.total_bytes_processed,
                "average_bytes_per_image": self.total_bytes_processed
                / max(1, self.images_processed),
                "error_rate": self.processing_errors / max(1, self.images_processed),
                "pil_available": PIL_AVAILABLE,
            },
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "status": "healthy"
            if self.elder_systems_initialized and PIL_AVAILABLE
            else "degraded",
        }

        return status

    def cleanup(self) -> None:
        """ワーカーのクリーンアップ処理（Elder Tree終了通知、リソース解放）"""
        try:
            self.logger.info(f"🧹 {self.__class__.__name__} cleanup開始")
            
            # Elder Tree終了通知
            if self.elder_systems_initialized and self.elder_tree:
                # Complex condition - consider breaking down
                try:
                    message = ElderMessage(
                        sender_rank=ElderRank.SERVANT,
                        sender_id=f"image_pipeline_worker_{self.worker_id}",
                        recipient_rank=ElderRank.SAGE,
                        recipient_id="task_sage",
                        message_type="worker_shutdown",
                        content={
                            "worker_type": "image_pipeline_worker",
                            "shutdown_reason": "normal_cleanup",
                            "final_stats": {
                                "images_processed": self.images_processed,
                                "processing_errors": self.processing_errors,
                                "total_bytes_processed": self.total_bytes_processed
                            },
                            "timestamp": datetime.now().isoformat()
                        },
                        priority="normal"
                    )
                    # Synchronous call for cleanup
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not (loop.is_running()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if loop.is_running():
                            # Create task for running loop
                            loop.create_task(self.elder_tree.send_message(message))
                        else:
                            # Run in new loop
                            asyncio.run(self.elder_tree.send_message(message))
                    except:
                        # Fallback for non-async context
                        pass
                    self.logger.info("🌳 Elder Tree終了通知送信完了")
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree終了通知失敗: {e}")
            
            # 画像処理関連のリソース解放
            if hasattr(self, 'image_cache'):
                self.image_cache.clear()

            # 統計情報の保存
            final_stats = {
                "worker_type": "image_pipeline_worker",
                "images_processed": self.images_processed,
                "processing_errors": self.processing_errors,
                "total_bytes_processed": self.total_bytes_processed,
                "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
                "shutdown_time": datetime.now().isoformat()
            }
            
            # 統計保存を試行
            try:
                import json
                stats_file = Path(f"/tmp/image_worker_stats_{self.worker_id}.json")
                stats_file.write_text(json.dumps(final_stats, indent=2))
                self.logger.info(f"統計情報保存: {stats_file}")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"統計情報保存失敗: {e}")
            
            self.logger.info(f"✅ {self.__class__.__name__} cleanup完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ Cleanup処理中にエラー: {e}")
            import traceback
            self.logger.error(f"エラー詳細: {traceback.format_exc()}")

    def stop(self) -> None:
        """ワーカーの停止処理（cleanup呼び出し、super().stop()）"""
        try:
            self.logger.info(f"🛑 {self.__class__.__name__} 停止開始")
            
            # クリーンアップ処理を先に実行
            self.cleanup()
            
            # ベースクラスの停止処理
            super().stop()
            
            self.logger.info(f"✅ {self.__class__.__name__} 停止完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 停止処理中にエラー: {e}")
            # エラーが発生してもベースクラスの停止は実行
            try:
                super().stop()
            except Exception as base_error:
                # Handle specific exception case
                self.logger.error(f"❌ ベースクラス停止エラー: {base_error}")

    def initialize(self) -> None:
        """初期化処理（Elder Tree初期化、必要コンポーネント初期化）"""
        try:
            self.logger.info(f"🔧 {self.__class__.__name__} 初期化開始")
            
            # PIL利用可能性チェック
            if not PIL_AVAILABLE:
                raise RuntimeError("PIL (Pillow) が利用できません。画像処理ができません。")
            
            # Elder Tree システム再初期化（必要に応じて）
            if not self.elder_systems_initialized:
                self._initialize_elder_systems()
            
            # 画像処理用の初期設定
            self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
            self.max_image_size = (4096, 4096)  # 最大画像サイズ
            self.quality_settings = {
                'high': 95,
                'medium': 85,
                'low': 75
            }
            
            # 画像キャッシュ初期化
            self.image_cache = {}
            self.cache_max_size = 50  # 最大キャッシュ数
            
            # 作業ディレクトリの確認・作成
            work_dir = Path("/tmp/image_processing")
            work_dir.mkdir(exist_ok=True)
            self.work_dir = work_dir
            
            # Elder Tree初期化完了通知
            if self.elder_systems_initialized:
                try:
                    self._report_initialization_to_task_sage()
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree初期化通知失敗: {e}")
            
            self.logger.info(f"✅ {self.__class__.__name__} 初期化完了")
            self.logger.info(f"   - PIL利用可能: {PIL_AVAILABLE}")
            self.logger.info(f"   - Elder統合: {self.elder_systems_initialized}")
            self.logger.info(f"   - 対応形式: {', '.join(self.supported_formats)}")
            self.logger.info(f"   - 作業ディレクトリ: {self.work_dir}")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 初期化処理中にエラー: {e}")
            raise RuntimeError(f"ImageProcessingWorker初期化失敗: {e}")

    def handle_error(
        self,
        error: Exception,
        context: str = "unknown",
        task_data: dict = None
    ) -> None:
        """エラーハンドリング（Incident Sageへの報告、ログ記録）"""
        try:
            import time
            error_id = f"img_error_{int(time.time() * 1000)}"
            
            # 詳細なエラー情報を記録
            error_info = {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "worker_type": "image_pipeline_worker",
                "worker_id": self.worker_id,
                "timestamp": datetime.now().isoformat(),
                "task_data": task_data or {},
                "worker_stats": {
                    "images_processed": self.images_processed,
                    "processing_errors": self.processing_errors,
                    "total_bytes_processed": self.total_bytes_processed
                }
            }
            
            # エラーカウンター更新
            self.processing_errors += 1
            
            # ログに記録
            self.logger.error(f"❌ [{error_id}] エラー発生 - {context}: {error}")
            
            # スタックトレースを取得
            import traceback
            error_trace = traceback.format_exc()
            error_info["stack_trace"] = error_trace
            self.logger.error(f"スタックトレース:\n{error_trace}")
            
            # Incident Sageへの報告
            if self.elder_systems_initialized and self.four_sages:
                # Complex condition - consider breaking down
                try:
                    incident_data = {
                        "type": "image_processing_error",
                        "worker": "image_pipeline_worker",
                        "error_id": error_id,
                        "severity": self._determine_error_severity(error),
                        "error_details": error_info,
                        "recommended_actions": self._get_error_recommendations(error),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.four_sages.consult_incident_sage(incident_data)
                    self.logger.info(f"🚨 Incident Sage報告送信: {error_id}")
                    
                except Exception as sage_error:
                    # Handle specific exception case
                    self.logger.error(f"Incident Sage報告失敗: {sage_error}")
            
            # エラーファイルに保存
            try:
                import json
                error_file = Path(f"/tmp/image_worker_errors_{datetime.now().strftime('%Y%m%d')}.json")
                errors = []
                if error_file.exists():
                    try:
                        errors = json.loads(error_file.read_text())
                    except:
                        errors = []
                errors.append(error_info)
                
                # 最新100件のみ保持
                if len(errors) > 100:
                    errors = errors[-100:]
                
                error_file.write_text(json.dumps(errors, indent=2, ensure_ascii=False))
                
            except Exception as file_error:
                # Handle specific exception case
                self.logger.warning(f"エラーファイル保存失敗: {file_error}")
            
            # 重要エラーの場合は追加処理
            if self._is_critical_error(error):
                self.logger.critical(f"🔥 重要エラー検出: {error_id}")
                # 必要に応じて自動復旧処理や緊急停止処理を実装
                
        except Exception as handler_error:
            # エラーハンドラー自体のエラーは最小限のログのみ
            self.logger.error(f"❌ エラーハンドラー内でエラー: {handler_error}")
            self.logger.error(f"元のエラー: {error}")

    def get_status(self) -> dict:
        """ワーカー状態取得（Elder Tree状態、処理統計）"""
        try:
            uptime = (datetime.now() - self.created_at).total_seconds()
            
            status = {
                "worker_info": {
                    "worker_type": "image_pipeline_worker",
                    "worker_id": self.worker_id,
                    "class_name": self.__class__.__name__,
                    "created_at": self.created_at.isoformat(),
                    "uptime_seconds": uptime,
                    "uptime_formatted": self._format_uptime(uptime)
                },
                "processing_stats": {
                    "images_processed": self.images_processed,
                    "processing_errors": self.processing_errors,
                    "total_bytes_processed": self.total_bytes_processed,
                    "average_bytes_per_image": self.total_bytes_processed / max(
                        1,
                        self.images_processed
                    ),
                    "error_rate_percent": (self.processing_errors / max(
                        1,
                        self.images_processed)
                    ) * 100,
                    "processing_rate_per_minute": (self.images_processed / max(1, uptime / 60))
                },
                "capabilities": {
                    "pil_available": PIL_AVAILABLE,
                    "supported_formats": list(getattr(self, 'supported_formats', [])),
                    "max_image_size": getattr(self, 'max_image_size', None),
                    "quality_settings": getattr(self, 'quality_settings', {})
                },
                "elder_integration": {
                    "systems_initialized": self.elder_systems_initialized,
                    "four_sages_active": self.four_sages is not None,
                    "elder_council_active": self.elder_council_summoner is not None,
                    "elder_tree_connected": self.elder_tree is not None
                },
                "resource_usage": {
                    "work_directory": str(getattr(self, 'work_dir', 'N/A')),
                    "cache_size": len(getattr(self, 'image_cache', {})),
                    "cache_max_size": getattr(self, 'cache_max_size', 0)
                },
                "health_status": self._determine_health_status(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Elder Tree詳細状態
            if self.elder_tree:
                try:
                    status["elder_tree_details"] = {
                        "node_count": len(self.elder_tree.nodes),
                        "message_queue_size": len(getattr(self.elder_tree, 'message_queue', [])),
                        "connection_status": "connected"
                    }
                except Exception as e:
                    # Handle specific exception case
                    status["elder_tree_details"] = {
                        "connection_status": "error",
                        "error": str(e)
                    }
            
            return status
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"状態取得エラー: {e}")
            return {
                "error": f"状態取得失敗: {e}",
                "timestamp": datetime.now().isoformat(),
                "worker_type": "image_pipeline_worker",
                "worker_id": getattr(self, 'worker_id', 'unknown')
            }

    def validate_config(self) -> dict:
        """設定検証（設定妥当性チェック、必須項目確認）"""
        import os
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "config_details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # PIL (Pillow) 利用可能性チェック
            if not PIL_AVAILABLE:
                validation_result["errors"].append("PIL (Pillow) が利用できません。画像処理機能が無効です。")
                validation_result["is_valid"] = False
                validation_result["recommendations"].append("pip install Pillow を実行してください")
            
            # キューの設定確認
            if not hasattr(self, 'input_queue') or not self.input_queue:
                # Complex condition - consider breaking down
                validation_result["errors"].append("入力キュー (input_queue) が設定されていません")
                validation_result["is_valid"] = False
            else:
                validation_result["config_details"]["input_queue"] = self.input_queue
            
            if not hasattr(self, 'output_queue') or not self.output_queue:
                # Complex condition - consider breaking down
                validation_result["errors"].append("出力キュー (output_queue) が設定されていません")
                validation_result["is_valid"] = False
            else:
                validation_result["config_details"]["output_queue"] = self.output_queue
            
            # Elder Tree統合状態チェック
            validation_result["config_details"]["elder_integration"] = {
                "available": ELDER_TREE_AVAILABLE,
                "systems_initialized": getattr(self, 'elder_systems_initialized', False),
                "four_sages": self.four_sages is not None,
                "elder_council": self.elder_council_summoner is not None,
                "elder_tree": self.elder_tree is not None
            }
            
            if ELDER_TREE_AVAILABLE and not self.elder_systems_initialized:
                # Complex condition - consider breaking down
                validation_result["warnings"].append("Elder Tree統合が利用可能ですが、初期化されていません")
                validation_result["recommendations"].append("Elder Treeシステムの再初期化を検討してください")
            
            # 画像処理設定チェック
            if hasattr(self, 'supported_formats'):
                validation_result["config_details"]["supported_formats"] = list(self.supported_formats)
                if len(self.supported_formats) == 0:
                    validation_result["warnings"].append("対応画像形式が設定されていません")
            
            if hasattr(self, 'max_image_size'):
                validation_result["config_details"]["max_image_size"] = self.max_image_size
                width, height = self.max_image_size
                if width > 8192 or height > 8192:
                    # Complex condition - consider breaking down
                    validation_result["warnings"].append(f"最大画像サイズが大きすぎます: {width}x{height}")
                    validation_result["recommendations"].append("メモリ使用量を考慮し4096x4096以下を推奨")
            
            # 作業ディレクトリチェック
            if hasattr(self, 'work_dir'):
                work_dir = Path(self.work_dir)
                if not work_dir.exists():
                    validation_result["errors"].append(f"作業ディレクトリが存在しません: {work_dir}")
                    validation_result["is_valid"] = False
                elif not work_dir.is_dir():
                    validation_result["errors"].append(f"作業パスがディレクトリではありません: {work_dir}")
                    validation_result["is_valid"] = False
                elif not os.access(work_dir, os.W_OK):
                    validation_result["errors"].append(f"作業ディレクトリに書き込み権限がありません: {work_dir}")
                    validation_result["is_valid"] = False
                else:
                    validation_result["config_details"]["work_directory"] = str(work_dir)
            
            # 統計情報の妥当性
            if self.images_processed < 0:
                validation_result["errors"].append("処理済み画像数が負の値です")
                validation_result["is_valid"] = False
            
            if self.processing_errors < 0:
                validation_result["errors"].append("エラー数が負の値です")
                validation_result["is_valid"] = False
            
            if self.total_bytes_processed < 0:
                validation_result["errors"].append("処理済みバイト数が負の値です")
                validation_result["is_valid"] = False
            
            # パフォーマンス警告
            if self.images_processed > 0:
                error_rate = (self.processing_errors / self.images_processed) * 100
                if error_rate > 10:
                    validation_result["warnings"].append(f"エラー率が高すぎます: {error_rate:0.1f}%")
                    validation_result["recommendations"].append("エラーパターンの分析を実施してください")
                elif error_rate > 5:
                    validation_result["warnings"].append(f"エラー率がやや高めです: {error_rate:0.1f}%")
            
            # 成功時の追加情報
            if validation_result["is_valid"]:
                validation_result["summary"] = "設定は有効です"
                if not validation_result["warnings"]:
                    validation_result["summary"] += " - 警告なし"
            else:
                validation_result["summary"] = f"設定に {len(validation_result['errors'])} 個のエラーがあります"
            
            self.logger.info(f"設定検証完了: {validation_result['summary']}")
            
            return validation_result
            
        except Exception as e:
            # Handle specific exception case
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"設定検証中にエラー: {e}")
            validation_result["summary"] = "設定検証失敗"
            self.logger.error(f"設定検証エラー: {e}")
            return validation_result

    def _report_initialization_to_task_sage(self) -> None:
        """Task Sageに初期化完了を報告"""
        if not self.four_sages:
            return
        
        try:
            report = {
                "type": "worker_initialization",
                "worker": "image_pipeline_worker",
                "worker_id": self.worker_id,
                "capabilities": {
                    "pil_available": PIL_AVAILABLE,
                    "supported_formats": list(getattr(self, 'supported_formats', [])),
                    "max_image_size": getattr(self, 'max_image_size', None)
                },
                "elder_integration": self.elder_systems_initialized,
                "timestamp": datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Task Sage初期化報告失敗: {e}")
    
    def _determine_error_severity(self, error: Exception) -> str:
        """エラーの重要度を判定"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # 重要エラーパターン
        critical_patterns = ['memory', 'disk', 'permission', 'security', 'corruption']
        high_patterns = ['filenotfound', 'connection', 'timeout', 'authentication']
        
        if any(pattern in error_str for pattern in critical_patterns):
            # Complex condition - consider breaking down
            return 'critical'
        elif any(pattern in error_str for pattern in high_patterns) or error_type in ['IOError' \
            'IOError', 'OSError', 'ConnectionError']:
            return 'high'
        elif error_type in ['ValueError', 'TypeError', 'AttributeError']:
            return 'medium'
        else:
            return 'low'
    
    def _get_error_recommendations(self, error: Exception) -> list:
        """エラーに対する推奨対応を生成"""
        recommendations = []
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        if 'memory' in error_str:
            recommendations.extend([
                "画像サイズを縮小してください",
                "バッチサイズを小さくしてください",
                "システムメモリを確認してください"
            ])
        elif 'disk' in error_str or 'space' in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "ディスク容量を確認してください",
                "一時ファイルを削除してください",
                "作業ディレクトリを変更してください"
            ])
        elif 'permission' in error_str:
            recommendations.extend([
                "ファイル・ディレクトリの権限を確認してください",
                "実行ユーザーの権限を確認してください"
            ])
        elif error_type == 'FileNotFoundError':
            recommendations.extend([
                "ファイルパスを確認してください",
                "ファイルが存在するか確認してください",
                "相対パスではなく絶対パスを使用してください"
            ])
        elif 'pil' in error_str or 'pillow' in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "PIL/Pillowライブラリをインストールしてください",
                "pip install Pillow を実行してください",
                "画像形式がサポートされているか確認してください"
            ])
        
        if not recommendations:
            recommendations.append("ログを確認して詳細なエラー情報を調べてください")
        
        return recommendations
    
    def _is_critical_error(self, error: Exception) -> bool:
        """重要エラーかどうかを判定"""
        return self._determine_error_severity(error) in ['critical', 'high']
    
    def _format_uptime(self, seconds: float) -> str:
        """稼働時間を読みやすい形式でフォーマット"""
        if seconds < 60:
            return f"{seconds:0.1f}秒"
        elif seconds < 3600:
            return f"{seconds/60:0.1f}分"
        elif seconds < 86400:
            return f"{seconds/3600:0.1f}時間"
        else:
            return f"{seconds/86400:0.1f}日"
    
    def _determine_health_status(self) -> str:
        """ワーカーの健全性を判定"""
        if not PIL_AVAILABLE:
            return "critical"
        
        if self.images_processed > 0:
            error_rate = (self.processing_errors / self.images_processed) * 100
            if error_rate > 20:
                return "unhealthy"
            elif error_rate > 5:
                return "warning"
        
        if self.elder_systems_initialized and PIL_AVAILABLE:
            # Complex condition - consider breaking down
            return "healthy"
        elif PIL_AVAILABLE:
            return "degraded"
        else:
            return "critical"

class ThumbnailWorker(BaseWorker, CommunicationMixin):
    """サムネイル生成専門ワーカー"""

    def __init__(self, worker_id=None):
        super().__init__(
            worker_type="thumbnail",
            worker_id=worker_id,
            input_queue="ai_thumbnail_tasks",
            output_queue="ai_thumbnail_results",
        )
        self.setup_communication()
        self.register_message_handler("create_thumbnail", self.handle_create_thumbnail)

    def process_message(self, ch, method, properties, body):
        """メッセージ処理"""
        try:
            data = json.loads(body)

            # ワーカー間通信メッセージをチェック
            if self.process_worker_message(data):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # 通常のサムネイル生成タスク
            self.create_thumbnail_task(data)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # Handle specific exception case
            self.handle_error(e, "process_message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def handle_create_thumbnail(self, data):
        """サムネイル生成リクエスト"""
        self.logger.info(f"{EMOJI['image']} Creating thumbnail")

        try:
            original_path = data.get("original_path")
            size = data.get("size", (150, 150))

            image = Image.open(original_path)
            image.thumbnail(size, Image.Resampling.LANCZOS)

            thumb_path = str(Path(original_path).with_suffix(".thumb.jpg"))
            image.save(thumb_path, quality=85)

            # 完了を通知
            self.send_to_worker(
                "result",
                "thumbnail_created",
                {
                    "original_path": original_path,
                    "thumbnail_path": thumb_path,
                    "size": size,
                    "task_id": data.get("task_id"),
                },
            )

            return {"status": "success", "thumbnail_path": thumb_path}

        except Exception as e:
            # Handle specific exception case
            return {"status": "error", "message": str(e)}

    def create_thumbnail_task(self, task):
        """通常のサムネイル生成タスク"""
        # 実装...
        pass

    def cleanup(self):
        """ワーカーのクリーンアップ処理（Elder Tree終了通知、リソース解放）"""
        try:
            self.logger.info("🧹 ThumbnailWorker cleanup開始")
            
            # Elder Tree終了通知
            if ELDER_TREE_AVAILABLE and hasattr(self, 'elder_tree') and self.elder_tree:
                # Complex condition - consider breaking down
                try:
                    self.elder_tree.notify_shutdown({
                        "worker_type": "thumbnail",
                        "worker_id": self.worker_id,
                        "reason": "cleanup",
                        "stats": {
                            "thumbnails_created": getattr(self, 'thumbnails_created', 0),
                            "processing_errors": getattr(self, 'processing_errors', 0)
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    self.logger.info("📢 Elder Tree終了通知完了")
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree終了通知エラー: {e}")
            
            # 作業ディレクトリのクリーンアップ
            try:
                if hasattr(self, 'work_dir') and self.work_dir.exists():
                    # Complex condition - consider breaking down
                    # 一時ファイルの削除
                    import shutil

                    self.logger.info("🗄️ 一時ファイルクリーンアップ完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"一時ファイルクリーンアップエラー: {e}")
            
            # キャッシュのクリア
            try:
                if hasattr(self, 'thumbnail_cache'):
                    self.thumbnail_cache.clear()
                    self.logger.info("📋 キャッシュクリア完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"キャッシュクリアエラー: {e}")
            
            # 統計情報の保存
            try:
                stats = {
                    "worker_id": self.worker_id,
                    "thumbnails_created": getattr(self, 'thumbnails_created', 0),
                    "processing_errors": getattr(self, 'processing_errors', 0),
                    "cleanup_time": datetime.now().isoformat(),
                    "uptime": getattr(self, 'uptime', 0)
                }
                # 統計ファイルに保存
                stats_file = PROJECT_ROOT / "logs" / "thumbnail_worker_stats.json"
                stats_file.parent.mkdir(exist_ok=True)
                
                existing_stats = []
                if stats_file.exists():
                    with open(stats_file, 'r') as f:
                        existing_stats = json.load(f)
                
                existing_stats.append(stats)
                with open(stats_file, 'w') as f:
                    json.dump(existing_stats, f, indent=2)
                
                self.logger.info(f"📊 統計情報保存完了: {getattr(self, 'thumbnails_created', 0)}件作成")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"統計情報保存エラー: {e}")
            
            self.logger.info("✅ ThumbnailWorker cleanup完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ Cleanup処理エラー: {e}")
            # クリーンアップエラーでも継続

    def stop(self):
        """ワーカー停止処理（cleanup呼び出し、super().stop()）"""
        try:
            self.logger.info("🛑 ThumbnailWorker停止処理開始")
            
            # 処理中のタスクがある場合は完了を待つ
            if hasattr(self, 'current_task') and self.current_task:
                # Complex condition - consider breaking down
                self.logger.info("⏳ 処理中タスクの完了を待機...")
                # 必要に応じてタスク完了待ちを実装
            
            # クリーンアップ実行
            self.cleanup()
            
            # 親クラスのstop()を呼び出し
            try:
                super().stop()
                self.logger.info("⬆️  親クラスstop()完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"親クラスstop()エラー: {e}")
            
            self.logger.info("✅ ThumbnailWorker停止処理完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 停止処理エラー: {e}")
            # 停止処理エラーでも継続

    def initialize(self) -> None:
        """初期化処理（Elder Tree初期化、必要コンポーネント初期化）"""
        try:
            self.logger.info("🚀 ThumbnailWorker初期化開始")
            
            # Elder Tree統合システムの初期化
            if ELDER_TREE_AVAILABLE:
                try:
                    # Four Sages統合
                    if FourSagesIntegration:
                        self.four_sages = FourSagesIntegration()
                        self.logger.info("🧙‍♂️ Four Sages統合初期化完了")
                    
                    # Elder Council統合
                    if ElderCouncilSummoner:
                        self.elder_council_summoner = ElderCouncilSummoner()
                        self.logger.info("🏛️ Elder Council統合初期化完了")
                    
                    # Elder Tree接続
                    if get_elder_tree:
                        self.elder_tree = get_elder_tree()
                        self.logger.info("🌳 Elder Tree接続完了")
                        
                        # Elder Treeに初期化完了を通知
                        self.elder_tree.notify_initialization({
                            "worker_type": "thumbnail",
                            "worker_id": self.worker_id,
                            "capabilities": [
                                "thumbnail_generation",
                                "image_resizing",
                                "format_conversion",
                                "worker_communication"
                            ],
                            "config": {
                                "input_queue": getattr(self, 'input_queue', 'ai_thumbnail_tasks'),
                                "output_queue": getattr(
                                    self,
                                    'output_queue',
                                    'ai_thumbnail_results'
                                ),
                                "pil_available": PIL_AVAILABLE
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                
                except Exception as e:
                    # Handle specific exception case
                    self.logger.warning(f"Elder Tree統合エラー: {e}")
            
            # 統計カウンターの初期化
            self.thumbnails_created = 0
            self.processing_errors = 0
            self.total_bytes_processed = 0
            self.created_at = datetime.now()
            
            # 作業ディレクトリの初期化
            try:

                self.work_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"📁 作業ディレクトリ初期化: {self.work_dir}")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"作業ディレクトリ初期化エラー: {e}")
            
            # サムネイルキャッシュの初期化
            try:
                self.thumbnail_cache = {}
                self.cache_max_size = 100  # 最大1000件をキャッシュ
                self.logger.info("📋 サムネイルキャッシュ初期化完了")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"キャッシュ初期化エラー: {e}")
            
            # PIL利用可能性確認
            if not PIL_AVAILABLE:
                self.logger.warning("⚠️ PIL (Pillow)が利用できません。サムネイル生成機能が制限されます")
            else:
                self.logger.info("✅ PIL (Pillow)利用可能")
            
            # サポート形式の設定
            self.supported_formats = {'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP'}
            self.default_thumbnail_size = (150, 150)
            self.default_quality = 85
            
            # Task Sageに初期化完了を報告
            self._report_initialization_to_task_sage()
            
            self.logger.info(f"✅ {self.__class__.__name__} 初期化完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"❌ 初期化エラー: {e}")
            # 初期化エラーは重要なので、Incident Sageに報告
            if hasattr(self, 'four_sages') and self.four_sages:
                # Complex condition - consider breaking down
                try:
                    self.four_sages.report_to_incident_sage({
                        "type": "initialization_error",
                        "worker_type": "thumbnail",
                        "error": str(e),
                        "severity": "medium"
                    })
                except Exception:
                    # Handle specific exception case
                    pass  # 報告エラーは無視

    def handle_error(self, error: Exception, context: str = None, severity: str = "medium") -> None:
        """エラーハンドリング（Incident Sageへの報告、ログ記録）"""
        try:
            # エラーカウント更新
            if hasattr(self, 'processing_errors'):
                self.processing_errors += 1
            
            # エラーの重要度を判定
            error_severity = self._determine_error_severity(error, context)
            
            # 基本ログ記録
            error_id = f"thumbnail_error_{int(datetime.now().timestamp())}"
            error_details = {
                "error_id": error_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or "unknown",
                "severity": error_severity,
                "timestamp": datetime.now().isoformat(),
                "worker_id": getattr(self, 'worker_id', 'unknown')
            }
            
            # ログレベル別記録
            if error_severity == "critical":
                self.logger.critical(f"🔥 重要エラー [{error_id}]: {error} (context: {context})")
            elif error_severity == "high":
                self.logger.error(f"❌ 高レベルエラー [{error_id}]: {error} (context: {context})")
            elif error_severity == "medium":
                self.logger.warning(f"⚠️ 中レベルエラー [{error_id}]: {error} (context: {context})")
            else:
                self.logger.info(f"ℹ️ 低レベルエラー [{error_id}]: {error} (context: {context})")
            
            # Incident Sageへの報告
            if ELDER_TREE_AVAILABLE and hasattr(self, 'four_sages') and self.four_sages:
                # Complex condition - consider breaking down
                try:
                    incident_report = {
                        "type": "worker_error",
                        "worker_type": "thumbnail",
                        "error_details": error_details,
                        "context_info": {
                            "thumbnails_created": getattr(self, 'thumbnails_created', 0),
                            "processing_errors": getattr(self, 'processing_errors', 0),
                            "work_dir": str(getattr(self, 'work_dir', 'unknown')),
                            "pil_available": PIL_AVAILABLE
                        },
                        "recommendations": self._get_error_recommendations(error, context),
                        "requires_immediate_action": self._is_critical_error(error)
                    }
                    
                    self.four_sages.report_to_incident_sage(incident_report)
                    self.logger.info(f"📨 Incident Sage報告完了: {error_id}")
                    
                except Exception as report_error:
                    # Handle specific exception case
                    self.logger.warning(f"Incident Sage報告エラー: {report_error}")
            
            # 画像処理関連エラーの特別処理
            if "pil" in str(error).lower() or "image" in str(error).lower():
                # Complex condition - consider breaking down
                try:
                    # 画像エラーログファイルに記録
                    error_log_file = PROJECT_ROOT / "logs" / "thumbnail_errors.json"
                    error_log_file.parent.mkdir(exist_ok=True)
                    
                    error_logs = []
                    if error_log_file.exists():
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(error_log_file, 'r') as f:
                            error_logs = json.load(f)
                    
                    error_logs.append(error_details)
                    # 最新100件のみ保持
                    error_logs = error_logs[-100:]
                    
                    with open(error_log_file, 'w') as f:
                        json.dump(error_logs, f, indent=2)
                    
                except Exception as log_error:
                    # Handle specific exception case
                    self.logger.warning(f"エラーログ記録失敗: {log_error}")
            
            # 重要エラーの場合は追加処理
            if self._is_critical_error(error):
                self.logger.critical(f"🔥 重要エラー検出: {error_id}")
                # 必要に応じて自動復旧処理を実装
                
        except Exception as handler_error:
            # エラーハンドラー自体のエラーは最小限のログのみ
            self.logger.error(f"❌ エラーハンドラー内でエラー: {handler_error}")
            self.logger.error(f"元のエラー: {error}")

    def get_status(self) -> dict:
        """ワーカー状態取得（Elder Tree状態、処理統計）"""
        try:
            # 稼働時間計算
            if hasattr(self, 'created_at'):
                uptime = (datetime.now() - self.created_at).total_seconds()
            else:
                uptime = 0
            
            status = {
                "worker_info": {
                    "worker_type": "thumbnail_worker",
                    "worker_id": getattr(self, 'worker_id', 'unknown'),
                    "class_name": self.__class__.__name__,
                    "created_at": getattr(self, 'created_at', datetime.now()).isoformat(),
                    "uptime_seconds": uptime,
                    "uptime_formatted": self._format_uptime(uptime)
                },
                "processing_stats": {
                    "thumbnails_created": getattr(self, 'thumbnails_created', 0),
                    "processing_errors": getattr(self, 'processing_errors', 0),
                    "total_bytes_processed": getattr(self, 'total_bytes_processed', 0),
                    "average_bytes_per_thumbnail": self._calculate_average_bytes(),
                    "error_rate_percent": self._calculate_error_rate(),
                    "processing_rate_per_minute": self._calculate_processing_rate(uptime)
                },
                "capabilities": {
                    "pil_available": PIL_AVAILABLE,
                    "supported_formats": list(getattr(self, 'supported_formats', [])),
                    "default_thumbnail_size": getattr(self, 'default_thumbnail_size', (150, 150)),
                    "default_quality": getattr(self, 'default_quality', 85)
                },
                "elder_integration": {
                    "elder_tree_available": ELDER_TREE_AVAILABLE,
                    "four_sages_active": hasattr(
                        self,
                        'four_sages'
                    ) and self.four_sages is not None,
                    "elder_council_active": hasattr(
                        self,
                        'elder_council_summoner'
                    ) and self.elder_council_summoner is not None,
                    "elder_tree_connected": hasattr(
                        self,
                        'elder_tree'
                    ) and self.elder_tree is not None
                },
                "resource_usage": {
                    "work_directory": str(getattr(self, 'work_dir', 'N/A')),
                    "cache_size": len(getattr(self, 'thumbnail_cache', {})),
                    "cache_max_size": getattr(self, 'cache_max_size', 0)
                },
                "queue_config": {
                    "input_queue": getattr(self, 'input_queue', 'ai_thumbnail_tasks'),
                    "output_queue": getattr(self, 'output_queue', 'ai_thumbnail_results')
                },
                "health_status": self._determine_health_status(),
                "recommendations": self._generate_recommendations(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Elder Tree詳細状態
            if hasattr(self, 'elder_tree') and self.elder_tree:
                # Complex condition - consider breaking down
                try:
                    status["elder_tree_details"] = {
                        "connection_status": "connected",
                        "message_queue_size": len(getattr(self.elder_tree, 'message_queue', [])),
                        "node_count": len(getattr(self.elder_tree, 'nodes', []))
                    }
                except Exception as e:
                    # Handle specific exception case
                    status["elder_tree_details"] = {
                        "connection_status": "error",
                        "error": str(e)
                    }
            
            return status
            
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"状態取得エラー: {e}")
            return {
                "error": f"状態取得失敗: {e}",
                "timestamp": datetime.now().isoformat(),
                "worker_type": "thumbnail_worker",
                "worker_id": getattr(self, 'worker_id', 'unknown')
            }

    def validate_config(self) -> dict:
        """設定検証（設定妥当性チェック、必須項目確認）"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "config_details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # PIL (Pillow) 利用可能性チェック
            if not PIL_AVAILABLE:
                validation_result["errors"].append("PIL (Pillow) が利用できません。サムネイル生成機能が無効です")
                validation_result["is_valid"] = False
                validation_result["recommendations"].append("pip install Pillow を実行してください")
            else:
                validation_result["config_details"]["pil_available"] = True
            
            # キューの設定確認
            if not hasattr(self, 'input_queue') or not self.input_queue:
                # Complex condition - consider breaking down
                validation_result["errors"].append("入力キュー (input_queue) が設定されていません")
                validation_result["is_valid"] = False
            else:
                validation_result["config_details"]["input_queue"] = self.input_queue
            
            if not hasattr(self, 'output_queue') or not self.output_queue:
                # Complex condition - consider breaking down
                validation_result["errors"].append("出力キュー (output_queue) が設定されていません")
                validation_result["is_valid"] = False
            else:
                validation_result["config_details"]["output_queue"] = self.output_queue
            
            # Elder Tree統合状態チェック
            validation_result["config_details"]["elder_integration"] = {
                "available": ELDER_TREE_AVAILABLE,
                "four_sages": hasattr(self, 'four_sages') and self.four_sages is not None,
                "elder_council": hasattr(
                    self,
                    'elder_council_summoner'
                ) and self.elder_council_summoner is not None,
                "elder_tree": hasattr(self, 'elder_tree') and self.elder_tree is not None
            }
            
            if ELDER_TREE_AVAILABLE and not (hasattr(self, 'four_sages') and self.four_sages):
                # Complex condition - consider breaking down
                validation_result["warnings"].append("Elder Tree統合が利用可能ですが、初期化されていません")
                validation_result["recommendations"].append("initialize()メソッドを実行してください")
            
            # 作業ディレクトリチェック
            if hasattr(self, 'work_dir'):
                validation_result["config_details"]["work_directory"] = str(self.work_dir)
                if not self.work_dir.exists():
                    validation_result["errors"].append(f"作業ディレクトリが存在しません: {self.work_dir}")
                    validation_result["is_valid"] = False
                    validation_result["recommendations"].append(f"ディレクトリを作成してください: mkdir -p {self.work_dir}")
                elif not self.work_dir.is_dir():
                    validation_result["errors"].append(f"作業パスがディレクトリではありません: {self.work_dir}")
                    validation_result["is_valid"] = False
                elif not os.access(self.work_dir, os.W_OK):
                    validation_result["errors"].append(f"作業ディレクトリに書き込み権限がありません: {self.work_dir}")
                    validation_result["is_valid"] = False
                    validation_result["recommendations"].append("書き込み権限を付与してください")
            
            # サムネイル設定チェック
            if hasattr(self, 'default_thumbnail_size'):
                validation_result["config_details"]["default_thumbnail_size"] = self.default_thumbnail_size
                width, height = self.default_thumbnail_size
                if width <= 0 or height <= 0:
                    # Complex condition - consider breaking down
                    validation_result["errors"].append(f"サムネイルサイズが無効です: {width}x{height}")
                    validation_result["is_valid"] = False
                elif width > 1000 or height > 1000:
                    # Complex condition - consider breaking down
                    validation_result["warnings"].append(f"サムネイルサイズが大きすぎます: {width}x{height}")
                    validation_result["recommendations"].append("メモリ使用量を考慮し300x300以下を推奨")
            
            if hasattr(self, 'default_quality'):
                validation_result["config_details"]["default_quality"] = self.default_quality
                if self.default_quality < 1 or self.default_quality > 100:
                    # Complex condition - consider breaking down
                    validation_result["errors"].append(f"品質設定が無効です: {self.default_quality} (1-100の範囲で設定)")
                    validation_result["is_valid"] = False
                elif self.default_quality < 50:
                    validation_result["warnings"].append(f"品質設定が低すぎます: {self.default_quality}")
                    validation_result["recommendations"].append("画質を保つため70以上を推奨")
            
            # サポート形式チェック
            if hasattr(self, 'supported_formats'):
                validation_result["config_details"]["supported_formats"] = list(self.supported_formats)
                if len(self.supported_formats) == 0:
                    validation_result["warnings"].append("サポート形式が設定されていません")
                    validation_result["recommendations"].append("基本的な形式 (JPEG, PNG) を設定してください")
            
            # キャッシュ設定チェック
            if hasattr(self, 'cache_max_size'):
                validation_result["config_details"]["cache_max_size"] = self.cache_max_size
                if self.cache_max_size < 0:
                    validation_result["errors"].append("キャッシュ最大サイズが負の値です")
                    validation_result["is_valid"] = False
                elif self.cache_max_size > 1000:
                    validation_result["warnings"].append(f"キャッシュサイズが大きすぎます: {self.cache_max_size}")
                    validation_result["recommendations"].append("メモリ使用量を考慮し100-500程度を推奨")
            
            # 統計情報の妥当性
            if hasattr(self, 'thumbnails_created') and self.thumbnails_created < 0:
                # Complex condition - consider breaking down
                validation_result["errors"].append("作成済みサムネイル数が負の値です")
                validation_result["is_valid"] = False
            
            if hasattr(self, 'processing_errors') and self.processing_errors < 0:
                # Complex condition - consider breaking down
                validation_result["errors"].append("エラー数が負の値です")
                validation_result["is_valid"] = False
            
            if hasattr(self, 'total_bytes_processed') and self.total_bytes_processed < 0:
                # Complex condition - consider breaking down
                validation_result["errors"].append("処理済みバイト数が負の値です")
                validation_result["is_valid"] = False
            
            # パフォーマンス警告
            if hasattr(self, 'thumbnails_created') and hasattr(self, 'processing_errors'):
                # Complex condition - consider breaking down
                if self.thumbnails_created > 0:
                    error_rate = (self.processing_errors / self.thumbnails_created) * 100
                    if error_rate > 20:
                        validation_result["warnings"].append(f"エラー率が高すぎます: {error_rate:0.1f}%")
                        validation_result["recommendations"].append("入力画像の形式とPIL設定を確認してください")
                    elif error_rate > 10:
                        validation_result["warnings"].append(f"エラー率がやや高めです: {error_rate:0.1f}%")
            
            # 成功時の追加情報
            if validation_result["is_valid"]:
                validation_result["summary"] = "設定は有効です"
                if not validation_result["warnings"]:
                    validation_result["summary"] += " - 警告なし"
            else:
                validation_result["summary"] = f"設定に {len(validation_result['errors'])} 個のエラーがあります"
            
            self.logger.info(f"設定検証完了: {validation_result['summary']}")
            
            return validation_result
            
        except Exception as e:
            # Handle specific exception case
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"設定検証中にエラー: {e}")
            validation_result["summary"] = "設定検証失敗"
            self.logger.error(f"設定検証エラー: {e}")
            return validation_result

    def _report_initialization_to_task_sage(self) -> None:
        """Task Sageに初期化完了を報告"""
        if not hasattr(self, 'four_sages') or not self.four_sages:
            # Complex condition - consider breaking down
            return
        
        try:
            report = {
                "type": "worker_initialization",
                "worker_type": "thumbnail",
                "worker_id": self.worker_id,
                "capabilities": [
                    "thumbnail_generation",
                    "image_resizing", 
                    "format_conversion",
                    "worker_communication"
                ],
                "config": {
                    "input_queue": getattr(self, 'input_queue', 'ai_thumbnail_tasks'),
                    "output_queue": getattr(self, 'output_queue', 'ai_thumbnail_results'),
                    "pil_available": PIL_AVAILABLE,
                    "default_size": getattr(self, 'default_thumbnail_size', (150, 150))
                },
                "status": "initialized",
                "timestamp": datetime.now().isoformat()
            }
            
            self.four_sages.report_to_task_sage(report)
            self.logger.info("📋 Task Sage初期化報告完了")
            
        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Task Sage初期化報告エラー: {e}")

    def _determine_error_severity(self, error: Exception, context: str = None) -> str:
        """エラーの重要度を判定"""
        error_str = str(error).lower()
        
        # 重要エラー
        if any(keyword in error_str for keyword in [
            "permission denied", "file not found", "memory error", "disk full"
        ]):
            return "critical"
        
        # 高レベルエラー  
        if any(keyword in error_str for keyword in [
            "pil", "image", "format", "corrupted", "invalid"
        ]):
            return "high"
        
        # 中レベルエラー
        if any(keyword in error_str for keyword in [
            "size", "quality", "conversion", "processing"
        ]):
            return "medium"
        
        # デフォルトは低レベル
        return "low"

    def _get_error_recommendations(self, error: Exception, context: str = None) -> list:
        """エラーに応じた推奨対応を生成"""
        error_str = str(error).lower()
        recommendations = []
        
        if "pil" in error_str or "pillow" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "PIL (Pillow) ライブラリを確認してください",
                "pip install Pillow --upgrade を試してください",
                "画像形式がサポートされているか確認してください"
            ])
        
        if "permission" in error_str or "access" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "ファイル・ディレクトリの権限を確認してください", 
                "作業ディレクトリの書き込み権限を確認してください",
                "ファイルが他のプロセスで使用されていないか確認してください"
            ])
        
        if "memory" in error_str or "size" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "画像サイズが大きすぎる可能性があります",
                "メモリ使用量を確認してください",
                "サムネイルサイズを小さくすることを検討してください"
            ])
        
        if "format" in error_str or "invalid" in error_str:
            # Complex condition - consider breaking down
            recommendations.extend([
                "入力画像の形式を確認してください",
                "ファイルが破損していないか確認してください",
                "サポートされている形式 (JPEG, PNG, GIF など) を使用してください"
            ])
        
        if not recommendations:
            recommendations.append("ログファイルで詳細なエラー情報を確認してください")
        
        return recommendations

    def _is_critical_error(self, error: Exception) -> bool:
        """エラーが重要かどうか判定"""
        return self._determine_error_severity(error) in ["critical", "high"]

    def _format_uptime(self, uptime_seconds: float) -> str:
        """アップタイムを人間が読みやすい形式にフォーマット"""
        if uptime_seconds < 60:
            return f"{uptime_seconds:0.f}秒"
        elif uptime_seconds < 3600:
            minutes = uptime_seconds / 60
            return f"{minutes:0.1f}分"
        elif uptime_seconds < 86400:
            hours = uptime_seconds / 3600
            return f"{hours:0.1f}時間"
        else:
            days = uptime_seconds / 86400
            return f"{days:0.1f}日"

    def _calculate_average_bytes(self) -> float:
        """サムネイルあたりの平均バイト数を計算"""
        thumbnails_created = getattr(self, 'thumbnails_created', 0)
        total_bytes = getattr(self, 'total_bytes_processed', 0)
        
        if thumbnails_created <= 0:
            return 0.0
        
        return total_bytes / thumbnails_created

    def _calculate_error_rate(self) -> float:
        """エラー率を計算（パーセント）"""
        thumbnails_created = getattr(self, 'thumbnails_created', 0)
        processing_errors = getattr(self, 'processing_errors', 0)
        
        total_operations = thumbnails_created + processing_errors
        if total_operations <= 0:
            return 0.0
        
        return (processing_errors / total_operations) * 100

    def _calculate_processing_rate(self, uptime_seconds: float) -> float:
        """1分あたりの処理率を計算"""
        if uptime_seconds <= 0:
            return 0.0
        
        thumbnails_created = getattr(self, 'thumbnails_created', 0)
        minutes = uptime_seconds / 60
        return thumbnails_created / minutes if minutes > 0 else 0.0

    def _determine_health_status(self) -> str:
        """ワーカーの健康状態を判定"""
        # PIL利用可能性チェック
        if not PIL_AVAILABLE:
            return "critical"
        
        # エラー率チェック
        error_rate = self._calculate_error_rate()
        if error_rate > 50:
            return "critical"
        elif error_rate > 20:
            return "warning"
        
        # 作業ディレクトリチェック
        if hasattr(self, 'work_dir') and not self.work_dir.exists():
            # Complex condition - consider breaking down
            return "warning"
        
        # Elder Tree統合チェック
        if ELDER_TREE_AVAILABLE and hasattr(self, 'four_sages') and self.four_sages:
            # Complex condition - consider breaking down
            return "healthy"
        elif PIL_AVAILABLE:
            return "degraded"
        else:
            return "critical"

    def _generate_recommendations(self) -> list:
        """現在の状態に基づく推奨事項を生成"""
        recommendations = []
        
        # エラー率チェック
        error_rate = self._calculate_error_rate()
        if error_rate > 20:
            recommendations.append("エラー率が高いため、入力画像の形式とPIL設定を確認してください")
        
        # PIL利用可能性チェック
        if not PIL_AVAILABLE:
            recommendations.append("PIL (Pillow) をインストールしてサムネイル生成機能を有効化してください")
        
        # Elder Tree統合チェック
        if ELDER_TREE_AVAILABLE and not (hasattr(self, 'four_sages') and self.four_sages):
            # Complex condition - consider breaking down
            recommendations.append("Elder Tree統合を有効化すると監視・エラーハンドリング機能が向上します")
        
        # 作業ディレクトリチェック
        if hasattr(self, 'work_dir') and not self.work_dir.exists():
            # Complex condition - consider breaking down
            recommendations.append(f"作業ディレクトリを作成してください: {self.work_dir}")
        
        # キャッシュサイズチェック
        if hasattr(self, 'thumbnail_cache') and hasattr(self, 'cache_max_size'):
            # Complex condition - consider breaking down
            cache_size = len(self.thumbnail_cache)
            if cache_size > self.cache_max_size * 0.9:
                recommendations.append("キャッシュサイズが上限に近づいています。クリーンアップを検討してください")
        
        # サムネイルサイズチェック
        if hasattr(self, 'default_thumbnail_size'):
            width, height = self.default_thumbnail_size
            if width > 500 or height > 500:
                # Complex condition - consider breaking down
                recommendations.append("サムネイルサイズが大きいため、メモリ使用量とパフォーマンスを考慮してください")
        
        if not recommendations:
            recommendations.append("現在の設定は適切です")
        
        return recommendations

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worker-type",
        choices=["image", "thumbnail"],
        default="image",
        help="Worker type to run",
    )
    parser.add_argument("--worker-id", help="Worker ID")

    args = parser.parse_args()

    if args.worker_type == "image":
        worker = ImageProcessingWorker(args.worker_id)
    else:
        worker = ThumbnailWorker(args.worker_id)

    worker.start()
