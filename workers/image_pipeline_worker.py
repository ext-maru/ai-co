#!/usr/bin/env python3
"""
イメージ処理パイプラインワーカー
ワーカー間通信を使って複数のワーカーが協調動作する例
"""

import sys
import json
import base64
from pathlib import Path
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available, image processing disabled")
import io

sys.path.append(str(Path(__file__).parent.parent))

from core.base_worker_ja import BaseWorker
from core.config import get_config
from core.common_utils import EMOJI
from core import msg
from core.worker_communication import CommunicationMixin


class ImageProcessingWorker(BaseWorker, CommunicationMixin):
    """画像処理を行うワーカー"""
    
    def __init__(self, worker_id=None):
        super().__init__(
            worker_type='image_processor',
            worker_id=worker_id
        )
        # キューの設定
        self.input_queue = 'ai_image_tasks'
        self.output_queue = 'ai_image_results'
        # CommunicationMixinの初期化が必要な場合
        if hasattr(self, 'setup_communication'):
            self.setup_communication()
        self._register_handlers()
        
    def _register_handlers(self):
        """メッセージハンドラーを登録"""
        self.register_message_handler('process_image', self.handle_process_image)
        self.register_message_handler('resize_request', self.handle_resize_request)
        
    def process_message(self, ch, method, properties, body):
        """メッセージ処理"""
        try:
            # ワーカー間通信メッセージをチェック
            data = json.loads(body)
            if self.process_worker_message(data):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            # 通常のタスク処理
            task = json.loads(body)
            self.logger.info(f"{EMOJI['process']} Processing image task: {task.get('task_id')}")
            
            image_path = task.get('image_path')
            operations = task.get('operations', [])
            
            # 画像を読み込み
            image = Image.open(image_path)
            
            # 各操作を実行
            for operation in operations:
                if operation['type'] == 'resize':
                    # リサイズ処理
                    size = operation.get('size', (800, 600))
                    image = image.resize(size, Image.Resampling.LANCZOS)
                    
                    # サムネイル生成ワーカーに通知
                    self.send_to_worker(
                        'thumbnail',
                        'create_thumbnail',
                        {
                            'original_path': image_path,
                            'size': (150, 150),
                            'task_id': task.get('task_id')
                        }
                    )
                    
                elif operation['type'] == 'rotate':
                    angle = operation.get('angle', 0)
                    image = image.rotate(angle, expand=True)
                    
                elif operation['type'] == 'filter':
                    # フィルター処理ワーカーに委譲
                    self.send_to_worker(
                        'filter',
                        'apply_filter',
                        {
                            'image_data': self._image_to_base64(image),
                            'filter_type': operation.get('filter_type'),
                            'task_id': task.get('task_id')
                        },
                        priority='high'
                    )
                    
            # 処理完了を通知
            output_path = str(Path(image_path).with_suffix('.processed.jpg'))
            image.save(output_path, quality=95)
            
            # PMワーカーに通知
            self.send_to_worker(
                'pm',
                'file_created',
                {
                    'file_path': output_path,
                    'task_id': task.get('task_id'),
                    'file_type': 'processed_image'
                }
            )
            
            # 結果を送信
            result = {
                'task_id': task.get('task_id'),
                'status': 'completed',
                'output_file': output_path,
                'operations_applied': len(operations)
            }
            
            self.send_result(result)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.handle_error(e, "process_message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
    def handle_process_image(self, data):
        """他のワーカーからの画像処理リクエスト"""
        self.logger.info(f"{EMOJI['receive']} Received image processing request")
        
        try:
            image_data = data.get('image_data')
            operations = data.get('operations', [])
            
            # Base64から画像に変換
            image = self._base64_to_image(image_data)
            
            # 処理実行
            for op in operations:
                if op['type'] == 'resize':
                    image = image.resize(op['size'], Image.Resampling.LANCZOS)
                elif op['type'] == 'rotate':
                    image = image.rotate(op['angle'], expand=True)
                    
            # 結果を返す
            return {
                'status': 'success',
                'image_data': self._image_to_base64(image)
            }
            
        except Exception as e:
            self.logger.error(f"{EMOJI['error']} Processing failed: {str(e)}")
            return {'status': 'error', 'message': str(e)}
            
    def handle_resize_request(self, data):
        """リサイズリクエストを処理"""
        image_path = data.get('image_path')
        size = data.get('size', (800, 600))
        
        try:
            image = Image.open(image_path)
            resized = image.resize(size, Image.Resampling.LANCZOS)
            
            output_path = str(Path(image_path).with_suffix(f'.{size[0]}x{size[1]}.jpg'))
            resized.save(output_path)
            
            return {
                'status': 'success',
                'output_path': output_path,
                'size': size
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def _image_to_base64(self, image):
        """画像をBase64エンコード"""
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
        
    def _base64_to_image(self, base64_data):
        """Base64から画像に変換"""
        image_data = base64.b64decode(base64_data)
        return Image.open(io.BytesIO(image_data))


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
            worker_type='thumbnail',
            worker_id=worker_id,
            input_queue='ai_thumbnail_tasks',
            output_queue='ai_thumbnail_results'
        )
        self.setup_communication()
        self.register_message_handler('create_thumbnail', self.handle_create_thumbnail)
        
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
            original_path = data.get('original_path')
            size = data.get('size', (150, 150))
            
            image = Image.open(original_path)
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumb_path = str(Path(original_path).with_suffix('.thumb.jpg'))
            image.save(thumb_path, quality=85)
            
            # 完了を通知
            self.send_to_worker(
                'result',
                'thumbnail_created',
                {
                    'original_path': original_path,
                    'thumbnail_path': thumb_path,
                    'size': size,
                    'task_id': data.get('task_id')
                }
            )
            
            return {'status': 'success', 'thumbnail_path': thumb_path}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
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
    parser.add_argument('--worker-type', 
                       choices=['image', 'thumbnail'],
                       default='image',
                       help='Worker type to run')
    parser.add_argument('--worker-id', help='Worker ID')
    
    args = parser.parse_args()
    
    if args.worker_type == 'image':
        worker = ImageProcessingWorker(args.worker_id)
    else:
        worker = ThumbnailWorker(args.worker_id)
        
    worker.start()
