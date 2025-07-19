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
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
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

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass


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
            return {"status": "error", "message": str(e)}

    def create_thumbnail_task(self, task):
        """通常のサムネイル生成タスク"""
        # 実装...
        pass

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass


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
